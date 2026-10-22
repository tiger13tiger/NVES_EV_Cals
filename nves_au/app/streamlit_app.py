"""Streamlit app: upload a fleet CSV (or use the synthetic demo fleet), see
the credit position and penalty exposure, run what-if scenarios, and view a
supplier league table. UI available in English and Simplified Chinese.

Run with: streamlit run nves_au/app/streamlit_app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from nves_au.app.i18n import translator
from nves_au.config import ConfigError, load_regulation_config
from nves_au.engine import (
    aggregate_by_supplier_type_year,
    aggregate_by_supplier_year,
    run_ledger,
    score_fleet,
)
from nves_au.engine.scenario import ScenarioAdjustment, run_scenario
from nves_au.io import dataframe_to_vehicle_records, vehicle_records_to_dataframe
from nves_au.synthetic import generate_demo_fleet

st.set_page_config(page_title="NVES-AU", page_icon="🚗", layout="wide")

if "scenario_adjustments" not in st.session_state:
    st.session_state.scenario_adjustments = []

config = load_regulation_config()

# Widget state for "lang_selector" is owned entirely by Streamlit via `key`
# -- deriving `index=` from session_state on every run (instead of this)
# makes Streamlit hash a different widget identity each time the language
# changes, which silently breaks switching back and forth.
with st.sidebar:
    lang_choice = st.selectbox(
        "Language / 语言", ["English", "简体中文"], key="lang_selector"
    )
st.session_state.lang = "en" if lang_choice == "English" else "zh"

t = translator(st.session_state.lang)

st.title(t("title"))
st.caption(t("subtitle"))
st.info(t("disclaimer"))

with st.expander(t("unverified_expander")):
    notes = config.unverified_notes()
    st.table(pd.DataFrame([{"file": n.file, "confidence": n.confidence} for n in notes]))

with st.sidebar:
    st.header(t("sidebar_datasource"))
    datasource = st.radio(
        t("sidebar_datasource"),
        [t("datasource_demo"), t("datasource_upload")],
        label_visibility="collapsed",
    )

fleet = None
if datasource == t("datasource_demo"):
    years = st.sidebar.multiselect(t("demo_years_label"), options=[2025], default=[2025])
    fleet = generate_demo_fleet(years=tuple(years or [2025]))
else:
    uploaded = st.sidebar.file_uploader(t("upload_label"), type="csv", help=t("upload_help"))
    if uploaded is not None:
        raw_df = pd.read_csv(uploaded, keep_default_na=False)
        try:
            fleet = dataframe_to_vehicle_records(raw_df)
        except (ValueError, TypeError) as exc:
            st.error(t("calc_error") + str(exc))

if not fleet:
    st.warning(t("no_data_warning"))
    st.stop()

st.subheader(t("fleet_preview"))
st.dataframe(vehicle_records_to_dataframe(fleet), width="stretch")

try:
    results = score_fleet(fleet, config)
except ConfigError as exc:
    st.error(t("calc_error") + str(exc))
    st.stop()

positions = aggregate_by_supplier_year(results)
_, outcomes = run_ledger(positions, config)

league_df = pd.DataFrame(
    [
        {
            t("col_supplier"): o.supplier,
            t("col_year"): o.performance_year,
            t("col_iev"): round(o.iev_units, 1),
            t("col_outstanding"): round(o.outstanding_debit_units, 1),
            t("col_balance"): round(o.bank_balance_after, 1),
            t("col_notice"): round(o.penalty.infringement_notice_aud),
            t("col_max_penalty"): round(o.penalty.max_civil_penalty_aud),
        }
        for o in outcomes
    ]
).sort_values(t("col_iev"))

st.subheader(t("league_table_title"))
st.dataframe(league_df, width="stretch", hide_index=True)
st.bar_chart(league_df.set_index(t("col_supplier"))[t("col_iev")])

with st.expander(t("breakdown_title")):
    type_summaries = aggregate_by_supplier_type_year(results)
    breakdown_df = pd.DataFrame(
        [
            {
                t("col_supplier"): s.supplier,
                "Type": s.vehicle_type,
                t("col_year"): s.performance_year,
                t("col_units"): s.total_units_sold,
                t("col_iev"): round(s.net_units, 1),
            }
            for s in type_summaries
        ]
    )
    st.dataframe(breakdown_df, width="stretch", hide_index=True)

st.divider()
st.subheader(t("scenario_title"))
st.caption(t("scenario_help"))

suppliers = sorted({r.supplier for r in fleet})
col1, col2, col3, col4 = st.columns(4)
with col1:
    sel_supplier = st.selectbox(t("scenario_supplier"), suppliers)
models_for_supplier = sorted({r.model_name for r in fleet if r.supplier == sel_supplier})
with col2:
    sel_model = st.selectbox(t("scenario_model"), models_for_supplier)
years_for_model = sorted(
    {r.performance_year for r in fleet if r.supplier == sel_supplier and r.model_name == sel_model}
)
with col3:
    sel_year = st.selectbox(t("scenario_year"), years_for_model)
with col4:
    delta = st.number_input(t("scenario_delta"), value=0, step=50)

if st.button(t("scenario_add")):
    st.session_state.scenario_adjustments.append(
        ScenarioAdjustment(
            supplier=sel_supplier,
            model_name=sel_model,
            performance_year=sel_year,
            delta_units=int(delta),
        )
    )

if st.session_state.scenario_adjustments:
    st.write(t("scenario_adjustments_title"))
    st.table(
        pd.DataFrame(
            [
                {
                    t("col_supplier"): a.supplier,
                    t("scenario_model"): a.model_name,
                    t("col_year"): a.performance_year,
                    t("scenario_delta"): a.delta_units,
                }
                for a in st.session_state.scenario_adjustments
            ]
        )
    )

    run_col, clear_col = st.columns(2)
    run_clicked = run_col.button(t("scenario_run"), type="primary")
    if clear_col.button(t("scenario_clear")):
        st.session_state.scenario_adjustments = []
        st.rerun()

    if run_clicked:
        try:
            comparison = run_scenario(fleet, st.session_state.scenario_adjustments, config)
        except (ValueError, ConfigError) as exc:
            st.error(t("calc_error") + str(exc))
        else:
            rows = [
                {
                    t("col_supplier"): supplier,
                    t("col_year"): year,
                    f"{t('col_iev')} ({t('scenario_before')})": round(before.iev_units, 1),
                    f"{t('col_iev')} ({t('scenario_after')})": round(after.iev_units, 1),
                    f"{t('col_notice')} ({t('scenario_before')})": round(
                        before.penalty.infringement_notice_aud
                    ),
                    f"{t('col_notice')} ({t('scenario_after')})": round(
                        after.penalty.infringement_notice_aud
                    ),
                }
                for (supplier, year), (before, after) in comparison.by_supplier_year().items()
            ]
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

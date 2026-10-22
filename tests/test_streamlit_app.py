"""Exercises the Streamlit app via Streamlit's AppTest harness: these are
the closest thing to an automated UI smoke test for this project, covering
the "launches with synthetic data and no setup" acceptance criterion and
the language toggle / scenario interaction flows.
"""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP_PATH = str(Path(__file__).resolve().parent.parent / "nves_au" / "app" / "streamlit_app.py")


def test_app_loads_with_demo_data_by_default():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    assert not at.exception
    assert at.title[0].value == "NVES-AU: Fleet CO2 Credit & Penalty Calculator"
    assert len(at.dataframe) >= 2  # fleet preview + league table


def test_language_toggle_switches_and_switches_back():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)

    at.sidebar.selectbox[0].set_value("简体中文").run()
    assert not at.exception
    assert at.session_state["lang"] == "zh"
    assert "NVES-AU：" in at.title[0].value

    at.sidebar.selectbox[0].set_value("English").run()
    assert not at.exception
    assert at.session_state["lang"] == "en"
    assert at.title[0].value.startswith("NVES-AU: ")


def test_upload_datasource_without_file_shows_warning():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    upload_label = at.sidebar.radio[0].options[1]
    at.sidebar.radio[0].set_value(upload_label).run()
    assert not at.exception
    assert len(at.warning) == 1


def test_scenario_add_and_run_flow():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)

    at.number_input[0].set_value(500).run()
    at.button[0].click().run()  # "Add adjustment" (only button before this)
    assert not at.exception

    run_button = next(b for b in at.button if b.label == "Run scenario")
    run_button.click().run()
    assert not at.exception

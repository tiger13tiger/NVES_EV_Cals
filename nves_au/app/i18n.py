"""Minimal English / Simplified Chinese dictionary for the Streamlit app."""

from __future__ import annotations

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "title": "NVES-AU: Fleet CO2 Credit & Penalty Calculator",
        "subtitle": "An open-source toolkit for Australia's New Vehicle Efficiency Standard.",
        "disclaimer": (
            "**Not legal or tax advice.** Several regulation parameters used here are "
            "unverified against primary legislation. Confirm every figure against the "
            "NVES Act, Rules and Regulator guidance before relying on it for a "
            "compliance decision."
        ),
        "unverified_expander": "Which parameters are unverified?",
        "sidebar_language": "Language",
        "sidebar_datasource": "Fleet data",
        "datasource_demo": "Use synthetic demo fleet",
        "datasource_upload": "Upload my own fleet CSV",
        "upload_label": "Upload fleet CSV",
        "upload_help": "Columns: supplier, model_name, performance_year, adr_category, "
        "body_on_frame, braked_tow_rating_kg, miro_kg, co2_g_km, units_sold",
        "demo_years_label": "Demo performance year(s)",
        "fleet_preview": "Fleet data preview",
        "league_table_title": "Supplier league table (combined Type 1 + Type 2 position)",
        "col_supplier": "Supplier",
        "col_year": "Year",
        "col_units": "Units sold",
        "col_iev": "IEV (units)",
        "col_outstanding": "Outstanding debit",
        "col_balance": "Bank balance",
        "col_notice": "Infringement notice (AUD)",
        "col_max_penalty": "Max civil penalty (AUD)",
        "breakdown_title": "Breakdown by vehicle type",
        "scenario_title": "Scenario simulator",
        "scenario_help": (
            "Add one or more sales-mix adjustments below, then run the scenario to "
            "compare the resulting credit position against the loaded fleet."
        ),
        "scenario_supplier": "Supplier",
        "scenario_model": "Model",
        "scenario_year": "Performance year",
        "scenario_delta": "Change in units sold (+/-)",
        "scenario_add": "Add adjustment",
        "scenario_adjustments_title": "Pending adjustments",
        "scenario_clear": "Clear adjustments",
        "scenario_run": "Run scenario",
        "scenario_before": "Before",
        "scenario_after": "After",
        "no_data_warning": (
            "Upload a fleet CSV, or switch to the synthetic demo fleet, to continue."
        ),
        "calc_error": "Could not calculate: ",
    },
    "zh": {
        "title": "NVES-AU：车队二氧化碳信用额与罚款计算器",
        "subtitle": "一款开源工具，用于澳大利亚新车能效标准（NVES）合规计算。",
        "disclaimer": (
            "**本工具不构成法律或税务建议。** 此处使用的部分监管参数尚未与官方立法原文核实。"
            "在用于合规决策之前，请对照 NVES 法案、规则及监管机构指引核实每一项数值。"
        ),
        "unverified_expander": "哪些参数尚未核实？",
        "sidebar_language": "语言",
        "sidebar_datasource": "车队数据",
        "datasource_demo": "使用合成演示车队数据",
        "datasource_upload": "上传我自己的车队 CSV",
        "upload_label": "上传车队 CSV 文件",
        "upload_help": "列：supplier, model_name, performance_year, adr_category, "
        "body_on_frame, braked_tow_rating_kg, miro_kg, co2_g_km, units_sold",
        "demo_years_label": "演示合规年度",
        "fleet_preview": "车队数据预览",
        "league_table_title": "供应商排行榜（Type 1 + Type 2 合并结果）",
        "col_supplier": "供应商",
        "col_year": "年度",
        "col_units": "销量",
        "col_iev": "IEV（单位）",
        "col_outstanding": "未抵消欠账",
        "col_balance": "信用余额",
        "col_notice": "罚款通知金额（澳元）",
        "col_max_penalty": "最高民事罚款（澳元）",
        "breakdown_title": "按车辆类型细分",
        "scenario_title": "情景模拟器",
        "scenario_help": "在下方添加一项或多项销量调整，然后运行情景模拟，"
        "与当前车队数据比较信用额结果。",
        "scenario_supplier": "供应商",
        "scenario_model": "车型",
        "scenario_year": "合规年度",
        "scenario_delta": "销量变化（正负皆可）",
        "scenario_add": "添加调整",
        "scenario_adjustments_title": "待运行的调整项",
        "scenario_clear": "清除调整项",
        "scenario_run": "运行情景模拟",
        "scenario_before": "调整前",
        "scenario_after": "调整后",
        "no_data_warning": "请上传车队 CSV，或切换到合成演示车队数据以继续。",
        "calc_error": "计算失败：",
    },
}


def translator(lang: str):
    table = TRANSLATIONS.get(lang, TRANSLATIONS["en"])

    def t(key: str) -> str:
        return table.get(key, key)

    return t

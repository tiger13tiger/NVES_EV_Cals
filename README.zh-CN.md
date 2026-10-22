# nves-au

[![CI](https://github.com/tiger13tiger/NVES_EV_Cals/actions/workflows/ci.yml/badge.svg)](https://github.com/tiger13tiger/NVES_EV_Cals/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

一款面向澳大利亚**新车能效标准（New Vehicle Efficiency Standard, NVES）**的开源
Python 工具包：计算车队按质量调整后的二氧化碳目标、信用额/欠账状况、信用额台账
（含 3 年到期与转让）以及预估罚款风险，并可运行销量结构的"假设情景"模拟。
面向车企本地的单个分析师设计，无需走采购或 IT 审批流程即可 `pip install` 使用。
完全本地运行，不会将任何数据发送给第三方。

**[English README](README.md)**

> ## ⚠️ 本工具不构成法律或税务建议
>
> 本工具是个人/作品集性质的开源项目，并非合规产品。工具所使用的部分监管参数
> **尚未与官方立法原文核实**（详见下方表格及
> [`config/regulation/README.md`](config/regulation/README.md)）。在用于任何
> 真实的合规、财务或法律决策之前，请务必对照 NVES 法案（2024）、NVES 规则、
> 部长决定（Ministerial Determination）以及 NVES 监管机构的指引核实每一项数值。

## 60 秒快速上手

```bash
git clone https://github.com/tiger13tiger/NVES_EV_Cals.git
cd NVES_EV_Cals
pip install -e ".[app]"

nves-au demo                    # 在合成演示车队上运行完整计算流程
streamlit run nves_au/app/streamlit_app.py   # 打开交互式仪表盘
```

使用你自己的数据而非合成车队：

```bash
nves-au calc examples/sample_fleet.csv
nves-au simulate examples/sample_fleet.csv examples/sample_scenario.yaml
```

你的车队 CSV 文件需要包含以下列（参见 `examples/sample_fleet.csv`）：

```
supplier, model_name, performance_year, adr_category, body_on_frame,
braked_tow_rating_kg, miro_kg, co2_g_km, units_sold
```

## 功能概览

1. **计算引擎** —— 将每台车辆分类为 Type 1（乘用车）或 Type 2（轻型商用车），
   计算其按质量调整后的二氧化碳目标及信用额/欠账贡献；按供应商、年度和车辆类型
   汇总；以 3 年有效期对信用额进行台账管理，优先核销最早批次的欠账，支持供应商
   间转让，并预估罚款风险（罚款通知与最高民事罚款费率）。
2. **情景模拟器** —— 模拟销量结构变化（例如 A 车型 +1,000 台，B 车型 -500 台），
   并比较调整前后的信用额状况与罚款风险。
3. **公共数据加载器** —— 用于加载 Green Vehicle Guide（车型 CO2/质量数据）和
   NVES 监管机构业绩报告的辅助工具，均附有明确的手动下载步骤说明
   （见 `nves_au/data/`）。
4. **合成数据生成器** —— 可重复生成的虚构多品牌车队数据，用于演示和测试
   （不含任何真实厂商数据）。
5. **Streamlit 应用** —— 上传 CSV 或使用合成车队数据，查看信用额状况，运行情景
   模拟，查看供应商排行榜。界面支持英文和简体中文。
6. **命令行工具（CLI）** —— `nves-au demo`、`nves-au calc <文件>`、
   `nves-au simulate <文件> <情景.yaml>`。

完整公式、引用来源与手工核算示例见：
**[docs/methodology.md](docs/methodology.md)**（英文）。

## 参数核实状态

引擎所使用的每一项数值都存放在 [`config/regulation/`](config/regulation/) 目录下
的带版本号 YAML 文件中，附有来源网址、获取日期和置信度标记——绝不在计算逻辑中
硬编码。本项目的研究阶段仅使用了网络搜索工具（该会话中对 legislation.gov.au 和
nvesregulator.gov.au 的直接访问被网络策略阻止），因此下表应视为你自行核实的
起点，而非已完成的审计结论。

| 参数 | 状态 | 说明 |
|---|---|---|
| 2025-2029 年基准二氧化碳目标（Type 1 和 Type 2） | ✅ 已确认 | 两个独立来源一致 |
| 质量调整公式（`ET = HL + MAF×(DM−RM)`） | ✅ 已确认 | 引用 NVES 法案第 21 条 |
| 质量调整系数 / 参考 MIRO，**2025 年** | ✅ 已确认 | 基础设施部指引文件 |
| 质量调整系数 / 参考 MIRO，**2026 年及以后** | ⛔ 未设置 | 有意留空——该部文件称未来可能通过部长决定调整 |
| 质量分界点（下限/上限，kg） | ✅ 已确认 | |
| Type 1 / Type 2 分类规则 | ⚠️ 未核实 | MA/MB/MC 对 NA/NB1，以及 MC 车型按牵引力重新归类为 Type 2 的规则 |
| IEV / FEV 核算方式 | 🟡 部分确认 | 公式本身有旁证；"1 单位 = 1 克/公里 × 1 辆车"为本项目自行推断 |
| 罚款通知（每单位 $50）与最高民事罚款（每单位 $100） | ✅ 已确认 | 两个独立来源一致 |
| 信用额有效期（3 年） | ⚠️ 未核实 | 仅有 1-2 个二级来源 |

"已确认"与"未核实"的具体含义见
[`config/regulation/README.md`](config/regulation/README.md)，完整来源列表见
[docs/methodology.md](docs/methodology.md)（英文）。

## 项目结构

```
nves_au/
  config.py        监管参数加载器（读取 config/regulation/*.yaml）
  engine/          分类、目标计算、汇总、信用额台账、情景模拟器
  data/            Green Vehicle Guide 与 NVES 监管机构数据加载器（基于手动下载）
  synthetic/       虚构演示车队生成器
  app/             Streamlit 仪表盘（中英双语）
  cli.py           Typer 命令行工具
config/regulation/ 带版本号的监管参数及其来源
tests/             单元测试，含手工核算示例
examples/          示例车队 CSV 与情景 YAML
docs/              methodology.md（方法论说明，英文）
```

## 开发

```bash
pip install -e ".[dev,app]"
ruff check nves_au tests
pytest --cov=nves_au
```

详见 [CONTRIBUTING.md](CONTRIBUTING.md)（英文）。修改
`config/regulation/` 中的任何参数前请务必注意：每一项参数变更都需要提供来源
网址、获取日期和置信度标记。

## 许可证

Apache License 2.0 —— 详见 [LICENSE](LICENSE)。本项目全程未使用任何专有 DMS
数据结构、前雇主数据或代码。

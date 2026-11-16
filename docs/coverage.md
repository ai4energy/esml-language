# SPEC 覆盖与规范↔实现缺口索引

> 本文件记录两件事：**① 校验口径与暂缺示例的规范条款**；**② 规范 / XSD / 引擎之间的已知缺口索引**（本仓只管规范、XSD 与示例，不改引擎代码）。

---

## 0. 口径与基线

- 仓内八道机判闸门由 `make check` 统一执行（定义见 [Makefile](../Makefile)）：
  `roots`、`examples`、`drift`、`elements`、`attr`、`engine-examples`、`spec-elements`、`expectations`。
- `make strict` 在 `validate_examples.py` 基础上追加「撤通配判别力闸」，并与 [strict-baseline.txt](audit/strict-baseline.txt) 比对：当前基线为 **3**（即 [metadata.esml](../D-skeleton/metadata.esml)、[provenance.esml](../D-skeleton/provenance.esml)、[doc-ref.esml](../D-skeleton/doc-ref.esml)，因 XSD 1.0 `UPA` 约束下 `MetadataType` 须以 `xs:any` 放行任意元数据子元素）。超过基线则退出码非 0。
- 涉及跨仓引擎检查的三道闸（`drift` / `engine-examples` / `expectations`）在未配置引擎目录（`ESML_ENGINE_DIR` 且默认回退路径不存在）时打印跳过并退出 0。

---

## 1. 暂缺示例的规范条款

下表列出 `SPEC.md` 中在示例目录无直接落点的条款；其中多数为纯散文/约定条款，其余**真实缺口**统一归档于下文 `§5`：

| 条款 | 性质 | 裁决 |
|---|---|---|
| §1 引言与设计原则 | 散文 | 不单列示例（§1.1 文档骨架已有示例） |
| §4.0a 方程形状决定因果计划 | 作者须知 | 散文约定，不单列示例 |
| §6.2 | 保留空号 | 保持章节号稳定，见 §5.4 |
| §6.3 分层归属（库 vs 案例） | 散文 | 不单列示例（`X-use/` 归 §6.1） |
| §9 展平与命名 / §10 求解语义 / §12 标准库 / §13 分层验收 / §14.4–§14.5 / 附录 A·C·D·G·H·J·L·M·N | 散文/验收 | 不单列示例 |
| §11 物性插件 | 真条款 | **缺口**：尚无 canonical 插件挂载语法与示例，见 §5.1 |
| §6.9 `<description>` 元素形态 | 表内自注暂缺示例 | 记账 |
| 附录 B（续）· 顶层裸 `<set>` | 真条款 | **缺口**：schema 只收 `<scope><set/>`，裸 `<set>` 不生效，见 §5.2 |
| 附录 F9 高指标 DAE（Pantelides） | 真条款 | **缺口**：降阶算法无独立 canonical 语法标记，见 §5.1 |
| 附录 F10 外部 I/O 端口壳 | 真条款 | **缺口**：当前示例仅覆盖 F2 信号连接，尚无 F10 单机端口壳示例，见 §5.1 |
| `ConstSetMember` 一等成员类型 | 真条款 | **缺口**：`xsd/` 尚未定义该类型，见 §5.3 |

---

## 5. 规范 ↔ Schema / 引擎缺口（记账，本仓不修引擎）

### 5.1 无 canonical 语法落点的三条条款

| 条款 | 现状 | 裁决 |
|---|---|---|
| §11 物性插件 | 示例中无对应挂载语法（`<use>` / 外部调用之外无独立 plugin 语法） | **留缺口**：需先在规范与 XSD 立定 canonical 语法，再补示例 |
| 附录 F9 高指标 DAE（Pantelides） | 属求解期结构降阶算法，文档语法层尚无独立可测标记 | **留缺口**：不造“无语义特征”的假绿示例 |
| 附录 F10 外部 I/O 经信号口 / 端口壳 | [signal-causal.esml](../L4-port/signal-causal.esml) 覆盖的是 F2 信号连接，尚无 F10 单机端口壳完整闭环示例 | **留缺口**：待后续规范修订与对应语法落地 |

### 5.2 附录 B（续）「顶层 `SET`」：schema 不许、实现不生效

`SPEC.md` 附录 B（续）描述了不带 `<scope instance=...>` 的顶层全局 `<set path value/>`；但 `xsd/esml-canonical-basic.xsd` 中 `SystemType` 的 `<sets>` 仅允许 `<scope>` 子元素（裸 `<set>` 被 XSD 拒绝），且实测求解时裸 `<set>` 对实例参数不生效（仅 `<scope instance=...>` 生效）。按 README「文字与 schema 出现分歧时，以 schema 为准」原则，此处属**文字超前于 schema**，不补假绿示例。

### 5.3 接受但零效应 / 实现未落地的项目

| 条目 | 现状说明 | 处理 |
|---|---|---|
| `ConstSetMember` | `SPEC.md` 提及一等成员类型，但 `xsd/` 未声明，示例中亦无覆盖 | 留缺口 |
| 附录 F2 信号因果护栏 | 引擎 `check` 对 `input↔input`、`output↔output`、端口变量同名不一致仍放行 | [signal-causal.esml](../L4-port/signal-causal.esml) 头注已标明 |
| `<param>`（`esml-canonical-compute.xsd`） | 已有示例 [hyperparams.esml](../T-tasks/hyperparams.esml)；`esml check` 与 `esml solve` 现均通过 | 已闭合 |
| `domain`（`<instance>` / `<modelType>` / `<system>`） | `esml check` 通过但求解期零读取；`<portType domain=...>` 则被引擎 F1 响亮拒收 | [attr-acceptance.tsv](../tools/attr-acceptance.tsv) 记 `no-example` / `rejected-legacy` |
| `side`（`<annotation><port>`） | `PortMarkType` 下图形标注可过 `check` 但无求解语义；模型侧 `<port side=...>` 被 F1 拒收 | [attr-acceptance.tsv](../tools/attr-acceptance.tsv) 记 `no-example` / `rejected-legacy` |
| `MetadataType` `xs:any`（`##targetNamespace` + `##other`） | XSD 1.0 UPA 禁止在同内容模型中混用同名元素与 `##targetNamespace` 通配 | `by-design`；见 §0 strict 基线 `3` |
| `<replace>` / `<moveTo>` / `<jumpTo>`（`<initialisationProcedures>`） | 默认 `esml solve` / `esml simulate` CLI 路径不消费初始化过程，写与不写同解 | 不另补假绿示例 |
| `<observe>` | 仅在显式传入 CLI `--observe` 时生效，默认输出忽略 | [observe-list.esml](../L0-type-unit/observe-list.esml) 头注已标明 |
| `<connectRules>` | `esml check` 仅校验语法条目，未联动 `connectClass` 且求解期未消费 | 见 §5.13 与 [engine-example-debt.tsv](../tools/engine-example-debt.tsv) |

### 5.4 章节编号 `§6.2` 保留空号

`SPEC.md` §6 中跳过 `§6.2`（`§6.0` / `§6.1` / `§6.3`）。为维持既有条款编号引用稳定，故意保留空号不重排。

### 5.5 附录 B（续）「FOR 按序集迭代」与「FOR 循环」

- 字面整数区间迭代（`in="1..3"`）对应 [for-in.esml](../L1-expr-equation/for-in.esml)；
- 序集迭代（`in="Species"`，绑定 1-based 序位）对应 [for-over-orderedset.esml](../L1-expr-equation/for-over-orderedset.esml)。两者形态与语义不同，勿混。

### 5.6 `<body>` 与 `<derivative>` 互斥：schema 拒、实现放行

`xsd/esml-canonical-basic.xsd` 中 `FunctionType` 将 `<body>` 与 `<derivative>` 置于 `xs:choice maxOccurs="1"`。四份负例（`L1-expr-equation/{derivativesymbol,noderivative,partial-derivative,zeroderivative}.esml`）在 canonical XSD 下必须报错；引擎 `check` 目前尚未实施该互斥检查，示例头注已统一标明为 **schema 负例**。

### 5.7 `esml simulate` 不消费 `<schedule>`

[call-method-body.esml](../L9-method-schedule/call-method-body.esml) 演示附录 K `<schedule>` 段前 `<call method>`；当前 `esml simulate` CLI 路径按命令行 `tspan` 积分并跳过 `<schedule>`，属校验工具能力缺口，已在示例头注说明。

### 5.8 语言仓与引擎仓校验边界

语言仓只维护 `SPEC.md`、`xsd/*.xsd`、示例语料及 `tools/`/`docs/` 台账闸门；引擎仓内部的参考对账快照或历史 conformance 编号归引擎仓自行维护，不在本仓修改或复制。

### 5.9 `§6.5` 条件组件：「参数」操作数当前无处声明

`SPEC.md` §6.5 允许 `<instance condition="..."/>` 在构建期静态折叠：
- `xsd/esml-canonical-basic.xsd` 的 `SystemType` 无 `<parameters>` 子元素；
- 实例自身模型参数在条件求值阶段尚未展开落表；
- 因此当前仅**常量表达式**（如 `L5-instance/instance-condition.esml`）与**序集成员序号**可静态判定；引用参数会在构建期报错（如负例 [instance-condition-undecidable.esml](../L5-instance/instance-condition-undecidable.esml)）。参数形态落地需后续同步修订 `SPEC.md`、XSD 与引擎。

### 5.10 算法段 `<for>` 拼写分歧

方程级 `<for>` 使用 `in="1..3"`；而算法段 `<algorithm>` 内 `<for>` 在引擎侧只消费 `range="a:b"` 且不带 `<body>` 壳，错误拼法可能静默得到错误结果。该分歧已记入 [engine-drift.tsv](../tools/engine-drift.tsv)，示例详见 [algorithm-for.esml](../L8-function/algorithm-for.esml)。

### 5.11 XSD 已声明而引擎未完全对齐的项

本节记录**语言层（`SPEC.md` + `xsd/`）已声明，但引擎尚有缺口**的项（与 `§5.12` / `§5.13` 方向严格区分）：

- **属性 `<type role=…>`（`VariableType`）**：`xsd/esml-canonical-basic.xsd` 的 `VariableType` 仍保留可选 `role` 属性声明，但引擎六轴单轨规定角色只属于 `<variable role="state|algebraic|discrete">`，对 `<type role=…>` 报 F1 Legacy。
- **属性 `phase` / `aPart` / `bPart` / `nominal` / `quantity` 等**：属 XSD 已声明但引擎 `F7` 拒收项，逐条裁决见 [engine-drift.tsv](../tools/engine-drift.tsv) 与 [attr-acceptance.tsv](../tools/attr-acceptance.tsv)。

此前曾在 `check` / `solve` 层被拒收的 `<literal>`、`<vary>`、`<while>`、`<hyperParams><param>` 及 `<transition synchronize=…>` 已随引擎 v1.9.4 收口，对应债行已按闭合判据从台账移除或转为 `accepted`。

### 5.12 属性面判别力边界（`lax` `xs:anyAttribute`）

- 本仓 XSD 中 `201` 处 `<xs:anyAttribute processContents="lax"/>` 全部为 `lax`（`17 / 106` 个命名 complexType 仅靠通配放行属性，无显式属性声明）。
- 按替代式测试 [aliases.tsv](../tools/aliases.tsv) 中的 `26` 条 legacy 属性拼法，XSD 仅能因核心属性 `use="required"` 拒收 `3` 条（`11.5%`：`max-time`、`model-type`、`component`），其余 `23` 条（`88.5%`）在 XSD 层放行，依赖引擎 F7/F1 拦截。
- **与 `§5.11` 的区别**：`§5.11` 是「XSD 声明 + 引擎拒」（引擎更窄）；`§5.12` 是「XSD 通配放行 + 引擎拒」（XSD 更宽）。

### 5.13 求解层引擎债与台账索引

**三角分界**：`§5.11` = XSD 收、check 拒；`§5.12` = XSD 通配收、check 拒；**`§5.13` = XSD 收且 `esml check` 收（`errors=0`），但 `esml solve` / `simulate` 失败**。

当前普查与债务台账指针（实时数据以两张 `.tsv` 为准）：
- **非负例求解普查**（[solve-smoke.tsv](../tools/solve-smoke.tsv)，非闸门）：`158` 件非负例中 `143 ok`、`8 ok-simulate`、`6 na`（`4 na-no-system` + `2 na-artifact`）、`1 fail`（`fail-engine-debt`）。
  - `na-artifact`（2 件）：`extern-cabi.esml`、`derivative-analytic.esml`（需外部动态库工件，非引擎缺陷）。
- **引擎可运行性闸门台账**（[engine-example-debt.tsv](../tools/engine-example-debt.tsv)，`4` 行）：
  - `stage=check`（3 行）：`D-skeleton/data-scenario.esml`（`<scenario tasks=...>`），`X-use/use-library.esml` 与 `X-use/use-multi-library.esml`（不带 `-L` 库根时的预期缺库失败）。
  - `stage=solve`（1 行）：`L6-connect/connect-rules.esml`（求解期不消费 `<connectRules>` 导致结构奇异）。

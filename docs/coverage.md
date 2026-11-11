# SPEC 覆盖对账表

本表回答一个问题：**`SPEC.md` 的每个编号承诺的语法点，仓内有没有一份可运行的示例
守着它？反过来，仓内每一份示例，指向的是不是真有一条规范条文？**

数字全部由 [`docs/validate_examples.py`](validate_examples.py) 机验产出，命令见文末
「复现命令」；本文件只做解释与裁决，不引入机器算不出来的判断。

- **BEFORE** = 本分支的起点 `58d2c0a`（用 `git archive` 取的快照）。
- **AFTER** = 本分支 HEAD。

> **时效层（W27 2026-11-11）**：本文件有两层口径——**历史层**（§1 总量对照表与 §2、
> §3、§4：记录 `58d2c0a` → 分支 HEAD 的 diff 对账，数字是当时的，不再随树变；§6 的
> 提交清单已不再逐条维护，以 `git log` 为准，见 §6）与**现状层**（§5 缺口台账与 §7 复现
> 命令：数字按**当下树**重算，2026-11-11 基线 = `union/lang-batch` `4760eee`（W33 重算，
> 旧基线 `0b34503`），示例 **189** 份（PASS 165 / 负例 24 / 非负例失败 0，
> `docs/validate_examples.py` 实测）/ 负例 **24** / 非负例 **165** 份）。W27 修现状层的
> 过时数字（§5.1/§5.3/§5.11/§7），W33 随示例从 170 → 177 重算同一批现状层数字，
> W51 2026-11-11 随示例从 177 → 189 重算同一批现状层数字；
> 历史层的旧数字（136 / 141 / 164 / 153 / 37 编号等）是当时对账事实，保留原值。

---

## 0. 口径与机器判据

判据全部来自本仓 README 的既有规矩，不新造：

| 判据 | 出处 | 机器怎么算 |
|---|---|---|
| XML Schema 是可机验的基准 | README「canonical XML 是正统语法……以 schema 为准」 | 每份 `.esml` 按**根元素**路由到 `xsd/` 下对应的 canonical schema；先剥掉 `<!--…-->` 注释再取根元素（否则 Author 注释里的 `<mingtao@xjtu.edu.cn>` 会把全部文件误路由到宽松入口 schema） |
| 负例**预期失败** | README「文件名含 `probe`、或头部注明为负例的文档**预期失败**」 | 负例失败**不算**缺陷；非负例失败才算 |
| 拼写单轨 | README「同一语义只有一种写法，其余写法一律报错，不做静默兼容」 | 稀有元素普查：某示例独有的语法点（全局出现 ≤3 次）若在 `SPEC.md` 里查无点名，即「无 SPEC 依据」 |
| 章节编号稳定，schema 与示例都按编号引用 | README「阅读规范」 | 示例头部写「规范条文：§x.y（…）」，反向聚合出「每个编号 → 示例清单」 |

五道检查的完整输出见「复现命令」。

---

## 1. 总量对照

| 指标 | BEFORE `58d2c0a` | AFTER（预期，W4 合入后） | 判据 |
|---|---:|---:|---|
| 示例件数 | 136 | **164** | `find . -name '*.esml'` |
| XSD 机验 · PASS | 130 | **153** | 检查 1 |
| XSD 机验 · 负例按预期失败 | 5 | 5 | 检查 1 |
| XSD 机验 · **非负例失败** | **1** | **0** | 检查 1 |
| SPEC → 示例：点名且存在的路径 | 0 | **70** | 检查 2 |
| SPEC → 示例：悬空路径 | 0 | **0** | 检查 2 |
| 示例头部指名规范条文 | 0 / 136 | **161 / 164** | 检查 3 |
| 被指名的编号数 | 0 | **37** | 检查 3 |
| **无 SPEC 依据的示例** | **54 / 136** | **2 / 164** | 检查 4 |
| `SPEC.md` 的 ```xml 段 · 自足文档级 | 0 段（`§6.8` 那段 **FAIL**） | **2 段全过** | 检查 5 |
| `SPEC.md` 的 ```xml 段 · 子元素片段 | 15 段 | 15 段 | 检查 5 |
| 引擎 `esml check -L <库根>` | — | rc0=**135** / 负例 6 / 非负例失败 **0** | 引擎 |

> BEFORE 的「头部指名 0/136」用的是本分支确立的新格式（`规范条文：§x.y（…）。`）。
> 旧格式下 BEFORE 只有 1 份（`D-skeleton/skeleton-doc.esml` 正文里一句「规范 §4」）
> 会被算作指名。

**BEFORE 唯一的非负例 XSD 失败**是 `T-tasks/tasks.esml`（`<tasks>` 元素不在
`esml-canonical-basic.xsd` 的模型面上）——已在 `ca8efc7` 里把 `§6.8` 的外壳写进
规范与 schema，示例随之转正。

---

## 2. 正向对账：`SPEC.md` → 示例

`SPEC.md` 正文里点名的仓内示例路径共 **70 条**，**全部存在，悬空 0 条**。
按目录归并：

| 目录 | 被点名 | 路径 |
|---|---:|---|
| `D-skeleton/` | 3 | `metadata.esml` `provenance.esml` `solutionparameters.esml` |
| `L0-type-unit/` | 6 | `observe-list.esml` `record-type.esml` `type-unit.esml` `typesgeneric.esml` `typesthermal.esml` `units-group.esml` |
| `L1-expr-equation/` | 1 | `ifelse.esml` |
| `L2-discrete/` | 7 | `case-branch.esml` `clock-functions.esml` `clock-sample.esml` `initialisationprocedure-advance.esml` `initialisationprocedures.esml` `reset-transition.esml` `state-machine.esml` |
| `L3-model/` | 4 | `component-probe.esml` `extends.esml` `if.esml` `selector-values.esml` |
| `L4-port/` | 1 | `signal-causal.esml` |
| `L5-instance/` | 2 | `instance-condition.esml` `instance-condition-undecidable.esml` |
| `L6-connect/` | 1 | `connect-rules.esml` |
| `L7-partition/` | 4 | `domain.esml` `partition-chain.esml` `partition-crosslink.esml` `subsystem-crosslink.esml` |
| `L8-function/` | 2 | `foreign-object.esml` `locals.esml` |
| `L9-method-schedule/` | 2 | `fixed-preset.esml` `stop.esml` |
| `T-tasks/` | 37 | 计算任务表一族（`task-*.esml` / `tasks*.esml` / `checks.esml` / `tolerance.esml` 等） |
| **合计** | **70** | |

`SPEC.md` 里另有 7 条「示意路径 / 管线记法」（`models/ctrl.sys.esml`、
`models/thermal-chain.esml`、`.comp.esml`、`.sys.esml` 等），它们指的是**库或
外部管线**里的文件，不是本仓示例，机器判据不判对错，只列出备查。

---

## 3. 反向对账：每个编号的「应当有示例」清单

机验口径：示例头部「规范条文：…」一行点名的**全部**编号（以 `＋` 分隔的
多条逐条计入）。共 **37 个编号 / 164 份示例**。

| 编号 · 条文 | 件数 | 示例（仓内路径） |
|---|---:|---|
| §1.1 §1.1（文档骨架与 `<metadata>`） ／ §1.1（文档骨架） | 8 | `D-skeleton/{data-scenario.esml,doc-ref.esml,esml-coordinate.esml,metadata.esml,provenance.esml,skeleton-doc.esml,skeleton-full.esml,skeleton-minimal.esml}` |
| §14.1 §14.1（canonical 元素） | 4 | `L1-expr-equation/{derivativesymbol.esml,partial-derivative.esml,zeroderivative.esml}` `L3-model/partials.esml` |
| §14.2 §14.2（求导三档） | 1 | `L1-expr-equation/noderivative.esml` |
| §14.3 §14.3（C ABI 类型映射） | 1 | `L8-function/extern-cabi.esml` |
| §2 §2（收紧词法） | 1 | `L3-model/component-probe.esml` |
| §3 §3（单位表分组） ／ §3（类型按类别包裹） ／ §3（类型系统） ／ §3（记录类型 `<recordTypes>`） | 6 | `L0-type-unit/{record-type.esml,type-unit.esml,typesgeneric.esml,typesthermal.esml,units-group.esml,variable-roles.esml}` |
| §4 §4（组件） | 1 | `L3-model/modeltype-basic.esml` |
| §4.0 §4.0（继承 `<extendsFrom>`） | 3 | `L3-model/{extends.esml,extendsfrom-child.esml,extendsfrom.esml}` |
| §4.1 §4.1（复合组件） | 1 | `L3-model/members-composite.esml` |
| §5 §5（端口） | 10 | `L4-port/{constant.esml,flow-potential.esml,flow.esml,port-category-size.esml,port-roles-io.esml,porttype-electrical.esml,porttype-thermal.esml,potential.esml}` `L4-portvar/{flow.esml,potential.esml}` |
| §6 §6（系统、实例与参数覆盖） | 3 | `L5-instance/{component-alias.esml,instance-basic.esml,instance-count.esml}` |
| §6.0 §6.0（实例参数覆盖：scope / set / path） | 3 | `L2-discrete/initial.esml` `L5-instance/{scope-nested.esml,scope-set.esml}` |
| §6.1 §6.1（标准库坐标引用） | 4 | `X-use/{systemref-libroot.esml,use-f12-mismatch.esml,use-library.esml,use-multi-library.esml}` |
| §6.10 §6.10（系统级观察与预设） | 2 | `L0-type-unit/observe-list.esml` `L9-method-schedule/fixed-preset.esml` |
| §6.4 §6.4（partition / crosslink） ／ §6.4（计算域声明） | 5 | `L5-instance/subsystem.esml` `L7-partition/{domain.esml,partition-chain.esml,partition-crosslink.esml,subsystem-crosslink.esml}` |
| §6.5 §6.5（条件组件） | 2 | `L5-instance/{instance-condition-undecidable.esml,instance-condition.esml}` |
| §6.6 §6.6（系统级方程） | 1 | `L4-port/port-roles-io.esml` |
| §6.7 §6.7（系统初始化过程） | 2 | `L2-discrete/{initialisationprocedure-advance.esml,initialisationprocedures.esml}` |
| §6.8 §6.8（工程包装容器） | 1 | `T-tasks/tasks.esml` |
| §6.9 §6.9（计算任务表） ／ §6.9（顶层 `<solutionParameters>` 段） | 46 | `D-skeleton/solutionparameters.esml` `L1-expr-equation/{expr.esml,reference.esml}` `L5-instance/setpoint.esml` `T-tasks/{actuator.esml,benchmarks.esml,check.esml,checks.esml,constraint-expr.esml,control-vars.esml,controlled-control-vars.esml,controlled.esml,controller-gains.esml,controller.esml,dataset.esml,design-vars.esml,feature.esml,features.esml,gains.esml,hyperparams.esml,method-tuning.esml,metric-tolerancepct.esml,mpc-matrices.esml,outputlist.esml,perturb-distribution.esml,reference.esml,sampling.esml,sensor.esml,setpoint.esml,solutionparameters.esml,status.esml,surrogate-model.esml,target.esml,targets.esml,task-constraint.esml,task-control.esml,task-estimation.esml,task-optimize.esml,task-sensitivity.esml,task-simulate.esml,task-surrogate.esml,task-validation.esml,task-vendor-text.esml,tasks-seven.esml,tasks-auxiliary.esml,test-data.esml,tolerance.esml}` |
| §7 §7（分段表达式） ／ §7（向量归约内建） ／ §7（数组下标与切片） ／ §7（方程类别与语义） ／ §7（算法段） ／ §7（表达式内建） | 13 | `L1-expr-equation/{array-index-probe.esml,array-index.esml,axis-reduce-probe.esml,axis-reduce.esml,builtins-complex.esml,builtins-delay.esml,builtins-expr.esml,builtins-math.esml,equation-basic.esml,ifelse.esml,oob-probe.esml,shape-mismatch-probe.esml}` `T-tasks/algorithm.esml` |
| §7.1 §7.1（状态机与时钟） | 5 | `L2-discrete/{clock-functions.esml,clock-sample.esml,reset-transition.esml,state-machine.esml,transition-attrs.esml}` |
| §8 §8（连接语义） | 2 | `L6-connect/{connect-basic.esml,connect-canonical.esml}` |
| 附录B（续） 附录 B（续）— CASE 多分支 ／ 附录 B（续）— FOR 循环 ／ 附录 B（续）— FOR 按序集迭代 ／ 附录 B（续）— ORDERED_SET 序集 ／ 附录 B（续）— SELECTOR ／ 附录 B（续）— 模型级 IF | 7 | `L0-type-unit/ordered-set.esml` `L1-expr-equation/{for-in.esml,for-over-orderedset.esml}` `L2-discrete/case-branch.esml` `L3-model/{if.esml,selector-values.esml}` `L7-partition/orderedsets.esml` |
| 附录F1 附录 F1（stream 流股） | 2 | `L4-port/{port-stream.esml,stream.esml}` |
| 附录F2 附录 F2（信号 causal 连接护栏） | 1 | `L4-port/signal-causal.esml` |
| 附录F3 附录 F3（事件语义糖） | 4 | `L2-discrete/{elsewhen.esml,when-assign.esml,when-multiple.esml,when-reinit.esml}` |
| 附录F4 附录 F4（连接规则表） | 1 | `L6-connect/connect-rules.esml` |
| 附录F5 附录 F5（on_load 预设方法） | 1 | `L9-method-schedule/onload.esml` |
| 附录F6 附录 F6（自由度 FIX） | 1 | `L9-method-schedule/fixed-preset.esml` |
| 附录F7 附录 F7（自由度 FREE） | 1 | `L9-method-schedule/methods-run.esml` |
| 附录F7b 附录 F7b（METHOD RUN 子过程） | 1 | `L9-method-schedule/methods-run.esml` |
| 附录F8 附录 F8（vector 归约内建） | 3 | `L1-expr-equation/{array-index.esml,axis-reduce.esml,builtins-expr.esml}` |
| 附录I 附录 I（用户函数与黑盒） | 3 | `L8-function/{foreign-object.esml,function-expr.esml,locals.esml}` |
| 附录J 附录 J（单位语义） | 6 | `L0-type-unit/{units-anchoring.esml,units-base-offset.esml,units-base.esml,units-contradiction.esml,units-derived-scale.esml,units-derived.esml}` |
| 附录K 附录 K（METHOD × Schedule 编排） | 5 | `L9-method-schedule/{call-method-body.esml,continue-until.esml,free.esml,schedule-call.esml,stop.esml}` |

### 3.1 目录分布

| 目录 | 件数 | 目录 | 件数 |
|---|---:|---|---:|
| `D-skeleton/` | 10 | `L6-connect/` | 3 |
| `L0-type-unit/` | 14 | `L7-partition/` | 5 |
| `L1-expr-equation/` | 24 | `L8-function/` | 4 |
| `L2-discrete/` | 13 | `L9-method-schedule/` | 9 |
| `L3-model/` | 10 | `T-tasks/` | 45 |
| `L4-port/` | 12 | `X-use/` | 4 |
| `L4-portvar/` | 2 | `L5-instance/` | 9 |
| | | **合计** | **164** |

### 3.2 仍然**没有示例**的条款（留缺口，不补）

下表是 `SPEC.md` 里**有编号、有条文、但仓内没有一份示例守着它**的条款。
其中多数是**散文条款**（术语表、验收标准、概念说明），本仓的示例层不覆盖它们；
另有三条是**真缺口**，已在 §5 逐条裁决。

| 条款 | 性质 | 裁决 |
|---|---|---|
| §1 引言与设计原则 | 散文 | 不覆盖（§1.1 有 6 份） |
| §4.0a 方程形状决定因果计划（作者须知） | 作者须知 | 不覆盖 |
| §6.2 | **编号缺失**（§6.0/§6.1 之后直接 §6.3） | 记账，见 §5.4 |
| §6.3 分层归属（库 vs 案例） | 散文 | 不覆盖 |
| §9 展平与命名（编译器） | 散文 | 不覆盖 |
| §10 求解语义 | 散文 | 不覆盖 |
| §11 物性插件 | 真条款 | **缺口**：`物性` / `plugin` / `mmprops` 在 189 份示例里 0 命中（W51 2026-11-11 重算）。补示例等于先立语义 ⇒ 另一次规范修订，见 §5.1 |
| §12 标准库（Standard Library） | 散文 | 不覆盖（`X-use/` 三份归 §6.1） |
| §13 分层验收 | 验收条款 | 不覆盖 |
| §14.4 注册 / 发现 / 缓存 | 散文 | 不覆盖 |
| §14.5 可验性 | 散文 | 不覆盖 |
| 附录 A 术语 / 附录 C 修订史 / 附录 D 旧版边界 | 散文 | 不覆盖 |
| 附录 B（续）· process 级全局默认参数传播（顶层 `SET`） | 真条款 | **缺口**：schema 的 `<sets>` 只许 `<scope>` 子元素，裸 `<set>` 不可机验；引擎接受但**不生效** ⇒ 不补示例，见 §5.2 |
| 附录 B（续）· FOR 按序集迭代 | 真条款 | **已补**：`for-over-orderedset.esml`（`in="Species"` 序集迭代，`array="Species"` 变量，`S=sum(C[1:3])=6`） |
| 附录 F9 高指标 DAE（Pantelides） | 真条款 | **缺口**：`pantelides` 在 189 份示例里 0 命中（W51 2026-11-11 重算）⇒ 见 §5.1 |
| 附录 F10 外部 I/O 经信号口 / 端口壳 | 真条款 | **缺口**：`signal` / `外部 I/O` 在示例里 0 命中（`signal-causal.esml` 是附录 F2 的**信号 causal 连接**，不是 F10 的外部 I/O）⇒ 见 §5.1 |
| 附录 G 能力概览 / 附录 G·序集运算（编译期） | 散文 | 不覆盖 |
| 附录 H XML Schema 与 canonical 校验 | 散文 | 不覆盖 |
| 附录 J · METHOD FIX/VARY | 已被 F6/F7 覆盖 | 不另立 |
| 附录 J · 连接参数单向传播 / 回退 | 散文 | 不覆盖 |
| 附录 K · `<call method>` 方法体 | 已被附录 K 覆盖 | 不另立 |
| 附录 L 术语表与命名 / L.1 / 附录 M / 附录 N | 散文 | 不覆盖 |
| ConstSetMember 一等成员类型 | 真条款 | **缺口**：`constSetMember` 在 189 份示例里 0 命中（W51 2026-11-11 重算）；且该成员类型在 `xsd/` 里未定义 ⇒ 记 §5.3 |
| `§6.9` 元数据表 · `<description>` 一行 | 表内已自注「（暂缺示例）」 | 记账 |

---

## 4. 多出来的（无 SPEC 依据的示例）：25 条逐条裁决

BEFORE 状态有 **54 / 136** 份示例在本仓 `SPEC.md` 里查无点名依据（稀有元素普查，
检查 4）。经 21ddbee / ca8efc7 / 526d283 / **b5b3557** 四刀补条文后，剩下
**25 条**待逐条裁决——**裁决结果：25 条全部「补规范条文」，0 条删除**。

| # | 示例 | 稀有元素 | 裁决 | 规范条文落点 |
|---:|---|---|---|---|
| 1 | `D-skeleton/metadata.esml` | `author` `license` | 补规范条文 | §1.1（`SPEC.md:43`） |
| 2 | `D-skeleton/provenance.esml` | `author` `provenance` | 补规范条文 | §1.1 |
| 3 | `D-skeleton/solutionparameters.esml` | `solutionParameters` | 补规范条文 | §6.9 顶层 `<solutionParameters>` 段（`SPEC.md:725`） |
| 4 | `L0-type-unit/observe-list.esml` | `observe` | 补规范条文 | §6.10（`SPEC.md:736`） |
| 5 | `L0-type-unit/record-type.esml` | `recordTypes` `recordType` `field` | 补规范条文 | §3 记录类型（`SPEC.md:151`） |
| 6 | `L0-type-unit/type-unit.esml` | `typesDimensionless` | 补规范条文 | §3 类型按类别包裹（`SPEC.md:145`） |
| 7 | `L0-type-unit/typesgeneric.esml` | `typesGeneric` | 补规范条文 | §3 类型按类别包裹 |
| 8 | `L0-type-unit/typesthermal.esml` | `typesThermal` | 补规范条文 | §3 类型按类别包裹 |
| 9 | `L2-discrete/clock-functions.esml` | `clocks` `clock` | 补规范条文 | §7.1 状态机与时钟（`SPEC.md:791`） |
| 10 | `L2-discrete/clock-sample.esml` | `clock` | 补规范条文 | §7.1 |
| 11 | `L2-discrete/reset-transition.esml` | `stateMachine` `state` | 补规范条文 | §7.1 |
| 12 | `L2-discrete/state-machine.esml` | `stateMachine` `state` | 补规范条文 | §7.1 |
| 13 | `L3-model/extendsfrom.esml` | `extendsFrom` | 补规范条文 | §4.0 继承（`SPEC.md:233`） |
| 14 | `L3-model/selector-values.esml` | `initialSelectors` `initialSelector` | 补规范条文 | 附录 B（续）SELECTOR（`SPEC.md:1107`） |
| 15 | `L6-connect/connect-rules.esml` | `typesDimensionless` | **误报**（见注 1） | §3 类型按类别包裹 |
| 16 | `L7-partition/domain.esml` | `domains` `discretization` | 补规范条文 | §6.4 计算域声明（`SPEC.md:448`） |
| 17 | `L7-partition/group.esml` | `group` | **改归位** → `L0-type-unit/units-group.esml` | §3 单位表分组（`SPEC.md:153`） |
| 18 | `L7-partition/partition-chain.esml` | `partitions` | 补规范条文 | §6.4 |
| 19 | `L7-partition/partition-crosslink.esml` | `partitions` | 补规范条文 | §6.4 |
| 20 | `L8-function/foreign-object.esml` | `foreignObjects` `foreignObject` | 补规范条文 | 附录 I（`SPEC.md:1315`） |
| 21 | `L8-function/locals.esml` | `locals` `local` | 补规范条文 | 附录 I |
| 22 | `L9-method-schedule/fixed-preset.esml` | `presets` | 补规范条文 | §6.10 |
| 23 | `L9-method-schedule/reset.esml` | `reset` | 补规范条文 | 附录 K（`SPEC.md:1354`） |
| 24 | `L9-method-schedule/stop.esml` | `stop` | 补规范条文 | 附录 K |
| 25 | `T-tasks/solutionparameters.esml` | `solutionParameters` | 补规范条文 | §6.9 顶层 `<solutionParameters>` 段 |

**注 1（第 15 条）**：`connect-rules.esml` 之所以被判「无 SPEC 依据」，是因为它
用了 `typesDimensionless` 而该词条在当时还没被点名；§3 的「类型按类别包裹」条文
补上后即自动消解，无需改示例。它不是真的「多出来」。

**注 2（第 17 条）**：`group.esml` 演示的是 `<unitsDerived>` 下的 `<group>`——
**单位表**的分组，与 `<partitions>` 的 `<partition>` 无关，却放在 `L7-partition/`
目录里，是归位错误。已移到 `L0-type-unit/units-group.esml`（`fc4d05c`），
全仓无任何引用指向旧路径。

**裁决汇总**：补规范条文 **25**、改归位 **1**（含在 25 内）、删除 **0**。
补条文后，无 SPEC 依据的示例 **54 / 136 → 0 / 141**。

---

## 5. 规范 ↔ 实现 / schema 缺口（记账，本仓不修引擎）

本仓是**规范仓**：只放规范、schema、示例。本节列出的都是**引擎侧**（`~/esml`）
或**规范仓内部**的落差，规范仓能做的已经做完（补条文、补示例、记账）。

### 5.1 三条条款在本仓**无 token 落点**，补示例等于先立语义

| 条款 | 症状 | 裁决 |
|---|---|---|
| 附录 F9 高指标 DAE（Pantelides） | `pantelides` 在 189 份示例里 **0 命中**（W51 2026-11-11 重算，注释剥除后 grep 全树） | **不补**。该条讲的是**降阶算法**（`pantelides.rs` 在引擎里），示例层要它就得先有 canonical 的指标降阶写法 |
| §11 物性插件 | `物性` / `plugin` / `mmprops` **0 命中** | **不补**。插件的挂载方式（`<use>`？`<plugin>`？自带库还是 extern？）在规范里还没有 canonical 拼写 |
| 附录 F10 外部 I/O 经信号口 / 端口壳 | `signal` 相关的**外部 I/O** 形态 **0 命中**（`L4-port/signal-causal.esml` 是附录 F2 的信号 causal 连接，**不是** F10 的外部 I/O 端口壳） | **不补**。F10 讲的是「block 化单机 + 语言层闭环」的端口壳，等于一次新语法 |

三条的共同点：**示例要先有规范，示例才能有**。硬造一份示例会造出一个「假绿」——
`check` 过、语义无——这正是本仓 README「失败响亮，不许静默兜底」反对的东西。
**留缺口、记账**，等各自立规范修订时一并补。

### 5.2 附录 B（续）「顶层 `SET`」：schema 不许、实现放行但不生效

三边实测（探针文档见下方；`esml` 取引擎仓 `~/esml/target/debug/esml`）：

```xml
<?xml version="1.0"?>
<esml xmlns="https://www.ai4energy.cn/esml/v1" schema="esml/v1" name="T_TopSet">
  <variableTypes><type name="real" unit="1" default="0.0"/></variableTypes>
  <modelTypes><modelType name="M">
    <parameters><parameter name="k" type="real" default="0.2"/></parameters>
    <variables><variable name="x" type="real" role="state" initial="1.0"/></variables>
    <equations><equation>Der(x) = -k * x</equation></equations>
  </modelType></modelTypes>
  <systems><system name="S">
    <instances><instance name="m" type="M"/></instances>
    <sets><set path="k" value="0.5"/></sets>     <!-- 裸 <set>：不带 <scope> -->
    <schedule><sequence><continueFor time="1"/></sequence></schedule>
  </system></systems>
</esml>
```

```
$ esml check toplevelset.esml -L ~/esml/library
    ok
    summary: errors=0 warnings=0 models=2 systems=1 types=1 portTypes=0 units=0 functions=0 five_level=ok
rc=0

$ python3 -c "import xmlschema; xmlschema.XMLSchema('xsd/esml-canonical-basic.xsd').validate('toplevelset.esml')"
XSD: FAIL
Reason: Unexpected child with tag '{https://www.ai4energy.cn/esml/v1}set' at position 1.
```

更要紧的是**语义不生效**——裸 `<set path="k" value="0.5"/>` 不带 `<scope>` 时，
两个实例都仍取参数默认值 `0.2`（`m1` 的 `<scope>` 覆盖才生效）：

```
$ esml solve toplevelset.esml --system S --full     # 两个实例 m1 / m2
system: S (2 unknowns)
  m1.y                     1e0     ← <scope instance="m1"> 覆盖 1.0
  m2.y                     2e-1    ← 全局 <set> 未生效，仍是 default 0.2
```

**裁决：不补示例**。补一份「`check` 过但语义无效」的示例等于造假绿。
另：schema 的 `<sets>` 只许 `<scope>` 子元素，与附录 B（续）的文字不一致——
按 README「文字与 schema 出现分歧时，以 schema 为准」，此处是**文字超前于
schema**；要落地「顶层 `SET`」须先做一次规范修订（`SPEC.md` + XSD + 示例），
且实现侧要先真正生效。

### 5.3 引擎收但语义无效 / 实现无的行

| 条目 | 实测 | 状态 |
|---|---|---|
| `ConstSetMember` 一等成员类型 | 189 份示例 0 命中（W51 2026-11-11 重算，`constSetMember` / `ConstSetMember` 注释剥除后 grep 全树均 0）；`xsd/` 里未定义该类型（重算确认） | 规范有、XSD 无 → 留缺口 |
| 附录 F2 的 `signal_causal_guard` | 引擎**接受** input↔input、output↔output、pvar 命名不一致三种写法（`check` rc=0） | 规范有、实现无 → `L4-port/signal-causal.esml` 的头部已注明 |
| `<param>` 元素（`compute.xsd:181` / `:387`） | **已有示例** `T-tasks/hyperparams.esml`（W21 补，`<hyperParams><param name="lr" value="0.01"/>`，`:30`）；引擎实测 **F7 unknown element + F1 legacy spelling 双拒**（verbatim 见该件头注与 §5.11）；189 份示例里元素形 `<param` 命中 1（即该件，W51 2026-11-11 重算） | 规范有、XSD 有（`compute.xsd` 两处声明）、引擎拒收 ⇒ **登记于 §5.11**，不另裁 |
| `domain` 属性（`<instance>` / `<modelType>` / `<system>` 宿主） | W17 2026-11-11 实测三宿主 `esml check` 均 `errors=0`，但 `esml solve` 取值与无 `domain` 同（`domain` 零读点，写与不写同解）；`<portType>` 宿主是 `F1 legacy spelling` 响亮拒收（台账 `PortTypeDef/domain` 行 `rejected-legacy`） | 引擎收但语义无效 → 按 §5.2 顶层 `SET` 先例**不补示例**，台账三宿主行记 `no-example` |
| `side` 属性（`<annotation><port>` 宿主，`PortMarkType`） | W17 2026-11-11 实测 `esml check` `errors=0`，但 `side` 只属标注侧图形标记，引擎 `check` 不消费其值（写 `left`/`right` 与不写同）；模型侧 `<modelType><ports><port>` 是 `F1 unknown attribute` 响亮拒收（台账 `PortInstanceType/side` 行 `rejected-legacy`） | 引擎收但语义无效 → 按 §5.2 先例**不补示例**，台账 `PortMarkType/side` 行记 `no-example` |
| `MetadataType` `xs:any` 兜底（`##targetNamespace` + `##other`） | SPEC:65「子结构不固定（schema 放行任意子元素）」是规范意图；XSD 1.0 UPA 禁止同一内容模型内命名元素与 `##targetNamespace` 通配并存（W23 2026-11-11 实测 sequence/choice 两种拼法均 `UPA violation`），故只能 lax | **by-design**，非缺口；strict 基线 3/3（`D-skeleton/metadata.esml` / `provenance.esml` / `doc-ref.esml`）不变 |
| `<replace path value/>`（`initialisationProcedure/start` 宿主，W20 新声明） | W28 2026-11-11 实测 `esml check` `errors=0`；`esml simulate` 下与不带 `<replace>` 的对照文档同值（state `x` initial=0 配 `<replace path="m.x" value="1.0"/>`，两文档 `simulate` 末行均 `m.x=0.0`） | 引擎收但零效果（CLI 默认 solve/simulate 路径不跑初始化过程，`esml-solve` 的 `solve_initialisation_procedure` 只有库级调用点）→ 按 §5.2 先例**不补示例** |
| `<next><moveTo>` / `<next><jumpTo>`（W20 新声明） | 同法实测：`check` `errors=0`，且整条初始isationProcedures 管线默认 `esml solve`/`simulate` 均不消费（库级 ADR-97/98 求解器存在但 CLI 无调用点） | 引擎收但零效果（同 `<replace>` 行，管线级）→ 不补示例 |
| `<observe name><var path name/></observe>`（W20 新声明） | W28 2026-11-11 实测：HIR 收（`observes`）、flat 层 `resolve_observes` 消费（`esml-flat/src/flat/observe.rs`）；但 `esml solve` 输出列与不带 `<observe>` 的对照文档逐字同（`m.x=1.0` 单行）；`<observe>` 只接 `esml simulate --observe`（`esml-cli/src/main.rs:2132` `resolve_observe_paths` 只消费命令行参数） | 引擎收但默认路径零效果（需 `simulate --observe` 才可见）→ 现有示例 `L0-type-unit/observe-list.esml` 头部已注明，不另补 |
| `<connectRules><rule from to/></connectRules>`（W20 新声明） | W28 2026-11-11 实测：`check` `errors=0`；负例（`from="feed" to="primary"` 但全文无对应 `connectClass` 声明）仍 `errors=0` —— `F-CONNECT-RULES-*` 校验（`esml-schema/src/connect_rules.rs:71`）只数 `rule` 条目，不联 `connectClass`；HIR/flat 层无 `connect_rules` 消费点 | 引擎收但零效果（不联 connectClass、不进入求解）→ 按 §5.2 先例**不补示例** |

### 5.4 章节编号 `§6.2` 缺失

`SPEC.md` 的 §6 下有 6.0 / 6.1 / 6.3 / 6.4 / … / 6.10，**没有 6.2**。README
承诺「章节编号稳定」，而 §6.2 的号被留空。本仓**不重排既有编号**（重排会
让所有按编号引用的外部文档失效），故保留空号、在此记账。

### 5.5 附录 B（续）「FOR 按序集迭代」与「FOR 循环」不是一回事

`L1-expr-equation/for-in.esml` 的 `in="1..3"` 是**字面整数范围**
（附录 B（续）· FOR 循环）；「FOR 按序集迭代」指的是 `in="Species"`
（`in` 取已声明序集名，`k` 绑成员**序位** 1 起，非 label 字符串）。
序集迭代形态已有示例 `L1-expr-equation/for-over-orderedset.esml`
（`array="Species"` 变量 + `for var="k" in="Species"` + `S=sum(C[1:3])=6`）。

### 5.6 `<body>` 与 `<derivative>` 互斥：schema 拒、实现放行

`xsd/esml-canonical-basic.xsd` 里 `<body>` 与 `<derivative>` 同属
`xs:choice maxOccurs=1`，二者互斥；四份负例
（`L1-expr-equation/{derivativesymbol,noderivative,partial-derivative,zeroderivative}.esml`）
因此**被 canonical schema 拒绝**。但实现侧的 `esml check` 目前**仍放行**
（未实现这条互斥）——四份示例的头部已从「`check` 应报错」改成
「**schema 校验**应报错」，并指向本文件。

### 5.7 引擎 `esml simulate` 不消费 `<schedule>`

`L9-method-schedule/call-method-body.esml`（附录 K · 段前方法体）用
`esml check` 验得过，但 `esml simulate` 只按命令行给的 tspan 积分、**跳过
`<schedule>`**（段划分与段前方法体都跳过），拿它跑会得到「方法体没落地」的那个值。
这是**校验工具的缺口**，不是本例的语义——已在该例头部注明。

### 5.8 四方闸门 [3] 角的 `reference=缺` 指的是**引擎仓**，规范仓改不动

引擎仓的 `tools/four_way_gate.py` 第 [3] 角把规范正文里引用的编号
（`claimed`）与**引擎仓** `reference/conformance.rs` 里的用例名对账：

```
$ grep -c "^fn conformance_" reference/conformance.rs
179
$ grep -n "fn conformance_14_\|fn conformance_83_" reference/conformance.rs
（无输出）
```

- `claimed` 取自**引擎仓**自带的规范副本 `docs/language/esml-language-spec.md`，
  **不是**本仓的 `SPEC.md`；闸门没有 `--spec` 之类的参数可以指到规范仓。
- `reference` 侧 = 引擎仓 `reference/conformance.rs`（179 个 `conformance_*`，
  **没有** `conformance_14_*` / `conformance_83_*`）。
- `rust` 侧 = 引擎仓的 Rust 用例：`14` 落在
  `crates/esml-engine/tests/support/conformance_block2_body.rs`，
  `83` 落在 `crates/esml-engine/tests/conformance_83_method_set.rs`。

因此 `[3] 角 reference=缺 → 0` **在规范仓里不可达**：它要动的是引擎仓的
`reference/conformance.rs`，而引擎仓的规范副本与本仓的 `SPEC.md` 是两份文件。
本工单在规范仓能做的部分——**补齐 14 与 83 的示例条目**——已完成：

| 编号 | 规范里的含义（引擎仓规范副本） | 本仓补的示例 |
|---:|---|---|
| 14 | 「系统=(子系统-link-子系统)」整体联立成立（副本 `docs/language/esml-language-spec.md:491`） | `L7-partition/subsystem-crosslink.esml`（`<system>` 作 instance 的 type 即得子系统，父系统 `<links><crosslink from="A.u.y" to="B.v.s"/>` 展开为相等约束） |
| 83 | `<call method>` 方法体：`<call method="X"/>` 归属**其后**那个 `<continueFor>` 段，段前执行（副本 `:1313`） | `L9-method-schedule/call-method-body.esml`（`<methods><method name="ramp"><set path="m.k" value="3.0"/></method></methods>` + `<call method="ramp"/>`） |

引擎仓那条「roadmap:51 的『spec 引用 14、83』指的是 spec 正文里引用的 14 与 83」
的留档见 `docs/design/conformance-residual-adjudication.md`（引擎仓）。

**补充（实测 `origin/main` 的闸门）**：[3] 角**并不因为 14/83 判红**——闸门
自己的文档写着，`have` 早已改从 **Rust 树**取（`reference/conformance.rs` 是
上游快照，只当两面对账里的 `on_reference` 侧），所以 14/83 的 `rust=ok` 即算
「有支撑」；那两行 `reference=缺` 只是说**上游快照里没有同号的用例**。要把这两
行也变成 `reference=ok`，得动引擎仓的 `reference/conformance.rs`（上游快照），
属引擎仓的事。

`origin/main` 上闸门整体 `verdict: DISAGREE`，**红在 [2] 角**（引擎仓自己的
`tests/fixtures/schedule_solver.esml` 与 `tests/fixtures/schedule_until.esml`
两个 unexpected），不在这两行上。

### 5.9 §6.5 条件组件：「参数」操作数当前**无处可声明**（规范 ↔ 实现 错位）

`SPEC.md` §6.5 说条件的操作数可以是「参数 / 常量 / 序集成员」，示例却写
`condition="useC"`。但 `useC` **没有 canonical 声明处**：

- `xsd/esml-canonical-basic.xsd` 的 `SystemType` **没有** `<parameters>` 子元素
  —— `<system><parameters>` 被 schema 拒（`Unexpected child with tag
  '…}parameters' at position 1`）；
- 实例**自身模型**里的参数（如 `CondComp.useC`）在条件求值时**尚未落表**
  —— 引擎 `crates/esml-flat/src/flat/instances.rs:50-66` 先算 `condition`、
  再 `flatten_instance`；`crates/esml-flat/src/flat/resolve.rs:7` 的 `eval_cond`
  经 `crates/esml-flat/src/flat/dof.rs:143` 的 `eval_shell` 去查参数表，查不到即 `None`。

实测（引擎 `~/esml/target/debug/esml`，探针件见本文件 §7「复现命令」）：

```
$ esml solve spec65-useC.esml --system S        # condition="useC"（useC 是模型参数）
error: instance condition `useC` is not statically decidable: an `<instance condition="…">`
is evaluated at flatten time to decide whether the instance (and all its connections) is
kept, so it must be a constant expression over the shell's declared parameters, constants,
or ordered-set members — references into other models, variables, or expressions that
depend on an unknown cannot be folded at build time. …
rc=1
```

`useC` / `c.useC` / `useC == 1` / `useC > 0` 四种写法**全部**落到同一条报错。
今日能折叠的只有两种形态：**常量**（`1 < 2`）与**序集成员序号**
（`ethane` ⇒ 序号 2 ≠ 0 判真）。

另：报错里建议的写法 `shell.K > 0.0` 里的 `shell` —— `SPEC.md` 与 `xsd/` 里
**0 命中**，实现侧也没有对应拼写。

**裁决**：这是**文字超前于 schema**（README「文字与 schema 出现分歧时，以 schema
为准」）。已做的动作：`SPEC.md` §6.5 补上操作数作用域、把「参数形态」标为
**待定**并指向本节（`89262a5`）；示例只演示**常量形态**（正例
`L5-instance/instance-condition.esml`）与**参数引用不可判定**（负例
`L5-instance/instance-condition-undecidable.esml`），**不**造一份「参数驱动」
的假绿示例。落地「参数驱动」要一次规范修订：`SPEC.md` ＋ XSD（给参数一个
canonical 声明处）＋ 至少一份演示该语法的示例，外加实现侧把参数在条件求值
前落表。

### 5.10 算法段 `<for>` 六拼法：引擎只认 `range="a:b"` 且无 `<body>` 壳

`L8-function/algorithm-for.esml` 头注记录了算法段 `<for>` 的六拼法实测
（`y` 初值 0、体 `y = y + i`）：

| 拼法 | `check` | `solve` `m.y` |
|---|---|---|
| `range="1:3"`（canonical） | errors=0 | 6.0 ✓ |
| `in="1..3"` | errors=0 | 0.0 ✗ |
| `in="1:3"` | errors=0 | 0.0 ✗ |
| `range="1..3"` | errors=0 | 0.0 ✗ |
| `range="1:3"` + `<body>` 壳 | errors=0 | 0.0 ✗ |
| `in="1..3"` + `<body>` 壳 | errors=0 | 0.0 ✗ |
| 无 `range` 属性 | errors=0 | 0.0 ✗ |

**关键事实**：所有错误拼写均 `check` 全绿、`solve` 得 0.0——**静默错答**，
严重度高于普通拼写漂移（引擎债务，台账 `engine-drift.tsv` `attr algorithm-for`
三行）。算法段 `<for>` 唯一能算对的是 `range="a:b"` 且**无** `<body>` 壳；
`in` 是 canonical 拼写（方程级 `<for>` 读 `in`，SPEC:241/1282/1298），但
算法段引擎只认 `range`（`components.rs:345`）。

### 5.11 XSD 已声明、引擎**拒绝**的四处（登记，本仓不裁）

`xsd/esml-canonical-basic.xsd` 已声明以下元素/属性，但引擎 `esml check`
**明确拒绝**（`F7[]: unknown element`）。W9 真声明时记为 `lang-wins`
（方向判断），此处登记**引擎当前不收**的事实本身，不隐藏于 `lang-wins` 之后。

| 条目 | XSD 声明处 | 示例文件（W27 2026-11-11 补列） | 引擎实测（verbatim） |
|---|---|---|---|
| `<literal name="a"/>` 在 `<variable>` 内 | `VariableType` / `LiteralType` | `L0-type-unit/literal-enum.esml` | `error: F7[]: unknown element <literal> at L0-type-unit/literal-enum.esml:16:7`（×3，`errors=3`；W27 2026-11-11 引擎 `~/esml-engine-user3/target/release/esml` 重跑） |
| `<vary name="m.x"/>` 在 `<methods><onLoad>` 内 | `MethodVaryType` / `MethodsType` | `L9-method-schedule/method-vary.esml` | `error: F7[]: unknown element <vary>`（该件引擎 `errors=1`；W27 2026-11-11 重跑） |
| `<while condition="…">` 在 `<algorithm>` 内 | `AlgorithmType`（`WhileType`） | `L8-function/algorithm-while.esml` | `error: F7[]: unknown element <while> at …:12:7` ＋ `F1[]: parser rejected…`，`errors=2`，`five_level=BAD` |
| `<connectionTypes>` 在文档根 | 顶层元素 | **仍无示例**（189 份示例里 `connectionTypes` 0 命中，W51 2026-11-11 重算）——根级元素无宿主可落，探针只能写 `/tmp`，不入库 | `error: F7[]: unknown element <connectionTypes>`（两处）｜`errors=2` |

**对照组**：`<fix name="m.x" value="2.0"/>` 在 `<methods><onLoad>` 内
→ `check` 输出 `ok`，`errors=0`（`fix` **被引擎接受**）。

**W28 复核**（2026-11-11，W20 新声明逐元素探针 `/tmp/w28-probes/`）：
W20 新增的 19 处声明里，`check` 层面**无新增拒收**——唯一拒收项
`<vary>` 在 `<methods><onLoad>` 内即上表第 2 行（`F7[]: unknown element
<vary> at …:9:22`，原文复现）。其余 W20 新声明（方程级 `if/case/for`、
`selectors`/`initialSelectors`、`initialisationProcedures` 全族、
`connectRules`/`rule`、`observe`/`var`、`presets`/`preset`、`extendsFrom`
系统级）`check` 均 `errors=0`；收但零效果的登记见 §5.3 新增四行
（`<replace>` / `moveTo`·`jumpTo` / `<observe>` / `<connectRules>`）。
「四处」计数因此不变。

探针件：`/tmp/w14-probes/w19_four.py`（W9 四处拒收）、`/tmp/w28-probes/`
（W28 逐元素复核；引擎 `~/esml-engine-user3/target/release/esml`，2026-11-11）。

### 5.12 属性面判别力：lax anyAttribute 的结构性放行（2026-11-11，W42 实测）

W4 做属性负例时发现：「拼写单轨」在**属性面**的执行力远低于**元素面**，
原因是本仓 XSD 大量使用 `xs:anyAttribute processContents="lax"`——
未声明的属性名在 lax 通配下**全部放行**，元素是闭集（未声明的
`<component>` 直接拒），属性却是开集（未声明的 `a-part` 收）。

**量化实测**（2026-11-11，本仓 HEAD `baf37b6`，命令见下）：

```sh
# anyAttribute 总数与 processContents 分布
grep -oP '<xs:anyAttribute\b' xsd/*.xsd | wc -l                # 201
grep -oP 'xs:anyAttribute[^/>]*' xsd/*.xsd | grep -oP 'processContents="[^"]*"' | sort | uniq -c
#   201 processContents="lax"    （100% lax，0 处 skip，0 处无值）

# 命名 complexTypes 里只靠 anyAttribute、无一条显式属性声明的宿主
#   17 / 106（16%）——这 17 个类型的任何属性都靠通配放行
```

**aliases.tsv 属性行 XSD 可拒比例**（2026-11-11，逐条探针实测）：

`tools/aliases.tsv` 属性行共 **26 条**；逐条在 canonical 宿主上写探针、
`xmlschema` 校验，**XSD 可拒的 0 条**（0%）——全部 **26 条**（100%）
因宿主顶层有 lax anyAttribute 而被放行。

> **W53 复核更正**：W42 原判「可拒 3 条（`max-time`/`model-type`/`component`）」
> 是**假 REJECT 工件**——W42 探针漏给宿主/根的必备 required 属性（`<system>` 的
> `name=`、`<continueUntil>` 的 `maxTime=`、`<instance>` 的 `type=`/`name=`、
> `<task>` 的 `name=`+`kind=`），探针因「缺 required 属性」而 REJECT，并非
> legacy 拼法顶不上。W53 探针给齐所有 required 属性后逐条复跑：**26/26 全部
> ACCEPT**（lax anyAttribute 放行），XSD 对属性面 0 判别力。下表中该 3 条
> 原判 REJECT 改标 ACCEPT，机制改为「W53 更正」。

| 拼法 | 宿主 | XSD 判定 | 机制 |
|---|---|---|---|
| `max-time` | `<continueUntil>` | **ACCEPT**（lax） | W53 更正：`maxTime` 虽 `use="required"`，但探针给齐 `maxTime=` 后 `max-time` 仍经 lax anyAttribute 放行（W42 漏给 `maxTime` 致假 REJECT） |
| `model-type` | `<instance>` | **ACCEPT**（lax） | W53 更正：`type` 虽 `use="required"`，但探针给齐 `type=` 后 `model-type` 仍经 lax anyAttribute 放行（W42 漏给 `type` 致假 REJECT） |
| `component` | `<instance>` | **ACCEPT**（lax） | W53 更正：同上（W42 漏给 `type` 致假 REJECT） |
| `time-layer` / `time_layer` | `<partition>` | ACCEPT（lax） | `timeLayer` 是 `use="optional"`，通配放行 |
| `upper-bound` / `upper_bound` | `<variable>` | ACCEPT（lax） | 同上 |
| `lower-bound` / `lower_bound` | `<variable>` | ACCEPT（lax） | 同上 |
| `a-part` / `b-part` | `<connection>` | ACCEPT（lax） | `aPart`/`bPart` 是 `use="optional"` |
| `porttype` | `<portType>` | ACCEPT（lax） | `portType` 是 `use="optional"` |
| `interface` | `<portType>` | ACCEPT（lax） | 同上 |
| `dir` | `<portType>` | ACCEPT（lax） | `category` 是 `use="optional"` |
| `port-set` | `<portType>` | ACCEPT（lax） | `portSet` 是 `use="optional"` |
| `desc` | `<equation>` | ACCEPT（lax） | `description` 是 `use="optional"` |
| `extends` / `extends-from` | `<instance>` | ACCEPT（lax） | 待入，XSD 未声明，通配放行 |
| `sample-time` / `control-horizon` | `<controller>`（compute.xsd） | ACCEPT（lax） | 宿主有 lax anyAttribute |
| `from_state`/`out_state`/`out_kind`/`out_system`/`to_state`/`tolerance_pct` 等 snake 拼法（共 7 条，均「待入」） | `<instance>`/`<transition>` 等 | ACCEPT（lax） | 宿主有 lax anyAttribute，XSD 未声明 |

**与 §5.11 的区别**（一句话）：§5.11 登记的属性是「XSD 真声明 + 引擎拒」——
XSD 收了但引擎不收（`phase`/`aPart`/`bPart`/`nominal`/`quantity`/`synchronize`
等，引擎比 XSD 窄）；§5.12 登记的是「XSD 本就不拒 + 引擎拒」——
XSD 和引擎都该拒但只有引擎拒得到（语言层比引擎层宽）。
两节方向相反，不能混。

**与元素面的对比**：

| 维度 | 元素面 | 属性面 |
|---|---|---|
| 集合性质 | **闭集**：未声明的 `<component>` 直接拒 | **开集**：未声明的 `a-part` 在 lax 通配下放行 |
| 拒收机制 | XSD 结构性拒（未知子元素） | 只有 canonical 属性 `use="required"` 时才能拒 legacy 拼法 |
| 可拒比例（aliases 实测） | 100%（element 行全部 XSD 拒） | **0%**（0/26，W53 复核） |
| 引擎层兜底 | F7 unknown element | F7 unknown attribute / F1 legacy spelling |

**影响**：

- legacy 拼法里 **26/26 条**（100%，W53 复核）在语言层（canonical XSD）能通过，
  只有引擎层 F7/F1 能兜住；
- 「拼写单轨」在属性面的执行力完全依赖引擎层，XSD 层形同虚设；
- 这 26 条 legacy 拼法如果出现在第三方工具链（不走 `esml check`），
  会**静默通过** XSD 校验、且无任何警告。

**候选处置**（三选一，owner 裁决，本单不推荐、不实现）：

1. **不改 XSD，只记账**（现状）——代价：第三方工具链对 legacy 属性拼法
   零判别力；本仓 XSD 对「拼写单轨」的执行力停留在 0%（W53 复核）。
2. **逐宿主收紧**：把 canonical 属性从 `use="optional"` 改为 `use="required"`、
   删除对应 `xs:anyAttribute`——代价：每处改动需逐宿主评估，201 处 anyAttribute
   里有多少该撤、多少该留是逐案裁决；改动量大、回归面广。
3. **维持现状，靠引擎兜底**（同 1，但明确把「引擎层是属性面唯一防线」写进
   SPEC 或 README）——代价：文档承诺与 XSD 实际能力有落差，读者可能误以为
   XSD 已拒收。

**探针方法**（2026-11-11 初测 W42；2026-11-11 W53 复核修正）：
将每条 legacy 拼法写进真实 canonical 宿主（`<system>`/`<modelType>`/`<portType>`
等），以真实全局根元素（`<system>`/`<modelTypes>`/`<portTypes>`/`<computeTasks>`）
为文档根、挂 ESML 命名空间，`xmlschema.XMLSchema('xsd/esml-canonical-basic.xsd')`
校验；判 ACCEPT / REJECT 并取失败原因。

> **W53 复核要点**：探针必须给齐宿主及其祖先根的**所有 required 属性**
> （`<system>` 的 `name=`、`<continueUntil>` 的 `maxTime=`、`<instance>` 的
> `name=`+`type=`、`<task>` 的 `name=`+`kind=` 等），否则探针因「缺 required
> 属性」而 REJECT，会把 legacy 拼法误判成「顶不上」。W42 初测正是漏给这些
> required 属性，才得出 3 条假 REJECT；W53 给齐后 26/26 全 ACCEPT。

```python
# 复算示例（单条，W53 给齐 required 属性的正确探针）
import xmlschema as xs, xml.etree.ElementTree as ET
NS='https://www.ai4energy.cn/esml/v1'
x = xs.XMLSchema('xsd/esml-canonical-basic.xsd')
# 给齐 <system> 的 name= 与 <continueUntil> 的 required maxTime=，
# 再把 legacy 拼法 max-time 注到 <continueUntil> 上：
frag = f'<system xmlns="{NS}" name="S">' \
       f'<schedule><sequence><continueUntil condition="c" maxTime="1" max-time="1"/></sequence></schedule>' \
       f'</system>'
try:
    x.validate(ET.fromstring(frag))
    print("ACCEPT  ← lax 放行（max-time 经 anyAttribute 通配收）")
except Exception as e:
    print("REJECT  ←", str(e).splitlines()[0])
```

**引用链**（证据行，本单不改台账）：

- `tools/attr-acceptance.tsv`：`aPart`/`bPart`（`rejected-f7`）+ `maxTime`
  （`rejected-f7`）+ `phase`（`rejected-f7`）+ `quantity`（`rejected-f7`）
  等行——「XSD 声明 + 引擎拒」（§5.11 方向）；与 §5.12 方向相反，不可互引。
- `tools/engine-example-debt.tsv`：`L9-method-schedule/continue-until.esml`
  （`maxTime` F7 引擎拒）——引擎层唯一防线在本例的具体落点。

---

## 6. 本分支的提交

**提交清单以 `git log` 为准，本节不再逐条维护。**

理由：v1.3.3 时代手工列了 21 行 SHA 清单，此后的每一批 lang 合并（W15/W16/W17/W19/
W20/W21/W22/W23/W24……）都让这张表**只增不减**——它记录的只是历史，而它自己
又成了需要维护的「现状」：W27 开工时表里最末一行 `35f32e8` 之后的提交**一行都没
进过表**，读者若把它当现状读就会被误导。现状的权威来源本来就只有一份（`git log`），
把同一事实抄进文档只会引入漂移；需要查这批提交时，在**当下 HEAD** 跑
`git log --oneline -- docs/coverage.md` 即可（本节所有内容的变更史都挂在这个路径上）。

锚点（2026-11-11，`union/lang-batch` `0b34503`，`git log --oneline -20` 摘录）：

```
0b34503 docs: README 跟上现状——make check 由两道闸变四道……
6f7aa31 merge: W23 MetadataType UPA 实测记录 + coverage §5.3 by-design 登记（lang 批）
1fa14ae merge: W24 元素覆盖双向闸 + 台账 + 接入 make check（lang 批）
202b6c4 merge: W22 SPEC 35 个幽灵尖括号名字逐个裁决 + 别名表补 12 行（lang 批）
f6cd473 merge: W21 四个零示例语法点补例 + replaceable 台账 + scenario tasks 实测（lang 批）
224b9b6 W23: MetadataType UPA 实测记录 + coverage.md §5.3 by-design 登记（纯文档）
c1c7459 merge: W20 19 处 xs:anyType 收成真声明（lang 批）
abca616 W21: 四个「XSD 声明但全仓零示例」语法点补例 + replaceable 台账行 + data-scenario tasks 属性实测
```

---

## 7. 复现命令

```sh
# 1) 全部五道检查
python3 docs/validate_examples.py
#    需要 xmlschema：pip install xmlschema

# 1b) 根矩阵对账（入口层根清单 ⇄ canonical 全局元素；仅标准库）
python3 docs/validate_roots.py
#    自证（好例 / 坏例）：python3 docs/validate_roots.py selftest

# 2) 单件 XSD 校验（README「校验与运行」一节的写法）
python3 -c "import xmlschema; xmlschema.XMLSchema('xsd/esml-canonical-basic.xsd').validate('L3-model/modeltype-basic.esml')"

# 3) 引擎侧：189 份示例逐件 check（负例预期非零退出；2026-11-11 重算，W51）
for f in $(find . -name '*.esml' | sort); do
  esml check "$f" -L "$HOME/esml-engine-user3/library" >/dev/null 2>&1 \
    && echo "ok    $f" || echo "fail  $f"
done
# 注：`-L` 后的标准库根随环境而变（本文档撰写时的引擎在 ~/esml-engine-user3/）；
# 只有 `X-use/` 两件需要库，其余 187 件不带 `-L` 也能逐件 check。

# 4) 引擎侧：四方闸门（[3] 角是 reference 侧对账；在引擎仓跑）
cd ~/esml && python3 tools/four_way_gate.py

# 5) §5.9 的 §6.5 探针（条件里的参数引用不可判定）
cat > spec65-useC.esml <<'EOF'
<?xml version="1.0"?>
<esml xmlns="https://www.ai4energy.cn/esml/v1" schema="esml/v1" name="T_Spec65_UseC">
  <variableTypes><type name="real" unit="1" default="0.0"/></variableTypes>
  <modelTypes><modelType name="CondComp">
    <parameters><parameter name="useC" type="real" default="1.0"/></parameters>
    <variables><variable name="y" type="real" role="algebraic"/></variables>
    <equations><equation>y = 1.0</equation></equations>
  </modelType></modelTypes>
  <systems><system name="S">
    <instances><instance name="c" type="CondComp" condition="useC"/></instances>
    <schedule><sequence><continueFor time="0"/></sequence></schedule>
  </system></systems>
</esml>
EOF
esml solve spec65-useC.esml --system S      # ⇒ 「not statically decidable」，rc=1
```

BEFORE 对照：用 `git archive 58d2c0a | tar -x -C <dir>` 取快照，把本仓当前的
`docs/validate_examples.py` 放进去跑同一脚本，即得 §1 表左列。

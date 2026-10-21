# SPEC 覆盖对账表

本表回答一个问题：**`SPEC.md` 的每个编号承诺的语法点，仓内有没有一份可运行的示例
守着它？反过来，仓内每一份示例，指向的是不是真有一条规范条文？**

数字全部由 [`docs/validate_examples.py`](validate_examples.py) 机验产出，命令见文末
「复现命令」；本文件只做解释与裁决，不引入机器算不出来的判断。

- **BEFORE** = 本分支的起点 `58d2c0a`（用 `git archive` 取的快照）。
- **AFTER** = 本分支 HEAD。

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

| 指标 | BEFORE `58d2c0a` | AFTER `HEAD` | 判据 |
|---|---:|---:|---|
| 示例件数 | 136 | **141** | `find . -name '*.esml'` |
| XSD 机验 · PASS | 130 | **136** | 检查 1 |
| XSD 机验 · 负例按预期失败 | 5 | 5 | 检查 1 |
| XSD 机验 · **非负例失败** | **1** | **0** | 检查 1 |
| SPEC → 示例：点名且存在的路径 | 0 | **71** | 检查 2 |
| SPEC → 示例：悬空路径 | 0 | **0** | 检查 2 |
| 示例头部指名规范条文 | 0 / 136 | **141 / 141** | 检查 3 |
| 被指名的编号数 | 0 | **36** | 检查 3 |
| **无 SPEC 依据的示例** | **54 / 136** | **0 / 141** | 检查 4 |
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

`SPEC.md` 正文里点名的仓内示例路径共 **71 条**，**全部存在，悬空 0 条**。
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
| `L9-method-schedule/` | 3 | `fixed-preset.esml` `reassign.esml` `stop.esml` |
| `T-tasks/` | 37 | 计算任务表一族（`task-*.esml` / `tasks*.esml` / `checks.esml` / `tolerance.esml` 等） |
| **合计** | **71** | |

`SPEC.md` 里另有 7 条「示意路径 / 管线记法」（`models/ctrl.sys.esml`、
`models/thermal-chain.esml`、`.comp.esml`、`.sys.esml` 等），它们指的是**库或
外部管线**里的文件，不是本仓示例，机器判据不判对错，只列出备查。

---

## 3. 反向对账：每个编号的「应当有示例」清单

机验口径：示例头部「规范条文：…」一行点名的**全部**编号（以 `＋` 分隔的
多条逐条计入）。共 **36 个编号 / 141 份示例**。

| 编号 · 条文 | 件数 | 示例（仓内路径） |
|---|---:|---|
| §1.1 §1.1（文档骨架与 `<metadata>`） ／ §1.1（文档骨架） | 6 | `D-skeleton/{esml-coordinate.esml,metadata.esml,provenance.esml,skeleton-doc.esml,skeleton-full.esml,skeleton-minimal.esml}` |
| §14.1 §14.1（canonical 元素） | 4 | `L1-expr-equation/{derivativesymbol.esml,partial-derivative.esml,zeroderivative.esml}` `L3-model/partials.esml` |
| §14.2 §14.2（求导三档） | 1 | `L1-expr-equation/noderivative.esml` |
| §14.3 §14.3（C ABI 类型映射） | 1 | `L8-function/extern-cabi.esml` |
| §2 §2（收紧词法） | 1 | `L3-model/component-probe.esml` |
| §3 §3（单位表分组） ／ §3（类型按类别包裹） ／ §3（类型系统） ／ §3（记录类型 `<recordTypes>`） | 6 | `L0-type-unit/{record-type.esml,type-unit.esml,typesgeneric.esml,typesthermal.esml,units-group.esml,variable-roles.esml}` |
| §4 §4（组件） | 1 | `L3-model/modeltype-basic.esml` |
| §4.0 §4.0（继承 `<extends>`） ／ §4.0（继承 `<extendsFrom>`） | 3 | `L3-model/{extends.esml,extendsfrom-child.esml,extendsfrom.esml}` |
| §4.1 §4.1（复合组件） | 1 | `L3-model/members-composite.esml` |
| §5 §5（端口） | 9 | `L4-port/{constant.esml,flow-potential.esml,flow.esml,port-roles-io.esml,porttype-electrical.esml,porttype-thermal.esml,potential.esml}` `L4-portvar/{flow.esml,potential.esml}` |
| §6 §6（系统、实例与参数覆盖） | 3 | `L5-instance/{component-alias.esml,instance-basic.esml,instance-count.esml}` |
| §6.0 §6.0（实例参数覆盖：scope / set / path） | 3 | `L2-discrete/initial.esml` `L5-instance/{scope-nested.esml,scope-set.esml}` |
| §6.1 §6.1（标准库坐标引用） | 3 | `X-use/{use-f12-mismatch.esml,use-library.esml,use-multi-library.esml}` |
| §6.10 §6.10（系统级观察与预设） | 2 | `L0-type-unit/observe-list.esml` `L9-method-schedule/fixed-preset.esml` |
| §6.4 §6.4（partition / crosslink） ／ §6.4（计算域声明） | 5 | `L5-instance/subsystem.esml` `L7-partition/{domain.esml,partition-chain.esml,partition-crosslink.esml,subsystem-crosslink.esml}` |
| §6.5 §6.5（条件组件） | 2 | `L5-instance/{instance-condition-undecidable.esml,instance-condition.esml}` |
| §6.6 §6.6（系统级方程） | 1 | `L4-port/port-roles-io.esml` |
| §6.7 §6.7（系统初始化过程） | 2 | `L2-discrete/{initialisationprocedure-advance.esml,initialisationprocedures.esml}` |
| §6.8 §6.8（工程包装容器） | 1 | `T-tasks/tasks.esml` |
| §6.9 §6.9（计算任务表） ／ §6.9（顶层 `<solutionParameters>` 段） | 39 | `D-skeleton/solutionparameters.esml` `L1-expr-equation/{expr.esml,reference.esml}` `L5-instance/setpoint.esml` `T-tasks/{actuator.esml,benchmarks.esml,check.esml,checks.esml,control-vars.esml,controlled-control-vars.esml,controlled.esml,controller-gains.esml,controller.esml,dataset.esml,design-vars.esml,feature.esml,features.esml,gains.esml,hyperparams.esml,outputlist.esml,reference.esml,sensor.esml,setpoint.esml,solutionparameters.esml,status.esml,target.esml,targets.esml,task-constraint.esml,task-control.esml,task-estimation.esml,task-optimize.esml,task-sensitivity.esml,task-simulate.esml,task-surrogate.esml,task-validation.esml,task-vendor-text.esml,tasks-seven.esml,test-data.esml,tolerance.esml}` |
| §7 §7（分段表达式） ／ §7（向量归约内建） ／ §7（数组下标与切片） ／ §7（方程类别与语义） ／ §7（算法段） ／ §7（表达式内建） | 13 | `L1-expr-equation/{array-index-probe.esml,array-index.esml,axis-reduce-probe.esml,axis-reduce.esml,builtins-complex.esml,builtins-delay.esml,builtins-expr.esml,builtins-math.esml,equation-basic.esml,ifelse.esml,oob-probe.esml,shape-mismatch-probe.esml}` `T-tasks/algorithm.esml` |
| §7.1 §7.1（状态机与时钟） | 4 | `L2-discrete/{clock-functions.esml,clock-sample.esml,reset-transition.esml,state-machine.esml}` |
| §8 §8（连接语义） | 2 | `L6-connect/{connect-basic.esml,connect-canonical.esml}` |
| 附录B（续） 附录 B（续）— CASE 多分支 ／ 附录 B（续）— FOR 循环 ／ 附录 B（续）— ORDERED_SET 序集 ／ 附录 B（续）— SELECTOR ／ 附录 B（续）— 模型级 IF | 6 | `L0-type-unit/ordered-set.esml` `L1-expr-equation/for-in.esml` `L2-discrete/case-branch.esml` `L3-model/{if.esml,selector-values.esml}` `L7-partition/orderedsets.esml` |
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
| 附录K 附录 K（METHOD × Schedule 编排） | 4 | `L9-method-schedule/{call-method-body.esml,reassign.esml,schedule-call.esml,stop.esml}` |

### 3.1 目录分布

| 目录 | 件数 | 目录 | 件数 |
|---|---:|---|---:|
| `D-skeleton/` | 7 | `L6-connect/` | 3 |
| `L0-type-unit/` | 14 | `L7-partition/` | 5 |
| `L1-expr-equation/` | 19 | `L8-function/` | 4 |
| `L2-discrete/` | 12 | `L9-method-schedule/` | 7 |
| `L3-model/` | 9 | `T-tasks/` | 37 |
| `L4-port/` | 10 | `X-use/` | 3 |
| `L4-portvar/` | 2 | `L5-instance/` | 9 |
| | | **合计** | **141** |

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
| §11 物性插件 | 真条款 | **缺口**：`物性` / `plugin` / `mmprops` 在 141 份示例里 0 命中。补示例等于先立语义 ⇒ 另一次规范修订，见 §5.1 |
| §12 标准库（Standard Library） | 散文 | 不覆盖（`X-use/` 三份归 §6.1） |
| §13 分层验收 | 验收条款 | 不覆盖 |
| §14.4 注册 / 发现 / 缓存 | 散文 | 不覆盖 |
| §14.5 可验性 | 散文 | 不覆盖 |
| 附录 A 术语 / 附录 C 修订史 / 附录 D 旧版边界 | 散文 | 不覆盖 |
| 附录 B（续）· process 级全局默认参数传播（顶层 `SET`） | 真条款 | **缺口**：schema 的 `<sets>` 只许 `<scope>` 子元素，裸 `<set>` 不可机验；引擎接受但**不生效** ⇒ 不补示例，见 §5.2 |
| 附录 B（续）· FOR 按序集迭代 | 真条款 | **缺口**：`for-in.esml` 的 `in="1..3"` 是**字面整数范围**，不是 `in="Species"` 序集迭代 ⇒ 不补示例，见 §5.5 |
| 附录 F9 高指标 DAE（Pantelides） | 真条款 | **缺口**：`pantelides` 在 141 份示例里 0 命中 ⇒ 见 §5.1 |
| 附录 F10 外部 I/O 经信号口 / 端口壳 | 真条款 | **缺口**：`signal` / `外部 I/O` 在示例里 0 命中（`signal-causal.esml` 是附录 F2 的**信号 causal 连接**，不是 F10 的外部 I/O）⇒ 见 §5.1 |
| 附录 G 能力概览 / 附录 G·序集运算（编译期） | 散文 | 不覆盖 |
| 附录 H XML Schema 与 canonical 校验 | 散文 | 不覆盖 |
| 附录 J · METHOD FIX/VARY | 已被 F6/F7 覆盖 | 不另立 |
| 附录 J · 连接参数单向传播 / 回退 | 散文 | 不覆盖 |
| 附录 K · `<call method>` 方法体 | 已被附录 K 覆盖 | 不另立 |
| 附录 L 术语表与命名 / L.1 / 附录 M / 附录 N | 散文 | 不覆盖 |
| ConstSetMember 一等成员类型 | 真条款 | **缺口**：`constSetMember` 0 命中；且该成员类型在 `xsd/` 里未定义 ⇒ 记 §5.3 |
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
| 13 | `L3-model/extends.esml` | `extends` | 补规范条文 | §4.0 继承（`SPEC.md:233`） |
| 14 | `L3-model/selector-values.esml` | `initialSelectors` `initialSelector` | 补规范条文 | 附录 B（续）SELECTOR（`SPEC.md:1107`） |
| 15 | `L6-connect/connect-rules.esml` | `typesDimensionless` | **误报**（见注 1） | §3 类型按类别包裹 |
| 16 | `L7-partition/domain.esml` | `domains` `discretization` | 补规范条文 | §6.4 计算域声明（`SPEC.md:448`） |
| 17 | `L7-partition/group.esml` | `group` | **改归位** → `L0-type-unit/units-group.esml` | §3 单位表分组（`SPEC.md:153`） |
| 18 | `L7-partition/partition-chain.esml` | `partitions` | 补规范条文 | §6.4 |
| 19 | `L7-partition/partition-crosslink.esml` | `partitions` | 补规范条文 | §6.4 |
| 20 | `L8-function/foreign-object.esml` | `foreignObjects` `foreignObject` | 补规范条文 | 附录 I（`SPEC.md:1315`） |
| 21 | `L8-function/locals.esml` | `locals` `local` | 补规范条文 | 附录 I |
| 22 | `L9-method-schedule/fixed-preset.esml` | `presets` | 补规范条文 | §6.10 |
| 23 | `L9-method-schedule/reassign.esml` | `reassign` | 补规范条文 | 附录 K（`SPEC.md:1354`） |
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
| 附录 F9 高指标 DAE（Pantelides） | `pantelides` 在 141 份示例里 **0 命中** | **不补**。该条讲的是**降阶算法**（`pantelides.rs` 在引擎里），示例层要它就得先有 canonical 的指标降阶写法 |
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
  <variableTypes><type name="real" unit="1" default="0.0" role="algebraic"/></variableTypes>
  <modelTypes><modelType name="M">
    <parameters><parameter name="k" type="real" default="0.2"/></parameters>
    <variables><variable name="x" type="real" role="state" initial="1.0"/></variables>
    <equations><equation>D(x) = -k * x</equation></equations>
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

### 5.3 两处规范有、实现无

| 条目 | 实测 | 状态 |
|---|---|---|
| `ConstSetMember` 一等成员类型 | 141 份示例 0 命中；`xsd/` 里未定义该类型 | 规范有、XSD 无 → 留缺口 |
| 附录 F2 的 `signal_causal_guard` | 引擎**接受** input↔input、output↔output、pvar 命名不一致三种写法（`check` rc=0） | 规范有、实现无 → `L4-port/signal-causal.esml` 的头部已注明 |

### 5.4 章节编号 `§6.2` 缺失

`SPEC.md` 的 §6 下有 6.0 / 6.1 / 6.3 / 6.4 / … / 6.10，**没有 6.2**。README
承诺「章节编号稳定」，而 §6.2 的号被留空。本仓**不重排既有编号**（重排会
让所有按编号引用的外部文档失效），故保留空号、在此记账。

### 5.5 附录 B（续）「FOR 按序集迭代」与「FOR 循环」不是一回事

`L1-expr-equation/for-in.esml` 的 `in="1..3"` 是**字面整数范围**
（附录 B（续）· FOR 循环）；「FOR 按序集迭代」指的是 `in="Species"`
（`in` 取已声明序集名，按成员 label 迭代）。仓内无第二份 FOR 示例，
序集迭代形态**无示例** ⇒ 留缺口。

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

---

## 6. 本分支的提交

| SHA | 主题 |
|---|---|
| `835fa02` | 补 §6.4 子系统 crosslink 与附录 K 段前方法体两份示例（**conformance 14 / 83**） |
| `21ddbee` | 修 §6.8 canonical 示例的三处 schema 违规，并补 §6.9 计算任务表条文 |
| `ca8efc7` | 补 §6.8 `<tasks>` 外壳与 §6.9 元数据族条文，修三处正文/schema 错位 |
| `526d283` | §6.7 初始化过程改回 canonical 拼写与载荷 |
| `fc4d05c` | 单位分组示例归位到 `L0-type-unit` |
| `b5b3557` | 为 25 份无 SPEC 依据的示例补规范条文 |
| `f844361` | 四份导数负例的头部把「check 应报错」改成「schema 校验应报错」 |
| `cfb2b31` | 138 份示例的头部逐份指名其规范条文 |
| `3a1934b` | `<partition>` 的显式属性改成 canonical 拼写 `discipline` / `timeLayer` |
| `c438e6d` | 落盘示例 ⇄ 规范 对账机验（`docs/validate_examples.py`） |
| `6ff438d` | 聚合器按头部指名的**全部**条文统计 |
| `90e3770` | 五份示例的头部补上第二条规范条文（附录 F6 / F7 / F8） |
| `17547ec` | 补附录 F2 的信号口跨 PortType 因果连接示例 |
| `35c2bfe` | `port-roles-io` 的头部补上 §6.6（系统级方程） |
| `1a494bd` | 补 §6.5 条件组件的正例与「条件不可静态判定」负例 |
| `c673d57` | 修 `instance-condition` 头部指向已删文件的旧引用 |
| `89262a5` | §6.5 补条件的操作数作用域，并把「参数形态」标为待定 |
| （本提交） | 落盘本对账表 |

---

## 7. 复现命令

```sh
# 1) 全部五道检查
python3 docs/validate_examples.py
#    需要 xmlschema：pip install xmlschema

# 2) 单件 XSD 校验（README「校验与运行」一节的写法）
python3 -c "import xmlschema; xmlschema.XMLSchema('xsd/esml-canonical-basic.xsd').validate('L3-model/modeltype-basic.esml')"

# 3) 引擎侧：141 份示例逐件 check（负例预期非零退出）
for f in $(find . -name '*.esml' | sort); do
  esml check "$f" -L /home/ai4e18/esml/library >/dev/null 2>&1 \
    && echo "ok    $f" || echo "fail  $f"
done

# 4) 引擎侧：四方闸门（[3] 角是 reference 侧对账；在引擎仓跑）
cd ~/esml && python3 tools/four_way_gate.py

# 5) §5.9 的 §6.5 探针（条件里的参数引用不可判定）
cat > spec65-useC.esml <<'EOF'
<?xml version="1.0"?>
<esml xmlns="https://www.ai4energy.cn/esml/v1" schema="esml/v1" name="T_Spec65_UseC">
  <variableTypes><type name="real" unit="1" default="0.0" role="algebraic"/></variableTypes>
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

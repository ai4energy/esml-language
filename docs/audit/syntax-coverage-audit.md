# 语法点 ⇄ 示例 全覆盖审计（2026-11-10）

本文件是一次**机器为主、人工裁决为辅**的审计留痕。审计问题是：
**`SPEC.md` 承诺的每一个语法点，仓内有没有一份可运行的示例守着它？反过来，
XSD 声明的每一个元素/属性，是否有规范条文与示例两层支撑？**

所有数字都由 `docs/validate_examples.py`、`docs/validate_roots.py` 与
`tools/check-examples.py` 机验产出，本节只解释与裁决。起点 HEAD = `dd0e22d`。

---

## 0. 起点实测（`make check` 是红的）

| 项 | 值 | 出处 |
|---|---|---|
| 示例件数 | 150 | 检查 1 |
| XSD 机验 PASS / 负例按预期失败 / **非负例失败** | 139 / 9 / **2** | 检查 1 |
| 负例登记 | 16（schema 9 / semantic 7） | `tools/negatives.tsv` |
| 示例头部指名 SPEC 章节 | 145 / 150（**未指名 5**） | 检查 3 |
| 无 SPEC 依据的示例 | 1（`L3-model/annotation.esml`） | 检查 4 |
| `tools/check-examples.py` | EXIT=1，**违规 4** | 辅助闸门 |
| `tools/check-neg-debt.py` / `tools/check-spec-xsd-parity.py` | EXIT=0 / EXIT=0 | 辅助闸门 |
| **`make check`** | **红**（`validate_examples.py` exit 1） | Makefile |

红的两件是 `L3-model/extends.esml` 与 `L9-method-schedule/reassign.esml`：
`<extends>` / `<reassign>` 是 SPEC 附录 C 明令删除的同义元素，语言仓 XSD 正确地
不声明它们，**示例本身是错的**。

---

## 1. 两仓 XSD 字节不一致（`schema/README.md` 承诺「字节一致」）

`esml-engine-user3/schema/README.md` 写着：本目录 = canonical，各实现
**以本目录为对齐基准（字节一致）**。实测五份全部不同：

| 文件 | 语言仓行数 | diff 行数 |
|---|---:|---:|
| `esml-canonical-basic.xsd` | 1117 | 391 |
| `esml-canonical-common.xsd` | 52 | 18 |
| `esml-canonical-compute.xsd` | 612 | 138 |
| `esml-canonical-project.xsd` | 102 | 12 |
| `esml-v1.xsd` | 124 | 106 |

**方向不是单向的 —— 这一条先前的判断有误，以本段为准。** 逐条拆开后是两个
方向的混合漂移，且**语言仓这一侧是错的那一半**：

| 分歧 | 引擎 XSD | 语言仓 XSD | 谁对 |
|---|---|---|---|
| 端口变量属性 | `portRole` `causality` `carrier` | `role` | **引擎对**（SPEC §5 L363 明写 `role=` 不接受；引擎解析期 F1 硬拒 `role`） |
| `portType` 属性 | `connectorFamily` `conservation` `description` | `domain` | **引擎对**（SPEC L83 明写 `domain=` 是旧拼写、报错） |
| `port` 属性 | `connectClass` `portSet` `description` | `count` | **引擎对**（SPEC L84 / L1222 用 `connectClass` / `portSet`） |
| `instance` 属性 | `count` `extends-from` | （`count` 声明在 `port` 上） | 引擎对 `count` 宿主；语言仓对 camelCase |
| `modelType`/`system` 描述属性 | `desc` | `description` | **语言仓对**（`aliases.tsv:91` 判 `desc` 是 legacy 缩写） |
| `connection` 端点 | `a-part` `b-part` `interface` | `aPart` `bPart` `portType` | **语言仓对**（`aliases.tsv:87/88/96`） |
| 续跑时长属性 | `max-time` | `maxTime` | **语言仓对**（SPEC 附录 K L1512 + `aliases.tsv`） |
| 类型级文档/注释 | 有 `DocRefType` 三处、`AnnotationType` | 同 | 一致 |
| 变量类型属性 | 无 `nominal` `quantity` | 有 | 两仓都没接进引擎 `KNOWN_ATTRS`，见 §6 |
| `TaskType` 扩展 | `mode` `rho` `wOver` `wUnder` | 无 | **引擎对**（`8e16c782` mpc-constraints M1 已落） |
| `VendorControllerType` | `antiWindup` `tauD` `trackingTime` … | 无 | **引擎对**（示例 `T-tasks/controller.esml` 在用） |
| 全局根（假根） | `domain` `schedule` `solutionParameters` `variables` | 已删 | **语言仓对**（SPEC §13 明写不是文档根） |
| 同义元素 `extends`/`reassign`/`component` | 仍声明 | 已删 | **语言仓对**（SPEC 附录 C） |

结论：12 组分歧里 **6 组引擎对、5 组语言仓对、1 组两仓皆缺**。也就是说
「`schema/README.md` 字节一致」这句话两边**同时**违反，任何一方都不是基准。

引擎 `tools/check_three_way.py` 只拿引擎自己的 XSD 跑；语言仓 `make check`
只拿语言仓的 XSD 跑 —— **两边都结构上无法发现这层漂移**。这是本次审计发现的
最贵的一个洞：见 §9。

---

## 2. 元素层：XSD 声明 157 / 零示例 12

| 元素 | 声明处 | SPEC 点名 | 引擎实测（`esml check`） | 裁决 |
|---|---|---:|---|---|
| `flow` `potential` `stream` `constant` `var` `variable` `discrete` | basic | 19–26 | **F1 硬拒**：`legacy spelling ... use <portVariable portRole="…">` | **删声明**（见 §4） |
| `continueUntil` | basic | 1 | 收；但 SPEC 写 `maxTime`，引擎收 `max-time`，语言仓 XSD 收 `maxTime` | **补示例**（用语言仓拼法）+ 引擎单 |
| `free` | basic | 8 | `ok` | **补示例** |
| `doc` | basic | **0** | `ok`（需 `ref`，两者都收） | **补条文 + 补示例** |
| `sampling` | compute | **0** | `ok`（`size` 必填） | **补条文 + 补示例** |
| `point` / `scenario` / `scenarioChain` | project | 1 / 1 / 4 | `ok`，`scenarioChain` 伴 F21「accepted and skipped」 | **补示例**（`<data><point>` 形态，XSD PASS） |
| `param` | compute | 3 | **F1 硬拒**：`legacy spelling <param> — use <parameter>` | **引擎债**，不补示例（见 §5） |

---

## 3. 属性层：XSD 声明 121 / 零示例 40

其中 **20 个连 SPEC 条文也没有**。逐条实测引擎接受度：

| 属性 | 宿主 | 引擎 | 裁决 |
|---|---|---|---|
| `ref` `title` `summary` | `DocRefType` | `ok` | 补示例（`<metadata><doc …/></metadata>`） |
| `category` `size` | `<port>` | `ok` | 补示例 |
| `libroot` | `<systemRef>` | `ok`（解析器只存不解析；见 §5） | 补示例 + 记账 |
| `distribution` 等 | `<perturb>` | `ok` | 补示例 |
| `expr` | `<constraint>` | `ok` | 补示例 |
| `samples` `timestep` `generations` `population` | `<method>` | `ok` | 补示例 |
| `tolerancePct` | `<metric>` | `ok` | 补示例 |
| `x0` `xref` `umin` `umax` `steps` `a` `b` `c` `q` `r` | `<mpc>` | `ok` | 补示例 |
| `model` | `<surrogate>` | `ok` | 补示例 |
| `priority` `immediate` `synchronize` | `<transition>` | `ok` | 补示例 |
| `phase` | `<clock>` | **F7 未知属性**（`KNOWN_ATTRS` 无 `phase`） | **引擎债** |
| `aPart` `bPart` | `<connection>` | **F7 未知属性** | **引擎债** |
| `nominal` `quantity` | `<type>` | **F7 未知属性** | **引擎债** |
| `side` | `<port>` | **F1 拒**：`unknown attribute side` | **引擎债** |

---

## 4. 裁决 A：端口变量元素形态按单轨删除（主人 2026-11-10 定）

现状是三边打架：

- 语言仓 `xsd/esml-canonical-basic.xsd:357-374` 声明七种元素形；
- `SPEC.md` 附录 C（L1149-1152）把它写成「**有意的例外**」；
- 引擎 commit **`3d43a516`（2026-10-28，比附录 C 晚一周）** 已硬拒收，只认
  `<portVariable portRole="…">`，引擎 XSD 也只剩属性形。

**裁决：删。** 元素名给角色与属性给角色是同一语义的两种拼法，正是
「规范语法单轨」要禁的。动作：

1. `xsd/esml-canonical-basic.xsd` 删 `<variables>` 与 `<portType>` 直接子层
   两处 `flow/potential/stream/constant/var/variable/discrete` 声明，只留
   `<portVariable>`；
2. `SPEC.md` 附录 C 删掉该段「有意的例外」；
3. `SPEC.md` §5 / §2 里凡以元素形举例的句子改为属性形；
4. `L4-portvar/` 两份（`flow.esml` / `potential.esml`）内容已是属性形，只需
   头部去掉「旧元素形 `<flow>` 已退役」这类**在描述一个不存在的语法**的措辞，
   改为正面陈述属性形。

依据：`xsd/esml-canonical-basic.xsd:344` 自己的注释写着这一族是「有意的并行
写法」，与单轨条文直接冲突；引擎已按单轨收口，规范仓跟上即可。

---

## 5. 裁决 B：`annotation` 补规范条文（主人 2026-11-10 定）

`L3-model/annotation.esml` 头部引用「L-ANNOT；手册 §8.3；`scripts/check-annotations.py`」，
但：

- `annotation` / `icon` / `placement` 在 `SPEC.md` **0 命中**；
- `§8.3` **不存在**（§8 无子编号，§8.3 是引擎仓手册的编号）；
- `scripts/check-annotations.py` **不在本仓**。

而语言仓 XSD 确实声明了 `AnnotationType` 三处（basic.xsd:278/279 的
`IconType`/`PlacementType`，531/667/804 的 `annotation`），引擎也有
`tests/annotation_numeric_invariance.rs` 钉住它不改数值 —— 属
**已实现、规范没写**。

**裁决：补规范条文。** 在 `SPEC.md` §4 下新立 §4.2「图形标注 `<annotation>`」，
写明 `icon src/w/h` + `placement x/y/w/h/rot` 是纯 UI 元数据、求解器不读、
不得影响任何数值结果；把示例头部改引该条。XSD 与示例内容不变。

---

## 6. 引擎仓债（本仓不改，登记）

| 条目 | 实测 | 结论 |
|---|---|---|
| `maxTime` vs `max-time` | 语言仓 XSD + SPEC 用 `maxTime`；引擎 `parser/model.rs:1320` 与 `unknown.rs:1108` 用 `max-time` | **引擎落后**，需引擎单改拼写 |
| `<hyperParams><param>` | `aliases.tsv:65` 给了豁免；引擎仍 F1 硬拒 | 引擎债 |
| `phase` / `aPart` / `bPart` / `nominal` / `quantity` / `side` | XSD 声明了，引擎 `KNOWN_ATTRS` 没有 | 引擎债 |
| 引擎 XSD 仍声明 `component` / `extends` / `reassign` | 语言仓已删 | 引擎债 |
| 引擎 XSD 把 `domain` / `schedule` / `solutionParameters` / `variables` 声明为全局（假根） | SPEC §13 明写它们不是文档根 | 引擎债 |
| `libroot` 只存不解析 | `systemRef libroot="/nonexistent-root"` 仍 `ok` | 解析器注释自认「只保证清单形状」，规范须写明 |
| `syntax-example-engine-debt.md` 两行失效 | `syntax_L4_stream` 写「仅剩白名单登记 + 补例」，实为已全部退役；`syntax_W2_project_subset` 写 project 受阻，实测 `ok` | 引擎仓文档债 |

---

## 6.5 假绿：`anyAttribute lax` 让 XSD 机验失去判别力（本轮最重的洞）

前面 §2/§3 的一切「XSD PASS」在下面这个实测面前都不成立。

**测量**：语言仓 183 个 `complexType` 里 **140 个（77%）**挂着
`<xs:anyAttribute processContents="lax"/>`，另有 **59 处** `<xs:any>` 元素通配。
`lax` 的含义是「不认识的属性/子元素一律放行、不报错」。

**对照实验**（`/tmp/langx6`、`/tmp/langx7`，脚本见本节末）：

| 条件 | 非负例失败件数 |
|---|---:|
| 原样 XSD | **2**（`extends.esml`、`reassign.esml`） |
| 只撤 `anyAttribute` | **93** |
| 只撤 `xs:any` | **111** |
| 两者都撤 | **121 / 148** |

也就是说：`make check` 现在报「PASS 139」，撤掉通配后只剩 **27**。
**91% 的「XSD 通过」是通配符放行，不是被校验过。**

撤 `anyAttribute` 后暴露的 16 组「用了但没声明」：

| 属性 | 宿主 | 语言仓 XSD | 引擎 XSD | SPEC |
|---|---|---|---|---|
| `portRole` | `<portVariable>` | **缺**（写的是 `role`） | 有 | L363 明写用 `portRole` |
| `causality` | `<portVariable>` | **缺** | 有 | L363 明写 |
| `carrier` | `<portVariable>` | **缺** | 有 | — |
| `connectorFamily` | `<portType>` | **缺** | 有 | L83 |
| `conservation` | `<portType>` | **缺** | 有 | — |
| `connectClass` | `<port>` | **缺** | 有 | L84 |
| `count` | `<instance>` | **宿主错**（声明在 `<port>` 上） | 有 | — |
| `discipline` | `<modelType>` `<system>` | **缺**（只有 `PartitionType` 上有） | **缺** | L186 / L280 / L404 都在用 |
| `abstol` `reltol` | `<solutionParameters>` | **宿主错**（在 compute 的 `TaskType` 上） | 同 | L? |
| `name` | `<solutionParameters>` | **缺**（类型零属性） | 同 | — |
| `coordinate` `version` | `<esml>` | **缺** | **缺** | L? 示例自己写「不参与求解」 |
| `schema` `version` | `<project>` | **宿主错** | 同 | — |
| `antiWindup` `bumpless` | `<controller>` | **缺** | 有 | — |

撤 `xs:any` 后暴露的结构空洞（16 个类型「零真子元素声明、只有通配」）：
`MetadataType`、`DocRefType`、`SolutionParametersType`、`MethodsType`、
`VariableTypesType`、`PartialType`、`ComputeTasksType`，以及 2 处匿名类型。
**其中 `VariableTypesType` 最要命**：它的 133 个裸 `<type>` 子元素一个都没被
XSD 校验过（`VariableType` 类型本身是声明的，但没有任何路径引用到它）。

**结论**：这 77% 的 `lax` 不是随手写的，它是有意的设计选择（引擎 XSD 的注释
写着「lax 校验：错拼名原样保留，由语义校验报告」）。问题在于——**语言仓没有
「语义校验」那一层**。引擎有 parser 的 F1/F7 兜底；语言仓只有 XSD。于是同一份
XSD 在引擎侧是合理的宽松，在语言仓侧就变成了**没有判别力的假门**。

裁决见 §9。

---

## 7. `<scope>` 之外的真缺口（不补，记账）

`docs/coverage.md` §5.1 已登记三条「无 token 落点」的条款（附录 F9 Pantelides、
§11 物性插件、附录 F10 外部 I/O）。本次审计复核：**仍成立**，且不需要新增
示例 —— 示例必须先有规范。

新增一条：**§6.2 编号缺失**（§6.0/§6.1 之后直接 §6.3）。本仓不重排既有编号。

---

## 8. 本轮动作清单

| # | 动作 | 文件 |
|---|---|---|
| 1 | 删端口变量元素形声明 + 附录 C 例外段 | `xsd/esml-canonical-basic.xsd`、`SPEC.md` |
| 2 | 新立 §4.2 图形标注 | `SPEC.md` |
| 3 | 修两件红示例（`extends.esml` → `extendsFrom`；`reassign.esml` 并入 `reset.esml` 后删） | `L3-model/`、`L9-method-schedule/` |
| 4 | 五件未指名示例补「规范条文：」行 | `L3-model/extends.esml`、`L4-port/{conservation,flow-potential}.esml`、`L9-method-schedule/reassign.esml`、`T-tasks/tasks.esml` |
| 5 | 补 `continueUntil` / `free` / `doc` / `sampling` / `point` / `scenario` / `scenarioChain` 示例 | 各层目录 |
| 6 | 补零示例属性示例（`<doc>` / `<port>` / `<perturb>` / `<constraint>` / `<method>` / `<metric>` / `<mpc>` / `<surrogate>` / `<transition>` / `<systemRef libroot>`） | 各层目录 |
| 7 | 更新 `docs/coverage.md` | `docs/` |
| 8 | 语言仓 XSD 补齐 §6.5 的 16 组属性/宿主 | `xsd/*.xsd` |
| 9 | 建跨仓 XSD 对账闸门（§9） | `tools/` + `Makefile` |

复现命令见 `docs/coverage.md` §7。

---

## 9. 裁决 C：语言仓自己的两道闸（补，不是删 `lax`）

§6.5 把问题定位清楚了：`lax` 本身不该删（它换来的是「引擎能响、语言仓不能」
这条既成事实下的一致性），缺的是语言仓侧的**第二层**。补两道闸：

### 闸一：`--strict` 模式（判别力闸）

`docs/validate_examples.py` 增加 `--strict`：用**撤掉 `anyAttribute lax` 与
`xs:any`** 的 XSD 副本再校一遍，报出「靠通配符才通过」的清单，并把**总数**
作为指标钉住（只降不升）。

要点：

- 不默认开。开成默认会让 `make check` 立刻 121 红 —— 那不是修，是把既有债
  一次性资本化。**先登记基线 121，再逐轮收口**（与仓内既有 G11「只收不放」
  的口径一致）。
- 撤通配必须**在内存里改**，不能落盘第二份 XSD（否则又违反「字节一致」）。

### 闸二：跨仓 XSD 对账闸（漂移闸）

新脚本 `tools/check-engine-xsd-parity.py`，拿语言仓 `xsd/` 与引擎仓
`schema/` 逐类型比（同名 `complexType` 的属性集与子元素集），产出三张表：

1. 属性差集（左独有 / 右独有）—— §1 那张表就是它算出来的；
2. 子元素差集；
3. 全局根差集。

**判据不能是「必须相等」** —— 实测 12 组分歧里 5 组是引擎落后、6 组是语言仓
落后。判据应是：**每一组分歧都必须在 `tools/engine-drift.tsv` 里有一条已裁决
记录**（`方向` + `依据` + `裁决日`）。新增分歧而无记录 ⇒ 红。这样闸门问的是
「这个分歧有人想过没有」，而不是「两边像不像」——后者会逼人把错的改成对的。

`make check` 加第三道。引擎路径由环境变量 `ESML_ENGINE_DIR` 给，缺省
`~/esml-engine-user3`；目录不存在 ⇒ **跳过并打印**（不静默绿，不误红）。

### 为什么不做「以引擎为准直接覆盖」

因为 §1 实测**引擎自己也错了 5 组**（`desc` / `a-part` / `max-time` / 假根 /
同义元素）。无条件以引擎为准会把语言仓 5 处对的改错。对账闸 + 裁决台账是唯一
不会掩盖这个事实的做法。

---

## 10. 复现命令（本节全部结论都可机验）

```bash
# 基线（应当红）
cd ~/esml-repos/esml-language && make check

# §6.5 判别力实验：撤通配后重校
python3 /tmp/langx6/strip.py            # 生成 /tmp/langx6/xsd/*.xsd（已撤 anyAttribute + xs:any）
python3 /tmp/langx6/strict.py           # 打印「撤后失败件数」与逐项原因
python3 /tmp/langx7/split.py            # 分别只撤 anyAttribute / 只撤 xs:any

# §1 两仓 XSD 分歧台账
python3 /tmp/langx8/drift.py

# §2/§3 元素层/属性层零示例
python3 /tmp/langx/elems.py
python3 /tmp/langx/attrs.py
```

三个实验脚本的值已抄进 §1 与 §6.5 的表里；脚本本身留在 `/tmp`，不进仓
（一次性审计工具，不是常驻闸门）。常驻闸门是 §9 的闸一闸二。

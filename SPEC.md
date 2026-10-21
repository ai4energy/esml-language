# ESML 语言规范 v0.6.6

> 本文件 = **ESML 语言规范（canonical）**。
> ESML canonical XML 是**正统语法**；XSD 只描述 canonical ESML。
> 本规范只定义语言（XML 语法、语义、展开与求解约定），不依赖任何具体语言实现：
> 凡涉及实现，一律以**语言中立**的措辞描述，不引用具体实现的语言、文件路径、函数名或测试路径。
> 机验基准是 **XSD**（`xsd/esml-v1.xsd` + `xsd/esml-canonical-*.xsd`）。
>
> 版本：v0.5.0 起定稿；v0.5.1 附录 K schedule 编排；v0.5.2 §6.4 partition/crosslink
> 求解单元分层 + 模型体系/计算求解体系两分；v0.6.0 §13 分层验收 + XSD 分层 +
> ComputeTask 七类正名；v0.6.3 §6.5 条件组件（实例级 condition）；
> v0.6.4 §6.6 系统（flowsheet）级 `<equations>`；
> v0.6.5 §5 端口变量可带 `array=`；v0.6.6 §4.0a 方程形状决定因果计划。
>
> 本文描述 ESML 声明式物理建模语言：XML 语法、语义、编译器展开与求解约定。
> 语言以自己的术语定义；词法已收紧。
>
> **架构分工**：本规范描述"**中间表示之前**"的语言面。
> 实现可有**多份前端**；分歧只许出现在中间表示之前，各前端在中间表示之后汇合，
> 后续的 "加载中间表示 → 建模 → 建问题 → 求解" 链路统一承担。
> 撕裂/去冗余/降阶（Pantelides / 高阶导 / 简化）等结构算法都在中间表示之后。
> 规范本身不含求解算法；外部工具链（若有）仅作为并存实现按需启用，不是语言的一部分。

---

## 1. 引言与设计原则

- **模型即 XML**：组件、端口、连接、边界全部写在 XML；编译器与求解器消费 XML。
- **单一真源**：库/系统 XML 是唯一权威，派生代码不成为维护对象。
- **扁平、无深继承**：组件自带内部方程。**作者层**不写继承（组合/参数覆盖表达）；
  实现另支持消费转换库的 `<extendsFrom>`（见 §4.0）——**能力覆盖，非最佳实践**。
- **求解走编译器路径**：从文档出发，**前端展开**（含端口物化）→ **构建模型**（生成
  模型壳）→ **构建问题**（残差/雅可比/Jacobian 结构）→ **求解**（按问题类型分派到
  对应求解器：显式/隐式时程积分、非线性方程组等）。**不维护 example 层裸求解器**。
- **物性是插件、XML 库是资产**：语言不内置物性实现；运行期按需注入物性
  （已注册的外部对象 + 导数契约）。
- **单位 = 界面层元数据，数值层用裸数**：单位表与 `VariableType.unit`
  只供界面做单位校验/显示/换算；方程字面量、`<set>/<initial>`、参数 default
  一律解析为无量纲数值，**建模/求解不做任何单位换算**。术语上
  **`instances` = 组件实例集合**（XML `<instances>` / `SystemDef.instances`），
  **`units` 只指单位表**（两者不再撞名）。

### 1.1 文档骨架（`<esml>` 根 · `<metadata>`）

一份 ESML 文档的根是 `<esml>`：命名空间 `https://www.ai4energy.cn/esml/v1` **必写**，
`name` 是文档名，`schema` 可选（写 `esml/v1`）。根之下是各**顶层段**——类型
（`variableTypes` / `portTypes` / `modelTypes` / `recordTypes`）、模型体系
（`systems`）、计算面（`computeTasks`）、单位表（`units`）、函数（`functions`）、
宿主对象（`foreignObjects`）、元数据（`metadata`）等；段清单见 §2 表与 §6.9。

**`<metadata>`** 是 `<esml>` 的**可选**子元素（最多一个），承载**文档级元数据**：
常用子元素 `<author>` / `<license>` / `<description>` / `<provenance>`。
其**子结构不固定**（schema 放行任意子元素），实现可以只读不消费。
`<metadata>` **不参与编译与求解**——它写什么都不改变方程数、可解性与数值结果。

- 示例：`D-skeleton/metadata.esml`（author / license / description）、
  `D-skeleton/provenance.esml`（出处声明）。

## 2. 词法（收紧集）

> **唯一真相 = XSD（机验基准）**：canonical 元素/属性一律 **camelCase**（`modelTypes` /
> `portTypes` / `variableTypes` / `modelType` / `portType` / `portVariable` /
> `extendsFrom` / `continueFor`…），与 `xsd/esml-v1.xsd` + `xsd/esml-canonical-*.xsd`
> 下表与 §4/§5/§6 均按 camelCase 书写；**kebab-case（`<model-types>` 等）不是合法语法**，
> 会报错并提示改用 `<modelTypes>`，文档与库不得再写。

| 语法对象 | 元素/属性（canonical） | 说明 |
|---|---|---|
| 顶层 | `<esml xmlns="https://www.ai4energy.cn/esml/v1" name=...>` | 根（namespace `https://www.ai4energy.cn/esml/v1`） |
| 类型容器 | `<variableTypes>`、`<portTypes>`、`<modelTypes>` | — |
| 端口协议 | `<portType name domain>`（旧别名 `<interface>` 弃用） | 连接器"类" |
| 端口实例 | `<port name portType="X" size? count?/>`（**canonical `portType=`**；`porttype=`/`interface=` 为兼容别名，归一为 `portType`） |  |
| 端口变量 | `<portVariable name role="potential\|flow\|stream\|input\|output" type/>` | effort 并入 potential；显式域不写 role（详附录 F1）；组件方程用点号 `port.pvar` |
| 组件 | `<modelType name>` | 组件类型声明；`<members><instance name type/></members>`（§4.1）；`<extendsFrom>Base</extendsFrom>` 继承（§4.0） |
| 系统/实例 | `<system name>`/`<instances><instance name type/>` | `<system>` 也可作为 instance 的 `type` 引用（子系统，§6.4） |
| 作用域引用 | `<scope instance=".."><set path value/>`（`unit=` 非法） | `unit` 只表度量单位 |
| 变量 | `<variable name type role="state\|algebraic\|flow\|parameter" initial default/>` | — |
| 方程 | `<equation>expr (=\|~) expr</equation>` | — |
| 连接 | `<connect from=path to=path/>` | 语义见 §8 |
| 标准库引用 | `<use library="group:artifact:version"/>` | 合并坐标化组件库（§6.1） |
| 序集 | `<orderedSet name static="true"><element>...</element></orderedSet>` | 顶层声明；见附录 F |
| 选择器 | `<selectors><selector name><values><value>...</value></values><default>...</default></selector></selectors>` | 模型级（附录 B（续）— SELECTOR） |
| 事件 | `<events><when condition><assign/reinit .../>[<elsewhen condition>...]</when></events>` | L8（附录 F3）；`<reinit>` 仅用于连续状态 |
| 方法 | `<methods><onLoad><set path= value=/>*</onLoad><method name><run name=/>[<set path= value=/>]*</method></methods>` | on_load/RUN（附录 F5/F7b） |
| 自由度 | `<fixed>/<free>` 系统级块 | 钉代数变量 / 参数升未知（附录 F6/F7） |
| 调度 | `<schedule><sequence><continueFor time=.../>[<call method=.../>]*</sequence></schedule>` | （附录 K）；多段连续求解 |

**收紧规则（canonical 唯一，不向后兼容旧写法）**：
解析器对旧词法直接报错（解析器）：
- 端口协议：`<portTypes>/<portType>`；`interfaces/interface/connector/portType` → 报错
- 端口引用属性：canonical **`portType=`**；`porttype=`/`interface=` 为兼容别名（归一，不报错）；裸 `type=` → 报错
- 组件类型：`<modelTypes>/<modelType>`；`components/component`（类型位）→ 报错
- 端口变量声明：`<portVariable .../>`（仅 portType 内）；模型变量 `<variable .../>`
- 容器/单位旧写（variableTypes、min/max、toSI 等）不再接受
- 实例标签 canonical **`<instance>`**（系统内）；`scope instance=`

> **唯一写法的边界**：实例一律写 `<instance>`；`<component>` 作为元素不是合法语法，
> 会报错并提示改用 `<instance>`。XSD 为兼容旧文档仍声明该元素，
> 二者以本规范的收紧规则为准。
> **属性形态合法**：`<instance name="b" component="M"/>` 与 `type="M"` 等价
> （优先级：`type=` &gt; `model-type=` &gt; `component=`）。
- **实例必须包在 `<instances>` 内**；裸 `<instance>`（直接挂 `<system>`/`<modelType>`）→ 报错
- **实例覆盖用 `<set path= value=>`**；`<bind name= value=>` → 报错

> 存量旧写法文档（部分示例/测试）尚未全部迁移，迁移后本规范即为唯一事实。
> **机验基准是 XSD**（`xsd/esml-v1.xsd` + `xsd/esml-canonical-*.xsd`）：规范与本表若与
> XSD 不一致，以 **XSD 为准**。附录 D 仅说明旧版文档的边界，不构成本线词法。

**文件扩展名**：官方扩展名 = **`.esml`** ——
**库文件、系统、案例、计算任务一律 `.esml`**（全仓已统一：`examples`/`library`/夹具）。
`.xml` 仅作**历史兼容**（加载器仍可读），
**不推荐、文档不再以 `.xml` 举例**。用 `<use>`/`-L` 加载的库文件与案例文件同用 `.esml`。

标识符（作者书写）`[A-Za-z_][A-Za-z0-9_]*`，**不得含 `__`**（`__` 为结构保留，见 §9）；实例路径用 `.`；数值支持科学计数。说明：生成层内部扁平名（含 `port__pvar` 等）可含 `__` 作段分隔——因作者标识符禁含 `__`，任何 `__` 都无歧义地按段切分。

**保留标识符（数学常数 / 基础符号）**：`pi`/`π`、`e`/`ℯ`、`eu`/`γ`、
`im`、`Inf`/`inf`、`NaN`/`nan`、`true`/`false`、`nothing`、`missing` 等**不得用作
作者变量/参数/类型名**。它们在方程/事件表达式里被当作数学常数/基础符号，**不参与
实例命名空间前缀**：若你声明 `parameter e`
或 `Real pi`，表达式里的 `e`/`pi` 会保持裸名、解析不到实例符号而报错/兜底。
（实例：回弹系数不要叫 `e`，用 `rest`/`cr` 等。）
函数/运算符名同理不参与前缀，避开与声明显名冲突。

## 3. 类型系统

- `variableTypes` 定义量纲类型（含 `role`，可带 bounds/unit/default）。
  字段集共 15 项：
  `name` · `unit` · `quantity` · `lower_bound` · `upper_bound` · `default` ·
  `nominal` · `role` · `kind` · `domain` · `delta` · `source` · `source_name` ·
  `dimension` · `description`。
- **枚举类型**：`<type name="E" kind="enumeration" values="a,b,c" default="a"/>`
  （字面量也可用子元素 `<literal name="a"/>`）。字面量引用 `E.a` 与枚举型默认**在编译期
  解析为声明序号整数**（`a`→0、`b`→1…），故中间表示仍为数值；`kind` 如实声明为 `"enumeration"`。
  兼容源拼写 `type E = enumeration(a,b,c)` 由转换器归一化。
- 变量/端口变量**必须引用**一个已声明类型（强约束，`type="..."` 缺失 → 报错）。
- `role=state` 的变量参与微分 `D(...)`；`role=flow` 的变量在连接里守恒
  （隐式连接器电学 `PortType.vars`）。`role=stream` 是元数据（不守恒），由
  Mixer 等单元做组分加权（详附录 F1）。
- `portVariable` 的**因果角色用 `role`**：`role=potential`（势，连接相等）/ `role=flow`
  （流，节点守恒）/ `role=stream`（流股，不守恒）/ `role=input|output`（信号因果）。
  `var=` 不是合法写法，出现即报错。
- 差值/仿射换算等按类型定义推进（quantity/delta 属后续类型扩展项）；
  单位/量纲语义由 `VariableType.unit/quantity` 标注，**数值层用裸数**
  （详见 §1 设计原则）。
- **类型按类别包裹（wrapper）**：`<variableTypes>` 里的 `<type>` 可以**直接裸放**，
  也可以按类别包一层——`<typesGeneric>` / `<typesThermal>` / `<typesDimensionless>`
  （`discipline=` 可选）。**包内 `<type>` 与裸放完全等价**，wrapper 只表达
  「这一批类型属于哪一类」，不改变声明语义。示例：`L0-type-unit/typesgeneric.esml`、
  `L0-type-unit/typesthermal.esml`、`L0-type-unit/type-unit.esml`
  （枚举类型放在 `<typesDimensionless>` 内）。
- **记录类型**：顶层 `<recordTypes>` 目录内写 `<recordType name>`，其下用
  `<field name type default role unit/>` 逐字段声明。示例：`L0-type-unit/record-type.esml`。
- **单位表分组**：`<units>` 的 `<unitsDerived>` 内可直接放 `<unit>`，也可先放
  `<group name>` 再在组内放 `<unit>`；组内 `<unit>` 与组外平级可用（分组只是组织形式，
  不改变单位语义——见附录 J）。示例：`L0-type-unit/units-group.esml`。

## 4. 组件（modelType）

组件 = `name + domain + parameters + variables + ports + equations`。

组件可带**可选文档性说明** `<description>人写的整段文本</description>`（`<modelType>` 的
直接子元素，最多一个）；它是**文档性内容**，不参与编译/求解，与类型字段里的
`description`（`VariableType` 的键）同名不同位。
**守恒/本构方程写在组件内部**，可引用自身参数/变量/端口变量（点号）。例：

```xml
<modelType name="Conductor" discipline="thermal">
  <ports>
    <port name="port_a" portType="HeatPort"/>
    <port name="port_b" portType="HeatPort"/>
  </ports>
  <parameters><parameter name="R" type="resistance" default="0.1"/></parameters>
  <variables/>
  <equations>
    <equation name="ohm">port_a.T - port_b.T = R * port_a.Q_flow</equation>
    <equation name="cons">port_a.Q_flow + port_b.Q_flow = 0</equation>
  </equations>
</modelType>
```

**端口变量作者语法**：方程用**点号** `port.pvar`（如 `port_a.T`、`port_a.Q_flow`）；
实现重写为内部扁平名 `port__pvar` 并**自动物化**端口未知量（仅被 `<connect>` 连接或被点号引用的
端口），**作者无需手写 `<variable name="port_a__T"/>`**。状态端口用点号声明覆盖：
`<variable name="port.T" role="state" initial="300"/>`。`__` 是**内部**命名分隔符（§9），作者层不写。

### 4.0a 方程形状决定因果计划（**作者须知**）

ESML 的因果化在**每个方程上做"可解变量判定"**：
**能隔离出哪个变量、就把它当成前向赋值**；隔离不出来的方程进 Newton 残差块。
由此有两条**会直接影响模型能否跑通**的作者规矩 —— 尤其在有**循环流股**（回流、
再循环、闭合回路）的流程里：

**① 想让方程进 Newton（保留环保留），就别让它能解出单变量。**

```xml
<!-- ✗ LHS 单变量 ⇒ 被当"前向赋值" ⇒ 在循环里把代数环强行打开、取未初始化值 -->
<equation>Outlet.F = Inlet1.F + Inlet2.F</equation>

<!-- ✓ 守恒式（LHS 含多项）⇒ 无法直接解出单变量 ⇒ 必须 Newton 同时解 ⇒ 环保留 -->
<equation>Outlet.F - Inlet1.F - Inlet2.F = 0</equation>
```

**② 绝不让"在循环里可能为 0 的量"成为赋值式的分母。**

`Outlet.w[i] = (Inlet1.F*Inlet1.w[i] + Inlet2.F*Inlet2.w[i]) / Outlet.F` 看似自然，
但 `Inlet2.w[i]` **也能被隔离出来**（移项后除以 `Inlet2.F`）—— 因果化在"解出口"
与"解入口"**同级**时可能选后者；而**循环流程在 t=0 时回流支路流量天然为 0** ⇒ **除零
⇒ `-inf`**，再沿循环链污染到储能单元（例如 `Mx.Inlet2.w_1` 取到 `-inf`，下游温度随之全错）。

**正解是两段式**（引入中间量，让**只有出口**可被隔离）：

```xml
<variables><variable name="mt" type="MASSFLOW" array="3"/></variables>
<equations>
  <for var="i" in="1..3"><body>
    <equation>mt[i] - Inlet1.F*Inlet1.w[i] - Inlet2.F*Inlet2.w[i] = 0</equation>  <!-- 真守恒 -->
    <equation>Outlet.w[i] - mt[i] / Outlet.F = 0</equation>                       <!-- 唯一可解：Outlet.w[i] -->
  </body></for>
</equations>
```

**一般原则**：写方程时问自己"**这条式子能解出哪些变量**"；凡是**不该被解出来**的量，
要让它在**结构上无法被隔离**（放进两边都含它的守恒式，或引入中间变量分段）。

**诊断约定**：实现**应**提供一种"打印因果计划"的诊断开关（打印三张表：
**自由量 / 前向赋值 / 残差行**，每条赋值式给出完整表达式；并标记求值中的非有限值），

> **另一条相关的**：模型级 `<if>`（§6.5 / 附录「模型级 IF」）是"模式选择"的
> **正规写法**，降级为 `lhs = ifelse(cond, rhsA, rhsB)` —— **一个 `<if>` 只产生一条
> 方程**（两分支 `lhs` 须一致）；要写 6 个出口量就写 **6 个 `<if>`**，塞进一个里
> **只生效第一条**（其余分支不生成方程，对应未知量会缺方程）。

### 4.0 继承 `<extendsFrom>`（消费转换库）

`<modelType>` 可声明 `<extendsFrom>Base,Other</extendsFrom>`（子元素，逗号分隔）或
`extendsFrom="Base"` 属性。build 前实现把基类 `ports / variables / parameters / equations /
discrete / events / members / connections` **合并**进派生类型（**派生同名优先**），递归解析、
环报错、基类缺失 → `@warn` stub。**定位为能力覆盖（capability），最佳实践不推荐继承**：
ESML 原生作者优先**组合（§4.1）/参数覆盖**；`<extendsFrom>` 主要服务于第三方转换库的消费。

**`redeclare` / `replaceable`（canonical 表示）**：`redeclare` 语义等价于
**派生组件里声明与基类同名的** parameter/variable/member/discrete（合并规则「派生同名胜」）。
可选显式标记 `redeclare="true"`：名字必须在基类存在（否则**响亮报错**，
防拼写错静默新增）。`replaceable="true"` 为元数据（未被替换时行为等同普通声明）。

**`<extends>`（类级继承的 canonical 子元素形态）**：`<modelType>` 内可写
`<extends name="Base"/>`（等价属性写法 `extends="Base"`），声明**同一文档内**声明的
基类。它与 `<extendsFrom>` **并列**、不是同一件事：`<extendsFrom>` 合并的是
**第三方转换库**的基类，`<extends>` 合并的是**本文档内**的基类；两者合并规则同为
**派生同名优先**。示例：`L3-model/extends.esml`（子类型继承基类参数 `k`）。

### 4.1 复合组件

复用 = 嵌入/组合（无深继承；类比 Go 嵌入而非 C++ 继承）。一个 `modelType` 若带
`<members>` 就是**复合组件**。**复合自身是一等模型**：
可声明自己的参数/变量/方程/端口；成员以 `父实例__成员名` 追加展开，壳实例**保留**，
内部 `<connections>` 把**自己的端口**（无实例头的裸口名，如 `"L"`）接到成员端口
（`"a.left"`），成员间内部接线同 。系统层连接复合端口与连接普通端口一致
（real↔real 逐 pvar 相等）。例：

```xml
<modelType name="BoilerA" discipline="thermal">
  <members>
    <instance name="hot"    type="FixedT"/>
    <instance name="heater" type="Conductor"/>
    <instance name="cold"   type="FixedT"/>
  </members>
  <connections>
    <connection from="hot.port" to="heater.port_a"/>
    <connection from="heater.port_b" to="cold.port"/>
  </connections>
</modelType>
```

语义（在中间表示之前完成展开）：
- **成员名即模板**：`<instance name type>` 的名是复合内部的固定名；实例化后
  展平为 `父实例__成员名`（嵌套复合再叠加，如 `d2__core__hot`）。递归展开直到
  全是叶组件。
- **内部接线**：`<connections>` 只引用本复合声明的成员名；展开时逐层加 `父__` 前缀
  并并入系统连接表。
- **使用侧限定路径寻址**（系统层 `<scope instance="复合实例">`）：
  `<set path="成员.参数" value/>` 在展开时改写为对叶实例 `父__成员` 的参数覆盖
  （嵌套链式：`core.hot.Tset` → `d2__core__hot`）。参数覆盖 vs 变量钉值分开：
  参数用 `set path=`，变量用方程/`<initial>`。
- 复合组件是**库内容**（§6.3 只收 component，复合=component 的装配形态，可入
  标准库）；`<set>` 只在**使用侧**（系统/子系统）写，组件内部不放。
- 复合自带参数/端口/方程：**支持**（壳保留）；穿透式端口（成员口自动对外可见）仍**不支持**，
  用壳自身端口显式接线建模。撕裂/去冗余/降阶不在此（中间表示之后）。
- 示例：复合组件 `Chain`（壳端口 L/R + 成员 a/b 串联），信号从 Src(5) 经 Chain 传到 Snk。

## 5. 端口（portType / port）

- **PortType = 类型**：声明一组端口变量（可带 role potential/flow/stream/input/output，也可为
  无 role 的显式域变量束），定义一次。
- **Port = 实例**：组件/系统上的连接点，`portType=` 引用一个 PortType。
- 端口本身**不携带方程**；耦合语义由连接生成（§8）。
- 端口机制是**通用组网接口**（电/热/流/工艺/信号皆然）：隐式域由连接生成守恒
  （potential/flow），显式域为 PortType-pure 逐 pvar 相等（守恒/本构在单元内）。示例（电隐式）：
```xml
<portTypes name="electrical-portTypes">
  <portType name="ElecPin" connectorFamily="electrical">
    <variables>
      <portVariable name="v" role="potential" type="voltage"/>
      <portVariable name="i" role="flow"      type="current"/>
    </variables>
  </portType>
</portTypes>
```

**role 词表与层次**：portVariable 的 `role=` 值分两类——
物理连接器 `potential | through(flow 别名) | stream`（隐式域电/力守恒生成用；through=结点守恒量）；信号 `input|output`
（因果）。**显式域（热/流/工艺）元件同样走 PortType 端口**（PortType-pure，
连接=逐 pvar 相等、守恒/本构在单元内）：端口变量多为无 role 的普通变量束，
**勿**标 `role="flow"`/`potential` 等（否则会触发隐式 wire 守恒叠加在显式相等上，见附录 F1）。
端口级可加 `category="inlet|outlet|bi-directional"` 或自定义类别 + 连接规则表（附录 F4）作护栏。

**端口变量可带数组维度 `array=`（与 `<variable>` 的写法一致）**：

流股是**显式变量束 + 组分数组**——例如标准库的
`fluidMaterial` 端口带 `w_i, i ∈ C`（组分分数）。故 `<portVariable>` 与 `<variable>` /
`<parameter>` 一致，接受以下属性：

```xml
<portType name="fluidMaterial" connectorFamily="fluid-material">
  <variables>
    <portVariable name="F" type="MASSFLOW"/>              <!-- 标量：质量流量 -->
    <portVariable name="w" type="MASSFRA" array="NComp"/> <!-- 数组：组分分数 -->
    <portVariable name="h" type="MASSENTH"/>
    <portVariable name="P" type="PRESSURE"/>
  </variables>
</portType>
```

**`initial` 在端口上尤其有用**：**循环流程 t=0 时回流支路
流量天然为 0**，而组分/焓方程若被因果化"解向入口"就会除它 ⇒ `-inf`。给一个**非零
起点**（即初值猜测）能让 Newton 从物理解附近出发：

```xml
<portVariable name="w" type="MASSFRA" array="NComp" initial="{1.0, 0.0, 0.0}"/>
```

（**注意**：`initial` 只是**求解起点**，不是"钉值" —— 端口变量的**值**仍由连接或
单元内方程给，见 §8。另见 §4.0a 的两条作者规矩。）

* **允许的属性**：`name`（必需）、`role`、`type`、`array`、`initial`、`default`、`description`。
  `direction=` **不接受**（端口的方向在 `<port category=/direction=>` 上，不在其内部变量上）；
  任何未知拼写一律**响亮报错**，不静默丢弃。
* **`array` 的展开规则与普通变量完全一致**（§9）：`array="n"` → `w_1..w_n`；
  `array="Species"`（ordered-set 维度）→ 按**成员名**展开；`array="n,m"` → `w_i_j`。
* **引用形式**：`port.pvar[i]`（如 `out.w[1]`）解析到展开后的元素符号 `out.w_1`。
* **连接语义不变**：仍按 §8 —— 显式域下 `connect` 只令两端 pvar **逐元素相等**，
  守恒写在单元内部；端口数组不引入任何额外的隐式守恒。
* **`role` 与 `array` 正交**：显式域端口通常**无 role**；标了 `potential`/`flow` 的
  数组端口才走隐式域（每元素势相等 + 每元素流守恒）。

**展开**：声明期展开为逐元素端口变量，索引写作 `port.pvar[i]`；
`<connect>` 对数组端口逐元素建相等约束，流程层无需手工绑定。

**`<constant>` 元素形态**：`PortVariableType` 接受 `<constant>` 作为
portVariable 子元素，语义等价于 `<portVariable role="constant">`。两种写法一致：
```xml
<portVariable name="g" role="constant" type="real" default="9.81"/>
<constant name="g" type="real" default="9.81"/>
```

**端口壳 / 外部 I/O（信号）建模约定**：需要把"外部输入"接进组件/单机时，用**信号口**
（`role="input|output"`，附录 F2/F10）而不是外部改参数：
- 被控/单机暴露 **command 口（input）**收操纵量、**measurement 口（output）**回读可观测量；
  驱动/源/控制器作为独立组件经 `connect`（output→input）接上——操纵量由此从"参数"变成
  **input 口代数变量**（由连接相等定值），不再靠 `<set>`/外部写参数驱动。
- 组件的 input 口变量需有驱动源（悬空 → 欠定，编译期应报）；output 口变量由组件内方程定值，可悬空。
- 闭环两类范式：**语言层连续控制器**（控制器为组件，积分/饱和在方程内，见附录 F10）与
  **软件 sample-hold 离散控制器**（外部循环逐 dt 驱动源，见 F10 分界）。
- 示例：教学热模型的端口闭环。

## 6. 系统、实例与参数覆盖

> **实例必须包在 `<instances>` 内**：`<system>`/`<modelType>` 直接挂裸 `<instance>` **非法**
> （XSD `SystemType` 的唯一实例容器是 `<instances>`；直接挂裸 `<instance>` 会**响亮报错**
> 并提示改为 `<instances>` 内声明，不静默忽略）。实例参数覆盖用
> `<instance><set path="…" value="…"/></instance>`；`<bind name= value=>` **非法** → 报错。

```xml
<system name="Min" discipline="thermal">
  <instances>
    <instance name="hot"  type="FixedT"/>
    <instance name="c1"   type="Conductor"/>
    <instance name="c2"   type="Conductor"/>
    <instance name="cold" type="FixedT"/>
  </instances>
  <connections> ... </connections>
  <sets>
    <scope instance="hot"><set path="Tset" value="400.0"/></scope>
    <scope instance="c1"><set path="R" value="0.2"/></scope>
  </sets>
</system>
```
- `<scope instance=...>`；`unit=` 不再接受。
- 参数覆盖 = 类型 default 的实例级修改。

### 6.0 实例参数覆盖：scope / set / path

```xml
<scope instance="R1">
  <set path="H_res" value="120.0"/>
</scope>
```
- `scope instance=`：选中一个实例（`unit=` 非法）；
- `set path=...`：在**该实例内部**按"声明位置路径"覆盖一个量的值；
  `path` 是属性路径（现在多为参数名，语义上可含 `.` 或下标，与 `<connect>` 的点号
  路径同体系），不是随意起名；旧写法 `<set name=` 已收紧报错；
- 语义 = **实例级参数覆盖**：覆盖实例的值，类型定义里的 default 不变 → 类型可复用。
- 路径若无匹配声明量，建系时报错（校验）。
- **语义基准（两分）**：
  1. `<set path=...>` 只做**参数覆盖**（参数/常量级修改）；参数可为叶子或**限定路径进模板成员**
     （`<set path="heater.T_in" .../>`，scope instance=boilerA；成员名模板定死、使用者可寻址不改名）；
  2. **变量不靠 `<set>` 钉值**：要把某变量当已知/边界，用**方程**（系统里加钉值方程 var=value），
     或 `<initial>` 约束初值；不要把待求变量的"规格化"与参数覆盖混为一谈。
- 内部成员默认**可限定路径寻址**（读/修饰参数/加方程钉值），模板作者可用封装/暴露控制可见度。

**初始化（同基准）**：
- 模板内 `<variable ... role="state" initial="..."/>` = 默认初值/猜测（组件作者设，内部成员同理）；
- 系统层覆盖用 `<initial><scope instance="a1"><equation>var = expr</equation></scope></initial>`
  （对顶层公开量；若实现支持层级，内部成员用限定路径如 `heater.T`），由 DAE 初值求解得自洽起点；
- `<set>` 不改变量初值、也不"规格化"变量——那些走 `<initial>`/边界方程。

### 6.1 标准库坐标引用

- **标准库包** = 一个坐标化的库 XML（`coordinate="g:a:v"`），包含组件/端口/类型定义，
  由库坐标经 registry 解析为文件。
- **系统文件**可只写拓扑/边界，用 `<use library="g:a:v"/>` 引用库包；`use` 指令
  读取各库并合并后再接入系统
- 目的：组件一次入库、多系统按坐标复用；系统文件保持"纯接线+边界"（热示例已示范）。
- 坐标规范：`group:artifact:version`（Maven 风格）。

### 6.3 分层归属（库 vs 案例）

- **标准库只收 component**（叶子 + 复合 `<members>`）；
- **system 与 partition 不是可复用的库内容**——可作为**案例/examples 保留**（演示用法），但
  不进入坐标包/registry 的内容集。
- **库文件可自带一个自包含示范 `<system>`**：让每个库 XML 都能被单独
  `solve`/`simulate` 验证（消灭"无法验证的文件"）。**消费语义**：被 `<use>`/`-L` 合并时，
  展开时只取参数/端口/方程正文，
  示例系统即使与主模型同文件也不会被实例化（只实例化被选系统）。
  `<instance>` 闭包线：若被引系统与主模型同文件，取缺省系统（无显式 `<system>` 时）
  显式 `--system Demo` 仍可运行该示范。

### 6.4 partition / crosslink（求解单元分层）

**可求解单元是 `<system>`**：内部自带组件/方程 → **内部联立**。
- 全局只有一个可求解单元 → 就叫 **system**（唯一系统，直接解）；
- 由多个可求解单元组成 → 每个是 **partition**（各自内部自解），单元之间用 **crosslink**
  表达边界/接口耦合（**模块间联立**）——即「系统 = 子系统-crosslink-子系统」的联立模块法两层结构
  （模块内联立 + 模块间联立方程）。求解实际发生在 partition；求解/协调属**计算求解体系**
  （S 层，见 §10 与附录 M），与模型体系分开。

**算符分层**：
- `connect` = **组件间**建模耦合（守恒/相等），端点是组件的 port（见 §8）；
- `crosslink` = **子系统间**边界/接口约束（跨域/跨时层传值或匹配），默认并入整体联立
  （= 联立方程法，结果与不分区一致）；显式分区时由协调器在各 partition 接口上迭代。

**crosslink 端点 = port 束（interface ≡ port）**：子系统要对外耦合的量也用 PortType 变量束在
子系统上声明成 port，不另造一类「interface」元素（ interface 一词已因类型/实例歧义改名
PortType/Port；这里仅指**叫法**，XML 仍是 `<port portType=…/>`）。区分语义的是算符
（connect vs crosslink）与层级，不是端点名词。

**子系统**：`<system>` 内一个 instance 的 `type` 引用另一个 `<system>` 名时，
后者即前者的子系统；展开时把后者的全部实例、连接与参数覆盖并入前者，
并统一加 `pf__` 前缀避免命名冲突，递归展开直至全部为原子组件。
instance 的 `type` 指向 `<system>` 时，它按子系统展开，不当作缺失外部库的占位处理。

> **`<subsystem>` 不是独立元素**：子系统只有 `<system>` 作 `type=` 复用这一种构造方式。
> `subsystem=` 属性别名无效，请用 `partition=`。

**语义**：系统级 `<links>` 下的 `<crosslink from to/>`（端点=子系统实例.成员.量 的限定路径）
在子系统展开时把父系统对子系统的边界引用重映射为扁平名，并入连接（相等约束），
即「系统 = 子系统×crosslink×子系统」整体联立。分区边界求解与协同仿真主控属计算求解体系
（S 层），另有规范；图分解建模（市场/分层/多尺度/储能/电解器/随机规划/SVaR/MHE）
的子系统显式表达属图模型层，不属于本节的基本求解单元分层。

**元素形态**：系统级 `<partitions>` 表内写 `<partition id name discipline timeLayer/>`——
`id` **从 1 起**（`0` 保留给「未分区」，`id="0"` 报错），`discipline` 标分区的学科域，
`timeLayer` 标跨时层序号（>0 时生效）；实例用 `partition="id"` 归入分区。
跨分区耦合写在系统级 `<links><crosslink from to/></links>`（端点 = 实例.成员.量 的限定路径；
旧拼写 `<link>` 已被拒绝）。**分区是可选的解耦标注**：去掉 `<partitions>` /
`partition=` / `<crosslink>`、改写为 `<connection>`，结果与不分区一致。
示例：`L7-partition/partition-crosslink.esml`（两分区一 crosslink）、
`L7-partition/partition-chain.esml`（三分区两 crosslink 串成一条链）、
`L7-partition/subsystem-crosslink.esml`（子系统型 crosslink）。

**计算域声明**：顶层 `<domains><domain name><discretization method order intervals/></domain></domains>`
声明计算域及其离散区间数（`lowerBound` / `upperBound` / `method` / `order` 是扩展属性，
不参与求解语义）。示例：`L7-partition/domain.esml`。

### 6.5 条件组件（实例级 `condition`）

组件可按条件实例化：条件为假则**该实例、其实例方程
与连接都不进模型**。ESML canonical 用 `condition` 属性表达（与 `<when condition=…>`
/ `<transition condition=…>` 同名）：

```xml
<instances>
  <instance name="c" type="CondComp" condition="useC"/>
</instances>
```

- `condition` = **布尔表达式**，操作数为**参数 / 常量 / 序集成员**（构建期可判）；
- 语义（建模期求值）：
  - **静态 false** → 实例被**排除**：其实例方程、以其为端点的 `<connect>` 全部丢弃；
  - **恒真 / 缺省** → 正常实例化（等价 `condition="true"`）；
  - **不可静态判定** → **报错**（条件组件必须由参数驱动；不引入运行期
    变结构，保持扁平 DAE 方程数固定）。
- 与**方程级**条件（§7 `ifelse` / `<if>` / `<case>`）不同：后者改方程右端，
  本条改**实例集合（拓扑）**。
- 属性写法：实例上写 `condition="…"`（等价 `if="…"`）。
- 示例：`L5-instance/instance-condition.esml`（三个实例：缺省恒真 / 条件为真 /
  条件为假——条件为假那个实例连同其实例方程一并消失，模型里**没有**它，
  不是「解成 0」）；
  负例 `L5-instance/instance-condition-undecidable.esml`（条件写成对参数的
  引用，构建期折叠不出来 ⇒ `solve` / `simulate` 响亮报错）。

### 6.6 系统（flowsheet）级方程 `<equations>`

一种方言把组件与方程放在同一个顶层（模型级 `equation` 段）；另一种
Process/Case 也有 flowsheet 级 `EQUATION`。ESML canonical 对应地允许 `<system>`
自带 `<equations>`：

```xml
<system name="P">
  <instances>
    <instance name="u1" type="Mixer"/>
    <instance name="u2" type="Tank"/>
  </instances>
  <equations>
    <equation>u2.T = 300</equation>        <!-- 流程级规格 -->
    <equation>u1.y = u2.y + 1</equation>
  </equations>
</system>
```

- 方程**引用实例量** `inst.var`（点号路径）；构建期折为扁平名
  `inst__var` 并入整体残差（与 `<connect>` 端点同体系）。
- 与 `<modelType>` 的 `<equations>` 语义一致；差别只是这一层没有自己的变量表，
  声明的量来自实例。
- 本层与 `<modelType>` 级方程同语义，二者可混用。

### 6.7 系统初始化过程（`<initialisationProcedures>`）

**用途**：系统求解前**有序初始化步骤**（赋值/求解/分支跳转），对应
`$ADVANCE` / `$COMPLETE` / `$JUMP_TO` 机制。

**canonical 形态**：
```xml
<system name="Seq">
  <instances>...</instances>
  <initialisationProcedures>
    <initialisationProcedure name="cooling">
      <use><unit name="real" procedure="standard"/></use>
      <start>
        <set path="m.x" value="0.5"/>
        <assign path="m.y" value="m.x + 1"/>
      </start>
      <next>
        <moveTo><set path="m.x" value="1.5"/></moveTo>
        <jumpTo><set path="m.y" value="2.5"/></jumpTo>
        <advance unit="s"/>
        <complete unit="s"/>
      </next>
    </initialisationProcedure>
  </initialisationProcedures>
</system>
```

**子元素**：

| 层 | 子元素 | 含义 |
|---|---|---|
| `<initialisationProcedures>` | `<initialisationProcedure name>` | 容器内一条条**单数**过程；`name` 是过程标识 |
| `<initialisationProcedure>` | `<use>` | 引用库包/单位过程：`<use><unit name="…" procedure="…"/></use>`（`<unit>` 是 `<use>` 的子元素，不是并列层） |
| `<initialisationProcedure>` | `<start>` | 入口序列；内含 `<set>` / `<assign>` / `<selector>` / `<replace>`（寻址用 `path=`） |
| `<initialisationProcedure>` | `<next>` | 序列延续；内含 `<moveTo>` / `<jumpTo>` / `<advance>` / `<complete>` |

**拼写单轨**：容器与全部子元素是 **camelCase** —— `<initialisationProcedures>` /
`<initialisationProcedure>` / `<moveTo>` / `<jumpTo>`；kebab 拼法
（`<initialisation-procedures>` / `<move-to>` / `<jump-to>`）一律拒收。

**载荷**：`<moveTo>` / `<jumpTo>` 的**子元素**带 `path` / `value`
（`<moveTo><set path="m.x" value="2.0"/></moveTo>`），不是自身的 `target` 属性；
`<advance>` / `<complete>` 带 `unit=`。寻址用作者点号 `m.x`（§3 / §9）。

> **待实现**：`<advance>` 的**条件**形式（`<advance until="t > 5"/>`）目前
> 解析层**不读** `until`（只读 `unit`），条件推进尚未实现；本节只列已实现形态。

示例：`L2-discrete/initialisationprocedures.esml`（`<jumpTo>` / `<complete>` 支）、
`L2-discrete/initialisationprocedure-advance.esml`（`<moveTo>` / `<advance>` 支）。

本结构在解析期读取并展开。

### 6.8 工程包装容器（`<project>` / `<tasks>` 顶层壳）

**用途**：把多个 `<esml>` 模型 + `<computeTasks>` 计算任务**打包**为一个工程单元。

**canonical 形态**（`xsd/esml-canonical-project.xsd`）：
```xml
<project name="MyProject" version="1.0">
  <systems>
    <systemRef name="chain" src="models/thermal-chain.esml"/>
    <systemRef name="ctrl" src="models/ctrl.sys.esml"/>
  </systems>
  <computeTasks>
    <task name="steady" kind="simulate" target="thermal_chain">
      <tspan from="0" to="60"/>
      <tolerance abstol="1e-6" reltol="1e-3"/>
    </task>
    <task name="tune" kind="optimize" target="ctrl">
      <method name="ipopt"/>
      <constraints>
        <constraint>x >= 0</constraint>
      </constraints>
    </task>
  </computeTasks>
</project>
```

> **拼写单轨**：任务条目元素名是 **`<task>`**（`<computeTasks>` 容器内的单数条目），
> 不是 `<computeTask>`。`xsd/esml-canonical-compute.xsd` 只声明 `<computeTasks>` → `<task>`
> 一种写法，`<computeTask>` 在任何 schema 里都不存在，按拼写单轨纪律一律拒绝。
> 段长属性用 `<tspan from to/>`（`TspanType`：`from` 默认 0、`to` 必填），
> 没有 `<duration>` 这种元素。

**结构**：

| 层级 | 内容 |
|---|---|
| `<project>` | 属性 `name`、`description`；子元素顺序 `systems` → `computeTasks` → `scenarioChain`，各至多一个 |
| `<systems>` | 一组 `<systemRef src="…">`；`src` 指向模型文件，`system` 可指定文件内系统名，`libroot` 可加库根 |
| `<computeTasks>` | 计算任务表：容器内一条条 `<task>`，七类 `kind`，见 §6.9 |
| `<scenarioChain>` | 一组 `<scenario>`，每个可含 `<point>` / `<set>` / `<data>` |

元素名用 camelCase（`systemRef`、`computeTasks`、`scenarioChain`）；
kebab-case 拼写作为兼容别名接受。

**`<tasks>` 外层壳**：`<computeTasks>` 之外的**可选外包装**，可与顶层其它元素并列。
壳内子元素按松散规则透传（不另设结构约束）—— 它不引入新语义，只是给任务表
套一层名字，便于同一文档放多张任务表。解析按 descendants() 找规范名
`computeTasks` ⇒ **壳内嵌套的 `<computeTasks>` 被实读**，`<tasks>` 与
`<computeTasks>` 不是两个平级概念，是同一个东西包了一层。
canonical 声明：`xsd/esml-canonical-compute.xsd` 的 `<tasks>` 全局元素，
`esml-canonical-basic.xsd` 的 `<esml>` 子元素表引用之（入口 schema
`esml-v1.xsd` 早已声明同名根）。
示例：`T-tasks/tasks.esml`。

### 6.9 计算任务表（`<computeTasks>` / `<task>`）

**用途**：模型体系与计算体系同处一个文档时，`<computeTasks>` 挂任务表，
`<task>` 是**单条任务声明** —— 描述层，只说「算什么」，不写算法。
模型面与任务面可同处一个 `<esml>` 根（`esml-canonical-basic.xsd` include compute）。

```xml
<computeTasks name="runs" target="thermal_chain">
  <task name="transient" kind="simulate" target="thermal_chain">
    <tspan from="0" to="60"/>
    <solver name="radau"/>
  </task>
  <task name="tune" kind="optimize" target="thermal_chain">
    <decision name="K" lower="1" upper="10"/>
    <objective>min (K - 4)^2</objective>
    <constraints><constraint>K &gt;= 0</constraint></constraints>
  </task>
</computeTasks>
```

**结构**：

| 层 | 内容 |
|---|---|
| `<computeTasks>` | 任务表容器；属性 `name` / `target` / `schema` 均可选 |
| `<task>` | 属性 **`kind` 必填**（七类闭集，见附录 M）、**`name` 必填**；`target` / `description` 可选 |
| 子元素 | 载荷由 `kind` 决定（见下表）；同一 `kind` 可按需重复与扩展元数据并存 |

**七类 `kind` 与其载荷**（`kind` 决定结构，守恒由结构决定）：

| `kind` | 核心载荷 |
|---|---|
| `simulate` | `<tspan from to/>`、`<solver>` |
| `sensitivity` | `<perturb>`（属性式：`name` / `fraction` / `lower` / `upper`）、`<output>`（`<var>` 列表） |
| `estimation` | `<estimate>`（`<var initial/>` 或属性式 `initial`）、`<data>` |
| `optimize` | `<decision>`（`<var lower upper/>` 或属性式）、`<objective>`（含 `<expr>`）、`<constraints>`（含 `<constraint>`）、`<solver>` |
| `control` | `<mpc N dt/>`（滚动时域） |
| `surrogate` | `<surrogate method degree/>`、`<data>` |
| `validation` | `<metrics>`（含 `<metric>`）、`<data>` |

**求解约定**：按 `kind` 构造问题再求解（任务声明 → 问题树 → 求解）；
`kind` 是**闭集**，新增能力走附录 M 的功能层机制与组合，不新增 `kind`。

**任务级元数据元素**（附录 M「metadata 参数」的落地清单）：`<task>` 除上表的
`kind` 载荷外，还可带**任务附属元数据** —— 只承载声明性信息（数据源引用、
目标/基准/验收、控制器与增益、执行器/传感器/被控量、超参），
**不参与求解语义**。清单与 `esml-canonical-compute.xsd` 的 `TaskType` 子元素
一一对应：

| 元数据元素 | 载荷 | 示例 |
|---|---|---|
| `<verdict>` / `<status>` | 自由文本 | `T-tasks/task-vendor-text.esml` / `T-tasks/status.esml` |
| `<tolerance>` | 自由文本 | `T-tasks/tolerance.esml` |
| `<dataset>` / `<testData>` / `<reference>` | 数据源引用（`source` / `cols` / `format`） | `T-tasks/dataset.esml` / `T-tasks/test-data.esml` / `T-tasks/reference.esml` |
| `<target>` / `<targets>` | 目标引用 | `T-tasks/target.esml` / `T-tasks/targets.esml` |
| `<features>` / `<feature>` | 特性声明 | `T-tasks/features.esml` / `T-tasks/feature.esml` |
| `<checks>` / `<check>` | 验收断言 | `T-tasks/checks.esml` / `T-tasks/check.esml` |
| `<constraints>` / `<constraint>` | 约束 | `T-tasks/task-constraint.esml` |
| `<hyperParams>` | 超参（`<param name value/>`） | `T-tasks/hyperparams.esml` |
| `<benchmarks>` / `<benchmark>` | 基准 | `T-tasks/benchmarks.esml` / `T-tasks/task-vendor-text.esml` |
| `<controller>`（内含 `<setpoint>` / `<gains>`） | 控制器声明 | `T-tasks/controller.esml` / `T-tasks/controller-gains.esml` / `T-tasks/gains.esml` |
| `<setpoint>` | 设定点 | `T-tasks/setpoint.esml` |
| `<actuator>` / `<sensor>` / `<controlled>` | 执行器 / 传感器 / 被控量 | `T-tasks/actuator.esml` / `T-tasks/sensor.esml` / `T-tasks/controlled.esml` |
| `<controlVars>` / `<designVars>` | 控制变量 / 设计变量（`<var name/>`） | `T-tasks/control-vars.esml` / `T-tasks/design-vars.esml` / `T-tasks/controlled-control-vars.esml` |
| `<outputList>` | 输出列表（`<var name/>`） | `T-tasks/outputlist.esml` |
| `<description>` | 自由文本 | （暂缺示例） |

⚠ **拼写**：这批元素在 schema 里是 camelCase（`hyperParams`、`testData`、
`outputList`、`controlVars`、`designVars`），不是 kebab-case；
`<task>` 另有同名**属性** `description`（`xs:string`），与 `<description>` 元素并存。

**示例**：`T-tasks/tasks-seven.esml`（七类各一条的合照）、`T-tasks/task-simulate.esml` /
`T-tasks/task-sensitivity.esml` / `T-tasks/task-estimation.esml` / `T-tasks/task-optimize.esml` /
`T-tasks/task-control.esml` / `T-tasks/task-surrogate.esml` / `T-tasks/task-validation.esml`
（逐类单跑），以及上表的任务附属元数据族。
机验基准：`xsd/esml-canonical-compute.xsd`。

**顶层 `<solutionParameters>` 段**（与 `<computeTasks>` 同族的顶层段）：承载**求解参数**，
**两种形状都合法**——

- **属性形态**：`<solutionParameters reltol="1e-6" abstol="1e-9"/>`；
- **子元素形态**：`<solutionParameters name="sp1"><solver name="Tsit5" abstol="1e-6"
  reltol="1e-3" saveat="0.1" maxsteps="10000"/></solutionParameters>`。

它是**字面量容器**：实现可接受、显式报告后跳过，**不参与求解语义**——真正生效的求解
设置来自 `<task>` 的载荷或调用参数。示例：`D-skeleton/solutionparameters.esml`
（子元素形态）、`T-tasks/solutionparameters.esml`（属性形态）。

### 6.10 系统级观察与预设（`<observe>` / `<presets>`）

系统级有两个**声明面**（都在 `<system>` 内，与 `<instances>` / `<connections>` 平级）：

- **观察列表 `<observe>`**：`<observe name="default"><var path="m.x" name="x"/>…</observe>`
  声明「这个系统要观测哪些量」。`path` 是**限定路径**（`m.x`；`t` 指时间本身），
  `name` 是输出名（可省，省了就用路径末段）。它**只声明观测量，不改变模型**。
  示例：`L0-type-unit/observe-list.esml`。
- **预设 `<presets>`**：`<presets><scope instance="u"><preset path="y" value="0.0"
  lower= upper=/></scope></presets>`，给作用域内的量**预设初值/取值域**。
  与方法级预设（附录 F5 的 `<methods><onLoad>`）**并列**：前者挂在**系统**上、
  以 `<scope instance=>` 定位；后者挂在**方法**上、以 `path` 定位。两者都是
  「preset 语义」——在求解前覆盖 `initial` / `default`。
  示例：`L9-method-schedule/fixed-preset.esml`（`<fixed>` 钉值 + `<presets>` 预设）。

## 7. 方程类别与语义

- 代数等式；微分 `D(x)=expr`（x 须为 state，且 `D(...)` 仅作 LHS）；
  高阶导 `D(D(x))` 自动降阶为一阶链（高阶导自动降阶，
  附录 F9 高阶导行）。
- 连接生成方程（§8）。
- 分段方程用 **`ifelse(cond, A, B)` 残差 + clamp/min/max**表达
  （稳态/准稳态分段），不引入硬 if 方程。
- **`integral(e)` 是糖**：在出现处**所在实例**上引入一个状态
  `integral__<key>`（`role=state`，`init=0`，可用 `<set>` 覆盖），并追加一条
  `D(integral__<key>) = e`；该处替换为这个状态。key 取实参裸引用的末段
  （`integral(sp)` → `integral__sp`），否则取实参渲染的净化串；同一实参在同一实例
  内**复用同一个状态**。
  **声明形式**（与上式等价、供作者显式命名）：作者自己写
  `D(integral_<x>) = <x>` 时，`integral_<x>` 即为该状态（`init=0`），
  `integral(<x>)` 指的是它——此时**不新建状态、不追加方程**。
  仅此一处用 `__` 生成内部名；`integral` **不是内建函数**：真漏到求值期会
  `unknown function 'integral'` 响亮报错，不做静默兜底。
- 模型级条件/分支：`<equations><if><condition>c</condition>
  <then>...<else>...</else></if></equations>`（对称可逆）；多分支用
  `<case on="sel"><branch value="k">...</branch>...</case>`（情形A 合并右端 /
  情形B gating）。
- 事件：`L8 <when condition>` 配 `<assign>`/`<reinit>`/`<elsewhen>`；D 改用
  重写变量的事件驱动。
- 数组变量求和/极值：内建 `sum(X)` / `mean(X)` / `min(X)` / `max(X)` /
  `size(X)`（附录 F8）。
- **算法段 `while`**：`<algorithm>` 内的 `<while condition="c">…</while>`。
  算法段降级为纯表达式（静态展开：`assign` 代入、`if/else`→`ifelse`、常量 `for` 展开），
  故仅**常量 `false`** 条件可处理（零次迭代）；**运行时条件为响亮错误**（不支持运行时循环）。
- **向量/矩阵表达式（「不拍平」）**：物化前把向量/矩阵方程展开为逐标量方程。
  支持：数组字面量 `{e1,…}`、comprehension `{f(i) for i in a:b}`（含 `if…then…else` 三元，
  展开期折叠）、`linspace(a,b,n)`、`fill(v,n[,m])`、切片 LHS `der(T[2:n-1])`/`T[a:b]`、
  `end`/`end±k`、逐元素 `.- .+ .* ./`、矩阵字面量 `[a,b;c,d]`、矩阵×向量 `A*x+B*u`。
  `coeff*der(x)=rhs` 归一为 `D(x)=rhs/coeff`（repo 显式导数式约定）。多维数组
  `array="n,m"` 展开为 `name_i_j`（允许 0 维）。
- **端口变量同规则展开**（见 §5）：`<portVariable array="…"/>` 按**完全相同**
  的规则物化为 `port.pvar_1..port.pvar_n`（ordered-set 维度按成员名、二维 `pvar_i_j`），
  与普通变量一视同仁；`port.pvar[i]` 引用解析到对应元素。
  换言之 **§9 的展开规则对「实例变量」与「端口变量」是同一张表**，不设第二条路径。

### 7.1 状态机与时钟（离散面）

**状态机 `<stateMachine>`**：模型级 `<stateMachine name="fsm">` 内写状态与迁移——
`<state name initialState/>` 与 `<transition from to condition reset/>`。
每个状态对应一个**互斥的离散 active 旗标**，方程里用 `activeState(A)` 读它；
`condition` 是迁移触发条件；`reset="true"` 表示该次迁移**复位**相关状态。
示例：`L2-discrete/state-machine.esml`（两状态 toggle）、
`L2-discrete/reset-transition.esml`（迁移带 `reset=`）。

**时钟 `<clock>`**：模型级可直挂 `<clock name="c" interval="0.1"/>`，也可用容器
`<clocks><clock name="c" interval="0.1"/></clocks>`——**两种写法等价**。
时钟面上的算子分两类：
- **采样/保持**：`sample(x, c)` 取 x 在**当前拍**上的采样值，`previous(x)` 取上一拍的值并保持；
- **时钟自身**：`interval(c)` 拍长、`firstTick(c)` 首拍时刻、`noClock(x)` x 无时钟时为真。

示例：`L2-discrete/clock-sample.esml`（`sample` / `previous`）、
`L2-discrete/clock-functions.esml`（`interval` / `firstTick` / `noClock`）。

## 8. 连接语义

**语义分层 + 域惯例默认**：
1. **语义由 PortType 决定**，不是按域硬编码：声明了 `flow` 角色的端口 → 连接点
   **自动生成守恒**（effort 相等 + flow 求和=0）；全"相等型"端口 → 仅相等。
2. **系统组网默认语义 = 显式平衡组件 + 变量/端口相等**（process 通用；水网已示范）：
   守恒/混合等复杂关系写进组件/节点实体，connect 本身不写守恒方程。
3. **域惯例默认（领域矩阵，/50，库层约定）**：
   - 电、力 → 隐式连接器（potential/flow，结点势相等+流守恒自动）。
   - 热、流体（水/气/热网）、工艺介质 → **显式**：connect=变量相等，守恒/本构/
     反向分片全在单元内；分/合流用显式 Node/Merge/Split。
   - 信号 → 变量级 `input/output` 因果；外部 I/O 建模约定/端口壳见附录 F10。
4. 三态语义不变；显式/隐式差异只在库层。给热/流加隐式连接 = 自建连接器体系，
   语言支持，官方库不代建。

- 变量级连接（`from=a.x to=b.y`，x/y 均为实例变量）→ `b_y = a_x`（直接相等）。
- 端口数组/虚拟节点连接 → potential 相等 + flow 求和=0。
- 端口级自动 KVL/KCL 对标量多命名端口是目标语义；编译器路径的标准写法为
  在**展开后的扁平变量**上连接（见 §9）。
- connect 不承载守恒；守恒由组件/节点体内方程负责（以组件内平衡为主）。

## 9. 展平与命名（编译器）

**命名模型**：
- **身份 = 层级路径向量**（如 `[:inst, :port_a, :T]`），不是扁平字符串；扁平名只是
  I/O/打印的投影。
- **扁平投影 = 单点构造器**生成（杜绝前端/代码生成的形状漂移）。
- **分隔符 = `__`**（双下划线）：`a__b__c`、`{inst}__{port}__{pvar}`、数组
  `{inst}__{port}__{idx}__{pvar}`；标识符内禁含 `__`（§2），保证无歧义、可逆。
- `__` 同时是**合成量保留前缀**（`__node_*`/`__du_*` 等），
  实现层统一。用户层避让所有 `__` 空间。
- **跨实现的命名边界**：ESML 的内部名 `__` **不外泄**给任何外部工具；
  跨实现只交换 canonical XML（`a.b.c` 路径），映射到各实现的内部名是**各自的事**。
- 展示（报错/日志）可用点号路径 `a.b.c`。
- **长度与规模**：符号名无硬长度上限；大系统风险
  是"扁平名爆炸"而非超限。策略：(1) 符号身份一律用**路径向量**，不预拼长串；
  (2) 扁平名只在需要时惰性生成并维护 name→index 映射
  （读值 O(1)）；(3) 报错/日志展示用点号路径；若需极短显示名允许短哈希，但身份
  仍以向量/映射为准，杜绝截断歧义。

**扁平投影**：扁平名由**单点构造器**统一生成；
多实例循环中实例命名空间前缀固定为 `inst.name + "__"`（如 `c1__a__left__x`），
端口数组下标按 §9 规则展开。端口展开拼接同名标量（如 `port_a_T` → `port_a__T`）；
组件内部方程的点号端口引用（`port_a.T`）也经同一构造器处理，
**实现内不再有散落的 `_` 拼接**。
**作者层端口变量用点号 `port.pvar`**，展开为 `port__pvar` 并自动物化；
**继承**：作者层不写继承（最佳实践=组合），实现支持消费转换库的
`<extendsFrom>`（§4.0）——**能力覆盖**。

## 10. 求解语义

- **稳态**：纯代数系统（`length(ml.states) == 0`）走 `NonlinearOnlySolver`
  （Newton 阻尼迭代，实现）；守恒/边界由方程闭合。
- **瞬态**：`role=state` + `D(...)`；初值来自 `<variable initial/>`；DE 求解
  按问题类型分派（ODE / DAE 各选对应积分器）。大规模代数部分自动启用**稀疏 Jacobian**
  （当代数未知量数达到阈值后启用）。
- 一致性初始化：求解入口接受 `NoInit` / `AlgConsistentInit` / `FullConsistentInit`
  （默认 Full；`NoInit` 同义）。
- **求解入口**（canonical 五段式）：
  `解析文档 → 语言层模型 → 构建问题 → 求解`，
  数值按官方向量映射读取（状态/代数/离散/参数的 name→idx 映射；
  解向量按各段索引切片）。
- **编译产物缓存**：编译产物（含结构变换前的形式）按内容哈希落盘
  （`SHA-256` + 源文档 + 产物），同文档同系统可复用；
  结构变换产物（`reduce_high_order` / `dae_index_lowering` / `pantelides`）**不参与**磁盘缓存。
  交付路径走加密的 `.esmlx`。

## 11. 物性插件

- 语言不强绑物性实现；组件方程可引用已注册的外部函数，由使用者注入。
- 插件须可求导：数值求解用解析、前向或有限差分；梯度契约见 §11.3。
- 物性入口分两层：
  1. **本地 helpers**（物性 helper 资产）—— 饱和水、制冷剂（R134a/NH3/R410A/R245fa/通用）、
     NASA 多项式理想气体、单相蒸汽/压缩液体；ESML 绑定以这些为公开 API
     （`psat_water` / `hf_R134a` / `props_ideal_gas_cp` / `T_isentropic_water` /
     `h_pump_water` 等；不在此处展开，转由物性后端求值，符号层不介入）。
  2. **物性总包**（外部独立包）—— 统一入口、后端注册表与多后端对比
     （例如 Clapeyron / IAPWS-95 / Zimmer / CoolProp / REFPROP 等后端）。
     物性库以 registered foreign 对象接入，不进入语言规范。

## 12. 标准库（Standard Library）

- 标准库以**坐标**寻址，由 registry 把 `group:artifact:version` 解析为库文件。
  现行坐标库：
  - `cn.ai4energy.esml.thermal:heat-elements` —— **显式**热元件（FixedT/Conductor/
    FixedHeatFlow/HeatCapacitor/Radiation/Node/Merge/Split + 复合 BoilerA*）。
  - `cn.ai4energy.esml.thermal:tclab` —— TCLab 教学双区热模型（2 阶线性）。
  - `cn.ai4energy.esml.fluid:water-elements` —— **显式**水网元件（Reservoir/Pipe/
    NodeDemand/Junction/Pump/Tank/PRV·FCV/N* 分合流 + 复合 PipeLeg）。
  - `cn.ai4energy.esml.electrical:dc-elements` —— **隐式连接器**电元件（Resistor/
    VoltageSource/CurrentSource/Capacitor/Ground，potential/flow 结点守恒）。
  - `cn.ai4energy.esml.electrical:power-elements` —— AC/DC 电源系统元件库。
  - `cn.ai4energy.esml.water:*` —— Reservoir/Pipe_HW/PRV/LossValve/PumpQuad/Ring
    Junction/Source/Sink 等水网与环网分合流元件。
  - `cn.ai4energy.esml.absorbed:*` —— 化工吸收类元件（esterification_eq/
    ether_dehydration_eq/adiabatic_equil_reactor/conversion_reactor_per_pass，
    4 条）等。
- **库文件自包含示范用例**：每个库文件**可以**在末尾放一个自包含
  `<system name="Demo">`，只用本文件类型 + 具体默认值，保证单文件可
  `solve`/`simulate`、数值可核。被别的文件 `<use>`/`-L` 消费时，示范系统
  **不被实例化**（见 §6.3）；这样每个库文件都可独立跑通。
- 回归以 canonical 语义加手解数值锚（热显式、水、电隐式）为准。
- 坐标与 registry 由库工具维护，不在语言规范范围内。

## 13. 分层验收（模型/计算两分 · 逐层链化 · XSD 分层）

**目的**：分层验收不是功能测试的堆叠，而是**从底层逐层验证语言设计正确可行**——
每层一条最小命题（解析 → 构建 →（求解）），后层 `<use>` 前层（后边要用到前面的，
前面就必须先有定义），全绿 = 该层语义成立。语言语义变化后跑一遍分层用例即可回归语言面。

**两分（与 §6.4/附录 M 一致）**：
- **模型体系**（可求解单元 `<system>`；单位/变量类型/变量/组件/接口(≡port)/connect/
  members/系统/partition/深层子系统；自由度 `<fixed>/<free>` 是标签）→
  每一层都有对应的 canonical 用例，逐层链式闭合即可回归语言面。
- **计算求解体系**（闭集七类 task：simulate/sensitivity/estimation/optimize/control/
  surrogate/validation；任务层×功能层，见附录 M）→
  由 `<computeTasks>` 构建计算任务并求解。

**XSD 分层文档化**（`xsd/`）：
| 文件 | 覆盖 | 根 | 校验 |
|---|---|---|---|
| `esml-v1.xsd` | 全库宽松入口 | `<esml>` + 独立库根 | lax |
| `esml-canonical-common.xsd` | 共享 primitive（Ident 等；basic/compute 互含防冲突） | — | 引用 |
| `esml-canonical-basic.xsd` | **模型体系** basic 子集（units/use/variableTypes/portTypes/modelType(含 members)/systems(含 sets/initial/connections/fixed/free/schedule)）；**include compute** → 同根混合文档（模型+`<computeTasks>`）可校验 | `<esml>` + units/variableTypes/modelTypes 独立根 | 严格 |
| `esml-canonical-compute.xsd` | **计算体系**（七类 task 声明 + 载荷）；独立 `xsd/esml-canonical-common.xsd` | `<computeTasks>` | 严格 |

校验命令：`python3 -c "import xmlschema; xmlschema.XMLSchema('xsd/esml-canonical-basic.xsd').validate('<fixture>')"`（compute 同理）。

**说明**：`esml-v1.xsd` 只校验顶层结构；`esml-canonical-basic.xsd` 提供更强的
内容校验，覆盖模型体系的主要元素（units、use、variableTypes、portTypes、
modelType、systems、sets、initial、connections、fixed/free、schedule）。
`esml-canonical-compute.xsd` 覆盖计算任务体系。

各部分的规范文本是判据；XSD 与规范同步更新。

## 14. 外部函数（extern，C ABI）

> **物性库只是第一方 extern 示例**，
> 用户可自建外部库（物性/算子/第三方求解器包装），走**同一机制**（无特权后门）。
> **只支持 C ABI**（不引 C++）。

### 14.1 canonical 元素

```xml
<functions>
  <!-- 纯表达式函数（可 AD 求导） -->
  <function name="weirFlow" returns="real">
    <inputs><input name="H" type="real"/></inputs>
    <body><equation>result = 1.84 * max(H - W, 0.0)^1.5</equation></body>
  </function>

  <!-- 外部函数：C ABI + 声明式导数契约 -->
  <function name="psatWater" kind="external" returns="real">
    <inputs><input name="T" type="real" unit="K"/></inputs>
    <extern ffi="c" library="libprops.so" symbol="props_psat_water" threadSafe="true"/>
    <derivative mode="analytic">                 <!-- analytic | fd | opaque -->
      <partial wrt="T"><equation>dPsat_dT</equation></partial>
      <derivativeSymbol order="1" symbol="props_dpsat_water_dT"/>
      <zeroDerivative wrt="comp"/>
    </derivative>
    <fd step="1e-6" relative="true"/>            <!-- mode="fd" 的步长契约 -->
  </function>
</functions>
```

- `kind="external"` **必须**含 `<extern>`；`ffi="c"` 是唯一合法值；`library`/`symbol` 必填；
  缺库/缺符号**响亮报错**（`UnknownLibrary`/`UnknownSymbol`）。
- `<derivative>` 省略 ⇒ 等价 `mode="opaque"`（**必须在报告/日志标注用了不透明导数**）。
- 可省 `threadSafe`（默认 true；`false` ⇒ 该函数串行化并标注）。
- 名字空间：`unit` 走单位系统；`returns`/`input@type` 用 ESML 类型名。

### 14.2 求导三档（**绝不静默**）

| mode | 语义 | 求解器行为 |
|---|---|---|
| `analytic` | `<partial wrt><equation>` 表达式 **或** `<derivativeSymbol order=1\|2 symbol>` | 填 Jacobian（最准） |
| `fd` | 实现前向差分（`<fd step relative>`，默认 `1e-6` 相对） | 自动差分，**报告标注"该函数用 FD"** |
| `opaque` | 无导数信息 | 符号层保持 `RExpr::OpaqueDeriv`（响亮）；仅无需解析 Jacobian 的路径可用，否则报错或降 FD 并**标注** |

`zeroDerivative`/`noDerivative wrt` 声明某输入偏导恒 0（省 Jacobian 项、省调用）；高阶用
`<derivativeSymbol order="2" …>`。

### 14.3 C ABI 类型映射（写死）

| ESML | C |
|---|---|
| `real` | `double` |
| `integer` | `int64_t` |
| `boolean` | `int32_t`（0/1） |
| 数组 | `(const double* p, size_t n)`，**列主序**；矩阵 `(p, rows, cols)` |
| 字符串 | `(const char* p, size_t len)`（非 NUL 依赖） |
| 查表/数据块 | `(const double*, size_t)` 或 `void*` 句柄 |

**返回码** `0=ok`，非 0 = 错误码 → 实现**响亮失败**（带 `symbol`+码+位置）；
**不许用 NaN 表示"没算出来"**。内存**调用方分配、被调方只写**，buffer 长度前置校验。
**无异常穿越边界**（`catch_unwind`；C 侧禁 `longjmp`）。

**调用约定（v1，写死）**：每个 extern 符号的 C 原型是
```c
int32_t <symbol>(<arg0_c_type>, <arg1_c_type>, …, double *out);
```
标量输入按**声明顺序传值**（`real→double` / `integer→int64_t` / `boolean→int32_t`），
最后一个参数是调用方分配的**结果 out 指针**（`double`）；返回 `0=ok`。
数组/字符串（`(const double*, size_t)` / `(const char*, size_t)`）是类型表的一部分，
但当前实现调用路径只传标量实参，遇到此类签名**响亮拒绝**（`UnsupportedSignature`）——
绝不猜测、绝不静默。`threadSafe="false"` ⇒ 实现在该 `symbol` 上串行化调用。

### 14.4 注册 / 发现 / 缓存

- 以**包**为单位：registry 项形如 `group:artifact:version<TAB>path`；`<extern library>` 相对声明文件
  所在包目录优先，再 `-L` 根取并集；失败响亮。
- **缓存/AOT 键**：`extern 声明 hash` ＋ `库文件内容 hash` ＋ `ABI 版本` ＋ `目标三元组` ＋ `flags`
  ＋ 既有键；任一变即失效。

### 14.5 可验性

每个 extern **必须自带 Demo 用例**（库文件可含 `<system name="Demo">`），
使"夹具夹"能覆盖，不留"无法验证的外部能力"。

## 附录 A 术语
PortType / Port / potential / flow / modelType / instance / D / role /
compiler expansion / extern / analytic·fd·opaque。

## 附录 B 语法骨架（简）
```
esml   := <esml> variableTypes? portTypes? modelTypes? systems? </esml>
portType := <portType name domain> portVariable+ </portType>
portVariable := <portVariable name role=potential|flow type/>
modelType := <modelType name domain> ports? parameters? variables?
              equations? members? connections? </modelType>
member := <members><instance name type/></members>
port := <port name portType size? count?/>
variable := <variable name type role initial default/>
equation := <equation> expr (=|~) expr </equation>
system := <system name> instances connections? sets? schedule? </system>
connect := <connect from=path to=path/>
scope := <scope instance=name><set path value/></scope>
```

## 附录 C 修订史
- v0.6.4：§6.6 系统（flowsheet）级 `<equations>` canonical 定义（引用实例量 `inst.var`，折为扁平名 `inst__var`）；basic XSD `SystemType` 加 `<equations>`。
- v0.6.3：§6.5 条件组件（实例级 `condition`）canonical 定义；basic XSD 补 `condition` 属性，并补 `kind`/`values`、partition/crosslink/partitions。
- v0.6.1：端口变量点号作者语法 `port.pvar` + 自动物化（`__` 回归内部，§4/§9）；
  `<extendsFrom>` 继承合并（§4.0/§9；XSD ModelType 加 `extendsFrom` 元素/属性）；
  向量/矩阵表达式「不拍平」（§7）；未连接守恒端口 `flow=0`（隐式规则）。
- v0.6.0：§13 分层验收（模型/计算两分、逐层链化、XSD 分层文档化）；
  ComputeTask 正名；canonical-compute XSD 七类声明；任务层×功能层。
- v0.6.2：§3 枚举类型（`kind="enumeration"`/`values`，字面量 `E.a`→声明序号）；
  §4.0 `redeclare`/`replaceable` 的 canonical 表示（派生同名覆盖 + `redeclare="true"`
  响亮校验）；§7 算法段 `while`（常量展开 + 运行时响亮报错）。
- v0.5.2：§6.4 求解单元分层定案——可求解单元=`<system>`（唯一=system；
  多个=partition 内部自解 + crosslink 模块间联立）；connect=组件间、crosslink=子系统间；
  crosslink 端点=port 束；模型体系与计算求解体系两分。
- v0.5.1：附录 K METHOD×Schedule 多段编排（语法 + 纯 ODE 段间续接/preset）。
- v0.5.0（v0.4.1 增补）：端口规范词收窄 inlet|outlet|bi-directional；纯 PortType 连接护栏；Connection-Type 参数/PortSet；Source/Sink；SELECTOR；Ordered-Set（数组定维/成员常量/label 下标/成员一等 ConstSetMember）；IF(对称可逆)；FOR(lo..hi 与序集迭代)；CARD/IN(一等/运行时)；CASE(STN 情形A+B)；process 级全局参数传播。**v0.4.1 增补**：stream 流股组成；信号 causal 护栏；自定义端口类别+连接规则表；when/edge/reinit 事件语义糖；复合嵌入(复合壳保留)；on_load 预设；自由度 FIX/FREE；vector 归约内建(size/sum/mean/min/max)；附录 F1–F8。**高阶导**：`D(D(x))` 自动降阶（见附录 F）。
**高指标 DAE（Pantelides）**：平衡高指标 DAE 自动降阶为一阶 index-1（见附录 F9）。
- v0.4.1：§4.1 复合组件（成员装配/限定路径/嵌套展开）入 spec；附录 B 骨架补 members。
- v0.4：§6.1 标准库坐标引用 `<use>`/registry.tsv；§12 标准库分层。
- v0.3：词法收紧（canonical 唯一、旧词法报错）；补 §2 收紧规则表。
- v0.2：改为自有术语；补插件/分段/scope 语义。
- v0.1：初稿（章节骨架参照规范样例，已重构）。

## 附录 D 旧版文档边界

canonical 求解线（§2 收紧词法 + plain-text 方程）之外，历史版本还留下若干旧
schema 文档。它们**不属于**本规范，也不在 canonical 工具链的接受范围内；
canonical 语法对旧词法直接报错（§2）。

这类文档的典型特征：

- 带 MathML 或混合状态机结构（`<discretes>/<switch-to>`），
- 带 `<constants>` / `<initialisation-procedures>`（kebab）等旧容器，
- 由早期研究模型或优化模型改用而来。

⚠ **别把 canonical 元素误当 legacy**：`<case>`（方程块内条件分支）与
`<algorithm>`（函数体的一种写法）**是 canonical 的** —— `esml-canonical-basic.xsd`
声明了它们，仓内 `L2-discrete/case-branch.esml` / `T-tasks/algorithm.esml` 即其
可运行示例。旧文档里的 legacy 形态是 `<discretes>` 这类**容器**与
`<initialisation-procedures>` 这种 **kebab 拼写**，不是 `<case>` / `<algorithm>` 本身。
旧容器名一律以 `esml-canonical-*.xsd` 的声明为准（README：「文字与 schema 出现
分歧时，以 schema 为准」）。

如需 canonical 表达，请按本规范重写或经转换器归一化，不要把旧文件改头换面
当作 canonical。canonical 案例以本仓按语言层次分目录的示例为准（`D-skeleton/`、
`L0-type-unit/` … `L9-method-schedule/`、`T-tasks/`、`X-use/`；见 README「示例目录」）。

## 附录 B（续）— 端口/角色规范词（canonical）

- 端口方向只用 `<port … category="inlet|outlet|bi-directional">`；
  自定义类别(如 node/connector)预留、连接规则后置。不再使用 dir/direction/in-out。
  变量级 `input/output` 保留给信号 causal role（不得当端口方向词用）。
- PORTSET（参数沿流股传播）：`<port … port-set="flow">`（同模型同 port-set 参数等值）。
- `<portType>` 变量：`role="potential|flow|stream|input|output|parameter"` 或省略。
  省略 = 显式域变量束（thermal/water/gas/process），连接=逐位置相等，无守恒 role。
- Connection-Type 参数：`<portType><parameters><parameter …/></parameters>` → 组件自动带
  `<leaf>__<p>`；构建期按连接/port-set 值统一 + 冲突检测。
- 边界组件：`Source`(固定头, bi-directional) / `Sink`(定流量, inlet) ≙ 电接地/电流源。

### SELECTOR / CASE·STN
- 模型级 `<selectors><selector name …><values><value>Below</value><value>Above</value></values><default>Below</default></selector></selectors>`
  → 实现降级为 discrete 数值变量（码 = 定义序 0..n-1，default 取 label 对应码，label 留 desc）。
- 方程用 `ifelse(sel==k,…)` 选分支；状态切换用 `<events><when condition>…<assign path="sel" value="k"/></when>`（同 PCM discrete+indicator 机制）。XSD `SelectorType`(common) 即规范。
- **系统级初值**：`<initialSelectors><scope instance="m"><initialSelector path="mode"
  value="fast"/></scope></initialSelectors>`——在**系统**上给某实例的选择器定初值，
  `value` 写**label 字符串**（不是码）。示例：`L3-model/selector-values.esml`。

### ORDERED_SET 序集
- 声明（文档顶层）：`<orderedSet name="Species" static="true"><element>H2O</element>…</orderedSet>`
  （XSD `OrderedSetType`，common）。成员序即数组下标序。
- 数组定维：变量/参数 `array="Species"` → 维度 = 序集成员数；元素符号命名 `name_i`（如 C_1..C_3），
  方程直接引用 `C_1`。
- 引用规则（已实现）：方程里可用成员 label 下标 `C(CO2)` / `C[CO2]` → 元素符号 `C_k`（k=序位）。
- 成员常量（已实现）：orderedSet 成员名 → 模型级自动生成 integer param（值为序位），方程直接用 label。
- 待实现：`IN/CARD/INTERSECTION` 序集内建与运算、`CHOICE/CHOOSE`、按 label 引用实例数组。

### 模型级 IF（对称可逆）
`<equations><if><condition>c</condition><then><equation>lhs = rhsA</equation></then>
<else><equation>lhs = rhsB</equation></else></if></equations>`
两分支 lhs 须一致 → 降级 `lhs = ifelse(c, rhsA, rhsB)`（XSD `EquationSectionType` 已含 `<if>`）。
CASE/多区/滞回：配 SELECTOR + `<events><when>`(STN)，方程用 `ifelse(sel==k,…)`。
示例：`L1-expr-equation/ifelse.esml`（`ifelse` 分段表达式）、
`L3-model/if.esml`（模型级 `<if>`）、`L2-discrete/case-branch.esml`（`<case on>` 多分支）、
`L3-model/selector-values.esml`（SELECTOR 值域与初值）。

### FOR 循环
- `<equations><for var="i" in="lo..hi"><body><equation>...i...</equation></body></for></equations>`
  按整数区间展开 body 方程，i 替换为整数字面量（XSD `004-equations` 含 `<for>`；当前 in 仅支持 lo..hi 整数字面量）。
- 数组维 `<variable name="C" array="3"/>` 直接支持整数大小（无需 named dim）。

### process 级全局默认参数传播（顶层 SET）
- `<set path="P" value="…"/>` 不带 `<scope instance=…>` → 作为系统级默认，对**所有**声明该 param 的实例生效（除非该实例有显式/祖先覆盖）。
- 层级参数传播（真嵌套）：子实例命名 = `父__子`；父作用域 `<scope instance="a"><set path="P"…` 向下覆盖子树 `a__…`，取最近祖先；自身显式最优先。
- `<set>` 的 `unit=""` 按三级解析：显式 ＞ 实例名前缀 ＞ 全局默认。

- `CARD(Name)` → 序集成员数；`IN(x, Name)` → 1/0。二者是一等表达式：编译期折叠
  字面量与成员标识（`IN("CO2",Sp)=1`、`IN(H2O,Sp)=1`），符号/参数形式展开为
  `IN(T,Sp) → ifelse(T<0,0,ifelse(T<n,1,0))`（n=成员数，越界夹紧，与 `ifelse` 语义一致）。
  例：`T=1` ∈ [0,3) → 1；`T2=5` → 0。
- 参数 `array="Sp"`（实例参数数组）按序集定维，展开为 `name_1..name_n`。

### FOR 按序集迭代
- `<for var="k" in="Species"><body>…</body></for>`：in 为已声明序集名时按成员 label 迭代，
  与成员 label 下标/成员常量配合（body 里 k → H2O/CO2/CH4 等，随后 C(k)→C_1…）。
  测试 test_for_over_set。

### CASE 多分支
`<case on="sel"><branch value="k"><body><equation>lhs = rhs</equation>*</body></branch>*</case>`
每方程 gated：`(1 - sign(abs(sel-k))) * (lhs-rhs) = 0`（激活分支才约束； 指示器风格）。
- **情形A（STN 正统）**：各分支 lhs 同为 `D(x)` → 合并右端 `D(x)=Σ_k (1-sign|sel-k|)·rhs_k`（selector+events 驱动，bang-bang 同款）。
- 示例：堰流代数情形；以及带 selector + case + 事件滞回的 STN 情形，平衡态 H≈W+(Fin/1.84)^(2/3)。

### 附录 F1 — stream 流股组成（组分加权混合）
- 流股语义：连接处变量**逐相等**（1:1 链），多股汇合的组分加权在单元（Mixer）内完成，
  而非连接层加权。隐式域才需要连接级加权；ESML 显式域采用同一约定。
- 组分变量可用 `role="stream"`（可选 `flow-reference="Q"` 标出载量参考）作元数据；它在
  PortType bundle 中是普通变量，**不要**标 `role="flow"` 等 role —— role 只留给隐式连接器（electric 等），
  否则实现会对该变量走隐式 wire KCL（求和=0）叠加在显式相等上，造成符号翻转/过定。
- 连接端点=同型 PortType 的真实实例端口 → 逐 pvar 相等（从 HydraulicPort 泛化到任意
  PortType：`f.port.pvar == t.port.pvar`，两端同型否则报错）。守恒/加权在单元内。
- 示例：两股 Feed 按 3:1 流量进 Mixer，混出组分为 c1=0.8 / c2=0.2。

### 附录 F3 — when/edge/reinit 一等事件语义糖
- `<when condition>`（既有）+ 新糖：条件支持 `edge(cond)`（真沿：cond 从假到真的穿越时刻）、
  `noEvent(e)`（no-op 注解，剥离）、`pre(x)`（事件间离散恒为常数，条件里 `pre(x)==x`，实现为恒等；
  `pre` 记忆按事件间离散量保存）。
- `<assign path=X value=v>`：事件把**离散**置 v；`<reinit path=X value=v>`：事件时刻把
  **连续状态** X 直接置 v（u 状态段写入）。
- `<elsewhen condition>` 嵌套于 `<when>`：扁平化为有序 EventDef，声明序=同时穿越时的优先级。
- 示例：锯齿泵注，液位 H 在 [0.05, 0.8] 间往复，周期 37.5 s。
- 限制：赋值 `value` 在编译期按常量求值；`elsewhen` 同时穿越的优先级按声明序确定。

### 附录 F4 — 自定义端口类别 + 连接规则表（opt-in）
- `<port category=...>` 可带自定义类别字符串（如 feed/primary/secondary）；语法对非标准类别
  方向按 `:bi`（双向），标准集合仍走 inlet/outlet 方向护栏。
- 系统级 `<connectRules><rule from= to=/>*</connectRules>`：仅当至少一端为自定义类别时启用
  规则表对称配对校验（bi-directional 万能）；无规则表而用自定义类别 → 编译期报错。
- 信号口按**位置配对**（pvar 命名可不同，如 OutSignal.y ↔ InSignal.u）。
- 示例：自定义类别端口的连接规则表 —— `L6-connect/connect-rules.esml`（feed 只允许接
  primary / secondary）。

### 附录 F2 — 信号 causal 连接护栏
- PortType 变量全为 `input|output` role → 该口是信号连接器（可跨 PortType：SigOut↔SigIn）。
  连接只许 **output↔input**：input↔input（无驱动源）与 output↔output（双驱动）在编译期报错
  （`signal_causal_guard`）。逐 pvar 命名须一致。
- 组件侧同样须显式声明 `<leaf>__<pvar>` 变量（非 autovivify）。
- 示例：信号口跨 PortType 的因果连接 —— `L4-port/signal-causal.esml`
  （`SigOut.y`(output) ↔ `SigIn.y`(input)，两份 portType 的 pvar 同名 `y`；
  组件侧显式声明 `p.y` / `q.y`）。
  ⚠ 护栏本身（`signal_causal_guard`）**实现侧未落地**：input↔input、output↔output、
  pvar 命名不一致这三种写法现实现一律放行，详见 `docs/coverage.md`。

### 附录 F5 — on_load 预设方法
- 模型级 `<methods><onLoad><set path="X" value="v"/>*</onLoad></methods>`：求解前覆盖
  变量初值(`:initial`) / 参数默认(`:default`)（preset 语义）。
  在解析期应用；成员/状态级 FIX/FREE 由 §附录 F6/F7 处理。
- 示例：`Calc.K` 由 1 预设为 5 ⇒ `x = 11`；`Tank.H` 由 0.1 设为 0.9 后排水。

### 附录 F6 — 自由度 FIX
- 系统级 `<fixed><scope instance="x"><set path="leaf" value="v"/></scope></fixed>`：把该组件的
  代数变量钉为常量 → 转为**参数**（同名替身，不进 u），其出现处（本实例方程与连接）替换为参数符号，
  u0 同步剔除。欠定系统由此可解/可做“钉量求自由未知”。state/未知量不可 FIX（报错）。
- 参数侧 FREE 与参数估计/优化目标不在本层。
- 示例：`y = K·a + c`，钉 `y = 5` ⇒ 解出 `a = 2`。

### 附录 F7 — 自由度 FREE（与 FIX 对偶）
- 系统级 `<free><scope instance="x"><set path="leaf"/></scope></free>`：把该组件**参数**升为代数
  未知（同名变量进 u，u0=原参数默认；从 ps 剔除；方程引用替换）。与 `<fixed>` 组合即可令方程
  决定自由参数值（Q=k·dP：FIX dP=3/Q=9 + FREE k ⇒ k=3≠默认5）。
- 示例：`Q = k·dP`，FIX `dP = 3`、`Q = 9`，FREE `k` ⇒ `k = 3`。
- 参数估计/优化目标不在本层。

### 附录 F7b — METHOD RUN 子过程
- `<methods>` 内可声明多个 `<method name="...">` 子过程；顶层 method 通过
  `<run name="..."/>` 顺序调用其它 method（`run`/`call` 同义）。调用深度上限 12（前端的 `onLoad` 方法应用）。
- 语义：按声明序 + 调用序应用 `<set>`；每个 `<set>` 走与 on_load 同一通道（变量改 `:initial`、
  参数改 `:default`），表达式 `value` 支持本组件内已解析参数默认/变量初值的引用
  （如 `"2*W"`、`"T_in-5"`）。`<run>` 与 `<set>` 同 method 体内可任意顺序，解析为
  一次深度优先 DFS（参数会按调用序与 `<set>` 序叠加）。
- 与系统级 `<fixed>/<free>` 的区别：method 级 `<fix>/<vary>`（见附录 K）走实现
  同一 FIX/FREE 路径，但**系统级 `<fixed>` 优先**（详 system methods/on_load/fix|vary）。
- 示例：顶层 `top` method 内 `<run name="scale"/>` 先把 W 设为 2，再
  `<set path="H" value="3*W"/>` ⇒ H = 3×2 = 6；没有 RUN 时 H = 3×1 = 3。
- 限制：method 仅在 `<onLoad>` 时机生效（与 `<methods><onLoad>` 同生命周期）；不引入
  不引入运行时方法表。

### 附录 F8 — vector 归约内建（size/sum/min/max 一等）
- 文本方程支持 `sum(X)` / `mean(X)` / `min(X)` / `max(X)` / `size(X)`，X 为声明的 array
  变量或 array 参数（`array="Dim"`）。物化时按 array 维解析 N（system `<set>` 覆盖优先，其次
  cdef 参数默认/序集长度/字面量），展开为逐元素 `X_1..X_N`：sum→和、mean→和/N、min/max→逐元、
  size→N 常量。标量/多参 `min(a,b)` 等原样走 原语内建。
- 示例：`C[1..3] = 1/2/3` ⇒ S=6、M=2、lo=1、hi=3、sz=3。
- 不支持：多维数组归约、嵌套调用。

### 附录 F9 — 高指标 DAE（Pantelides）
- **状态**：建模对**平衡**高指标 DAE（未知=方程、含代数变量、存在纯状态约束残差）自动走
  Pantelides 降阶 → 平衡一阶 index-1 DAE；纯 ODE / index-1 DAE / 非平衡系统零扰动。
  结构层：等价变量消元 + DFS 增广路匹配 → Pantelides 指标降低/提升，
  直到不再有 runaway。多层求导自动降为一阶，ESML 未知量仍按**原变量**存储（非 `x(t)` 的高阶导形式）。
  结构层求导在符号层原生展开（`D(常量) ≡ 0`）。

### 附录 F10 — 外部 I/O 经信号口 / 端口壳（block 化单机 + 语言层闭环）

让"单机/被控对象"可复用、外部输入一律走端口（信号 causal）：

- **端口壳**：被控对象定义两个信号口——`cmd`（input：操纵量 Q1/Q2）与 `meas`（output：回读
  T1/T2）；对象本体方程用 `cmd__*` 口变量，`meas__* = 状态` 回读。操纵量不再是裸参数。
- **规则**：
  1. 输入口变量（input）由连接相等定值，必须有驱动源；悬空欠定（编译期应报）。
  2. 输出口变量（output）由组件内方程定值，可悬空。
  3. 驱动方 = 输出口组件（源/控制器/Driver）；`connect` 只许 output→input（附录 F2 护栏）。
  4. 对象端口 `category="bi-directional"`（避免  方向护栏把信号口误判）。
  5. 连续量接口：控制量在饱和内用 `ifelse(u<lo,lo,ifelse(u>hi,hi,u))` 夹紧；积分器用状态
     `D(ei)=e`（无 anti-windup 的连续 PI 会有积分饱和，需注意——离散实现见范式二）。
- **两类闭环范式分界**：
  - 范式一（**语言层连续闭环**）：控制器/设定值源均为组件，`connect` 组网，一次 ODE/DAE 求解。

  - 范式二（**软件 sample-hold 离散闭环**）：控制器在外部软件，
    每控制步 dt 用当前量重算 Q 并改**驱动块参数**，再解一小段；测量可加 A/D 量化/噪声。
    可与开源 TCLab 参考模型（`tclab.TCLabModel`）在同一控制器下闭环对标。
- **对照**：把参考模型的 4 态线性 ODE 以 canonical 写法复刻，开环 Q1=30 时与参考实现
  逐点比较，最大偏差 < 1e-4 °C。

### ConstSetMember 一等成员类型
- 成员常量符号携带 `OrderedSetMemberRef` 元数据：`(set, member, index)`；编译期读取成员，
  物化时挂到符号上。

## 附录 G — 能力概览

| 能力 | 入口 |
|---|---|
| 端口变量束与方向护栏 | `portType` / `role=inlet\|outlet` |
| 连接类型参数与 PortSet 等值、冲突检查 | `<connectionType>` / `<portSet>` |
| Source / Sink 边界 | 标准库 |
| 序集：数组定维、成员常量、label 下标、成员一等 | `<orderedSet>` |
| SELECTOR 离散化与事件 | `<selector>` / `when` |
| 条件式 IF（对称可逆） | `<if>` |
| FOR 循环（区间与序集迭代） | `<for>` |
| CARD / IN 集合算子 | 内建 |
| CASE 多分支（合并右端 / gating 两种情形） | `<case>` |
| stream 流股组成：连接逐相等 + Mixer 单元加权 | `role=stream` / Mixer |
| 高阶导 D(D(x)) | 自动降阶 |
| 高指标 DAE | 自动降阶至 index-1 |

未纳入规范的能力：嵌套层级参数传播、分布式 PDE。

### 序集运算（编译期）

- `COMMON(A,B)` → `|A∩B|`（编译期折叠整数；同集用 CARD）。

## 附录 H — XML Schema（XSD）与 canonical 校验

- **入口**：`xsd/esml-v1.xsd`；模块化分解为 `esml-canonical-common.xsd` /
  `esml-canonical-basic.xsd`（模型面）/ `esml-canonical-compute.xsd`（计算面）/
  `esml-canonical-project.xsd`（工程壳）。
- **严格 canonical 子集**：`xsd/esml-canonical-basic.xsd`（自包含、可编译），覆盖
  基本面：`variableTypes/type`、`modelType(parameter/variable[array/distribution]/
  equation/methods on_load(表达式))/system(component/sets/initial 逐索引)`。
  对本子集外（实现已支持但 XSD 待对账）的元素/属性用 `##other` 宽容跳过，
  不影响既有文档。
- **校验**：
  ```
  xmllint --schema xsd/esml-canonical-basic.xsd <file>.esml
  ```
  扩展段（case / methods / discrete / orderedSet / fixed / PORTSET /
  connectRules / functions / …）由 `##other` 宽容跳过。

## 附录 I — 用户函数与黑盒

- **声明**：`<esml><functions>` 顶层区段；`<function name>` + `<inputs><input name>` + `<body>纯代数式</body>`；
  可选 `kind="external"`（黑盒：`evaluator` 句柄 + `<partials><partial wrt>` 解析偏导，OpenMDAO 风格）。
- **纯函数语义**：调用在方程里内联展开（宏语义），天然可求导、可嵌套（function 内调 function）。
示例：`weir_flow` 与 `weir_half` 的嵌套调用。
- **外部函数**：`kind="external"` 数值 body 函数 + 已注册的外部对象 + `<partials>` 机制。
  解析偏导可注入以构造残差 Jacobian；evaluator 句柄为无 body 的外部源。
- **局部量 `<locals>`**：`<function>` 内可声明 `<locals><local name="t"/></locals>`；
  函数体（`<algorithm>`）里用 `<assign name="t" value="…"/>` 逐句赋值，局部量随函数
  调用被**内联展开**（不进入模型命名空间）。示例：`L8-function/locals.esml`。
- **宿主对象 `<foreignObjects>`**：顶层
  `<foreignObjects><foreignObject name="fo" class="sensor"><method name="Level">
  <set path="y" value="3.0"/></method></foreignObject></foreignObjects>`；
  方程里以 `fo.Method()` 调用，方法体**只有 `<set>`**（先赋值后返回该值）。
  示例：`L8-function/foreign-object.esml`。
- **XSD**：canonical 子集收录 `<functions>`（inputs / body / partials）。

## 附录 J · 单位语义

- **定案**：数值层用裸数——单位只是**界面与边界**的元数据；实现侧可留单位库
- 单位语义操作：解析单位、取量纲、同量纲换算（含 `℃` 偏移）、一致性核验。
  `<set unit="cm" value="500">`：值单位 vs 声明单位——同维换算（scale/offset），异维报错。
  strict 日志指示器已修（原注组 external 不调用的 bug 已修），`<initial>` 为程序式调用的单位、形状类型。
- 本语言不绑定具体单位库。
- XSD：canonical/esml-v1 已带 `unit` 属性书写；esml-v1 全库校验不涉单位语义（单位语义由处理器校验）。

### METHOD FIX/VARY
- `<system><methods><onLoad>` 内 `<fix name="inst.leaf" value?/>` / `<vary name="inst.leaf"/>`，
  与系统级 `<fixed>/<free>` 同一 FIX/FREE 实现路径（显式 `<fixed>` 优先）；语义=钉值/参数升未知。
  canonical XSD 已收 `methods/on_load/fix|vary`。

### 连接参数单向传播 / 回退
- 现状：连接/PortSet 参数**无向值统一**（单锚传播+汇合冲突，构建期）。
- ：连图定向检测（`_orient_connection`：out↔in 顺向/bi 随对方）；**bi↔bi 或环向 → @warn 回退无向**
  （不破既有库）；equality 与汇合冲突语义不变；含 PORTSET 的方向探测。
- 严格“最上游锚=唯一传播源/下游再设报错”单向语义为延伸（需行为收紧与全库审计）。
- 回归：。（`_orient_connection` + cycle detection）。

## 附录 K — METHOD × Schedule 编排

- 语法（P1，向后兼容单段）：
  ```xml
  <schedule><sequence>
    <continueFor time="2"/>        <!-- 每段时长；连续时间顺序拼接（现求和多段） -->
    <call method="ramp"/>           <!-- 段前预设（v0 由 preset 回调落地；XML 方法体接线=后续） -->
    <continueFor time="3"/>
  </sequence></schedule>
  ```
  多段（按时间段切分）求解，把末状态写回作下段初值，`preset` 在第 i≥2 段前
  多段（按时间段切分）求解，把末状态写回作下段初值，`preset` 在第 i≥2 段前
  运行（可 `_set_param_default!` 段间改参数 = piecewise 阶跃操作）。
- **调度步类型**：`<sequence>` 里的步有三种——
  - `<continueFor time="2"/>`：**推进**一段时长（连续时间顺序拼接）；
  - `<reassign path="g.N" value="50.0"/>`：在**该步的累计时刻**（前面 `<continueFor time=>`
    之和）把 `path` 置为 `value`；`path` 必须指向状态或变量（指到参数会显式告警且不改值）；
  - `<stop time="10"/>`：**记录 STOP 边界**——其后若再跟 `<continueFor>` 会被校验拒绝。
    它是**结构校验标记，不是运行时截断**：求解时长仍由 tspan 决定。

  示例：`L9-method-schedule/reassign.esml`（段间重赋值）、`L9-method-schedule/stop.esml`（STOP 标记）。
- v0 边界：仅**纯 ODE**（无 algebraic/discrete）；段时长总和 = tspan 长度（否则报错）；
  **控制器 / 无定模型 = 普通 simulate**（为单元测试注入，不改 ESMLModel 结构本身）
- 示例：段解析、多段拼接等价单次连续求解、段间改 k ⇒ H=6.8。
- 不支持：代数/离散模型、求解器切换、事件触发编排。

### `<call method>` 方法体
- `<methods><method name="ramp"><set path="m.k" value="1.0"/></method></methods>` 解析为
  `metadata[:__schedule_methods__]`（命令序列）；`<sequence>` 内 `<call method="X">` 归属**其后**
  `<continueFor>` 段（`metadata[:__schedule_seg_calls__]`）。
- 段前执行该段 call 的方法体（`set/fix` 改参数默认值），
  先于程序化 `preset`。寻址属性（`path` 等）只收**作者点号** `m.k`：`__` 是生成层内部
  段分隔、作者标识符禁含（§3），故 `m__k` 一律拒收并提示规范写法。
- **代数/离散模型**：多段连续求解不再限纯 ODE；未知量含状态、代数量与离散量
  布局写回 `ml.u0` 续接。
- **每段 solver 切换**：`<continueFor time="1" solver="rodas5p"/>`；可在段内覆盖求解器
  （tsit5 / rodas5p / fbdf / ida / dfbdf / qndf / nonlinear）。
- **事件触发段间切换**：`<continueUntil condition="m.x &lt; 1.0" max-time="5"/>`——
  条件穿越零时提前结束该段，下段从其终止时刻续接。

## 附录 L — 术语表与命名（类型/实例词义）

### L.1 类型词规范：`X-type` 与一个异类
- **规范**：类型（可被实例化）一律带 `-type` 后缀 —— `variable-type`、`portType`、`modelType`；
  实例/结构对象裸词 —— `instance`、`variable`、`port`、`system`、`connection`。
- **异类 1 · `unit`（度量单位类型）**：类型层唯一不带 `-type` 的词，且三重歧义
  （① `<units><unit>` 类型；② 变量/端口 `unit=` 属性；③ 曾是实例别名 `<unit>`，现已 ban）。
  叶子型、无实例树；历史歧义已逐项收紧（实例位只认 instance/component，`<scope unit=>` 报错）。
- **`system` 兼作类型**：一个 instance 的 `type=` 可以引用另一个 `<system>` 的名字，
  此时该 instance 按子系统展开（§6.4）。不为子系统另设类型元素；
  `<system>` 的「场景」与「可复用类型」两义由引用位置区分。

> `portType` 符合 `X-type` 规范。

> 目的：钉死"类型 vs 实例 vs 场景"用词，消历史双关；`component` 降为兼容别名。

| 词 | 语义 | 说明 |
|---|---|---|
| `modelType` | **类型（class）** | 唯一类型容器/词（`<modelTypes>/<modelType>`）；带 `type` 后缀以别实例 |
| `instance` | **实例（主词）** | `<instances>/<members>` 内的实例元素 `<instance name type/>` |
| `component` | 实例的**兼容别名** | XSD **仅在 `<members>` 内接受**；`<instances>` 内拒绝（负例 `L3-model/component-probe.esml`）。新写一律用 `instance`；"曾经当类型容器"的用法已取消 |
| `system` | **场景/装配**（实例树顶层），兼作**子系统类型** | 作为 `type=` 引用目标时按子系统展开（§6.4） |
| `members` | 复合 modelType 的**成员实例**（instance） | ：members 内 instance=成员实例，非子类型 |
| `model-instance` / `unit` | 更旧的实例别名 | 不推荐；新写一律用 `instance` |

- **文件后缀**：明文 `.esml` / 加密交付 `.esmlx` / `.xml` 过渡兼容（历史，不推荐）；角色前缀
  `*.comp.esml`=组件/模型类型库、`*.sys.esml`=系统/场景实例。
- **role 词**（port）：potential/flow(through)/stream = acausal；input/output = 信号；不写 = 显式束（附录 B（续））。

## 附录 M — 计算面术语（任务 / 问题类 / 调度 / 求解器）

**抽象分层（一层又一层）：每层对上层是黑盒。**
- **任务层 = 闭集七类**：simulate / sensitivity / estimation / optimize / control / surrogate /
  validation。只开七个"按钮"，不再新增 kind。
- **功能层 = 机制 + 组合**（放某类之下，作其 method/模式/载荷，不进 enum）：
  - simulate × `solve=steady|transient` · `schedule` 多段 · 求解器（AE/ODE/DAE 自动分派）；
  - sensitivity = simulate × 扰动后处理；estimation = optimize(simulate 目标) × data；validation = simulate × 对比指标 —— 三者是 **simulate 的驱动组合**，不重复实现 simulate；
  - optimize × lp/qp/nlp/minlp（HiGHS/Ipopt 等后端）· objective/decision/bounds/constraints；
  - control = optimize × simulate 滚动（MPC/PID/setpoint）；
  - surrogate = 采样(simulate)→拟合（lsq/lasso/alamo/degree）；
  - 分区 co-sim / crosslink 协调 / Schur 等 = 求解机制层（S 层）。
- 新能力 = 给**功能层**加机制或组合；任务层词表/枚举不动。

| 词 | 语义 | 说明 |
|---|---|---|
| `task`（`ComputeTask`） | 计算流程"外壳" | 描述层：`kind`(simulate/sensitivity/estimation/optimize/control/surrogate/validation) + 目标模型 + 参数 |
| 问题类（七类） | 抽象问题类型 | `SimulationProblem / SensitivityProblem / EstimationProblem / OptimizationProblem / ControlProblem / DataDrivenProblem / ValidationProblem` |
| metadata 参数 | 每模块声明"具有哪些" | 每类任务各自声明其可用的元数据项，建模时生成 |
| 求解角色 | AE / ODE / DAE | 按模型（纯代数/状态/高指标降阶后）自动选 |
| `schedule` 段 | 运行时编排 | ：多 `<continueFor>` 段 + 段前 `<call method>`；`METHOD/RUN` 逐段 |
| `METHOD` | 求解流程声明 | 方法脚本式参考 风格；`FIX/VARY`(自由度)、`RUN`(驱动)、`solve` 组合（附录 K） |
| `<tasks>` / `<task>` XSD | tasks/compute 各层 schema | `esml-canonical-compute.xsd`：kind 决定载荷结构，守恒由结构决定；**按 kind 构造问题再求解**（task 声明 → 问题树 → 求解）；条目元素名单轨为 `<task>`（§6.9） |

> 术语原则：**类型 modelType · 实例 instance（component 兼容）· 场景/子系统 system ·
> 计算任务 task / 问题类七类 · 求解角色 AE/ODE/DAE · 编排 schedule + METHOD** —— 详见附录 L/M。

## 附录 N — 处理管线与中间表示

**拓扑**：`XML/.esml（解析）→ 中间表示 → 编译产物`：
- **解析**：把 XML 读为有类型的第一遍对象图（units / types / ports / components /
  systems / tasks 等）。
- **中间表示**：结构化的对象图（组件定义、模型类型、系统定义、模型实例、端口…）；
  连接 / 方程 / 调度是对象间的关系。
- **编译**：展平嵌套、端口物化等展开后得到求解所需的编译产物。

**中间表示的组织原则**：
1. **实例一律类型化**：系统的 `<instances>` 与复合组件的 `<members>` 使用同一种
   实例结构（名字 + 类型），不因所在容器不同而分叉。
2. **命名对齐词法**：实例字段/容器统一用 `instance`；类型定义统一以 `Def`/`Type`
   命名；`component` 只作别名，不进入新的字段名。
3. **一切皆对象**：units / variable-type / portType / modelType / system /
   task / schedule 都共享
   `name + type/kind + description + 坐标引用` 的统一元数据骨架。
4. 结构调整应逐项进行，每一步都保持语义与数值结果不变，避免静默漂移。

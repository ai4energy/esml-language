# T-LANG-SMOKE 报告：solve-smoke 8 条 fail 收口（2026-11-12）

单：`/home/ai4e-hermes/lang-orders/T-LANG-SMOKE.md`。分支 `task/lang-smoke`
（基 55400ce）。引擎 `~/esml-engine-user3/target/release/esml`，`ESML_PROPS=off`，
120 s/件。未 push；未碰引擎仓。

## 一、smoke 前后 census

改前（W52 基线，`tools/solve-smoke.tsv` 头注行原文）：
```
# 共 158 行 / ok 137 / ok-simulate 7 / na 6 / fail 8（fail 内分：fail-check-debt 5 / fail-engine-debt 2 / 示例侧待修 1）
```
改后（本单重算，复跑实测）：
```
# 共 158 行 / ok 138 / ok-simulate 7 / na 6 / fail 7（fail 内分：fail-check-debt 5 / fail-engine-debt 2 / 示例侧待修 0）
```
fail 8→7：唯一下降来自「示例侧待修 1」（axis-reduce 改写）。5 条 check-debt
定性为 engine-debt（不改引擎，如实保留）；2 条 engine-debt 复核后原样保留。
逐件复跑（2026-11-12，`esml solve`，rc + 错误首行）：

| 件 | rc | 首行（实测原文，截断） |
|---|---|---|
| `L1-expr-equation/vector-reduce.esml` | 0 | （解出 8 未知量：s=6.0 m=2.0 lo=1.0 hi=3.0 sz=3.0） |
| `L0-type-unit/literal-enum.esml` | 1 | `error[F7]: …:16:7 — unknown element <literal>` |
| `L8-function/algorithm-while.esml` | 1 | `error[F7]: …:20:9 — unknown element <while>` |
| `L9-method-schedule/continue-until.esml` | 1 | `error[F7]: …:20:7 — unknown attribute maxTime on <continueUntil>` |
| `L9-method-schedule/method-vary.esml` | 1 | `error[F7]: …:23:9 — unknown element <vary>` |
| `T-tasks/hyperparams.esml` | 1 | `error[F7]: …:30:22 — unknown element <param>` |
| `L4-port/port-carrier.esml` | 1 | `[diag] solve failed: pantelides: structurally singular: 4 unmatched unknown(s), 1 redundant equation(s)` |
| `L6-connect/connect-rules.esml` | 1 | `[diag] solve failed: pantelides: structurally singular: 2 unmatched unknown(s), 0 redundant equation(s)` |

`esml check` 复测（闭合判据，与 `engine-example-debt.tsv` stage=check 行计数一致）：
literal-enum 3 / algorithm-while 1 / continue-until 1 / method-vary 1 / hyperparams 2；
port-carrier 0 / connect-rules 0（stage=solve 判据：check=0 且 solve 非零，均满足）。

## 二、8 条逐条「改前/改后」

### 1. `L0-type-unit/literal-enum.esml`（check-debt ⇒ 定 engine-debt，示例不动）
写法核查：`<type name="Mode" kind="enumeration" values="off,on,boost" default="off">` +
3×`<literal name=…/>` 已是 canonical——XSD `esml-canonical-basic.xsd:398-409`
（VariableType 下 LiteralType）+ SPEC:159-160（「字面量也可用子元素
`<literal name="a"/>`」）。引擎 `unknown::KNOWN_SUB_TAGS` 无 `literal` ⇒ 引擎债。
改前/改后（仅头注行号引用 158→159；SPEC:158 现是字段集行，枚举类型行现为 :159）：
```
改前: <!-- W21 语法点 `<literal name=>` in `<type>` (SPEC:158 — 枚举类型显式列出字面量)。
改后: <!-- W21 语法点 `<literal name=>` in `<type>` (SPEC:159 — 枚举类型显式列出字面量)。
```
登记：`engine-example-debt.tsv:18`（errors=3，实测一致）+ coverage §5.11 行 1。
**未修（引擎侧），不冒充已修。**

### 2. `L8-function/algorithm-while.esml`（check-debt ⇒ 定 engine-debt）
写法核查：`<algorithm>` 内 `<while condition="false">` 已是 canonical——XSD
`esml-canonical-basic.xsd:1529` + SPEC:871（「`<algorithm>` 内的
`<while condition="c">…</while>`」）。改前/改后（头注行号 858→871）：
```
改前: <!-- W21 语法点 `<algorithm><while condition=>…</while></algorithm>`（算法段循环，SPEC:858）。
改后: <!-- W21 语法点 `<algorithm><while condition=>…</while></algorithm>`（算法段循环，SPEC:871）。
```
台账 verbatim 刷新（§5.11 行 3，旧 verbatim 过期）：
```
改前: `error: F7[]: unknown element <while> at …:12:7` ＋ `F1[]: parser rejected…`，`errors=2`，`five_level=BAD`
改后: `error: F7[]: unknown element <while> at L8-function/algorithm-while.esml:20:9`（`errors=1`，`five_level=ok`；T-LANG-SMOKE 2026-11-12 复测，替代 W27 旧 verbatim …）
```
登记：`engine-example-debt.tsv:19`（errors=1，实测一致）。**未修（引擎侧）。**

### 3. `L9-method-schedule/continue-until.esml`（check-debt ⇒ 定 engine-debt）
写法核查：`<continueUntil condition="m.x < 1.0" maxTime="10"/>` 已是 canonical——
XSD `esml-canonical-basic.xsd:1689`（`maxTime` `use="required"`，
ScheduleContinueUntilType :1672-1689）+ SPEC:1583。引擎只认 `max-time`
（`engine-drift.tsv:18` lang-wins 裁决行）⇒ 引擎债。改前/改后（头注两处行号）：
```
改前: 本文件判据是本仓 XSD（esml-canonical-basic.xsd L1091，`maxTime` required）
      与 SPEC.md:1513（`maxTime` canonical 拼法，附录 C v1.3.3 kebab 退位裁决）。
改后: 本文件判据是本仓 XSD（esml-canonical-basic.xsd:1689，`maxTime` required）
      与 SPEC.md:1583（`maxTime` canonical 拼法，附录 C v1.3.3 kebab 退位裁决）。
```
（basic.xsd:1091 现为 `<selector>` 声明；:1689 才是 maxTime required。）
登记：`engine-example-debt.tsv:20`（errors=1，实测一致）。**未修（引擎侧）。**

### 4. `L9-method-schedule/method-vary.esml`（check-debt ⇒ 定 engine-debt）
写法核查：`<methods><vary name="u.y"/>` 已是 canonical——XSD
`esml-canonical-basic.xsd:303/314/345`（MethodsType / MethodOnLoadType /
MethodDefType 三宿主 MethodVaryType）+ SPEC:1535（METHOD FIX/VARY）。
改前/改后（头注行号 1518→1535；附录号 F7b→K——F7b 是 METHOD RUN 子过程
SPEC:1413，vary 在附录 K / METHOD FIX/VARY）：
```
改前: <!-- W21 语法点 `<methods><vary name=>…</vary></methods>`（METHOD VARY，SPEC:1518）。
      规范条文：附录 F7b（METHOD VARY 子过程）— `<vary name=>` 将变量标为可变。
改后: <!-- W21 语法点 `<methods><vary name=>…</vary></methods>`（METHOD VARY，SPEC:1535）。
      规范条文：附录 K / METHOD FIX/VARY（SPEC:1535）— `<vary name=>` 将变量标为可变。
```
台账 verbatim 刷新（§5.11 行 2，W28 旧 verbatim `:9:22` 过期）：
```
改前: `error: F7[]: unknown element <vary>`（该件引擎 `errors=1`；W27 2026-11-11 重跑）
改后: `error: F7[]: unknown element <vary> at L9-method-schedule/method-vary.esml:23:9`（该件引擎 `errors=1`；W27 2026-11-11 首测，T-LANG-SMOKE 2026-11-12 复测同值）
```
登记：`engine-example-debt.tsv:21`（errors=1，实测一致）。**未修（引擎侧）。**

### 5. `T-tasks/hyperparams.esml`（check-debt ⇒ 定 engine-debt）
写法核查：`<hyperParams><param name="lr" value="0.01"/></hyperParams>` 已是
canonical——XSD `esml-canonical-compute.xsd:384-395`（hyperParams 子元素
`<param>` 0..unbounded，`name`/`value` 属性）+ SPEC:785（§6.9 计算任务表行
「`<hyperParams>` | 超参（`<param name value/>`）」）。**引擎 F1 的
「legacy spelling `<param>` — use `<parameter>`」与本仓 XSD 冲突**：`<param>`
是 `<hyperParams>` 的 canonical 子元素，与 `<parameters><parameter>`
（SPEC:208）是不同容器、不同语义，引擎把 canonical 判成 legacy。
改前/改后（头注两处行号 781→785）：
```
改前: `<param name value/>` 是 `<hyperParams>` 的 vendor 超参数子元素（SPEC:781 —
      规范条文：§6.9（计算任务表）+ SPEC:781（VendorHyperParamsType 允许 `<param>` 0..unbounded）。
改后: `<param name value/>` 是 `<hyperParams>` 的 vendor 超参数子元素（SPEC:785 —
      规范条文：§6.9（计算任务表）+ SPEC:785（VendorHyperParamsType 允许 `<param>` 0..unbounded）。
```
台账：`engine-example-debt.tsv:22`（errors=2 = F7+F1，实测一致）；本次把
`<param>` 行并入 coverage §5.11 表（四处→五处），使 §5.3 的「登记于 §5.11，
不另裁」指针落实。**未修（引擎侧）。**

### 6. `L1-expr-equation/axis-reduce.esml` ⇒ `vector-reduce.esml`（**示例侧已修**）
定性：旧件建在 SPEC 未定义的写法上，且台账归因错误：
- SPEC 无两参 axis 形态：F8（SPEC:1427-1433）只定义单参 `sum(X)/mean(X)/
  min(X)/max(X)/size(X)`（SPEC:860-861 同），明文「不支持：多维数组归约、
  嵌套调用」；`prod` 亦非 F8 内建；SPEC 全文无 `axis`/`I25b`/两参 `sum(x,` 字样。
- 台账旧归因（census 行 + coverage §5.13:646）「演示 check 层 axis 范围校验
  （I25b）…solve 失败属预期行为，非引擎 bug」——错：I25b 是**求解期**校验
  （`negatives.tsv:13` 明文「求解期报 I25b」）；且崩溃发生在 **1D** 件（`m__x`）
  与 2D 件（`m__M_1..3`），不是「多维 spec backlog」。
- 最小复现（本单探针，引擎 release 二进制，`ESML_PROPS=off`，原始行）：
  ```
  1D 两参  s = sum(x, 0)  → error: undeclared symbol(s) referenced during flatten: m__x — …（rc=1）
  2D 两参  r = sum(M, 1)  → error: undeclared symbol(s) referenced during flatten: m__M_1, m__M_2, m__M_3 — …（rc=1）
  1D 单参  s = sum(x)     → system: S (4 unknowns) … m.s 6.0000000000e0（rc=0）
  ```
  即：两参 axis 形（1D/2D）在引擎 flatten 层全崩；单参 F8 canonical 正常。
  两参形态是引擎**非 SPEC 扩展、半实现**：越界 axis 求解期 I25b 有效（探针
  `axis-reduce-probe.esml` 仍有效），在界输入 flatten 崩溃。
修法：示例改写为 F8 单参 canonical（5 内建 × 1D 数组），重命名
`axis-reduce.esml` → `vector-reduce.esml`（名实相符；负例探针保留原名，内容
是两参 axis 越界，名实相符）。改前/改后（census 行）：
```
改前: L1-expr-equation/axis-reduce.esml	1	1	1	0	fail	[spec-backlog F8] SPEC 附录 F8 明文「不支持：多维数组归约」；本件演示 check 层 axis 范围校验（I25b），errors=0，不宣称可 solve。solve rc=1（flatten 层 undeclared symbol m__x，属预期）｜ simulate rc=1（同因）
改后: L1-expr-equation/vector-reduce.esml	1	0	N/A	8	ok	T-LANG-SMOKE（2026-11-12）自 axis-reduce.esml 改写：旧件两参 axis 形 sum(X,k)/prod(M,0) 无 SPEC 拼写（F8 仅单参）、在界输入引擎 flatten 层崩溃（引擎侧缺口，登记见报告）；本件仅用 F8 单参 canonical（SPEC:1427-1433），solve rc=0，值 s=6.0/m=2.0/lo=1.0/hi=3.0/sz=3.0
```
实测：`esml check` errors=0；`esml solve` rc=0，8 未知量
（x=1/2/3，s=6.0，m=2.0，lo=1.0，hi=3.0，sz=3.0）。
台账同步：coverage §5.13.1 删 spec-backlog 行（合计 10→9，加闭合注记）、
§5.13 引言计数、§5.13.2 计数（含旧陈述「11 行 check 8/solve 3」→实际 10 行
check 8/solve 2、`port-array` 已由引擎 J2 修好移出）、:120/:132 文件清单。
**引擎侧缺口登记（本单不修引擎）**：两参 axis 形属非 SPEC 扩展半实现——
错误码 flatten `undeclared symbol`（最小复现：`sum(x, 0)` 1D / `sum(M, 1)` 2D，
x 全元素赋值后仍报 `m__x` / `m__M_1..3` undeclared）；期望行为：要么按
F8 逐元素展开可解，要么 F7/F1 响亮拒收两参拼写（canonical 单轨）。SPEC 是否
收录两参形态未决，留语言侧后续裁决。

### 7. `L4-port/port-carrier.esml`（engine-debt，复核登记，不动）
复核：`esml check` errors=0 ✓；`esml solve` rc=1，
`[diag] solve failed: pantelides: structurally singular: 4 unmatched unknown(s)
i.a.h/i.b.h/j.a.h/j.b.h（+ redundant i.a.q）`（基线原始行，与本次复跑一致）。
台账 `engine-example-debt.tsv:26`（stage=solve，W56b，闭合判据满足）。
错误码：pantelides 结构奇异；最小复现：本文件原样；期望行为：两 flow 变量
端口连接时对第二个 flow 变量 `q` 发守恒残差（W55 探针 14 变体证实缺口在引擎）。

### 8. `L6-connect/connect-rules.esml`（engine-debt，复核登记，不动）
复核：`esml check` errors=0 ✓；`esml solve` rc=1，
`[diag] solve failed: pantelides: structurally singular: 2 unmatched unknown(s),
0 redundant equation(s)`（基线原始行，与本次复跑一致）。
台账 `engine-example-debt.tsv:25`（stage=solve，W56a）。
错误码：pantelides 结构奇异（2 unmatched）；最小复现：本文件原样；期望行为：
求解路径消费 `<connectRules><rule from to/>`（现 `F-CONNECT-RULES-*` 只数
`rule` 条目不联 `connectClass`、HIR/flat 层无消费点，coverage §5.3）。

## 三、修复/未修清单

**修复（本单，示例侧/台账陈述）**
1. `axis-reduce.esml` → `vector-reduce.esml`：重写为 F8 单参 canonical 5 内建，
   重命名，solve 通过（fail→ok）。
2. `tools/solve-smoke.tsv`：行 31 改前/改后（上）+ 计数行 137/8→138/7 +
   来源行加 T-LANG-SMOKE 注记。
3. `docs/coverage.md`：§5.13 引言/分型表/指针计数（含 5.13.2 旧陈述
   「11 行 check 8/solve 3 + port-array」→ 实际「10 行 check 8/solve 2」）；
   §5.11 四处→五处（补 `<param>` 行、刷新 while/vary 旧 verbatim、literal 行
   「`<variable>` 内」→「`<type>` 内」）；:120/:132 文件清单。
4. 5 件 check-debt 示例头注过期引用：literal-enum SPEC:158→159；
   algorithm-while SPEC:858→871；continue-until XSD L1091→:1689 / SPEC:1513→1583；
   method-vary SPEC:1518→1535 / 附录 F7b→K；hyperparams SPEC:781→785（×2）。

**未修（引擎侧，超出本单，已登记）**
1. F7 check 层不认 5 个 XSD/SPEC canonical 名（`<literal>` / `<while>` /
   `maxTime` / `<vary>` / `<param>`）——`engine-example-debt.tsv` stage=check
   5 行（计数与 2026-11-12 复测一致）+ coverage §5.11 五处。其中 `<param>` 件
   引擎 F1 还把 canonical 判成 legacy（与 XSD compute.xsd:387 冲突）。
2. **两参 axis 形态 flatten 崩溃（本单新发现）**：非 SPEC 扩展半实现，在界
   输入 1D/2D 均崩（错误码/最小复现/期望行为见 §二.6）。不登记
   `engine-example-debt.tsv`（改后无阳性示例文件演示该形态；负例探针
   `axis-reduce-probe.esml` 记越界行为），登记于本报告。
3. pantelides 两 flow 端口闭合缺口（port-carrier，W56b）。
4. `<connectRules>` 求解路径不消费（connect-rules，W56a）。

## 四、make check 尾行（2026-11-12，8 常驻闸）

```
[check-element-coverage] 声明 183 个命名元素 · 非负例示例用到 186 个 · 方向 A 缺示例 0 · 方向 B 未声明 3 · 台账 3 行（pending 0 / by-design 3）· 违规 0（警告 3）
[check-attr-coverage] 声明 133 个命名属性 · 非负例示例用到 125 个 · 方向 A 零示例 9 · 方向 B 未声明 1 · 方向 C accepted 未落地 0（accepted 共 28 行）· 台账 10 行（pending 0 / by-design 1 / covered 9）· attr-acceptance 登记 42 属性 · 违规 0（警告 1）
[check-engine-examples] 非负例 158 件 · 引擎实跑逐件 · 台账 10 行（check 8 / solve 2）· 违规 0
[check-spec-element-coverage] XSD 声明 183 个命名元素 · 133 个命名属性 · SPEC 点名 183 个元素 / 133 个属性 · 方向 A 缺 0 · 方向 B 缺 0 · 台账 0 行（pending 0 / by-design 0）· 违规 0（警告 0）
[check-example-expectations] 台账 15 行（8 件示例）· 违规 0

make check: 全绿
```

## 五、六原则证据与自评

- **正确**：每条 fail 给改前/改后原始行（§二）；5 条 check-debt 的
  `esml check` 复测计数（3/1/1/1/2）与台账逐一对齐，2 条 engine-debt 的
  solve 非零复跑确认——engine-debt 一律保留 fail 原状，不冒充已修；
  vector-reduce 的 solve rc=0 与 5 内建数值（6/2/1/3/3）实测。
  自评 A。
- **优雅**：vector-reduce 只用 F8 单参 canonical 单源写法（无两参形态、无
  `prod`、无别名）；台账与示例一致（census 行/§5.13/§5.11/台账计数全部
  对齐当日实测；5 件头注引用全部刷到现行 SPEC/XSD 行号）；两参形态不留
  阳性示例、负例探针保留其行为记录——无别名双轨。自评 A。
- **规范**：提交范围只本单 10 文件（5 示例 + 1 新示例 + census + coverage +
  本报告；`git add` 显式清单）；`make check` 8 闸全绿。自评 A。
- **可扩展**：修法可复用——「示例建在非 canonical 形态上 ⇒ 改写为 SPEC
  canonical 形态 + 文件名随 SPEC 特性名 + 台账/coverage 同步刷新 + 引擎侧
  缺口按错误码/最小复现/期望行为登记」这一套适用于任何同类示例；头注行号
  刷新与 §5.11 verbatim 刷新模式同样可复用到后续 W 批次。自评 A。
- **高效**：smoke 复跑只 8 件 × 120 s 上限，实际 <30 s；探针 5 件最小文件；
  未引入任何新长耗时步骤。自评 A。
- **鲁棒**：本单实际撞上两道工具闸的响亮报错并照报修复：
  ① `check-examples` manifest 闸把新件头注里的「负例」字样判成「自称负例
  却不在 negatives.tsv」→ 措辞改为「探针」；② `validate_examples` 第 3 节
  把「规范条文：」行折行（同行无 `。`）判成「未指名 SPEC 章节」（188/189）
  → 合并单行。无静默跳过、不放宽判据。自评 A。

## 六、留置（不在本单范围，如实记录）

- `engine-drift.tsv` 内多处 SPEC 行号引用（L1512/L846/:1526 等）随 SPEC 增长
  已漂移——全仓台账级旧债，非本单 8 条 fail 的组成，留置不修。
- 两参 axis 形态是否入 SPEC（语言侧裁决）与引擎侧 flatten 修复（引擎侧单）
  均待后续单。

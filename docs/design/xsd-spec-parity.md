# SPEC ↔ XSD 文档根对账

> 门：`tools/check-spec-xsd-parity.py`（三方对账 + 自证，仅标准库依赖）。
> 基线：`c6333f1`（`origin/main`）。
> 本轮结论：**改前 6 处机判 → 3 处是门的误判（改规则）→ 4 处真实差异 → 逐条裁定 → 改后 0 处**。

## 一、为什么要有这道门

`xsd/esml-v1.xsd`（入口层）的**根清单**是手写的；`SPEC.md` 正文里散着「什么是文档根」
的散文描述。两边一旦漂移，机器拦不住，只有等某个文档被拒收时才有人发现：

| 漂移方向 | 后果 | 历史实例 |
|---|---|---|
| 入口层**多收**一个根（canonical 层没有的假根） | 放行一份 canonical 层必然拒收的文档 ⇒ **假绿** | `schedule` / `solutionParameters` / `variables` / `domain`（v1.3.3 已删） |
| 入口层**漏收**一个根（canonical 的全局元素没进清单） | 入口层拒收一份 canonical 层认可的文档 ⇒ **误拒** | `metadata` / `project`（v1.3.3 已补） |
| SPEC 把它写成文档根，XSD 不认 | 人读哪边都「有道理」，schema 与规范对不上 | 本轮 4 处（canonical 的全局根，SPEC 正文只字不提） |

口径写在 `xsd/esml-v1.xsd:26-34` 的注释里：**入口层根清单 = canonical 层的全局元素集**。
本门把这句话变成机器判据，并补上 SPEC 这一路。

## 二、三个集合

| 集合 | 取自 | 抽取方式 |
|---|---|---|
| `R_canon` | `xsd/esml-canonical-*.xsd` | 每个 schema 顶层的**全局** `xs:element`（只看 `xs:schema` 的直接子元素） |
| `R_entry` | `xsd/esml-v1.xsd` | 同上 |
| `R_spec` | `SPEC.md` | 正文里被描述为**文档根**的元素名（散文抽取，规则见 §六） |

当前三个集合（12 个）：`esml` / `units` / `variableTypes` / `portTypes` / `modelTypes` /
`systems` / `system` / `orderedSet` / `metadata` / `computeTasks` / `project` / `tasks`。

## 三、判定规则

| 编号 | 判据 | 红了意味着 |
|---|---|---|
| `C1` | `R_entry ⊆ R_canon` | 入口层多收根 ⇒ 假绿 |
| `C2` | `R_canon ⊆ R_entry` | 入口层漏收根 ⇒ 误拒 |
| `C3` | `R_spec ⊆ R_canon` | SPEC 把 XSD 不认的写法写成文档根 |
| `C4` | `R_canon ⊆ R_spec` | canonical 的全局根，SPEC 正文只字不提 |
| `C5` | SPEC 的 ```` ```xml ```` 示例块最外层元素 | XSD 里有同名声明（全局或局部） |

`C1`+`C2` 合起来 = 「入口层根清单 = canonical 层全局元素集」；`C3`+`C4` 合起来 =
「SPEC 说的根 = XSD 的根」。任一条不成立即红，退出码 1。

## 四、本轮差异与逐条裁定

### 4.1 改前：先有 6 处，其中 3 处是**门自己的误判**

在 `c6333f1` 上跑第一版门（抽取规则未修）：

```
[parity] 对账结果
  [C3] SPEC 声明了 XSD 不认的文档根 —— 3 处
      <recordType>  SPEC 把它写成文档根，canonical 层却没有这个全局元素 （证据 SPEC.md:162）
      <recordTypes>  SPEC 把它写成文档根，canonical 层却没有这个全局元素 （证据 SPEC.md:162）
      <solutionParameters>  SPEC 把它写成文档根，canonical 层却没有这个全局元素 （证据 SPEC.md:753）
  [C4] canonical 有全局根而 SPEC 未写成文档根 —— 3 处
      <portTypes>  canonical 层的全局根，SPEC 正文里没被写成文档根
      <system>  canonical 层的全局根，SPEC 正文里没被写成文档根
      <systems>  canonical 层的全局根，SPEC 正文里没被写成文档根

[parity] 共 6 处差异。
```

前 3 处（C3）**不是** SPEC 与 XSD 的分歧，是**门把成员级「顶层段」当成了文档根**：

| 误判项 | SPEC 原文（`c6333f1`） | 实际含义 |
|---|---|---|
| `<recordTypes>` / `<recordType>` | 「顶层 `<recordTypes>` 目录内写 `<recordType name>`」（:162） | `<esml>` 的一个**成员段**（类型段） |
| `<solutionParameters>` | 「**顶层 `<solutionParameters>` 段**（与 `<computeTasks>` 同族的顶层段）」（:753） | `<esml>` 的一个**成员段**（求解参数段） |

「顶层」在规范里有两义：文档级（「顶层声明」）与成员级（「顶层段」）。第一版门把
「顶层 + 行内代码 span」当成了文档级，于是把成员段读成了根。

**裁定：改门（抽取规则），不动 SPEC、不动 XSD** —— 这三处 SPEC 与 schema 本来就是对的，
改任何一边都是把对的改错。规则怎么改见 §六（`R7`）。

### 4.2 修完规则：剩下 4 处，是真的

```
[parity] 对账结果
  [C4] canonical 有全局根而 SPEC 未写成文档根 —— 4 处
      <metadata>  canonical 层的全局根，SPEC 正文里没被写成文档根
      <portTypes>  canonical 层的全局根，SPEC 正文里没被写成文档根
      <system>  canonical 层的全局根，SPEC 正文里没被写成文档根
      <systems>  canonical 层的全局根，SPEC 正文里没被写成文档根

[parity] 共 4 处差异。
```

### 4.3 裁定表

| # | 差异 | 依据 | 裁定 | 落地 |
|---|---|---|---|---|
| 1 | **`<portTypes>`**：canonical 全局元素（`esml-canonical-basic.xsd:900`），入口层已收（`esml-v1.xsd:43`），SPEC 正文却没写成文档根 | 口径「根清单 = canonical 全局元素集」下它**就是**合法文档根；SPEC 不写 = 读者无从判断能不能单独成文件 | **改 SPEC** | §13 新增「文档根清单」（12 个），点名哪些**不是**根 |
| 2 | **`<system>`**：同上（`esml-canonical-basic.xsd:912` / `esml-v1.xsd:53`） | 同上 | **改 SPEC** | 同上 |
| 3 | **`<systems>`**：同上（`esml-canonical-basic.xsd:890` / `esml-v1.xsd:49`） | 同上 | **改 SPEC** | 同上 |
| 4 | **`<metadata>`**：同上（`esml-canonical-basic.xsd:919` / `esml-v1.xsd:63`） | 同上 | **改 SPEC** | 同上 |
| 附 A | §13「XSD 分层」表**漏了 `esml-canonical-project.xsd` 一行**（附录 H 里有），而 `<project>` 正是它声明的根（`esml-canonical-project.xsd:86`） | 根清单的来源 schema 不该在表里缺席 | **改 SPEC** | §13 表补一行（覆盖 / 根 / 校验） |
| 附 B | 附录 C 的 v1.3.3 条目仍写「删 5 个 canonical 并不存在的假根（… / `tasks` / …）」——本轮合并（`4c5bf4d`）已把 `<tasks>` 升为 canonical 全局元素并在入口层声明，**它不是假根** | 修订史条目描述的是 v1.3.3 的最终状态；条目与 schema 相反 = 读者照着它会判错 | **改 SPEC** | 改成「删 4 个假根」，并写明 `<tasks>` 先删后升、如今是文档根 |
| 附 C | 3 处 C3 误判（`<recordTypes>` / `<recordType>` / `<solutionParameters>`） | 见 §4.1 | **改门**（抽取规则 `R7`），SPEC/XSD 不动 | 门 + 合成自证用例「好 4」 |

**为什么都不改成 XSD**：这 4 个名字在 canonical 层**本来就是**全局元素、入口层**本来就**照收了
—— 漂移只发生在 SPEC 正文这一侧。改 XSD 只能把已经对的 schema 改错；而删掉 canonical 的
全局元素又会让已有的合法文档（独立单位表、独立系统表 …）被拒收。

**为什么不用 by-design 登记**：by-design 是「确有据可查、判为不改」的分歧。这 4 处都有确定
修法（把清单写进规范），登记进去等于把一个**缺口**伪装成**设计**。所以登记表本轮为空，
见 §五。

### 4.4 落地后（`SPEC.md` §13）

```
**文档根清单**（入口层 `xsd/esml-v1.xsd` 的根清单 = canonical 层**全局元素集**）：
`<esml>` / `<units>` / `<variableTypes>` / `<portTypes>` / `<modelTypes>` / `<systems>` /
`<system>` / `<orderedSet>` / `<metadata>` / `<computeTasks>` / `<project>` / `<tasks>`
—— 共 12 个。
除 `<esml>` 外其余 11 个都可**单独成文件**（独立单位表 / 变量类型表 / 端口类型表 /
组件类型表 / 系统表 / 单个系统 / 独立序集 / 独立元数据 / 独立计算任务表 / 独立工程壳 /
独立任务表外壳）。

这 12 个之外的名字**不是文档根**：`<schedule>` / `<solutionParameters>` /
`<variables>` / `<domain>` 都不是 —— 它们只在 `<system>` / `<esml>` / `<modelType>` /
`<domains>` 内部出现，入口层不收它们作根。
```

改后机判：**0 处差异**（`R_canon = R_entry = R_spec = 12`）。

## 五、by-design 登记

登记口径在 `tools/spec-xsd-bydesign.tsv`（`kind<TAB>name<TAB>reason`，`kind ∈ spec-root / entry-root`）。
**本轮为空** —— 差异都有确定修法，没有「判为不改」的。

这张表**先于**代码存在：下一个想给入口层加根、或想在 SPEC 里写一个新根的人，会先撞上它，
而不是撞上一句注释。将来真有「确有据可查、判为不改」的分歧（例如某个 canonical 全局元素
**故意**不做文档根），登记进去，本门对它放行 —— 但必须写清理由，理由要能被下一个人复核。

## 六、SPEC 侧的抽取规则（散文 → 元素名）

SPEC 是散文，没有「根清单」字段，只能从正文抽。规则写死在
`tools/check-spec-xsd-parity.py` 里，**规则本身也是可审的**（改规则 = 改判定口径，
必须同步改本节与脚本内的注释）：

| 编号 | 规则 |
|---|---|
| `R1` | **根声明行** = 散文行/段里出现根标记词（`根` / `顶层`）的行/段。排除假朋友：`可加库根`（libroot）、`根目录`、`根取并集` 等 |
| `R2` | **行级否定**：出现 `删` / `移除` / `退位` / `不再` / `曾经` / `漏根` / `假根` / `旧版` / `历史` / `过时` 的行，是在讲「改了什么」，不是「现在什么是根」——附录 C（修订史）里的「删 4 个假根、补 2 个漏根」正属此类 |
| `R3` | **分句级否定**：子句里出现 `不是文档根` / `非文档根` / `不作为根` / `不能作根` 时，该子句里的元素名不算根声明 |
| `R4` | **表格**：表头含根标记词的表，其「根」列是根声明列，只从那一列抽（不从「覆盖」列抽——那列全是元素名，抽了就是噪声）；非根表按整行抽 |
| `R5` | **元素名来源**：行内代码 span 能当 XML 片段解析 ⇒ 取其**根元素名**（`<orderedSet>…</orderedSet>` 只算 `orderedSet`，不算里面的 `<element>`）；解析不了 ⇒ 取 span 里**最外层**的标签名；根声明列里还可以是裸写的 `/` 分隔列表（`units/variableTypes/modelTypes`） |
| `R6` | **示例块**：```` ```xml ```` 代码块的最外层元素单列成信息表，并机验它在 XSD 里有同名声明（`C5`）——示例顶层写个 XSD 根本没声明的名字，一定是拼写漂移 |
| `R7` | **成员级「顶层」**：「顶层」后面**紧跟行内代码 span** ⇒ 它点名的是某个**元素**（「顶层 `<solutionParameters>` 段」「顶层 `<domains>` 声明计算域」），说的是文档的一个**成员段**，不是文档根。例外：「顶层 `<X>` 根」—— 那时 `X` 就是根（`R8`） |
| `R8` | **「`<X>` 根」句式独占**：紧跟在「根」前面的那个 span 才是被声明的根，同一子句里并列提到的别的名字不算 —— §1.1 标题「（`<esml>` 根 · `<metadata>`）」里 `<metadata>` 只是骨架的一项，不是「它是根」的声明 |

`R7` / `R8` 是本轮补的：它们对应 §4.1 的 3 处误判与「§1.1 标题把 `<metadata>` 算成根声明」
的连带问题。**两条规则都有合成自证用例钉住**（见 §七：拆掉任一条，对应的好用例立刻变红）。

### 已知的语义歧义（机器判不了的那部分）

1. **「顶层」两义**：文档级（「顶层声明」= 声明在文档顶层）与成员级（「顶层区段」「顶层
   method」「对顶层公开量」「顶层 `<X>` 段」）。`R7` 按「顶层后面紧不紧跟代码 span」判：
   紧跟 ⇒ 成员级。**词表漏收会让 C3/C4 多红**；补规则即可，判定口径在脚本顶部常量里。
2. **同一个词、两个层级**：`<project>`（工程容器，文档根）与 `<tasks>`（`<computeTasks>` 的
   外层壳）在 §6.8 里被同一个词「顶层壳」并称 —— 而两者**都是**文档根（`<tasks>` 是
   canonical-compute.xsd:604 的全局元素，入口层 esml-v1.xsd:60 同步声明）。机器只能报出
   「同一句里并列了几个名字」，**裁不了**「谁是壳、谁是容器」；这靠 §6.8 正文分开写。
3. **附录 C（修订史）不算规范性声明**：讲「改了什么」的段落整行排除（`R2`）。**代价**：
   门看不见修订史与 schema 的**事实性**矛盾（附 B 那条就是靠人读发现的）—— 修订史描述的是
   「当时做了什么」，机器判它等于判历史，若要判，只能另写一条「当前状态一致性」的查法。
4. **SPEC 示例块当片段看**：§5 的示例最外层是 `<portTypes>`、§6 的是 `<system>`，但它们是
   片段而不是整份文档 —— 所以示例块只进信息表与 `C5`，不进 `R_spec`。

## 七、自证

```sh
python3 tools/check-spec-xsd-parity.py --self-test
```

「一个对任何东西都说 OK 的检查器，和没有检查器等价。」所以门自带构造样例：

* **合成树 5 好 4 坏**（好例必须 0 红、坏例必须红，任一翻转即自证失败）：
  * 好 1 / 好 2：三方一致的树；
  * 好 3：SPEC 明说某元素不是文档根 ⇒ 该名字不得进根声明集
    （把分句否定词表拆掉，这条**立刻变红**）；
  * 好 4：成员级「顶层」不算文档根（把 `R7` 拆掉，这条**立刻变红**）；
  * 好 5：「`<X>` 根」句式独占（把 `R8` 拆掉，这条**立刻变红**）；
  * 坏 1：入口层**删**一个根（漏收）；坏 2：入口层**多**一个根（多收）；
    坏 3：SPEC 把 XSD 不认的写成根；坏 4：canonical 有根而 SPEC 只字不提。
* **反向自检**：SPEC 凭空声明 `<ghostRoot>` ⇒ `C3` 必须抓到（抓不到说明判定被架空了）。
* **真实树上的变异测试**（4 例，直接在本仓这棵树上做）：删根 / 多根 / SPEC 凭空加根 /
  canonical 加全局元素而入口层没收 —— 每一条都必须**真的变红**。

原始输出见 §九。

## 八、怎么跑 / 改完怎么验

```sh
python3 tools/check-spec-xsd-parity.py                # 全量对账；退出码 0 = 三方一致
python3 tools/check-spec-xsd-parity.py --report        # 附带 SPEC 根声明清单与证据行
python3 tools/check-spec-xsd-parity.py --self-test     # 5 好 4 坏 + 反向 + 真实树变异
```

改 XSD 根清单或改 SPEC 根描述之后，**两件事都要跑**：

```sh
python3 tools/check-spec-xsd-parity.py
/home/ai4e17/.venv-xmllint/bin/python tools/check-examples.py   # 示例 × XSD 门（需 lxml）
```

## 九、原始输出

### 改前 · 第一版门（抽取规则未修，`c6333f1`）

```
[parity] 对账结果
  [C3] SPEC 声明了 XSD 不认的文档根 —— 3 处
      <recordType>  SPEC 把它写成文档根，canonical 层却没有这个全局元素 （证据 SPEC.md:162）
      <recordTypes>  SPEC 把它写成文档根，canonical 层却没有这个全局元素 （证据 SPEC.md:162）
      <solutionParameters>  SPEC 把它写成文档根，canonical 层却没有这个全局元素 （证据 SPEC.md:753）
  [C4] canonical 有全局根而 SPEC 未写成文档根 —— 3 处
      <portTypes>  canonical 层的全局根，SPEC 正文里没被写成文档根
      <system>  canonical 层的全局根，SPEC 正文里没被写成文档根
      <systems>  canonical 层的全局根，SPEC 正文里没被写成文档根

[parity] 共 6 处差异。裁决见 docs/design/xsd-spec-parity.md
```

### 改前 · 修完规则（同一棵 `c6333f1` 树，只改了门）

```
[parity] 对账结果
  [C4] canonical 有全局根而 SPEC 未写成文档根 —— 4 处
      <metadata>  canonical 层的全局根，SPEC 正文里没被写成文档根
      <portTypes>  canonical 层的全局根，SPEC 正文里没被写成文档根
      <system>  canonical 层的全局根，SPEC 正文里没被写成文档根
      <systems>  canonical 层的全局根，SPEC 正文里没被写成文档根

[parity] 共 4 处差异。裁决见 docs/design/xsd-spec-parity.md
```

### 改后

```
[parity] 三方集合
  R_canon  canonical 层全局元素 (12): computeTasks esml metadata modelTypes orderedSet portTypes project system systems tasks units variableTypes
  R_entry  入口层全局元素     (12): computeTasks esml metadata modelTypes orderedSet portTypes project system systems tasks units variableTypes
  R_spec   SPEC 文档根声明     (12): computeTasks esml metadata modelTypes orderedSet portTypes project system systems tasks units variableTypes

[parity] 对账结果
  三方一致：入口层根清单 = canonical 层全局元素集 = SPEC 文档根声明。0 处差异。
```

### 自证

```
[self-test] 构造样例 5 好 4 坏 —— 证明本检查器真的会红
  [PASS] 好 1：三方一致（2 根）                      应判绿 → 实际判绿了
  [PASS] 好 2：三方一致（4 根）                      应判绿 → 实际判绿了
  [PASS] 好 3：SPEC 明说 <innerShell> 不是文档根     应判绿 → 实际判绿了
  [PASS] 好 4：成员级「顶层」不算文档根                   应判绿 → 实际判绿了
  [PASS] 好 5：并列提及不算根声明                      应判绿 → 实际判绿了
  [PASS] 坏 1：入口层删了一个根（漏收）                   应判红 → 实际判红了（C2:units）
  [PASS] 坏 2：入口层多了一个根（多收）                   应判红 → 实际判红了（C1:schedule）
  [PASS] 坏 3：SPEC 把 XSD 不认的写成根              应判红 → 实际判红了（C3:bogusRoot）
  [PASS] 坏 4：canonical 有根而 SPEC 只字不提        应判红 → 实际判红了（C4:project）
  [PASS] 反向自检：SPEC 凭空声明的根 <ghostRoot> 被 C3 抓到

[self-test] 真实树上的变异测试（人为删一个根 / 多一个根 / SPEC 凭空加一个根）
  [PASS] 变异 1：入口层删掉 <metadata>（漏收） ⇒ 变红：[('C2', 'metadata')]
  [PASS] 变异 2：入口层多一个 <ghostRoot>（多收） ⇒ 变红：[('C1', 'ghostRoot')]
  [PASS] 变异 3：SPEC 凭空写一个根 <ghostRoot> ⇒ 变红：[('C3', 'ghostRoot')]
  [PASS] 变异 4：canonical 多一个全局元素而入口层没收 ⇒ 变红：[('C2', 'newGlobal'), ('C4', 'newGlobal')]
```

### 「好例必须实的」——拆掉规则看重例翻红

```
=== 拆掉「分句否定词表」⇒ 好 3 必须变红 ===
  [BROKEN] 好 3：SPEC 明说 <innerShell> 不是文档根     应判绿 → 实际判红了（C3:innerShell）

=== 拆掉「顶层 + 代码 span ⇒ 成员级」⇒ 好 4 必须变红 ===
  [BROKEN] 好 4：成员级「顶层」不算文档根                   应判绿 → 实际判红了（C3:metaSeg）
```

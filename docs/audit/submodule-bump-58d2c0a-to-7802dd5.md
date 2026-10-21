# 审计：引擎子模块指针 `58d2c0a` → `7802dd5`

- **审计日期**：2026-10-21
- **审计对象**：规范仓 `esml-language`（`~/work-language`）在 `58d2c0a..7802dd5` 之间的 **59 个提交**
- **审计分支**：`b8-submodule-bump-audit`（从 `origin/main` = `7802dd5` 建）
- **性质**：**严格只读审计**。本轮未改引擎、未改本仓源文件；本仓唯一的改动是新增本文件。
- **口径**：所有数字都在本轮用 `git log --oneline` / `git diff --stat` / `git ls-tree` / `git show`
  当场跑出来，原始行贴在文末 §8；**不引用任何旧批次结论**。引擎侧的数字由**引擎自己的闸门程序**
  `tools/four_way_gate.py` 实跑得出（只读运行，不改引擎仓任何文件）。

---

## 0. 摘要

**一句话**：这 59 个提交里，**XSD 结构改动 18 笔、规范正文改动 11 笔、示例语料改动 11 笔、仅工具 15 笔**
（另 4 笔合流提交、7 组重复 patch），净内容 41 笔；**指针提升会让引擎的闸门第 [1] 层多一件未登记的红
（`examples/syntax/D-skeleton/project.esml`）、闸门第 [2] 层多一件未登记的拒绝（同一件）**，
因为引擎至今**不认 `<project>` 这个根**（`git grep -n '"project"' origin/main -- crates/` 零命中）。
而**引擎基线本来就是红的**（`origin/main` 上闸门已判 `DISAGREE`），提指针只是在这条红线上**再加一件**。
⇒ **指针不能先提**：必须等引擎侧把 `<project>` 支持与闸门根路由补齐（§6）。

| 关键实测 | 数值 | 证据 |
|---|---|---|
| 区间提交数 | **59** | §8.1 |
| 内容提交 / 合流提交 | 55 / 4 | §2.2 |
| 重复 patch-id（同一改动提了两次） | **7 组 / 14 笔** ⇒ 净内容 41 笔 | §2.3 |
| 四桶提交数（A/B/C/D） | 18 / 11 / 11 / 15 | §2.2 |
| 四桶文件数（A/B/C/D） | 4 / 1 / 143 / 13 | §2.1 |
| 改动 `xsd/` 的提交 | **24** | §3.1 |
| 改动语料（`*.esml`）的提交 | **22** | §3.2 |
| 改动闸门/对账判据的提交 | **29** | §3.3 |
| 改动白名单/登记表行数的提交 | **3 类**（`negatives.tsv` 0→11→12；`aliases.tsv` 0→82；`spec-xsd-bydesign.tsv` 0→0） | §3.4 |
| 闸门第 [1] 层 XSD 违规 | **10 → 11**（+`project.esml`） | §4.1、§8.4 |
| 闸门第 [2] 层「未登记拒绝」 | **2 → 3**（+`project.esml`） | §4.1、§8.5 |
| G16 白名单里指向子模块的行 | **10 行**，提升后 10 行全部仍存在、判定层不漂移 ⇒ **白名单行数不变** | §3.4、§4.1 |
| 语料件数 | **136 → 141**（净 A 6 / R 2 / D 1） | §3.2 |

---

## 1. 审计对象：指针是什么，两端是谁

### 1.1 引擎侧的子模块登记与当前指针

引擎仓（`~/esml`，`origin` = `/home/ai4e-hermes/esml-engine-user3`）在 **2026-10-20** 把
`examples/syntax`（语法点矩阵的语料）从「引擎仓内嵌副本」改成**规范仓的 git submodule**：

```console
$ git -C ~/esml show origin/main:.gitmodules
[submodule "examples/syntax"]
	path = examples/syntax
	url = git@github.com:ai4energy/esml-language.git

$ git -C ~/esml ls-tree origin/main examples/ | grep syntax
160000 commit 58d2c0af3b3ee8502c4e9455ae63b0284c75eb7e	examples/syntax

$ git -C ~/esml log --oneline -2 --format='%h %ad %s' --date=short origin/main -- examples/syntax
a995dd4e 2026-10-20 chore(syntax): 示例仓指针 → 58d2c0a（L6 连接改规范拼写）
339f4442 2026-10-20 build(syntax): examples/syntax 改为 esml-language 规范仓 submodule（pin v1.3.2）

$ git -C ~/esml log --oneline -1 origin/main
b12a0d93 feat(perf): 阀网墙钟上限按 §6.2 收紧到 2.0x，G17 带上 kyv8/kyv18
```

**指针的当前值 = `58d2c0a`**，落在引擎 `origin/main` 上。

### 1.2 提升目标 `7802dd5` 是谁

`7802dd5` 是**规范仓自己的 `origin/main`**：

```console
$ git -C ~/work-language log --oneline -1 origin/main
7802dd5 merge: 合入 ai4e18 根矩阵门（2 提交）—— SPEC §6.8/§13 与入口 XSD 三方并集

$ git -C ~/work-language log --oneline -1 58d2c0a
58d2c0a Canonicalize L6 connect example to <connection>
```

⇒ **本审计审的是「规范仓这 59 个提交会被子模块指针一次性吞进引擎」**。这 59 个提交落在四个面上：
XSD 声明、规范正文、示例语料、工具/台账。

### 1.3 区间原始输出（59 行，逐行）

```console
$ git -C ~/work-language log --oneline 58d2c0a..7802dd5 | wc -l
59
```

```console
7802dd5 merge: 合入 ai4e18 根矩阵门（2 提交）—— SPEC §6.8/§13 与入口 XSD 三方并集
4f3010c merge: 合入 ai4e17 SPEC↔XSD 文档根对账门（2 提交）
1175d70 docs(spec): 文档根清单入正文（12 个），附录 C 假根条目收口
093558f feat(tools): SPEC ↔ XSD 文档根对账门——入口/canonical/规范三方机判
e93c9b2 docs(coverage): 把 §6 提交表里的「（本提交）」换成实际 SHA
35f32e8 fix(xsd,spec): 入口层根清单收敛到 canonical 全局元素，并落成常驻机判
c6333f1 merge: 合入 ai4e18 台账收口（SPEC 改名遗留、负例登记、<tasks> 根对齐）
4c5bf4d fix(validate): 合并后收口——SPEC 改名遗留、负例登记、<tasks> 根对齐
e7e5275 docs(spec): 版本头升到 v1.3.3，附录 C 写清本轮变更
5ffa05c docs(xsd): 注释里的 kebab 拼写与「兼容别名」说法改成 canonical
ba79096 feat(examples): 补一份 <project> 示例——project schema 此前零覆盖
6e6b25e docs(spec): 正文其余段落逐条改成 canonical 拼法，与 XSD 对齐
eecbb3d docs(spec): §2 收紧集与 XSD 对齐——去掉「兼容别名」与「XSD 仍声明」的说法
d65f384 feat(tools): 词法别名裁决表落成数据，机验「同一语义只有一种写法」
ed1ce5d fix(xsd): 入口 schema 的根清单对齐 canonical 的全局元素集
c7fe19c 删掉 legacy 元素 `<component>` 的 schema 声明，复合成员只收 `<instance>`
fd4d92d 属性名收敛到 canonical 拼法：porttype/interface/desc 三处 legacy 名退位
daf9371 类级继承的元素名收敛为 `<extendsFrom>`，去掉同语义的 `<extends>`
b5f4fbf 调度步的同语义别名收敛为一个：`<reset>` 留，`<reassign>` 去
6409928 XSD 属性名收敛为 camelCase：kebab 拼写不再是合法语法
d45e955 refactor(xsd): 拆掉三处「包着单元素的 xs:choice」死脚手架
c573f97 fix(xsd): canonical <esml> 根补声明 <tasks> 外层壳
10bf96f feat(tools): 示例 × XSD 一致性门（含 2 好 2 坏自证与负例清单）
14a9ffb merge: XSD/示例一致性收敛 + 别名裁决表（ai4e17，16 提交）
d63d39f docs(coverage): 把 §6 提交表里的「（本提交）」换成实际 SHA
03b8b38 docs(coverage): §5.8 补一句闸门实测——[3] 角并不因 14/83 判红
696aecd docs: 落盘 SPEC 覆盖对账表，并在 README 挂上入口
89262a5 docs(SPEC): §6.5 补条件的操作数作用域，并把「参数形态」标为待定
c673d57 docs(examples): 修 instance-condition 头部指向已删文件的旧引用
1a494bd docs(examples): 补 §6.5 条件组件的正例与「条件不可静态判定」负例
35c2bfe docs(examples): port-roles-io 的头部补上 §6.6（系统级方程）
17547ec docs(examples): 补附录 F2 的信号口跨 PortType 因果连接示例
90e3770 docs(examples): 五份示例的头部补上第二条规范条文（附录 F6 / F7 / F8）
6ff438d docs(validate_examples): 聚合器按头部指名的**全部**条文统计
c438e6d docs(validate_examples): 落盘示例 ⇄ 规范 对账机验（coverage.md 的数字来源）
3a1934b fix(xsd): `<partition>` 的显式属性改成 canonical 拼写 discipline / timeLayer
cfb2b31 docs(examples): 138 份示例的头部逐份指名其规范条文
e239003 docs(spec): 版本头升到 v1.3.3，附录 C 写清本轮变更
0d28be6 docs(xsd): 注释里的 kebab 拼写与「兼容别名」说法改成 canonical
6f5d321 feat(examples): 补一份 <project> 示例——project schema 此前零覆盖
f844361 fix(examples): 四份导数负例的头部把「check 应报错」改成「schema 校验应报错」
49f7882 docs(spec): 正文其余段落逐条改成 canonical 拼法，与 XSD 对齐
fc4d05c chore(examples): 单位分组示例归位到 L0-type-unit
cc102dc docs(spec): §2 收紧集与 XSD 对齐——去掉「兼容别名」与「XSD 仍声明」的说法
b4b9599 feat(tools): 词法别名裁决表落成数据，机验「同一语义只有一种写法」
fecce7a fix(xsd): 入口 schema 的根清单对齐 canonical 的全局元素集
526d283 docs(SPEC): §6.7 初始化过程改回 canonical 拼写与载荷（正文落后于示例与实现）
ca8efc7 docs(SPEC,xsd): 补 §6.8 `<tasks>` 外壳与 §6.9 元数据族条文，修三处正文/schema 错位
a392a77 删掉 legacy 元素 `<component>` 的 schema 声明，复合成员只收 `<instance>`
aaa10fc 属性名收敛到 canonical 拼法：porttype/interface/desc 三处 legacy 名退位
21ddbee docs(SPEC): 修 §6.8 canonical 示例的三处 schema 违规，并补 §6.9 计算任务表条文
354aac6 类级继承的元素名收敛为 `<extendsFrom>`，去掉同语义的 `<extends>`
89039d7 调度步的同语义别名收敛为一个：`<reset>` 留，`<reassign>` 去
ee8ae31 XSD 属性名收敛为 camelCase：kebab 拼写不再是合法语法
c63f0c4 refactor(xsd): 拆掉三处「包着单元素的 xs:choice」死脚手架
835fa02 docs(examples): 补 §6.4 子系统 crosslink 与附录 K 段前方法体两份示例
13e2dd3 fix(xsd): canonical <esml> 根补声明 <tasks> 外层壳
cf498a3 feat(tools): 示例 × XSD 一致性门（含 2 好 2 坏自证与负例清单）
```

### 1.4 归桶口径（本审计自定义，可复核）

| 规则 | 内容 |
|---|---|
| **按路径归桶** | `xsd/**` → **A**；`SPEC.md` → **B**；示例目录（`D-skeleton/` `L0-`…`L9-` `T-tasks/` `X-use/`，即 `*.esml`）→ **C**；其余（`tools/` `docs/` `Makefile` `README.md`）→ **D** |
| **主桶（提交级）** | 该提交改动文件数最多的桶；并列时按 **A > B > C > D** 取先者 |
| **合流提交** | 4 笔 merge 只带内容不带新提交（其并入的净内容已由各内容提交承担），**单列**，不摊进四桶，避免重复计数 |
| **重复 patch** | 同一 patch 在两条分支各提一次（`git patch-id --stable` 相同）⇒ 记为 **1 笔净改动** |
| **跨桶提交** | 一个提交同时改动了多桶的文件 ⇒ 在逐桶汇总里单列，**不藏**（§2.2 跨桶明细） |

---

## 2. 四桶清单与文件计数

### 2.1 表 A · 文件级统计（`git diff --numstat` 逐提交累加）

```console
桶    名称                           文件数        改动次数       插入           删除           触及提交数
A    XSD 结构改动                     4          34         487          300          24
B    规范正文改动                     1          20         994          256          20
C    示例语料改动                     146        314         786          121          22
D    仅工具（工具/台账/说明）                13          53         7884         28           20
合计：去重文件 164 ；插入 10151 ；删除 705
```

> **C 桶「146」的口径说明**：`git diff --numstat` 对**改名**输出的是一条
> `L6-connect/{connect-legacy.esml => connect-canonical.esml}` 这样的**改名伪路径**，
> 脚本把它当成独立文件计了 3 次。核账：
> **真实路径并集 = 143**（逐提交 `--name-only` 去重），
> **端点净差集 = 142**（`git diff --name-status -M` 展开成 A 6 / R 2 / D 1）。
> 三个数字都对，只是口径不同；**本报告一律用 143**。

各桶的文件清单：

| 桶 | 文件（改动次数） |
|---|---|
| A | `xsd/esml-canonical-basic.xsd`（17）· `xsd/esml-v1.xsd`（4）· `xsd/esml-canonical-compute.xsd`（3）· `xsd/esml-canonical-project.xsd`（2） |
| B | `SPEC.md`（16） |
| C | 143 个 `*.esml`（改动 ≥2 次的：`L3-model/component-probe.esml` 3 次、`D-skeleton/project.esml` 3 次、`L1-expr-equation/array-index.esml` 等 5 个 2 次，其余 1 次） |
| D | `tools/check-examples.py`（3）· `tools/aliases.tsv`（1）· `tools/negatives.tsv`（2）· `tools/check-spec-xsd-parity.py`（1）· `tools/spec-xsd-bydesign.tsv`（1）· `docs/validate_examples.py`（2）· `docs/validate_roots.py`（1）· `docs/coverage.md`（4）· `docs/design/{root-matrix-adjudication,tasks-shell-adjudication,xsd-spec-parity}.md`（各 1）· `Makefile`（1）· `README.md`（4） |

### 2.2 表 B · 提交级归桶（主桶 + 跨桶数）

```console
桶    名称                           提交数      跨桶提交
A    XSD 结构改动                     18       9
B    规范正文改动                     11       1
C    示例语料改动                     11       2
D    仅工具（工具/台账/说明）                15       3
内容提交合计：55 ；合流提交：4 ；总提交：59
```

**A 桶逐提交（18 笔，主桶）**：

```
13e2dd3  fix(xsd): canonical <esml> 根补声明 <tasks> 外层壳                        [跨桶: XS×1, 仅工×2]
c63f0c4  refactor(xsd): 拆掉三处「包着单元素的 xs:choice」死脚手架
ee8ae31  XSD 属性名收敛为 camelCase：kebab 拼写不再是合法语法
89039d7  调度步的同语义别名收敛为一个：`<reset>` 留，`<reassign>` 去              [跨桶: XS×1, 示例×1]
354aac6  类级继承的元素名收敛为 `<extendsFrom>`，去掉同语义的 `<extends>`            [跨桶: XS×1, 示例×1]
aaa10fc  属性名收敛到 canonical 拼法：porttype/interface/desc 三处 legacy 名退位     [跨桶: XS×1, 示例×1]
a392a77  删掉 legacy 元素 `<component>` 的 schema 声明，复合成员只收 `<instance>`      [跨桶: XS×1, 示例×1]
ca8efc7  docs(SPEC,xsd): 补 §6.8 `<tasks>` 外壳与 §6.9 元数据族条文                 [跨桶: XS×2, 规范×1]
fecce7a  fix(xsd): 入口 schema 的根清单对齐 canonical 的全局元素集
0d28be6  docs(xsd): 注释里的 kebab 拼写与「兼容别名」说法改成 canonical              （3 个 canonical 文件）
3a1934b  fix(xsd): `<partition>` 的显式属性改成 canonical 拼写 discipline / timeLayer
d45e955  refactor(xsd): 拆掉三处「包着单元素的 xs:choice」死脚手架
6409928  XSD 属性名收敛为 camelCase：kebab 拼写不再是合法语法
b5f4fbf  调度步的同语义别名收敛为一个：`<reset>` 留，`<reassign>` 去              [跨桶: XS×1, 示例×1]
daf9371  类级继承的元素名收敛为 `<extendsFrom>`，去掉同语义的 `<extends>`            [跨桶: XS×1, 示例×1]
fd4d92d  属性名收敛到 canonical 拼法：porttype/interface/desc 三处 legacy 名退位     [跨桶: XS×1, 示例×1]
c7fe19c  删掉 legacy 元素 `<component>` 的 schema 声明，复合成员只收 `<instance>`      [跨桶: XS×1, 示例×1]
ed1ce5d  fix(xsd): 入口 schema 的根清单对齐 canonical 的全局元素集
5ffa05c  docs(xsd): 注释里的 kebab 拼写与「兼容别名」说法改成 canonical              （3 个 canonical 文件）
4c5bf4d  fix(validate): 合并后收口——SPEC 改名遗留、负例登记、<tasks> 根对齐            [跨桶: XS×1, 规范×1, 示例×2, 仅工×2]
35f32e8  fix(xsd,spec): 入口层根清单收敛到 canonical 全局元素，并落成常驻机判           [跨桶: XS×1, 规范×1, 仅工×6]
```

**B 桶逐提交（11 笔）**：`21ddbee` `526d283` `cc102dc` `49f7882` `b5b3557` `e239003`
`17547ec`（+示例 1）`89262a5` `eecbb3d` `6e6b25e` `e7e5275` —— 全部只动 `SPEC.md`。

**C 桶逐提交（11 笔）**：`835fa02`（2 件）`fc4d05c`（改名 1）`f844361`（4 件）`6f5d321`（+1）
`cfb2b31`（**138 件**）`90e3770`（5 件）`35c2bfe`（1）`1a494bd`（+2，+规范 1）`c673d57`（1）
`ba79096`（+1）`4c5bf4d`（2 件，跨 4 桶）。

**D 桶逐提交（15 笔）**：`cf498a3` `13e2dd3` `b4b9599` `c438e6d` `6ff438d` `696aecd` `03b8b38`
`d63d39f` `10bf96f` `c573f97` `d65f384` `e93c9b2` `093558f` `1175d70` `35f32e8`。

**跨桶提交明细（15 笔）**：

```
89039d7  A  ← XS×1，示例×1        354aac6  A  ← XS×1，示例×1
aaa10fc  A  ← XS×1，示例×1        a392a77  A  ← XS×1，示例×1
ca8efc7  A  ← XS×2，规范×1        b5f4fbf  A  ← XS×1，示例×1
daf9371  A  ← XS×1，示例×1        fd4d92d  A  ← XS×1，示例×1
c7fe19c  A  ← XS×1，示例×1        17547ec  B  ← 规范×1，示例×1
1a494bd  C  ← 规范×1，示例×2       4c5bf4d  C  ← XS×1，规范×1，示例×2，仅工×2
13e2dd3  D  ← XS×1，仅工×2        35f32e8  D  ← XS×1，规范×1，仅工×6
1175d70  D  ← 规范×1，仅工×2
```

### 2.3 表 C · 重复 patch-id（同一改动在两条分支各提一次）

```console
patch-id a719ab64781a3d741b8e44f343de4d5f74146f8c   cf498a3 ≡ 10bf96f  feat(tools): 示例 × XSD 一致性门
patch-id ffe2a14a6a1f5f5ec454ab1b8bf28337a0fdc0cf   c63f0c4 ≡ d45e955  refactor(xsd): 拆掉三处死脚手架
patch-id 96eeba8f1621b5a35569f193c89ae003a7f5450a   fecce7a ≡ ed1ce5d  fix(xsd): 入口 schema 根清单对齐
patch-id d5ff949ba0327ad57fca4673a2dc2c57b54f9426   b4b9599 ≡ d65f384  feat(tools): 词法别名裁决表
patch-id 9b8458e30e038e6d5f41b5ce4650f07147bb5201   6f5d321 ≡ ba79096  feat(examples): 补一份 <project> 示例
patch-id 20e0cf9ec17328f55f710e20127a1dffa7db5b58   0d28be6 ≡ 5ffa05c  docs(xsd): 注释里的 kebab 拼写
patch-id 3d8587fa62b437fc599d004ea4a291feaef934f7   e239003 ≡ e7e5275  docs(spec): 版本头升到 v1.3.3
重复组数：7 ；涉及提交 14 （去重后净内容提交 = 41）
```

⇒ **提指针时真正「第一次进入引擎」的净改动是 41 笔**，不是 55 笔。

### 2.4 每桶的最高风险项

| 桶 | 最高风险项 | 为什么最高（附实测） |
|---|---|---|
| **A · XSD 结构改动** | `354aac6` / `daf9371`「类级继承的元素名收敛为 `<extendsFrom>`，去掉同语义的 `<extends>`」与 `89039d7` / `b5f4fbf`「`<reset>` 留，`<reassign>` 去」 | 这两笔是**唯一会直接把既有合法文档判成非法**的 XSD 改动：规范仓新 XSD 对 `<extends>` / `<reassign>` **拒收**，对旧 XSD **接受**（§8.3 探针）。引擎侧 `tests/fixtures/modelica_extends.esml`、`tests/fixtures/redeclare.esml` 现在用的就是 `<extends>` ⇒ 若同步 `schema/`，这两件立刻从绿变红（实测见 §4.1 第 1b 行：闸门第 [1] 层违规 11 → 14）。 |
| **B · 规范正文改动** | `35f32e8` + `1175d70`（SPEC §13 的 XSD 分层表被重写：补 `esml-canonical-project.xsd` 一行、根列写全 12 个根） | 引擎四方闸门第 [1] 层**就是按 SPEC §13 的根路由判定的**（`tools/four_way_gate.py` 的 `judge_xsd_file`：`schema = compute if r in ("compute-tasks","computeTasks") else basic`），而代码只实现了两条路由。SPEC 表新增 `<project>` 行 ⇒ 引擎闸门必须补第三条路由，否则 `<project>` 根**永远**判红（§8.2 探针）。 |
| **C · 示例语料改动** | `6f5d321` / `ba79096`「补一份 `<project>` 示例」 | 这是 59 笔里**唯一**让引擎当场变红的一笔：新增件 `D-skeleton/project.esml` 在引擎现有 `schema/` 下 XSD 判红，在引擎现有 parser 下 `esml check` 判红（F3 / F7 / I1），且**不在** G16 白名单里 ⇒ 闸门第 [1] 层与第 [2] 层同时多一件未登记的红。 |
| **D · 仅工具** | `4c5bf4d`（`tools/negatives.tsv` 11 → 12 行 + `xsd/esml-v1.xsd` 根清单改动） | 规范仓自建了「子模块内白名单」（`tools/negatives.tsv`，12 行 = schema 5 / semantic 7），引擎侧另有一份 G16 白名单（`scripts/gate-baselines/corpus-neg.tsv`，27 行 / 其中指向子模块 10 行）—— **两份登记表必须逐行对齐**。实测二者**共有 10 行、零矛盾**（§3.4），差集 2 行在规范仓侧且**实测 `esml check` 退出 0** ⇒ 不需要登记进 G16。 |

---

## 3. 旗标：会改引擎解析结果 / 闸门判据 / G16 白名单行数的提交

### 3.1 旗标 1 · 改 XSD 声明 ⇒ 引擎解析结果 / 闸门第 [1] 层判据会变（**24 笔**）

```
13e2dd3  fix(xsd): canonical <esml> 根补声明 <tasks> 外层壳                      esml-canonical-basic.xsd
c63f0c4  refactor(xsd): 拆掉三处「包着单元素的 xs:choice」死脚手架                esml-canonical-basic.xsd
ee8ae31  XSD 属性名收敛为 camelCase：kebab 拼写不再是合法语法                     esml-canonical-basic.xsd
89039d7  调度步的同语义别名收敛为一个：`<reset>` 留，`<reassign>` 去            esml-canonical-basic.xsd
354aac6  类级继承的元素名收敛为 `<extendsFrom>`，去掉同语义的 `<extends>`          esml-canonical-basic.xsd
aaa10fc  属性名收敛到 canonical 拼法：porttype/interface/desc 三处 legacy 名退位   esml-canonical-basic.xsd
a392a77  删掉 legacy 元素 `<component>` 的 schema 声明，复合成员只收 `<instance>`    esml-canonical-basic.xsd
ca8efc7  docs(SPEC,xsd): 补 §6.8 `<tasks>` 外壳与 §6.9 元数据族条文             esml-canonical-basic.xsd,esml-canonical-compute.xsd
fecce7a  fix(xsd): 入口 schema 的根清单对齐 canonical 的全局元素集                esml-v1.xsd
0d28be6  docs(xsd): 注释里的 kebab 拼写与「兼容别名」说法改成 canonical            basic,compute,project
3a1934b  fix(xsd): `<partition>` 的显式属性改成 canonical 拼写 discipline / timeLayer
14a9ffb  merge（合流）
d45e955 / 6409928 / b5f4fbf / daf9371 / fd4d92d / c7fe19c / ed1ce5d / 5ffa05c   （同上 7 笔的另一分支副本）
4c5bf4d / c6333f1 / 35f32e8 / 7802dd5
小计：24 个提交改动了 xsd/
```

**入口层根清单的具体增减**（`git show --unified=0` 抽 `xs:element name=`）：

```
fecce7a / ed1ce5d : -schedule  -solutionParameters  -tasks  -variables  -domain   +metadata  +project
4c5bf4d           : +tasks
35f32e8           : -portTypes -modelTypes -systems -schedule -solutionParameters -computeTasks
                    -tasks -variables -domain   +systems +portTypes +metadata +modelTypes +computeTasks +tasks +project
```

⇒ 提升后子模块里的入口 schema **声明 12 个根**
（`computeTasks esml metadata modelTypes orderedSet portTypes project system systems tasks units variableTypes`），
与 SPEC §13 表一致。

### 3.2 旗标 2 · 改语料（`*.esml`）⇒ G16 语料集合变（**22 笔**）

语料**净**增删改名（`git diff --name-status -M 58d2c0a..7802dd5 -- '*.esml'`）：

```
A    D-skeleton/project.esml
R095 L7-partition/group.esml → L0-type-unit/units-group.esml
D    L3-model/extends.esml
A    L4-port/signal-causal.esml
A    L5-instance/instance-condition-undecidable.esml
A    L5-instance/instance-condition.esml
A    L7-partition/subsystem-crosslink.esml
A    L9-method-schedule/call-method-body.esml
R076 L9-method-schedule/reassign.esml → L9-method-schedule/reset.esml
```

件数：**136 → 141**（新增 6 / 改名 2 / 删除 1）。
逐提交视角另有 `L6-connect/connect-legacy.esml → connect-canonical.esml` 这条中间态改名
（后续又被改回），它只出现在逐提交并集里，不出现在端点净差集里。

**22 笔改动语料的提交**：`835fa02` `89039d7` `354aac6` `aaa10fc` `a392a77` `fc4d05c`
`f844361` `6f5d321` `cfb2b31` `90e3770` `17547ec` `35c2bfe` `1a494bd` `c673d57` `14a9ffb`
`b5f4fbf` `daf9371` `fd4d92d` `c7fe19c` `ba79096` `4c5bf4d` `c6333f1`。

### 3.3 旗标 3 · 改闸门/对账判据（**29 笔**）

`tools/**`（`check-examples.py` `check-spec-xsd-parity.py` `negatives.tsv` `aliases.tsv` `spec-xsd-bydesign.tsv`）、
`docs/validate_examples.py`、`docs/validate_roots.py`、`Makefile`、`SPEC.md`。
逐笔见 §8.2 旗标 3 原始输出。

⇒ **指针提升会把「规范仓自己的三道机判」带进引擎视野**（`tools/check-examples.py`、
`tools/check-spec-xsd-parity.py` 三方对账、`docs/validate_roots.py` 根矩阵），
引擎若要在自己的 CI 里镜像这套判据，需要额外接线（不在本轮范围）。

### 3.4 旗标 4 · 改白名单 / 登记表行数（**3 类真改动**）

```console
【tools/negatives.tsv】（子模块内的「自述负例清单」）
  cf498a3 / 10bf96f   行数 — → 11   （新建）
  4c5bf4d             行数 11 → 12  （+1）

【tools/aliases.tsv】（词法别名裁决表）
  b4b9599 / d65f384   行数 — → 82   （新建）

【tools/spec-xsd-bydesign.tsv】（SPEC↔XSD 分歧的 by-design 登记表）
  093558f             行数 — → 0    （新建；本轮登记条目为 0）
```

**「子模块内白名单 10 行」的两边对账**：

```console
$ git -C ~/esml show origin/main:scripts/gate-baselines/corpus-neg.tsv | grep -c "^examples/syntax/"
10
```

引擎那 10 行 = `array-index-probe` `axis-reduce-probe` `derivativesymbol` `noderivative` `oob-probe`
`partial-derivative` `shape-mismatch-probe` `zeroderivative` `component-probe` `use-f12-mismatch`。

规范仓自述表（`tools/negatives.tsv` @7802dd5）**12 行 = schema 5 / semantic 7**，逐行对账：

```console
规范仓子模块行=12  引擎行=10
-- 共有（10 行）--
    examples/syntax/L1-expr-equation/array-index-probe.esml      [semantic / I25a]
    examples/syntax/L1-expr-equation/axis-reduce-probe.esml      [semantic / I25b]
    examples/syntax/L1-expr-equation/derivativesymbol.esml       [schema   / F1]
    examples/syntax/L1-expr-equation/noderivative.esml           [schema   / F1]
    examples/syntax/L1-expr-equation/oob-probe.esml              [semantic / I25d]
    examples/syntax/L1-expr-equation/partial-derivative.esml     [schema   / F1]
    examples/syntax/L1-expr-equation/shape-mismatch-probe.esml   [semantic / I25c]
    examples/syntax/L1-expr-equation/zeroderivative.esml         [schema   / F1]
    examples/syntax/L3-model/component-probe.esml                [schema   / F1]
    examples/syntax/X-use/use-f12-mismatch.esml                  [semantic / F12]
-- 仅规范仓（2 行）--
    examples/syntax/L0-type-unit/units-contradiction.esml
    examples/syntax/L5-instance/instance-condition-undecidable.esml
-- 仅引擎（0 行）--
```

⇒ **两边零矛盾**：共有 10 行、连「红在哪一层」都对得上（规范仓的 `level=schema` 5 件 ↔ 引擎的 F1 5 件；
`level=semantic` 5 件 ↔ 引擎的 I25a/I25b/I25c/I25d/F12）。
规范仓多的 2 行是 `level=semantic`（红在求解期），实测 `esml check` **退出 0** ⇒ 它们**不该**进 G16 白名单
（G16 收的是 `esml check` 失败件）。

⇒ **指针提升本身不要求 G16 白名单增减行**：10 个目标文件在 `7802dd5` 全部仍存在、判定层不漂移。

> **一处必须写进台账的跨仓漂移**：引擎 `origin/main` 的 `corpus-neg.tsv`（27 行）与引擎**工作区**
> （分支 `task/ledger-clean`，25 行）**不是同一份**——工作区多登记了
> `tests/fixtures/schedule_solver.esml` 与 `tests/fixtures/schedule_until.esml`（`F7 wrong-entry`），
> `origin/main` 上这两行**已被删掉**。这直接导致 `origin/main` 的闸门第 [2] 层在**基线**就判出
> 2 件「未登记拒绝」（§4.1）。**这是提指针之前就存在的红，不是指针带来的**，但提指针会让它
> 从 2 件变 3 件。

---

## 4. 对引擎的影响面表

**先说一个决定性的前提**：引擎四方闸门的「四权威」是**引擎仓自己**的文件
（`schema/`、`docs/language/esml-language-spec.md`、`library/`+`tests/fixtures/`+`test/`、`reference/`），
**子模块只以「语料」身份进入**（`examples/` 在闸门的 `SCOPE` 内）。所以：

| 影响面 | 指针提升（只动指针） | 指针提升 **+** 同步 `schema/` |
|---|---|---|
| XSD 校验 | **不变**（引擎 `schema/` 不在子模块里） | 变（见下） |
| 闸门第 [1] 层 | **变**（语料集合变） | 变 |
| 闸门第 [2] 层 | **变**（语料集合变） | 变 |
| G16 语料 | **变** | 变 |

引擎 `schema/` 与规范仓 `xsd/` **已经分叉**（五个文件里两个不同）：

```console
$ for f in esml-v1.xsd esml-canonical-common.xsd esml-canonical-basic.xsd esml-canonical-compute.xsd esml-canonical-project.xsd; do
    a=$(git -C ~/work-language show 58d2c0a:xsd/$f | sha256sum | cut -c1-16)
    b=$(git -C ~/work-language show 7802dd5:xsd/$f | sha256sum | cut -c1-16)
    c=$(sha256sum /home/ai4e18/esml/schema/$f | cut -c1-16)
    printf "%-30s 规范仓58d2c0a=%s 规范仓7802dd5=%s 引擎=%s\n" "$f" "$a" "$b" "$c"
  done
```

### 4.1 四行影响面表（全部为本轮实测）

| # | 影响面 | 现状（指针 `58d2c0a`） | 提升后（`7802dd5`） | 证据 |
|---|---|---|---|---|
| 1 | **XSD 校验**（引擎 `schema/`） | 引擎 `origin/main` 的 `schema/` × 闸门语料域（883 件）：**违规 10** | **不变**（`schema/` 不在子模块内，提升指针不碰它）⇒ 仍 **10** | §8.4 |
| 1b | XSD 校验（**若**把 `schema/` 同步到 `7802dd5`） | 规范仓新 XSD × 现状语料：**违规 15** | 规范仓新 XSD × 新语料：**违规 14** ⇒ 新增红 `tests/fixtures/modelica_extends.esml`、`tests/fixtures/redeclare.esml`、`tests/fixtures/schedule_until.esml`；转绿 `examples/syntax/L3-model/extends.esml`、`examples/syntax/L9-method-schedule/reassign.esml`（这两件随指针消失）、`examples/syntax/T-tasks/tasks.esml` | §8.4 |
| 2 | **四方闸门第 [1] 层**（XSD × 语料） | 引擎 `schema/` × 旧指针语料：**违规 10**，闸门 `fail += 1` | 引擎 `schema/` × 新指针语料：**违规 11** ⇒ **+1 = `D-skeleton/project.esml`**（「`<project>` is not an element of the schema」） | §8.4 |
| 3 | **四方闸门第 [2] 层**（语料 × 引擎） | `esml check` × 旧指针语料（136 件）：**exit≠0 6 件**，全部已登记；闸门全语料域：**拒收 25 件，其中未登记 2 件**（`tests/fixtures/schedule_solver.esml`、`tests/fixtures/schedule_until.esml`） | `esml check` × 新指针语料（141 件）：**exit≠0 7 件** ⇒ **+1 = `D-skeleton/project.esml`**（F3 / F7 / I1，**未登记**）；闸门全语料域：**拒收 26 件，其中未登记 3 件** | §8.4、§8.5 |
| 4 | **G16 语料** | 语料 136 件；白名单 27 行，其中**指向子模块的 10 行** | 语料 **141 件**（+6 / R 2 / D 1）；白名单**行数不变**（10 行全部仍存在、判定层不漂移）；但**多出 1 件未登记失败件** ⇒ **G16 判红** | §3.4、§8.5 |
| 5 | **子模块内白名单 10 行** | 10 行（`I25a I25b I25c I25d F1×5 F12`） | **仍是 10 行**：10 个目标文件在 `7802dd5` 全部存在，红在哪一层也不漂移。规范仓自述表多出的 2 行实测 `esml check` exit=0 ⇒ **不应进白名单** | §3.4、§8.5 |

> **第 [1] 层与第 [2] 层的判定口径不同，这不是笔误**：
> 第 [1] 层（`check_xsd`）**不查白名单**——`main()` 里只要 `xsd_bad` 非空就 `fail += 1`；
> 第 [2] 层（`check_engine`）**才查白名单**——`classify_engine_failure()` 把拒收分成
> `registered`（在 `corpus-neg.tsv` 里、或 stderr 含 `unsupported:`）与 `unexpected`，
> **只有 `unexpected` 才让这一角红**。
> ⇒ 所以「闸门第 [1] 层违规数」和「第 [2] 层未登记拒绝数」是**两把不同的尺子**，
> 报的时候不能混。

### 4.2 基线状态（提指针之前闸门就已经是红的）

```console
$ python3 tools/four_way_gate.py --ref <引擎 origin/main + 子模块@58d2c0a> --engine target/debug/esml
corpus: 883 .esml
[1] XSD(strict) × corpus : 合规 873 / 违规 10 / 不可解析 0  (corpus 883)
[2] engine(check) × corpus: 858/883
    UNEXPECTED tests/fixtures/schedule_solver.esml
    UNEXPECTED tests/fixtures/schedule_until.esml
verdict: DISAGREE
```

⇒ **提指针前 `origin/main` 的闸门就判 `DISAGREE`**（第 [1] 层 10 件违规 + 第 [2] 层 2 件未登记拒绝）。
提指针把它变成 **11 / 3**。**审计口径因此必须写清「+1」而不是「变红」**。

### 4.3 引擎侧「被指针变更直接打到」的引用（11 处）

指针提升会**删掉或改名** 3 个子模块文件，而引擎仓的文档在引用它们：

```console
$ grep -rn --exclude-dir=target --exclude-dir=.git -F "examples/syntax/L3-model/extends.esml" ~/esml
  docs/bench/ascend4-coverage.md:81
  docs/manual/syntax-coverage.md:34       （`<extendsFrom>` 的用例出处）
  docs/manual/syntax-coverage.md:266      （`<extends>` 元素的用例出处）
  docs/manual/user-manual.md:316          （`<extends>` 元素形 —— **当作文法条目写进了手册**）
  docs/manual/user-manual.md:319
  docs/design/syntax-coverage-matrix.md:54
$ grep -rn --exclude-dir=target --exclude-dir=.git -F "examples/syntax/L7-partition/group.esml" ~/esml
  docs/manual/syntax-coverage.md:215
  docs/manual/user-manual.md:281          （`<group>` 当作文法条目写进了手册）
  docs/design/syntax-coverage-matrix.md:60
  docs/design/xsd-backlog-triage.md:75
$ grep -rn --exclude-dir=target --exclude-dir=.git -F "examples/syntax/L9-method-schedule/reassign.esml" ~/esml
  docs/manual/user-manual.md:295           （`<reassign>` 当作文法条目写进了手册**）
```

⇒ 手册 `user-manual.md` 把 **`<extends>`、`<reassign>`、`<group>` 当作现行文法**写，
而规范仓在 `354aac6`/`89039d7`/`fc4d05c` 里**已经把前两个删掉**、第三个改名。
指针一提升，引擎手册与规范**正面冲突**（这不是「文档陈旧」，是「两套文法」）。

### 4.4 引擎 parser 没有 `<project>` 这个概念（代码级证据）

```console
$ git -C ~/esml grep -n '"project"' origin/main -- crates/
  （零命中）

$ git -C ~/esml grep -n "is not the canonical\|is not a recognised ESML root" origin/main -- crates/
  origin/main:crates/esml-engine/src/verify/src_layer.rs:57:  "root element `<{root}>` is not a recognised ESML root"
  origin/main:crates/esml-schema/src/src_layer.rs:66:            "root element `<{root}>` is not a recognised ESML root"
  origin/main:crates/esml-schema/src/validate.rs:466:            "root `<{root_tag}>` is not the canonical `<esml>` root"
```

⇒ `project.esml` 的 F3（`validate.rs:466`）、I1（`src_layer.rs:66`）与 F7（未知元素）**都是必然**，
不是偶发。

---

## 5. 提升指针的分步预案与每步回退点

> **原则**：①**先只读验证，再动指针**；②每步一个提交，回退点 = 上一提交；
> ③**指针提升必须是最后一步**，且单独成提交（回退只需把指针拨回去）。

### 步骤 0 · 只读验证（**不改 ENGINE 就能先做**，本轮已完成）

| 验证 | 命令（本轮已跑，可复跑） | 本轮结果 |
|---|---|---|
| 0.1 两个指针的语料快照 | `git archive 58d2c0a \| tar -x -C /tmp/sub-58d2c0a`；`git archive 7802dd5 \| tar -x -C /tmp/sub-7802dd5` | 136 件 / 141 件 |
| 0.2 引擎树快照 | `git -C ~/esml archive origin/main \| tar -x -C /tmp/eng-<rev>`，再把子模块快照覆盖进 `examples/syntax/` | 883 件 / 888 件（闸门语料域） |
| 0.3 闸门第 [1] 层预演 | `python3 tools/four_way_gate.py --ref /tmp/eng-<rev> --engine target/debug/esml` | 违规 10 → 11（+`project.esml`） |
| 0.4 闸门第 [2] 层预演 | 同上命令（`check_engine` 段） | 拒收 25 → 26；未登记 2 → 3（+`project.esml`） |
| 0.5 「若同步 `schema/`」预演 | 用 `xmlschema` 按闸门路由（`compute-tasks`/`computeTasks` → compute，其余 → basic）分别校验两份树 | 15 → 14 |
| 0.6 G16 白名单对账 | `grep '^examples/syntax/' scripts/gate-baselines/corpus-neg.tsv` × `tools/negatives.tsv` | 10 行 vs 12 行，零矛盾，差 2 行（都是 semantic，不需要进白名单） |

**回退点**：无需回退（本步零改动，全部在 `/tmp` 下）。

### 步骤 1 · 引擎侧补 `<project>` 支持（**属 B7，见 §6**）

- 动：parser 根判定（`crates/esml-schema/src/validate.rs` 的 F3、`crates/esml-schema/src/src_layer.rs` 的 I1）、
  `unknown::KNOWN_SUB_TAGS` 的 F7（`project` / `systemRef`）、
  四方闸门第 [1] 层的根路由（加 `<project>` → `esml-canonical-project.xsd`，并把该 schema 纳入加载）。
- 判据：`esml check examples/syntax/D-skeleton/project.esml` ⇒ exit=0；
  `four_way_gate.py` 对 `examples/syntax/D-skeleton/project.esml` 不报违规；`--self-test` 仍全过。
- **回退点**：`git revert <本步提交>`（纯引擎仓，不影响指针）。

### 步骤 2 · 引擎侧同步 `schema/`（**必须与步骤 1 分开，可整体放弃**）

- 动：`schema/esml-v1.xsd` + `schema/esml-canonical-*.xsd` 覆盖为规范仓 `7802dd5` 的版本。
- 判据：`bash scripts/gate.sh`（G0–G17）全绿；闸门第 [1] 层违规由 11 → 14 且**逐件有账**
  （新增的 `tests/fixtures/modelica_extends.esml`、`tests/fixtures/redeclare.esml`、
  `tests/fixtures/schedule_until.esml` 必须处理：改件 or 登记，**不许**默默变红）。
- **回退点**：`git revert <本步提交>` ⇒ `schema/` 回到引擎原版；此步不做则第 1 行影响面保持「不变」。

### 步骤 3 · 白名单与文档引用收口

- 动：`scripts/gate-baselines/corpus-neg.tsv`（按步骤 1/2 的实测结果增删行，**只许缩小不许放大**——
  `scripts/check-corpus.sh` 自带棘轮）；把 `user-manual.md` / `syntax-coverage.md` /
  `syntax-coverage-matrix.md` / `ascend4-coverage.md` / `xsd-backlog-triage.md` 里指向
  `extends.esml` / `group.esml` / `reassign.esml` 的 **11 处**引用改到新路径，并把
  `<extends>` / `<reassign>` 两条**文法条目**按规范仓的新裁决撤下或改写。
  另需**显式处置** `origin/main` 上那 2 件未登记拒绝（`schedule_solver` / `schedule_until`）——
  它们与指针无关，但会让闸门一直红着。
- 判据：`grep -rn "syntax/L3-model/extends.esml\|syntax/L7-partition/group.esml\|syntax/L9-method-schedule/reassign.esml" .`
  ⇒ 0 命中；`bash scripts/gate.sh` 全绿。
- **回退点**：`git revert <本步提交>`。

### 步骤 4 · **指针提升本身**（单独一个提交）

```sh
git update-index --cacheinfo 160000,7802dd5116acfcdd3d21c67ed2a1e2e26ff9954b,examples/syntax
git commit -m "chore(syntax): 示例仓指针 → 7802dd5（根矩阵门 / XSD 收敛 / <project> 示例）"
```

- 判据：`git submodule status examples/syntax` ⇒ `7802dd5…`；`bash scripts/gate.sh` 全绿；
  `python3 tools/four_way_gate.py` 判绿；`python3 tools/four_way_gate.py --self-test` 全过。
- **回退点**：`git update-index --cacheinfo 160000,58d2c0af3b3ee8502c4e9455ae63b0284c75eb7e,examples/syntax`
  后再提交，或直接 `git revert <本步提交>`。

### 步骤 5 · 全量复跑与留档

- 动：把步骤 1–4 的实测数字写进引擎台账（`docs/design/` 下的裁决记录），并在本仓
  `docs/coverage.md` 记一笔「指针提升已合入」。
- 判据：全门输出贴进台账。
- **回退点**：`git revert <本步提交>`（纯文档）。

> **推荐顺序的理由**：步骤 1–3 全是**引擎侧**改动，彼此可独立回退；步骤 4 是唯一不可逆面最大的动作
> （一旦指针指向 `7802dd5`，引擎的 G16 / G14 / 文档引用都要跟着新语料重算），
> 因此**只有在步骤 1 的实测判定为「+1 件未登记红已被消掉」之后**才做。

---

## 6. 必须等 B7 合完才能做的（**明确清单**）

> **口径说明**：本机两个仓都查不到 “B7” 这个字样
> （`git grep -n "B7" 7802dd5` 只命中一个无关的十六进制串；
> 引擎仓里 `B7` 只出现在 `vendor-restore-design.md` / `boundary-layer-contract.md` 的**批次编号**里，
> 与本指针提升无关）。
> 因此下面按「**与本次规范改动配对的引擎侧批次**」来理解 B7：即**引擎侧必须先合的那一批**。
> 每条都给出**可机器核对的判据**，B7 合完后按判据逐条销项即可。

| # | 必须等 B7 的项 | 为什么不能先做 | 销项判据（机器可查） |
|---|---|---|---|
| **B7-1** | 引擎 parser 支持 `<project>` 根（F3 / I1 根判定 + F7 的 `KNOWN_SUB_TAGS` 加 `project`/`systemRef`） | 指针一提升，`examples/syntax/D-skeleton/project.esml` 就进闸门与 G16 的扫描目录，**必然**判红（实测 F3/F7/I1）。引擎 HEAD 的代码里 `git grep -n '"project"' origin/main -- crates/` **零命中** ⇒ 引擎至今没有 `<project>` 这个概念 | `esml check examples/syntax/D-skeleton/project.esml` ⇒ exit=0 |
| **B7-2** | 四方闸门第 [1] 层的**根路由**补 `<project>` → `esml-canonical-project.xsd`（并加载该 schema） | 闸门的路由是**代码里的两条**（`compute-tasks`/`computeTasks` → compute；其余 → basic），而 SPEC §13 现在有**三行** schema（含 project）。不补 ⇒ `<project>` 根永远判红，即使 XSD 本身是对的 | `four_way_gate.py` 对 `examples/syntax/D-skeleton/project.esml` 不报违规；`--self-test` 全过 |
| **B7-3** | 引擎 `schema/` 与规范仓的**同步裁决**（做 / 不做都要显式决定并留档） | 引擎 `schema/` 与规范仓 `xsd/` **已经分叉**（§4）。不同步 ⇒ XSD 校验面「不变」但规范与实现继续漂；同步 ⇒ 闸门第 [1] 层违规 11 → 14，且 `<extends>` / `<reassign>` 在引擎侧的两件 fixture 变红。**这是 owner 决策，不是机械动作** | 台账里有一条明确裁决；且 `bash scripts/gate.sh` 在该裁决下全绿 |
| **B7-4** | G16 白名单 `scripts/gate-baselines/corpus-neg.tsv` 的**重对账** | 白名单棘轮「只许缩小」；子模块侧的登记表是 12 行（含 2 行 semantic），两边虽已零矛盾，但口径必须先对齐再动指针；另外 `origin/main` 与工作区的白名单**已经不一致**（2 行 `schedule_*`） | `bash scripts/check-corpus.sh` 退出 0，且白名单无 `stale` / `drift` / 悬空行 |
| **B7-5** | G14（`tools/check_three_way.py`）的**语法覆盖矩阵**与新语料对齐 | 该门双向对账：`examples/syntax/**` 用的 canonical 名必须在矩阵里有点；矩阵标「已覆盖」必须在 `examples/syntax` 有可跑例。指针提升会 **+6 件 / −1 件 / 改名 2 件**，且 `<extends>` `<reassign>` `<group>` 三个矩阵点会失去用例 | `python3 tools/check_three_way.py` 退出 0 |
| **B7-6** | 引擎文档里 **11 处**指向被删/改名示例的引用，以及 `<extends>` / `<reassign>` 两条**文法条目**的处置 | `docs/manual/user-manual.md` 把 `<extends>`（第 316 行）、`<reassign>`（第 295 行）、`<group>`（第 281 行）当现行文法写；规范仓已删前两个写法、改了第三个的路径。指针一提升，手册与规范正面冲突 | `grep -rn "syntax/L3-model/extends.esml\|syntax/L7-partition/group.esml\|syntax/L9-method-schedule/reassign.esml" .` ⇒ 0 命中；手册里不再出现 `<extends>` / `<reassign>` 条目 |
| **B7-7** | 规范仓本区间留下的**台账漂移**另开一轮修，不许混进指针提升 | `SPEC.md` 附录 C 自述「全仓 **136** 件」「负例 **11** 件（schema 5 / semantic 6）」，而 `7802dd5` 的实际是 **141** 件、**12** 件（schema 5 / semantic 7）⇒ 附录 C 落后 5 件 / 1 件。这是**规范仓自身**的账，不是引擎的账 | `SPEC.md` 附录 C 的两个数字与 `git ls-tree` / `tools/negatives.tsv` 对齐（下一轮单独提交） |

**⇒ 结论：指针提升（步骤 4）必须等 B7-1 / B7-2 合完**（否则闸门第 [1] 层与 G16 各多一件未登记红）；
**B7-3 ~ B7-6 必须与指针提升同批或先批合完**（否则会留下「引擎自相矛盾」或「手册与规范打架」）；
**B7-7 与指针提升无关**，可并行，但**不得**混进同一次提交。

---

## 7. 本审计的边界（自证）

| 边界 | 说明 |
|---|---|
| 引擎仓 | **只读**：`git log` / `git show` / `git ls-tree` / `git archive` / `grep` / 运行现成二进制与现成闸门脚本。**未** fetch / checkout / commit / 改文件；`examples/syntax` 未动。 |
| 本仓 | 只新增 `docs/audit/` 下的文档；`git status` 见交付回报。 |
| 网络 | 只 `git fetch origin`（规范仓）与读远端指针，**未 push**。 |
| 依赖 | XSD 判定用 `/tmp/esml-venv` 里的 `xmlschema 4.3.2`（系统 pip 被 PEP 668 挡住，未改系统包）。 |
| 未做的 | 未跑引擎 `cargo build/test`（构建会写引擎仓 `target/`）；闸门第 [2] 层的结论因此以「同一二进制下前后对照」的方式给出（见 §8.5 的口径声明）。 |

---

## 8. 本轮原始行（证据）

### 8.1 区间提交数与桶统计

```console
$ git -C ~/work-language log --oneline 58d2c0a..7802dd5 | wc -l
59

$ git -C ~/work-language ls-tree -r --name-only 58d2c0a | grep -c '\.esml$'
136
$ git -C ~/work-language ls-tree -r --name-only 7802dd5 | grep -c '\.esml$'
141
```

桶统计（表 A / 表 B / 表 C 的原始输出见 §2.1、§2.2、§2.3；表 A 合计行原文）：

```console
桶    名称                           文件数        改动次数       插入           删除           触及提交数
A    XSD 结构改动                     4          34         487          300          24
B    规范正文改动                     1          20         994          256          20
C    示例语料改动                     146        314         786          121          22
D    仅工具（工具/台账/说明）                13          53         7884         28           20
合计：去重文件 164 ；插入 10151 ；删除 705
```

### 8.2 旗标输出（原始）

**旗标 1 · 改 `xsd/` 的 24 笔**：

```console
  13e2dd3  fix(xsd): canonical <esml> 根补声明 <tasks> 外层壳                      esml-canonical-basic.xsd
  c63f0c4  refactor(xsd): 拆掉三处「包着单元素的 xs:choice」死脚手架                esml-canonical-basic.xsd
  ee8ae31  XSD 属性名收敛为 camelCase：kebab 拼写不再是合法语法                     esml-canonical-basic.xsd
  89039d7  调度步的同语义别名收敛为一个：`<reset>` 留，`<reassign>` 去            esml-canonical-basic.xsd
  354aac6  类级继承的元素名收敛为 `<extendsFrom>`，去掉同语义的 `<extends>`          esml-canonical-basic.xsd
  aaa10fc  属性名收敛到 canonical 拼法：porttype/interface/desc 三处 legacy 名退位   esml-canonical-basic.xsd
  a392a77  删掉 legacy 元素 `<component>` 的 schema 声明，复合成员只收 `<instance>`    esml-canonical-basic.xsd
  ca8efc7  docs(SPEC,xsd): 补 §6.8 `<tasks>` 外壳与 §6.9 元数据族条文             esml-canonical-basic.xsd,esml-canonical-compute.xsd
  fecce7a  fix(xsd): 入口 schema 的根清单对齐 canonical 的全局元素集                esml-v1.xsd
  0d28be6  docs(xsd): 注释里的 kebab 拼写与「兼容别名」说法改成 canonical            basic,compute,project
  3a1934b  fix(xsd): `<partition>` 的显式属性改成 canonical 拼写 discipline / timeLayer
  14a9ffb  merge: XSD/示例一致性收敛 + 别名裁决表（ai4e17，16 提交）                 basic,compute,project,esml-v1
  d45e955 / 6409928 / b5f4fbf / daf9371 / fd4d92d / c7fe19c / ed1ce5d / 5ffa05c
  4c5bf4d / c6333f1 / 35f32e8 / 7802dd5
  小计：24 个提交改动了 xsd/
```

**旗标 3 · 改判据面的 29 笔**：

```console
  cf498a3  feat(tools): 示例 × XSD 一致性门（含 2 好 2 坏自证与负例清单）             tools/check-examples.py,tools/negatives.tsv
  13e2dd3  fix(xsd): canonical <esml> 根补声明 <tasks> 外层壳                        tools/check-examples.py
  21ddbee  docs(SPEC): 修 §6.8 canonical 示例的三处 schema 违规，并补 §6.9 计算任务表条文  SPEC.md
  ca8efc7  docs(SPEC,xsd): 补 §6.8 `<tasks>` 外壳与 §6.9 元数据族条文，修三处正文/schema 错位  SPEC.md
  526d283  docs(SPEC): §6.7 初始化过程改回 canonical 拼写与载荷（正文落后于示例与实现）      SPEC.md
  b4b9599  feat(tools): 词法别名裁决表落成数据，机验「同一语义只有一种写法」                   tools/aliases.tsv,tools/check-examples.py
  cc102dc  docs(spec): §2 收紧集与 XSD 对齐——去掉「兼容别名」与「XSD 仍声明」的说法         SPEC.md
  49f7882  docs(spec): 正文其余段落逐条改成 canonical 拼法，与 XSD 对齐                    SPEC.md
  b5b3557  docs(SPEC): 为 25 份无 SPEC 依据的示例补规范条文                               SPEC.md
  e239003  docs(spec): 版本头升到 v1.3.3，附录 C 写清本轮变更                              SPEC.md
  c438e6d  docs(validate_examples): 落盘示例 ⇄ 规范 对账机验（coverage.md 的数字来源）      docs/validate_examples.py
  6ff438d  docs(validate_examples): 聚合器按头部指名的**全部**条文统计                      docs/validate_examples.py
  17547ec  docs(examples): 补附录 F2 的信号口跨 PortType 因果连接示例                        SPEC.md
  1a494bd  docs(examples): 补 §6.5 条件组件的正例与「条件不可静态判定」负例                   SPEC.md
  89262a5  docs(SPEC): §6.5 补条件的操作数作用域，并把「参数形态」标为待定                    SPEC.md
  14a9ffb  merge（合流）                                                                    SPEC.md,tools/aliases.tsv,tools/check-examples.py,tools/negatives.tsv
  10bf96f  feat(tools): 示例 × XSD 一致性门（含 2 好 2 坏自证与负例清单）                     tools/check-examples.py,tools/negatives.tsv
  c573f97  fix(xsd): canonical <esml> 根补声明 <tasks> 外层壳                              tools/check-examples.py
  d65f384  feat(tools): 词法别名裁决表落成数据，机验「同一语义只有一种写法」                   tools/aliases.tsv,tools/check-examples.py
  eecbb3d  docs(spec): §2 收紧集与 XSD 对齐——去掉「兼容别名」与「XSD 仍声明」的说法          SPEC.md
  6e6b25e  docs(spec): 正文其余段落逐条改成 canonical 拼法，与 XSD 对齐                     SPEC.md
  e7e5275  docs(spec): 版本头升到 v1.3.3，附录 C 写清本轮变更                               SPEC.md
  4c5bf4d  fix(validate): 合并后收口——SPEC 改名遗留、负例登记、<tasks> 根对齐                  SPEC.md,tools/negatives.tsv
  c6333f1  merge（合流）                                                                     SPEC.md,docs/validate_examples.py,tools/negatives.tsv
  35f32e8  fix(xsd,spec): 入口层根清单收敛到 canonical 全局元素，并落成常驻机判                 Makefile,SPEC.md,docs/validate_roots.py
  093558f  feat(tools): SPEC ↔ XSD 文档根对账门——入口/canonical/规范三方机判                   tools/check-spec-xsd-parity.py,tools/spec-xsd-bydesign.tsv
  1175d70  docs(spec): 文档根清单入正文（12 个），附录 C 假根条目收口                          SPEC.md
  4f3010c  merge（合流）                                                                     SPEC.md,tools/check-spec-xsd-parity.py,tools/spec-xsd-bydesign.tsv
  7802dd5  merge（合流）                                                                     Makefile,SPEC.md,docs/validate_roots.py
  小计：29 个提交改动了判据面
```

**旗标 5 · 入口层根清单增减**：

```console
  fecce7a / ed1ce5d  fix(xsd): 入口 schema 的根清单对齐 canonical 的全局元素集
      - <xs:element name="schedule">
      - <xs:element name="solutionParameters">
      - <xs:element name="tasks">
      - <xs:element name="variables">
      - <xs:element name="domain">
      + <xs:element name="metadata">
      + <xs:element name="project">
  4c5bf4d            fix(validate): 合并后收口
      + <xs:element name="tasks">
  35f32e8            fix(xsd,spec): 入口层根清单收敛到 canonical 全局元素
      - <xs:element name="portTypes">  - <xs:element name="modelTypes">  - <xs:element name="systems">
      - <xs:element name="schedule">   - <xs:element name="solutionParameters">
      - <xs:element name="computeTasks"> - <xs:element name="tasks">
      - <xs:element name="variables">  - <xs:element name="domain">
      + <xs:element name="systems">    + <xs:element name="portTypes"> + <xs:element name="metadata">
      + <xs:element name="modelTypes"> + <xs:element name="computeTasks"> + <xs:element name="tasks">
      + <xs:element name="project">
```

### 8.3 三个语法点在新旧 XSD 下的接受/拒收

```console
== XSD 源：/tmp/sub-58d2c0a/xsd ==      == XSD 源：/tmp/sub-7802dd5/xsd ==     == XSD 源：引擎 schema/ ==
  connect      接受                          connect      接受                        connect      接受
  extends      接受                          extends      拒收  '{…}extends'           extends      接受
  reassign     接受                          reassign     拒收  '{…}reassign'          reassign     接受
  orderedsets  拒收                          orderedsets  拒收                        orderedsets  拒收
  tasks        拒收                          tasks        接受                        tasks        拒收
```

（第三列取的是引擎 `origin/main` 的 `schema/`；若取引擎**工作区**的 `schema/`，
`tasks` 一列同为「拒收」，另两列一致。）

### 8.4 闸门第 [1] 层：XSD 来源 × 语料状态（6 组实测）

```console
schema=引擎 origin/main schema/  corpus=子模块@58d2c0a   corpus件=883   违规=10
schema=引擎 origin/main schema/  corpus=子模块@7802dd5   corpus件=888   违规=11   （+D-skeleton/project.esml）
schema=规范仓 58d2c0a xsd/       corpus=子模块@58d2c0a   corpus件=883   违规=11   （+T-tasks/tasks.esml）
schema=规范仓 58d2c0a xsd/       corpus=子模块@7802dd5   corpus件=888   违规=12   （+project.esml）
schema=规范仓 7802dd5 xsd/       corpus=子模块@58d2c0a   corpus件=883   违规=15
                                     （+L3-model/extends.esml +L9-method-schedule/reassign.esml
                                       +tests/fixtures/modelica_extends.esml +tests/fixtures/redeclare.esml
                                       +tests/fixtures/schedule_until.esml）
schema=规范仓 7802dd5 xsd/       corpus=子模块@7802dd5   corpus件=888   违规=14
                                     （+project.esml；extends.esml / reassign.esml 随指针消失而转绿）
```

违规明细（引擎 `origin/main` 的 `schema/`，子模块@7802dd5，11 件）：

```console
    examples/syntax/D-skeleton/project.esml  ::  '{…}project' is not an element of the schema
    examples/syntax/L1-expr-equation/derivativesymbol.esml  ::  Unexpected child with tag '{…}derivative' at position 4.
    examples/syntax/L1-expr-equation/noderivative.esml  ::  Unexpected child with tag '{…}derivative' at position 4.
    examples/syntax/L1-expr-equation/partial-derivative.esml  ::  Unexpected child with tag '{…}derivative' at position 4.
    examples/syntax/L1-expr-equation/zeroderivative.esml  ::  Unexpected child with tag '{…}derivative' at position 4.
    examples/syntax/L3-model/component-probe.esml  ::  Unexpected child with tag '{…}component' at position 1.
    tests/fixtures/_eng7_t1/range_check.esml  ::  Unexpected child with tag '{…}algorithm' at position 1.
    tests/fixtures/b2-events-memory/phase1-negative/assign-value-missing.esml  ::  missing required attribute 'value'
    tests/fixtures/b2-events-memory/phase1-negative/when-condition-missing.esml  ::  missing required attribute 'condition'
    tests/fixtures/b2-events-memory/phase1-negative/when-nested.esml  ::  Unexpected child with tag '{…}when' at position 1.
    tests/fixtures/b2-events-memory/phase1-negative/xsd-when-missing-condition.esml  ::  missing required attribute 'condition'
```

### 8.5 闸门实跑（第 [1]/[2]/[3] 层全量）与 `esml check` 差分

```console
$ python3 tools/four_way_gate.py --ref /home/ai4e18/esml --engine .../target/debug/esml
corpus: 882 .esml under /home/ai4e18/esml
[1] XSD(strict) × corpus : 合规 868 / 违规 14 / 不可解析 0  (corpus 882)
[2] engine(check) × corpus: 857/882
[3] spec × conformance    : 148 Rust cases; legacy `test/conformance/NN` chain ABSENT
verdict: DISAGREE
   ↑ 这是引擎**工作区**（分支 task/ledger-clean，内嵌语料 135 件），白名单 25 行

$ python3 tools/four_way_gate.py --ref /tmp/eng-58d2c0a --engine .../target/debug/esml
corpus: 883 .esml under /tmp/eng-58d2c0a
[1] XSD(strict) × corpus : 合规 873 / 违规 10 / 不可解析 0  (corpus 883)
                    by element: {'<derivative>': 4, '<component>': 1, '<algorithm>': 1, '<assign>': 1, '<when>': 3}
                    by dir    : {'examples/syntax/L1-expr-equation': 4, 'examples/syntax/L3-model': 1,
                                 'tests/fixtures/_eng7_t1': 1, 'tests/fixtures/b2-events-memory/phase1-negative': 4}
[2] engine(check) × corpus: 858/883
    UNEXPECTED /tmp/eng-58d2c0a/tests/fixtures/schedule_solver.esml
    UNEXPECTED /tmp/eng-58d2c0a/tests/fixtures/schedule_until.esml
verdict: DISAGREE
   ↑ 引擎 origin/main + 子模块@58d2c0a（**提指针前的真实基线**），白名单 27 行

$ python3 tools/four_way_gate.py --ref /tmp/eng-7802dd5 --engine .../target/debug/esml
corpus: 888 .esml under /tmp/eng-7802dd5
[1] XSD(strict) × corpus : 合规 877 / 违规 11 / 不可解析 0  (corpus 888)
[2] engine(check) × corpus: 862/888
    UNEXPECTED /tmp/eng-7802dd5/examples/syntax/D-skeleton/project.esml
    UNEXPECTED /tmp/eng-7802dd5/tests/fixtures/schedule_solver.esml
    UNEXPECTED /tmp/eng-7802dd5/tests/fixtures/schedule_until.esml
verdict: DISAGREE
   ↑ 引擎 origin/main + 子模块@7802dd5（**提指针后**）
```

`project.esml` 在引擎 parser 下的完整报错：

```console
$ target/debug/esml check /tmp/sub-7802dd5/D-skeleton/project.esml -L ~/esml/library
    error: F3[]: root `<project>` is not the canonical `<esml>` root … — wrap the document in `<esml xmlns="…" name="…">…</esml>`
    error: F7[]: unknown element `<project>` … — use a canonical element name (see `unknown::KNOWN_SUB_TAGS`)
    error: F7[]: unknown element `<systemRef>` … — use a canonical element name (see `unknown::KNOWN_SUB_TAGS`)
    error: F7[]: unknown attribute `system` on `<systemRef>` … — remove or rename; canonical attributes are in `unknown::KNOWN_ATTRS`
    error: I1[]: root element `<project>` is not a recognised ESML root … — wrap the document in `<esml>` (canonical) or a known section root
    summary: errors=5 warnings=0 models=0 systems=0 types=0 portTypes=0 units=0 functions=0 five_level=ok
```

`esml check` 差分（子模块语料，两端快照）：

```console
=== sub-58d2c0a：esml check 汇总 ===
  总件 136 · exit=0 130 · exit≠0 6
    非零：X-use/use-f12-mismatch.esml                 rc=1  codes=F12,F17
    非零：L1-expr-equation/axis-reduce-probe.esml     rc=1  codes=I25b
    非零：L1-expr-equation/array-index-probe.esml     rc=1  codes=I25a
    非零：L1-expr-equation/shape-mismatch-probe.esml  rc=1  codes=I25c
    非零：L1-expr-equation/oob-probe.esml            rc=1  codes=I25d
    非零：L3-model/component-probe.esml               rc=1  codes=F1
=== sub-7802dd5：esml check 汇总 ===
  总件 141 · exit=0 134 · exit≠0 7
    非零：X-use/use-f12-mismatch.esml                 rc=1  codes=F12,F17
    非零：D-skeleton/project.esml                     rc=1  codes=F3,F7,I1      ← 新增，未登记
    非零：L1-expr-equation/axis-reduce-probe.esml     rc=1  codes=I25b
    非零：L1-expr-equation/array-index-probe.esml     rc=1  codes=I25a
    非零：L1-expr-equation/shape-mismatch-probe.esml  rc=1  codes=I25c
    非零：L1-expr-equation/oob-probe.esml            rc=1  codes=I25d
    非零：L3-model/component-probe.esml               rc=1  codes=F1
```

> **口径声明（重要）**：以上用的是本机现存的二进制 `~/esml/target/debug/esml`
> （`ESML v1.2.0`，构建于 2026-10-19 14:41）。它**早于**引擎 `origin/main` 的
> `4846cdae`（2026-10-20「`<body>` 解析失败响亮化 + `<derivative>` 必须挂 extern」），
> 而那笔提交正是让 4 件导数负例重新报 F1 的改动。
> **但这 4 件在提升指针后仍然会报 F1**：实测引擎 `4846cdae` 版与规范仓 `58d2c0a` / `7802dd5` 版
> 的 `derivativesymbol.esml` **只有文件头注释不同、XML 主体完全一致**，
> 而引擎 `origin/main` 的 `corpus-neg.tsv` 已把这 4 件登记为 `F1 negative`
> ⇒ **那 4 行白名单在提升后依然有效，不是 stale 行**。
> ⇒ 因此本表在**引擎当前 HEAD** 上应当是 **10 件非零（全部已登记）→ 11 件（多出 `project.esml`）**；
> 表中实测的 6 → 7 是**同一二进制下**的差分，差分方向与结论不受影响。
> `scripts/check-corpus.sh` 自带二进制新鲜度棘轮（`ensure_bin`），本审计未绕过它。

### 8.6 白名单对账（原始行）

```console
$ git -C ~/esml show origin/main:scripts/gate-baselines/corpus-neg.tsv | grep '^examples/syntax/' | nl
     1  examples/syntax/L1-expr-equation/array-index-probe.esml       I25a   negative
     2  examples/syntax/L1-expr-equation/axis-reduce-probe.esml       I25b   negative
     3  examples/syntax/L1-expr-equation/derivativesymbol.esml        F1     negative
     4  examples/syntax/L1-expr-equation/noderivative.esml            F1     negative
     5  examples/syntax/L1-expr-equation/oob-probe.esml               I25d   negative
     6  examples/syntax/L1-expr-equation/partial-derivative.esml      F1     negative
     7  examples/syntax/L1-expr-equation/shape-mismatch-probe.esml    I25c   negative
     8  examples/syntax/L1-expr-equation/zeroderivative.esml          F1     negative
     9  examples/syntax/L3-model/component-probe.esml                 F1     negative
    10  examples/syntax/X-use/use-f12-mismatch.esml                   F12    negative
```

10 个目标在 `7802dd5` 快照中的存在性：**10/10 全部存在**（逐个 `test -f` 核对）。

规范仓侧登记表（`tools/negatives.tsv` @7802dd5，12 行）：

```console
# tools/negatives.tsv · 自述负例清单（check-examples.py 读它）
# 列：path <TAB> level <TAB> reason
# level=schema    该件必须被 XSD **拒收**；XSD 收下它 = 判据漏了（红）
# level=semantic 该件必须**通过** XSD（它红在语义/求解层，不在 schema 层）
  L0-type-unit/units-contradiction.esml          semantic  单位声明与 type unit= 矛盾（§11 量纲冲突）
  L1-expr-equation/array-index-probe.esml        semantic  数组下标越界，求解期报 I25a
  L1-expr-equation/axis-reduce-probe.esml        semantic  沿 axis 归约维度不匹配，求解期报 I25b
  L1-expr-equation/oob-probe.esml                semantic  序集下标越界，求解期报 I25d
  L1-expr-equation/shape-mismatch-probe.esml     semantic  形状不匹配，求解期报 I25c
  X-use/use-f12-mismatch.esml                    semantic  F12 端口类别与连接方向不匹配
  L1-expr-equation/derivativesymbol.esml         schema    <derivativeSymbol> 依附的 <body>+<derivative> 违反 xs:choice
  L1-expr-equation/noderivative.esml             schema    同上（<noDerivative>）
  L1-expr-equation/partial-derivative.esml       schema    同上（<partial>）
  L1-expr-equation/zeroderivative.esml           schema    同上（<zeroDerivative>）
  L3-model/component-probe.esml                  schema    legacy <component> 元素形态，canonical 只收 <instance>
  L5-instance/instance-condition-undecidable.esml semantic  instance condition 引用模型参数，构建期不可静态判定
level 分布：schema = 5 ；semantic = 7
```

⇒ 差集 2 行（`units-contradiction` / `instance-condition-undecidable`）在 `7802dd5` 快照里
`esml check` **退出 0** ⇒ 不需要进 G16 白名单。

### 8.7 规范仓两端的登记表行数与 SPEC 附录 C 漂移

```console
  58d2c0a   语料=136  negatives.tsv 行=0    aliases.tsv 行=0
  c6333f1   语料=141  negatives.tsv 行=12   aliases.tsv 行=82
  093558f   语料=141  negatives.tsv 行=12   aliases.tsv 行=82
  1175d70   语料=141  negatives.tsv 行=12   aliases.tsv 行=82
  7802dd5   语料=141  negatives.tsv 行=12   aliases.tsv 行=82

7802dd5 的 SPEC 附录 C 自述数：
  1137:  2. **示例**：全仓 136 件逐件过**两道**校验（入口 `esml-v1.xsd` + 逐元素的
  1138:     `esml-canonical-basic.xsd`）；刻意保留的负例 11 件（schema 5 / semantic 6）
```

⇒ 附录 C 落后 **5 件**（136 → 141）与 **1 件**（11 → 12，且 semantic 6 → 7）。

### 8.8 区间总 diff --stat（按桶切）

```console
$ git diff --stat 58d2c0a..7802dd5 -- xsd/
 xsd/esml-canonical-basic.xsd   | 137 +++++++++++++++++++++++------------------
 xsd/esml-canonical-compute.xsd |  32 ++++++++--
 xsd/esml-canonical-project.xsd |   3 +-
 xsd/esml-v1.xsd                |  94 ++++++++++++++++++++++--------
 4 files changed, 175 insertions(+), 91 deletions(-)

$ git diff --stat 58d2c0a..7802dd5 -- SPEC.md
 SPEC.md | 507 ++++++++++++++++++++++++++++++++++++++++++++++++++++++----------
 1 file changed, 427 insertions(+), 80 deletions(-)

$ git diff --stat 58d2c0a..7802dd5 -- '*.esml' | tail -3
 142 files changed, 369 insertions(+), 36 deletions(-)

$ git diff --stat 58d2c0a..7802dd5 -- tools/ docs/ Makefile README.md
 Makefile                                |  29 ++
 README.md                                |  58 +++
 docs/coverage.md                        | 481 +++++++++++++++++++
 docs/design/root-matrix-adjudication.md | 146 ++++++
 docs/design/tasks-shell-adjudication.md | 125 +++++
 docs/design/xsd-spec-parity.md          | 283 +++++++++++
 docs/validate_examples.py               | 264 +++++++++++
 docs/validate_roots.py                  | 595 ++++++++++++++++++++++
 tools/aliases.tsv                       | 112 +++++
 tools/check-examples.py                 | 603 ++++++++++++++++++++++
 tools/check-spec-xsd-parity.py         | 809 ++++++++++++++++++++++++++++
 tools/negatives.tsv                     |  18 +
 tools/spec-xsd-bydesign.tsv             |  26 +
 13 files changed, 3549 insertions(+)
```

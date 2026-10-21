# 裁决：入口层根清单 ⇄ canonical 层全局元素（根矩阵）

- **日期**：2026-10-21
- **范围**：`xsd/esml-v1.xsd`（入口层）的全局元素集合 ⇄ `xsd/esml-canonical-*.xsd`
  的全局元素集合；连带 `SPEC.md` §1.1 / §6.8 / §13 的措辞。
- **触发**：工单「`<tasks>` 根与 canonical 层全局元素清单的机判化」。上一轮
  `ca8efc7` 已把 `<tasks>` 对齐进 canonical 层，但「入口层根清单 = canonical 层
  全局元素」这句对账**只存在于人的印象里**，没有机判。

## 1. 裁定

> **入口层 `esml-v1.xsd` 的全局元素集合 ≡ canonical 层（`esml-canonical-*.xsd`）
> 的全局元素集合。**

理由三条，都是机验出来的：

1. **入口层是「根合法性闸」，不是第二套语言。** `esml-v1.xsd` 的自述是
   「规范入口：校验文档为合法 ESML（namespace / 根元素 / 基本属性）」，内容一律
   lax 透传。它对「什么是合法文档根」的回答，必须和 canonical 层说同一句话，
   否则同一份文档在两层得到相反的裁决。
2. **canonical 层是唯一真相**（SPEC §2「唯一真相 = XSD（机验基准）」）。所以
   「合法文档根」的清单只能由 canonical 层给出，入口层照抄。
3. **两种偏差都是缺陷，不是风格问题。**
   - 少一个 ⇒ **假拒**：一份合法的 canonical 文档被入口层判非法（实测见 §3）。
   - 多一个 ⇒ **假收**：入口层放行一份**没有任何 canonical schema 能校验**的
     文档——根合法性闸有洞，而下游拿到的文档没人能验。

**例外机制**：脚本 `docs/validate_roots.py` 留了 `EXCEPTIONS` 表（根名 → 理由 +
裁决记录路径），当前**为空**。保留机制是为了让「以后确实要放宽根集合」变成一次
**显式决策**（必须写理由、必须留档），而不是一次没人看见的 schema 改动。

## 2. 逐条差异与处置

改动前的差集（`python3 docs/validate_roots.py` 首次运行的原始输出）：

```
   canonical 有而入口层没有：`<metadata>`、`<project>`
   入口层有而 canonical 没有：`<domain>`、`<schedule>`、`<solutionParameters>`、`<variables>`
```

### 2.1 假拒（canonical 有、入口层没有）→ **补进入口层**

| 根 | canonical 声明处 | 处置 |
|---|---|---|
| `<metadata>` | `esml-canonical-basic.xsd:909`（「独立根 `<metadata>` 块」） | 加进 `esml-v1.xsd` |
| `<project>` | `esml-canonical-project.xsd:85` | 加进 `esml-v1.xsd` |

`<project>` 是**假拒的典型**：SPEC §6.8 用整段 XML 演示 `<project>` 作文档根，
`esml-canonical-project.xsd` 也把它声明成全局元素，但入口层不收 ⇒ 一份完全合法
的 ESML 文档过不了入口层。两处补都是**纯增量**，不拒任何原先能过的文档。

### 2.2 假收（入口层有、canonical 没有）→ **移出入口层**

| 根 | canonical 层里的真实位置 | 处置 |
|---|---|---|
| `<schedule>` | `esml-canonical-basic.xsd:749`，嵌在 `SystemType` 里（`<system>` 的子元素） | 移出入口层 |
| `<solutionParameters>` | `esml-canonical-basic.xsd:804`，嵌在 `<esml>` 里（顶层**段**） | 移出入口层 |
| `<variables>` | `esml-canonical-basic.xsd:351`（`PortTypeDef` 内）与 `:545`（`ModelType` 内） | 移出入口层 |
| `<domain>` | `esml-canonical-basic.xsd:180`，嵌在 `DomainsType` 里（`<domains>` 的子元素） | 移出入口层 |

这四个在 canonical 层**都只是嵌套元素**，从来不是全局元素，也从来不是 SPEC
写过的文档根。作为**文档根**，它们不构成任何合法的 ESML 文档：`<variables>`
作根是一张没有模型的变量表，`<schedule>` 作根是一段没有系统的调度，
`<domain>` 作根是一个单位域，`<solutionParameters>` 作根是一段没有模型的求解参数。
入口层放行它们 = 放行「没有 schema 能验」的文档。

> **这是本次唯一一处行为可见的收紧**：以前以这四个为根的文档过得了入口层，现在
> 过不了。判定它不是 breaking change 的依据：SPEC §1.1 的根是 `<esml>`、§13 的
> 入口层根是「`<esml>` + 独立库根」，这四个从来不在合法根清单里；仓内 141 份
> 示例**没有一份**以它们为根（全部是 `<esml>`）；canonical 层从来没有接受过它们。
> 换句话说，它们是**校验层的假收**，不是语言语义的一部分。
>
> 若将来确实要让某个元素成为文档根，**正确的做法是把它声明成 canonical 全局
> 元素**（并补 SPEC 条文与示例），而不是往入口层私加一个根——那正是本次要消灭的
> 「入口层自成一套清单」。

### 2.3 清单本身的处置

入口层注释里原来那句手写的
`<!-- 独立库文件根（units/types/ports/components/processes/schedules/tasks 等） -->`
连拼写都已过时（canonical 里根本没有 `types` / `ports` / `components` 这三个元素
名），改为**由脚本生成的根矩阵块**（`ROOT-MATRIX:BEGIN` … `ROOT-MATRIX:END`）：

- `python3 docs/validate_roots.py sync` 重生成；
- `python3 docs/validate_roots.py` 逐字复核，漂移即判红。

**清单不再由人手抄**，谁改 schema 谁跑一次 sync，机器兜底。

## 3. 证据（实测，不是推理）

改前的入口层（`git show HEAD:xsd/esml-v1.xsd`）对几份文档的裁决：

```
--- <project> 为根        vs 旧入口层：FAIL   vs esml-canonical-project.xsd：PASS
--- <metadata> 为根      vs 旧入口层：FAIL   vs esml-canonical-basic.xsd：PASS
--- <schedule> 为根      vs 旧入口层：PASS   vs esml-canonical-basic.xsd：FAIL
```

即：旧入口层**拒掉两份合法文档**、**放行一份没人能验的文档**。

改后机判（`python3 docs/validate_roots.py`）：

```
== 1. 入口层根 ⇄ canonical 全局元素 ==
   canonical 全局元素：12 个（esml-canonical-basic.xsd 9 / esml-canonical-compute.xsd 2 / esml-canonical-project.xsd 1）
   入口层根：12 个
   canonical 有而入口层没有：无
   入口层有而 canonical 没有：无
   [OK] 两个集合相等（R1 可达 + R2 无洞），例外登记 0 条
== 2. 入口层注释里的根矩阵清单 ⇄ XSD ==
   [OK] ROOT-MATRIX 块与生成内容逐字一致
== 3. SPEC.md §13 的 XSD 分层表 ⇄ XSD ==
   [OK] 表内文件集合与每行的「根」集合均与 schema 一致
```

## 4. 规范措辞改动（连同理由）

规范文字与 schema 分歧时以 schema 为准（SPEC 开头），但手抄的清单必须跟着改，
否则又是一处「转述漂移」。本次改了三处，**没有一处是语义变更**：

| 位置 | 改动 | 理由 |
|---|---|---|
| §1.1 | 新增一段「根清单」，点名独立根并指向 §13 与机判脚本 | 原文只说「根是 `<esml>`」，没交代其余独立根从哪来 |
| §6.8 | 「壳内子元素按松散规则透传（不另设结构约束）」→ 按 `##targetNamespace` + lax 透传，**已声明的子元素按其自身声明校验** | 原文与 schema 行为不符：lax 遇到有全局声明的子元素（如 `<computeTasks>`）**会**校验它。措辞收紧到与 schema 一致，语义不变 |
| §13 | XSD 分层表补 `esml-canonical-project.xsd` 整行；「根」一列改为逐文件列全（原来是「`<esml>` + 独立库根」这种概括） | 原来那列是**手抄**且已漂：整行漏了 project.xsd，根集合漏了 `<tasks>` / `<metadata>` / `<project>`。改后由 `docs/validate_roots.py` 逐行机判 |

## 5. 不做什么（以及为什么）

- **没有给这四个元素补 canonical 全局元素**：那会**新增**语言能力（新形态的合法
  文档），需要补 SPEC 条文与示例，超出「只修缺陷」的范围。§2.2 已写明将来的正确
  路径。
- **没有保留成「例外」**：例外表是给「将来要放宽」留的口子；这四个是**假收**，
  留着就是留着洞。例外机制本身保留在脚本里，当前为空。
- **没有动 canonical 层**：本次的差异全部由入口层单方面收敛到 canonical 层的
  既有事实，canonical 层一个字没改（`git diff --stat` 可查）。

## 6. 怎么跑

```sh
python3 docs/validate_roots.py            # 机判（退出码非 0 = 判红）
python3 docs/validate_roots.py sync       # 改了 schema 后重生成入口层注释里的清单
python3 docs/validate_roots.py selftest   # 自证：好例 / 坏例
make check                                 # 根矩阵 + 示例对账，一起跑
```

相关裁决：`<tasks>` 壳的单独裁定见 [`tasks-shell-adjudication.md`](tasks-shell-adjudication.md)。

# 裁决：§6.8 的 `<tasks>` 壳与 `<computeTasks>` 的关系

- **日期**：2026-10-21
- **范围**：SPEC §6.8 / §6.9、`xsd/esml-canonical-compute.xsd`、
  `xsd/esml-canonical-basic.xsd`、`xsd/esml-v1.xsd`
- **触发**：工单第 4 条「检讨 `<tasks>`：§6.8 的壳是否应作为全局元素、
  `<tasks>` 与 `<computeTasks>` 的关系是否在 SPEC、XSD、canonical 三处一致；
  不一致就裁定并留档」。

## 1. 问题

`<tasks>` 是 `<computeTasks>` 之外的**可选外包装**（SPEC §6.8）。三处对这个壳的
说法必须一致：

| 处 | 说法 |
|---|---|
| **SPEC §6.8** | 「`<tasks>` 外层壳：`<computeTasks>` 之外的**可选外包装**」「不是两个平级概念，是同一个东西包了一层」「canonical 声明：`esml-canonical-compute.xsd` 的 `<tasks>` 全局元素，`esml-canonical-basic.xsd` 的 `<esml>` 子元素表引用之（入口 schema `esml-v1.xsd` 早已声明同名根）」 |
| **canonical（compute.xsd:602）** | `<xs:element name="tasks">`，内容 `<xs:any namespace="##targetNamespace" processContents="lax"/>` |
| **canonical（basic.xsd）** | `<esml>` 的子元素表里 `<xs:element ref="esml:tasks" minOccurs="0" maxOccurs="1"/>` |
| **入口层（esml-v1.xsd）** | `<tasks>` 是一个**全局元素**（根） |

## 2. 裁定

> **`<tasks>` 应当、且已经是一个 canonical 全局元素**；它与 `<computeTasks>` 的关系
> 是「**同一个东西包了一层**」，不是两个平级概念。

理由：

1. **它必须先是全局元素，`<esml>` 才能引用它。** `basic.xsd` 的 `<esml>` 子元素
   表写的是 `ref="esml:tasks"`——引用的是 compute.xsd 里的全局元素声明。
   「壳可作 `<esml>` 子元素」与「壳是全局元素」不是二选一：`<computeTasks>`
   自己也是**既作 `<esml>` 子元素、又作全局元素（文档根）**的，`<tasks>` 与它
   同构。
2. **上一轮 `ca8efc7` 已经把它补成全局元素，且补得有据。** 那一版的原话：
   「`esml-canonical-basic.xsd` / `esml-canonical-compute.xsd` **都没声明它**
   ⇒ 唯一用它的示例 `T-tasks/tasks.esml` 机验失败（`Unexpected child with tag
   'tasks'`）」。补全局元素之后，`T-tasks/tasks.esml` 过机验。**壳作为全局元素
   是修缺陷，不是加功能**——§6.8 正文早就是那个写法，是 schema 落后于正文。
3. **它作为文档根是既有事实**，不是本次新增：入口 schema 早已声明同名根，
   canonical 里它就是全局元素 ⇒ 用哪个 schema 校验，它都能作根。本次只是把
   入口层的根清单与 canonical 对齐（见
   [`root-matrix-adjudication.md`](root-matrix-adjudication.md)）。

## 3. 三处核对结果

| 事项 | SPEC §6.8 | XSD | canonical | 结论 |
|---|---|---|---|---|
| `<tasks>` 是全局元素？ | 说「是」（「`esml-canonical-compute.xsd` 的 `<tasks>` 全局元素」） | 入口层声明同名根 | `compute.xsd:602` 全局元素 | **一致**（本次把入口层补齐到 12 根） |
| `<tasks>` 可作 `<esml>` 子元素？ | 说「可与顶层其它元素并列」 | — | `basic.xsd` 的 `<esml>` 子元素表 `ref="esml:tasks"` | **一致** |
| `<tasks>` ⊃ `<computeTasks>`？ | 说「壳内嵌套的 `<computeTasks>` 被实读」 | — | `<xs:any ##targetNamespace lax/>` 透传 | **一致** |
| 壳内子元素的校验强度？ | 「按松散规则透传（不另设结构约束）」 | — | `processContents="lax"` ⇒ **有全局声明的子元素按其自身声明校验** | **不一致 → 本次改措辞**（见 §4） |
| `<tasks>` 与 `<computeTasks>` 是两个平级概念吗？ | 「不是，是同一个东西包了一层」 | — | 壳的透传规则 + 引擎 `parse_tasks` 按 `descendants()` 找 `computetasks` | **一致** |
| 根清单 | §13 的表**漏了** `<tasks>`（compute.xsd 行只写 `<computeTasks>`） | — | compute.xsd 有**两个**全局元素 | **不一致 → 本次改表 + 落机判** |

## 4. 本次改的两处措辞

### 4.1 §6.8「不另设结构约束」→「已声明的子元素按其自身声明校验」

原文：

> 壳内子元素按松散规则透传（不另设结构约束）

schema 实况：`processContents="lax"` 的语义是「**能**找到声明就校验，找不到就
放行」。壳内若有 `<computeTasks>`（它有全局声明），**会被严格校验**。所以原文
「不另设结构约束」过宽。

改后：

> 壳内子元素按 `##targetNamespace` + lax 透传——**已声明的子元素（如
> `<computeTasks>`）按其自身声明校验**，未声明的放行。

**语义不变**（描述的是既有行为），只是把话说准。判据来自
`xsd/esml-canonical-compute.xsd` 的 `processContents="lax"`，不是印象。

### 4.2 §6.8 补一句「`<tasks>` 也是文档根」；§13 的表补 `<tasks>` / `<project>` /
`<metadata>` 等

原文 §6.8 承认入口层有同名根，但没说清「所以它可以作文档根」；§13 的表又把
compute.xsd 的根写成只有 `<computeTasks>`。两处一起把「壳是不是根」讲成了一团
浆糊。本次：

- §6.8 补「`<tasks>` 是 canonical **全局元素**，既可作 `<esml>` 的可选子元素，
  也可作**文档根**（入口 schema `esml-v1.xsd` 的根清单与之相等，由
  `docs/validate_roots.py` 机判）」；
- §13 的「根」一列逐文件列全，并补上漏掉的 `esml-canonical-project.xsd` 整行。

**不是 breaking change**：两处都只是把 schema 里**早已存在**的事实写进正文，
没有收窄也没有放宽任何语言的合法写法。

## 5. 顺带查清的三件事（不改，只记）

1. **`<tasks>` 在 `<esml>` 里可以出现多次。** `basic.xsd` 写的是
   `<xs:element ref="esml:tasks" minOccurs="0" maxOccurs="1"/>`，但它嵌在
   `<xs:choice minOccurs="0" maxOccurs="unbounded">` 里 —— XSD 里外层 choice 的
   `maxOccurs` 与内层元素的 `maxOccurs` 是**相乘**的，所以实际是 0..∞。
   实测：同一 `<esml>` 里放两个 `<tasks>`（各含一张 `<computeTasks>`）过
   `esml-canonical-basic.xsd`。这正好支撑 §6.8「便于同一文档放多张任务表」。
   （同理，直接并列多个 `<computeTasks>` 也合法。）
2. **`<tasks>` 作文档根过 canonical-basic。** `basic.xsd` include 了
   `compute.xsd`，`<tasks>` 的全局声明随之并入 ⇒ 用 basic 也能校验
   `<tasks>` 根的文档。实测 PASS。
3. **`esml-canonical-project.xsd` 是自包含的**，它自己另定义了一个宽松的
   `ComputeTasksType`（`<xs:any namespace="##any" lax/>`）来接 `<computeTasks>`，
   因此 `<project>` 里的任务表**不受** `esml-canonical-compute.xsd` 的七类
   `kind` 约束（文件头注释说「so the seven-task payload stays validated by
   `esml-canonical-compute.xsd`」，与实况不符）。**本轮不动**——它不属于根
   矩阵，且改动会牵动 `<project>` 的载荷语义，超出「只修缺陷、只做根清单」的
   范围。留待单独一轮。

## 6. 证据

```sh
$ python3 docs/validate_roots.py selftest
   [好例 1] 本仓当前状态（入口层根 = canonical 全局元素）
      → PASS（0 个问题）
   [坏例 1] 从入口层删掉一个根 `<project>`（canonical 层仍有）
      → 判红（3 个问题）
   [坏例 2] 给 canonical 层加一个假根 `<fakeRoot>`（入口层没有）
      → 判红（4 个问题）
   ...
selftest: OK
```

`<tasks>` / `<computeTasks>` / `<metadata>` / `<project>` 的根位次，由
`docs/validate_roots.py` 第 1、2 道对账常驻机判。

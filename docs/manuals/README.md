# ESML 语言规范手册

本目录是 `esml-language`（规范 + XSD + 示例）的三本手册：

| 手册 | 用途 |
|---|---|
| [development.md](development.md) | 改 SPEC / XSD / 示例，跑根矩阵与示例门 |
| [deployment.md](deployment.md) | 发版、发布 XSD、给引擎 bump 子模块指针 |
| [operations.md](operations.md) | 日常校验、负例登记、版本漂移处置 |

当前规范基线：`v1.3.4`（最后核对：2026-11-28）。规范是**单一真源**：`SPEC.md` + `xsd/` + 示例；
与 `esml-engine` 实现间已达成 **0/0 零漂移对账**（`engine-drift.tsv` 残留清零），完整五份 canonical XSD 已同步发布至公开文档站 `ai4energy-docs/docs/public/schema/`；下游不得各自维护方言。

## 跨仓关系

```
esml-language ──(SPEC / XSD / 示例)──┬─► esml-engine（examples/syntax 子模块 + schema/ 对账）
                                      ├─► esml-libraries（canonical XSD · G-L1..G-L6）
                                      ├─► esml-books（101-language-book · G-B1）
                                      └─► esml-studio（XSD + 编辑器能力探测）
```

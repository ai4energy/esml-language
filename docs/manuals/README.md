# ESML 语言规范手册

本目录是 `esml-language`（规范 + XSD + 示例）的三本手册：

| 手册 | 用途 |
|---|---|
| [development.md](development.md) | 改 SPEC / XSD / 示例，跑根矩阵与示例门 |
| [deployment.md](deployment.md) | 发版、发布 XSD、给引擎 bump 子模块指针 |
| [operations.md](operations.md) | 日常校验、负例登记、版本漂移处置 |

当前版本：`v1.3.3`。规范是**单一真源**：`SPEC.md` + `xsd/` + 示例；
引擎按子模块指针消费，下游不得各自维护一份方言。

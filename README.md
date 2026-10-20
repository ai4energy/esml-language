# esml-language

**ESML**（Energy System Modeling Language）的语言规范仓库。

ESML 是一种声明式、基于方程的物理系统建模语言，文档即 XML：类型、端口、组件、
系统、连接与任务全部写在同一份文档里，求解器读的就是这份文档——不存在需要与模型
保持同步的独立代码生成步骤。

| 路径 | 内容 |
|---|---|
| [`SPEC.md`](SPEC.md) | 语言规范：词法、类型系统、组件、端口、系统、方程、展开与求解约定 |
| [`xsd/esml-v1.xsd`](xsd/esml-v1.xsd) | 入口 Schema：根元素、命名空间与基本属性 |
| [`xsd/esml-canonical-common.xsd`](xsd/esml-canonical-common.xsd) | 共享 primitive：标识符、单位词法 |
| [`xsd/esml-canonical-basic.xsd`](xsd/esml-canonical-basic.xsd) | 模型体系子集：单位、类型、组件、端口、连接、系统 |
| [`xsd/esml-canonical-compute.xsd`](xsd/esml-canonical-compute.xsd) | 计算体系子集：七类任务及其载荷 |
| [`xsd/esml-canonical-project.xsd`](xsd/esml-canonical-project.xsd) | 项目容器：系统、任务、场景链、结果 |
| [`examples/syntax/`](examples/syntax/) | 每个语法点一份可运行文档，按语言层次分目录 |

canonical XML 是正统语法；XML Schema 描述 canonical XML，是可机验的基准。
文字与 schema 出现分歧时，以 schema 为准。

## 阅读规范

`SPEC.md` 的章节编号稳定，schema 与示例都按该编号引用。示例文件头部的注释写明
该文件演示的语法点；目录与语言层次的对应关系见
[`examples/syntax/README.md`](examples/syntax/README.md)。

## 校验文档

任意 XML Schema 校验器均可。入口 schema 校验良构性与命名空间，canonical schema
校验文档结构：

```sh
python3 -c "import xmlschema; xmlschema.XMLSchema('xsd/esml-canonical-basic.xsd').validate('examples/syntax/L3-model/modeltype-basic.esml')"
```

## 贡献

语言变更先落为规范修订：一处改动同时涉及 `SPEC.md`、它蕴含的 XSD 变更，以及
至少一份演示该语法的示例。拼写单轨——同一语义只有一种写法，其余写法一律报错，
不做静默兼容。

## 许可

MIT，详见 [`LICENSE.md`](LICENSE.md)。

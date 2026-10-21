# esml-language

**ESML**（Energy System Modeling Language）的语言规范仓库。

ESML 是一种声明式、基于方程的物理系统建模语言，文档即 XML：类型、端口、组件、
系统、连接与任务全部写在同一份文档里，求解器读的就是这份文档——不存在需要与模型
保持同步的独立代码生成步骤。

| 路径 | 内容 |
|---|---|
| [`SPEC.md`](SPEC.md) | 语言规范：词法、类型系统、组件、端口、系统、方程、展开与求解约定 |
| [`xsd/`](xsd/) | XML Schema：入口 schema 一份，canonical 子集四份（共享 primitive / 模型体系 / 计算体系 / 项目容器） |
| [`docs/`](docs/) | 规范 ⇄ 示例 的机验对账：[`validate_examples.py`](docs/validate_examples.py)（五道检查）与 [`coverage.md`](docs/coverage.md)（对账表与逐条裁决） |
| `D-skeleton/` … `X-use/` | 每个语法点一份可运行文档，按语言层次分目录（见下表） |

canonical XML 是正统语法；XML Schema 描述 canonical XML，是可机验的基准。
文字与 schema 出现分歧时，以 schema 为准。

## 示例目录

| 目录 | 层次 |
|---|---|
| `D-skeleton/` | 文档骨架、根属性与元数据 |
| `L0-type-unit/` | 类型、量纲与单位 |
| `L1-expr-equation/` | 表达式与方程 |
| `L2-discrete/` | 离散事件与初始化 |
| `L3-model/` | 模型组装与继承 |
| `L4-port/` `L4-portvar/` | 端口类型与端口变量 |
| `L5-instance/` | 实例与参数覆盖 |
| `L6-connect/` | 连接与拓扑 |
| `L7-partition/` | 分区与分区化 |
| `L8-function/` | 外部函数与用户函数 |
| `L9-method-schedule/` | 方法脚本与调度 |
| `T-tasks/` | 计算任务 |
| `X-use/` | 库组合 |

每个文件都是一份完整的 ESML 文档，头部的注释块写明它演示的语法点。

## 阅读规范

`SPEC.md` 的章节编号稳定，schema 与示例都按该编号引用。

## 校验与运行

任意 XML Schema 校验器均可。入口 schema 校验良构性与命名空间，canonical schema
校验文档结构：

```sh
python3 -c "import xmlschema; xmlschema.XMLSchema('xsd/esml-canonical-basic.xsd').validate('L3-model/modeltype-basic.esml')"
```

多数示例自包含，可直接交给实现校验：

```sh
esml check L0-type-unit/type-unit.esml
```

部分示例引用库模型，需要把库根目录加进路径：

```sh
esml simulate path/to/example.esml -L path/to/library
```

文件名含 `probe`、或头部注明为负例的文档**预期失败**：它们演示的是被拒绝的写法，
非零退出码正是正确结果。

## 约定

- 文档使用 `.esml` 扩展名。
- 作者标识符匹配 `[A-Za-z_][A-Za-z0-9_]*`；双下划线 `__` 是结构分隔符，
  作者标识符中禁止出现。
- 实例路径用 `.` 书写。

## 机验

示例与 XSD 的一致性由 [`tools/check-examples.py`](tools/check-examples.py) 把关：

```sh
python3 -m venv .venv && .venv/bin/pip install lxml   # 只需一次
.venv/bin/python tools/check-examples.py              # 全仓；退出码 0 = 全绿
.venv/bin/python tools/check-examples.py --vocab      # 附带逐元素对账表
.venv/bin/python tools/check-examples.py --self-test  # 3 好 4 坏 + 反向自检
```

它对每件示例跑**两道**校验：入口 `xsd/esml-v1.xsd` 与逐元素的
`xsd/esml-canonical-basic.xsd`。只跑入口是不够的——入口的内容模型是
`processContents="lax"`，**未声明的元素名原样放过**，`--self-test` 里专门有一个
反向用例把这件事钉住。

刻意保留的负例登记在 [`tools/negatives.tsv`](tools/negatives.tsv)，并写明它
**红在哪一层**：`schema` 表示 XSD 必须拒收它，`semantic` 表示拼写合法、红在求解层。
标成 `schema` 的负例哪天被 XSD 收下了，门就红——那说明判据漏了，不是件变好了。

## 贡献

语言变更先落为规范修订：一处改动同时涉及 `SPEC.md`、它蕴含的 XSD 变更，以及
至少一份演示该语法的示例。拼写单轨——同一语义只有一种写法，其余写法一律报错，
不做静默兼容。

## 许可

MIT，详见 [`LICENSE.md`](LICENSE.md)。

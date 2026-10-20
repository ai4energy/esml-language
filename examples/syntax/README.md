# 语法示例

每个语法点一份可运行文档，按语言层次分目录：

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

## 运行

多数示例自包含：

```sh
esml check examples/syntax/L0-type-unit/type-unit.esml
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

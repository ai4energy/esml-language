# esml-language

**ESML**（Energy System Modeling Language）的语言规范仓库。

ESML（Energy System Modeling Language，面向能源系统建模的声明式语言）是一种面向复杂能源系统的声明式、基于方程的物理系统建模与计算语言。其核心特征在于“文档即模型”——类型、端口、组件、系统、连接与求解任务全部收敛于同一份结构化 XML 文档中，由求解器直接解析执行，彻底消除了传统建模中需要与模型保持同步的独立代码生成步骤。

| 路径 | 内容 |
|---|---|
| [`SPEC.md`](SPEC.md) | 语言规范：词法、类型系统、组件、端口、系统、方程、展开与求解约定 |
| [`xsd/`](xsd/) | XML Schema：入口 schema 一份，canonical 子集四份（共享 primitive / 模型体系 / 计算体系 / 项目容器） |
| [`docs/`](docs/) | 机验对账：[`validate_roots.py`](docs/validate_roots.py)（入口层根清单 ⇄ canonical 全局元素）与 [`validate_examples.py`](docs/validate_examples.py)（规范 ⇄ 示例，五道检查）、[`coverage.md`](docs/coverage.md)（对账表与逐条裁决）、[`design/`](docs/design/)（裁决记录）、[`audit/`](docs/audit/)（strict 基线等审计件） |
| [`tools/`](tools/) | 台账闸：[`element-coverage.tsv`](tools/element-coverage.tsv)（元素覆盖双向台账）、[`attr-acceptance.tsv`](tools/attr-acceptance.tsv)（属性验收台账：引擎裁决）、[`attr-coverage.tsv`](tools/attr-coverage.tsv)（属性覆盖双向台账：完整性）、[`engine-example-debt.tsv`](tools/engine-example-debt.tsv)（引擎 × 示例可运行性台账；`stage` 列取值 `check` / `solve`）、[`engine-drift.tsv`](tools/engine-drift.tsv)（跨仓 schema 漂移裁决）、[`aliases.tsv`](tools/aliases.tsv)（legacy 拼法清单）、[`negatives.tsv`](tools/negatives.tsv)（负例清单：红在哪一层） |
| `D-skeleton/` … `X-use/` | 每个语法点一份可运行文档，按语言层次分目录（见下表） |

canonical XML 是正统语法；XML Schema 描述 canonical XML，是可机验的基准。
文字与 schema 出现分歧时，以 schema 为准。

```sh
python3 -m venv .venv && .venv/bin/pip install xmlschema lxml   # 一次装齐八道闸的依赖
PY=.venv/bin/python make check                                  # 全绿 = 可以提交
```

## 手册

开发 / 部署 / 运维三本手册见 [`docs/manuals/`](docs/manuals/README.md)。

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

> **可运行口径**：① `esml check` 全绿（errors=0）；② 求解面按 [`tools/solve-smoke.tsv`](tools/solve-smoke.tsv) 普查口径——`ok` / `ok-simulate` 为可运行，求解层未通过的件在 [`tools/engine-example-debt.tsv`](tools/engine-example-debt.tsv) 的 `stage=solve` 行登记（引擎侧债务，示例本身不动）。

## 阅读规范

`SPEC.md` 的章节编号稳定，schema 与示例都按该编号引用。

## 校验与运行

仓内八道**常驻机判**，`make check` 一起跑（任一失败即非零退出）：

| 脚本 | 查什么 | 依赖 |
|---|---|---|
| [`docs/validate_roots.py`](docs/validate_roots.py) | **根矩阵**：入口层 `esml-v1.xsd` 的根集合 ⇄ canonical 层的全局元素集合；入口层注释里的根清单由脚本生成、逐字复核；SPEC §13 的 XSD 分层表逐行对账 | 仅标准库 |
| [`docs/validate_examples.py`](docs/validate_examples.py) | 规范 ⇄ 示例 五道检查（XSD 机验 / 路径 / 章节引用 / 稀有元素 / SPEC 代码块）；`--strict` 追加第六道「撤通配判别力闸」，与 `docs/audit/strict-baseline.txt` 基线比较 | `xmlschema` |
| [`tools/check-engine-xsd-parity.py`](tools/check-engine-xsd-parity.py) | **跨仓 schema 漂移**：本仓 `xsd/` ⇄ 引擎仓 `$ESML_ENGINE_DIR/schema/` 的属性集 / 子元素集 / 全局根三项对账，每组分歧须在 [`tools/engine-drift.tsv`](tools/engine-drift.tsv) 有裁决行 | `lxml` |
| [`tools/check-element-coverage.py`](tools/check-element-coverage.py) | **元素覆盖双向闸**：方向 A「每个 XSD 命名元素必须有非负例示例或在台账登记」，方向 B「示例用到的每个元素必须已声明或登记 by-design」；台账 [`tools/element-coverage.tsv`](tools/element-coverage.tsv)，头部计数当场重算 | 仅标准库 |
| [`tools/check-attr-coverage.py`](tools/check-attr-coverage.py) | **属性覆盖双向闸**：声明→示例（每个 XSD 声明的属性必须有非负例示例或在台账登记）与示例→声明（示例用到的每个属性必须已声明或登记 by-design）；台账 [`tools/attr-coverage.tsv`](tools/attr-coverage.tsv)，头部计数当场重算。与 `attr-acceptance.tsv` 分工：后者记**引擎裁决**（收 / 拒 / 零效果），本闸查**完整性**（声明 ⇄ 示例闭合） | 仅标准库 |
| [`tools/check-engine-examples.py`](tools/check-engine-examples.py) | **示例 × 引擎可运行性闸**：每个非负例示例（负例识别照抄 `validate_examples.py`）要么 `esml check` 绿（`errors=0`）、要么在 [`tools/engine-example-debt.tsv`](tools/engine-example-debt.tsv) 登记引擎债；台账数字与实测不符即「台账过时」判红；缺引擎跳过（同跨仓漂移闸）。台账 `stage` 列分两值域：`check` 行 = `esml check` 层不收（`errors>0`，闭合判据：`ESML_PROPS=off esml check <file>` 的 errors 数与台账一致）；`solve` 行 = `esml check` 绿但 `esml solve` 失败（闭合判据：`errors=0` 且求解层失败，evidence 记求解层首行错误） | `lxml` 无；逐件实跑引擎，缺引擎仓跳过 rc=0 |
| [`tools/check-spec-element-coverage.py`](tools/check-spec-element-coverage.py) | **XSD 声明 ⇄ SPEC 点名闸**：每个 XSD 命名元素都必须在 `SPEC.md` 正文点名（判据 `name=` 声明去重、正则以属性/闭合为界）；未点名须在 [`tools/spec-element-coverage.tsv`](tools/spec-element-coverage.tsv) 登记 pending / by-design（依据必填）；台账头部计数当场重算 | 仅标准库 |
| [`tools/check-example-expectations.py`](tools/check-example-expectations.py) | **示例「期望值」台账闸**：逐台账行实跑引擎（`ESML_PROPS=off esml <mode> <file> [--steps N]`），从输出解析变量值，与台账 `value` 按 `tol` 绝对差比对；值超 tol ⇒ 红（台账过时或头注双标）；引擎跑不出 ⇒ 红；缺引擎仓跳过 rc=0。台账 [`tools/example-expectations.tsv`](tools/example-expectations.tsv)，头部计数当场重算 | 引擎二进制；缺引擎仓跳过 rc=0 |

```sh
make check                                   # 八道都跑
make roots                                   # 只跑根矩阵
make strict                                  # 只跑撤通配判别力闸
python3 docs/validate_roots.py selftest      # 根矩阵的自证（好例 / 坏例）
python3 tools/check-element-coverage.py      # 只跑元素覆盖闸
python3 tools/check-element-coverage.py --self-test  # 自证：好树零违规、坏树必红
python3 tools/check-attr-coverage.py --self-test      # 自证：好树零违规、坏树必红
python3 tools/check-engine-examples.py --self-test   # 自证：台账逻辑（负例识别 / 对账 / 计数）
make spec-elements                           # 只跑 XSD 声明 ⇄ SPEC 点名闸
```

属性面另有台账闸 [`tools/check-attr-acceptance.py`](tools/check-attr-acceptance.py)：
逐行核对 [`tools/attr-acceptance.tsv`](tools/attr-acceptance.tsv) 的 verdict，
`--engine-check` 把每个属性注入真实示例实跑引擎复算，`--self-test` 自证。
依赖引擎二进制（`ESML_ENGINE_DIR` 指向 `target/release`；缺引擎时打印「跳过」）。
`docs/coverage.md` 汇总所有**规范有、实现无**与 **by-design** 的登记项。

改了 schema 之后，先 `python3 docs/validate_roots.py sync` 重生成入口层注释里的
根矩阵清单（**清单不手工转述**），再跑 `make check`。`make check` 第三道
（跨仓漂移）在缺引擎仓时打印「跳过」并放行——它只在能读到 `$ESML_ENGINE_DIR/schema/`
时才是硬闸；第六道（示例 × 引擎可运行性）同款「缺引擎跳过」：逐件实跑引擎不可用时
不静默、不误红，头部台账计数检查照常做。台账的 `stage` 列把「引擎不收」拆成两层：`check` 行是 `esml check` 层拒收，`solve` 行是 `check` 绿、求解层失败——一条台账管两层，各按各的闭合判据对账。

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

## 机验（进阶工具）

示例与 XSD 的一致性另由 [`tools/check-examples.py`](tools/check-examples.py) 把关：

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

`negatives.tsv` 头部的「登记条数」（schema / semantic 各几件）由
`tools/check-examples.py` 每次跑**当场重算并核对**，对不上就红——条数不是注释里的摆设。
早期的 G16 语料门白名单处置台账（`neg-debt.tsv` 14 行）与它的对账门
`check-neg-debt.py` 已于 2026-11-11 退役，原件归档在
[`ai4ecom/esml-adr-archive`](https://github.com/ai4ecom/esml-adr-archive)
的 `language/tools-archive/`（一次性结算已完毕，不再有新行）。

「哪些写法算 legacy」这条知识落在 [`tools/aliases.tsv`](tools/aliases.tsv)，
门据此逐条机验：legacy 元素名/属性名不得被任何 `xsd/*.xsd` 声明、不得出现在示例里；
别名表里指认的 canonical 拼法必须真的在 XSD 里有声明（表与 schema 不得脱节）；
入口 schema 的**根清单**必须与 canonical 层的全局元素集**完全一致**——入口多收一个
根，等于放行一份 canonical 必然拒收的文档（假绿）；入口少收一个，则是误拒。

规范正文与 schema 的**文档根**对账由 [`tools/check-spec-xsd-parity.py`](tools/check-spec-xsd-parity.py)
把关（仅标准库依赖）：

```sh
python3 tools/check-spec-xsd-parity.py                # 三方对账；退出码 0 = 一致
python3 tools/check-spec-xsd-parity.py --report        # 附带 SPEC 根声明清单与证据行
python3 tools/check-spec-xsd-parity.py --self-test     # 5 好 4 坏 + 反向 + 真实树变异
```

它把三个集合摆在一起对账：canonical 层的全局元素、入口 schema 的全局元素、
`SPEC.md` 正文里被描述为文档根的元素。入口多收 = 假绿，入口漏收 = 误拒，
SPEC 写了 XSD 不认的根 = 规范与 schema 对不上。确有据可查、判为不改的分歧登记在
[`tools/spec-xsd-bydesign.tsv`](tools/spec-xsd-bydesign.tsv)（理由必填）。
本轮的对账结论与逐条裁定见 [`docs/design/xsd-spec-parity.md`](docs/design/xsd-spec-parity.md)。

## 贡献

语言变更先落为规范修订：一处改动同时涉及 `SPEC.md`、它蕴含的 XSD 变更，以及
至少一份演示该语法的示例。拼写单轨——同一语义只有一种写法，其余写法一律报错，
不做静默兼容。

新增一个语法点的完整工序（缺一步闸门会替你抓住）：

1. `SPEC.md` 落条文（带编号，示例要能引用它）；
2. `xsd/*.xsd` 落声明；
3. 至少一份示例演示**合法写法**（头注指名 SPEC 条文）；被拒的写法补负例并登记
   [`tools/negatives.tsv`](tools/negatives.tsv)；
4. `make check` 全绿；元素/属性覆盖闸若报「声明了没示例」，在对应台账登记或补示例。

## 许可

MIT，详见 [`LICENSE.md`](LICENSE.md)。

# 语言规范开发手册

> 适用：改 `SPEC.md`、`xsd/`、`L0`–`L9` / `T-tasks` / `X-use` 示例。
> 最后核对：2026-10-30（v1.3.3）。

## 1. 环境

- Python ≥ 3.10。
- `make check` 的示例门需要 `xmlschema`：
  `python3 -m venv .venv && .venv/bin/pip install xmlschema`。
- 可选：任意 XSD 校验器（`xmllint` 等）。
- 引擎 `esml`（只在跨仓冒烟时需要，不参与本仓门）。

## 2. 目录

| 路径 | 内容 |
|---|---|
| `SPEC.md` | 语言规范主文 |
| `xsd/esml-v1.xsd` | 入口 schema（根矩阵入口） |
| `xsd/esml-canonical-*.xsd` | canonical 分层 schema |
| `L0`–`L9` | 分层示例（类型/表达式/离散/模型/端口/实例/连接/分区/函数/方法调度） |
| `T-tasks` | 计算任务示例 |
| `X-use` | 库引用示例 |
| `docs/validate_roots.py` | 根矩阵对账 |
| `docs/validate_examples.py` | 规范 ⇄ 示例五道检查 |
| `tools/check-examples.py` | 逐件双 schema 校验 + 负例登记 |
| `tools/negatives.tsv` | 刻意负例及红在哪一层 |

## 3. 改 schema 的顺序

1. 改 `xsd/` 与 `SPEC.md`（两者必须同批）；
2. `python3 docs/validate_roots.py sync` 重生成入口层注释里的根矩阵清单；
3. `make check`；
4. 改/加示例；每件都要过双 schema；
5. 若新增负例，登记 `tools/negatives.tsv` 并写明 `schema` / `semantic` 层。

## 4. 校验命令

```sh
make check                                  # 根矩阵 + 示例，任一红即非零
make roots                                  # 只跑根矩阵
make examples                               # 只跑示例
make selftest                               # 根矩阵好例/坏例自证
.venv/bin/python tools/check-examples.py --self-test
```

示例的引擎冒烟（跨仓，不在本仓门内）：

```sh
esml check L0-type-unit/type-unit.esml
esml simulate path/to/example.esml -L path/to/library
```

文件名含 `probe` 或头部注明负例的文档**预期失败**；非零退出是正确结果。

## 5. 写作约定

- 文档扩展名 `.esml`；作者标识符 `[A-Za-z_][A-Za-z0-9_]*`，禁止 `__`。
- 实例路径用 `.`；元素/属性用 canonical 拼写，旧拼写在解析期响亮拒绝。
- 规范里不写实现细节（crate 名、函数名）；实现映射留给引擎文档。
- 改语言语义必须同时给：规范条文、XSD、至少一个好例、一个负例。

## 6. 提交与发版

1. 提交只含本仓改动；不把引擎/书仓文件带进来；
2. 跑 `make check` + `tools/check-examples.py --self-test`；
3. 发版：更新版本说明 → 打 annotated tag `vX.Y.Z` → 推 `ai4energy`；
4. 通知引擎仓 bump 子模块指针（见部署手册）。

## 7. 常见问题

| 症状 | 处理 |
|---|---|
| 根矩阵红 | 入口 XSD 的根集合与 canonical 不一致；先 `sync` 再人工核对 |
| 示例门红但 XSD 合法 | 看 `validate_examples.py` 的五道检查；可能是路径/章节引用/稀有元素 |
| 负例突然变绿 | 判据退化，不是件变好；补 XSD 或改负例层 |
| 引擎不认新元素 | 引擎子模块指针未 bump，或 canonical XSD 未同步 |

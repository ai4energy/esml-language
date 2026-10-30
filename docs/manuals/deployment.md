# 语言规范部署手册

> 适用：发布规范版本、发布 XSD/示例、给引擎仓 bump 子模块。
> 最后核对：2026-10-30（v1.3.3）。

## 1. 产物

本仓没有运行时服务；“部署”指发布以下不可变产物：

| 产物 | 路径 | 消费者 |
|---|---|---|
| 语言规范 | `SPEC.md`（网页/PDF 由站点构建） | 人、引擎文档、书系 |
| 入口 XSD | `xsd/esml-v1.xsd` | 引擎、编辑器、第三方工具 |
| canonical XSD | `xsd/esml-canonical-*.xsd` | 引擎/库/书仓的机验 |
| 示例与负例 | `L*/`、`T-tasks/`、`X-use/`、`tools/negatives.tsv` | 引擎 G16 语料、书系示例 |

## 2. 发版前检查

```sh
make check
.venv/bin/python tools/check-examples.py --self-test
git status --short          # 只应含本仓改动
```

- 入口层注释里的根清单必须是 `validate_roots.py sync` 生成的，不手工改；
- `SPEC.md` 与 XSD 同版；示例与规范同版；
- 新负例已登记并说明红在哪一层。

## 3. 打 tag

```sh
git tag -a vX.Y.Z -m "ESML language vX.Y.Z"
git push ai4energy main
git push ai4energy vX.Y.Z
```

版本号只增不改；破坏性语义变更走主版本，并在 `SPEC.md` 写明迁移。

## 4. 给引擎 bump 子模块

```sh
cd /path/to/esml-engine
git submodule update --remote examples/syntax   # 或手工 checkout 新 tag
git add examples/syntax
git commit -m "chore(syntax): bump language submodule to vX.Y.Z"
```

随后在引擎跑：

```sh
bash scripts/gate.sh
cargo test -p esml-engine --test conformance
```

## 5. 兼容性

| 变更 | 影响 |
|---|---|
| 新增元素/属性 | 引擎需实现后才认；旧文档不受影响 |
| 收窄拼写 | 旧文档在解析期被拒；需 `esml migrate` 或逐条迁移 |
| 改 XSD 分层 | 引擎/库/书仓的四方闸门同时红；必须同批更新 |

发布后在 `docs/design/xsd-spec-parity.md` 与引擎兼容矩阵里登记版本与影响。

## 6. 回滚

- 规范/XSD 是文本产物：回滚 = 把 tag 指回上一版并重新 bump 引擎子模块；
- 已发布 tag 不删除、不重打；用新 patch 版本修正；
- 回滚后重跑 `make check` 与引擎 conformance。

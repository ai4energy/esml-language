# 语言规范运维手册

> 适用：维护规范/XSD/示例的持续一致性，处置版本漂移与门红。
> 最后核对：2026-10-30（v1.3.3）。

## 1. 日常巡检

```sh
make check
python3 docs/validate_roots.py selftest
.venv/bin/python tools/check-examples.py
```

三条都应退出 0。任何一条红都先修，不要先发版。

## 2. 关键判据

| 判据 | 位置 | 失败意味着 |
|---|---|---|
| 根矩阵 | `docs/validate_roots.py` | 入口根集合与 canonical 不一致 |
| 示例五检查 | `docs/validate_examples.py` | 规范与示例不同步 |
| 双 schema | `tools/check-examples.py` | 入口 lax 放过、canonical 拒收 |
| 负例登记 | `tools/negatives.tsv` | 判据退化/文件漂移 |

负例是**棘轮**：标 `schema` 的负例必须被 XSD 拒收；它变绿说明判据漏了。

## 3. 版本漂移

- 引擎仓的 `examples/syntax` 子模块指针必须等于本仓发布 tag；
- 检查：`git -C esml-engine submodule status examples/syntax`；
- 指针落后 ⇒ 引擎不认新元素；指针超前 ⇒ 引擎可能编译到未发布 schema。
- 漂移处置：先在本仓确认 tag/`make check`，再 bump 引擎子模块并跑引擎 gate。

## 4. 与引擎/库/书的联动

| 下游 | 消费方式 | 变更后要跑 |
|---|---|---|
| 引擎 | 子模块 + XSD | `scripts/gate.sh`、conformance |
| 库仓 | canonical XSD | G-L1/G-L2/G-L3/G-L4/G-L5 |
| 书仓 | 示例语法 + 规范 | G-B1 语料门、示例检查 |
| 编辑器 | XSD + 引擎能力探测 | 编辑器冒烟/兼容矩阵 |

改语言语义时，四端都要在同一个发布窗口内更新；不要只改本仓。

## 5. 故障处置

| 症状 | 处理 |
|---|---|
| `make check` 根矩阵红 | 先 `validate_roots.py sync`，再人工核对根清单 |
| 示例门报路径/章节引用 | 改示例或规范引用；不要关检查 |
| 负例变绿 | 补 XSD/校验；确认不是把负例误改成好例 |
| 引擎不认新元素 | 子模块指针未 bump 或引擎未实现；先查指针 |
| 下游库/书大面积红 | 多半是拼写收窄；给迁移说明，不要回退判据 |

## 6. 备份与恢复

- 本仓是文本 + git；备份 = 远端 tag 与镜像；
- 发布物不可变；恢复旧版用旧 tag，不修改历史；
- 规范网页/PDF 由站点仓构建，重建时以本仓 tag 为准。

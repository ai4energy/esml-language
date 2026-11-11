# 语言规范运维手册

> 适用：维护规范/XSD/示例的持续一致性，处置版本漂移与门红。
> 最后核对：2026-11-11（v1.3.3）。

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
| 跨仓 XSD 漂移闸 | `tools/check-engine-xsd-parity.py` + `tools/engine-drift.tsv` | 本仓 `xsd/` 与引擎仓 schema 有分歧且台账未裁决（缺引擎仓时跳过） |
| 元素覆盖双向闸 | `tools/check-element-coverage.py` + `tools/element-coverage.tsv` | XSD 元素声明 ⇄ 示例用法差集未闭合（台账没跟上） |
| 属性覆盖双向闸 | `tools/check-attr-coverage.py` + `tools/attr-coverage.tsv`（登记来源 `attr-acceptance.tsv`） | XSD 属性声明 ⇄ 示例用法差集未闭合 |
| 引擎 × 示例可运行性闸 | `tools/check-engine-examples.py` + `tools/engine-example-debt.tsv` | 非负例示例 `esml check` 有错且台账没登记 / 台账 errors 数与实测不符（缺引擎仓时跳过） |

五张台账（element-coverage / attr-coverage / attr-acceptance / engine-drift / engine-example-debt）
各管一件事、互不重叠；owner 语义（`W1`/`W3`/`W4` 警告不红 vs `engine-debt` 红）见 development.md 台账表。

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
| 跨仓 XSD 漂移闸红 | 本仓 `xsd/` 与引擎仓有分歧且 `engine-drift.tsv` 没裁决 ⇒ 补台账行写明依据；分歧已消解决策可删该行（不炸）。缺引擎仓时本闸打印「跳过」不算红 |
| 元素/属性覆盖闸红 | 台账没跟上当天差集 ⇒ 当场重算差集，补行（pending / by-design）或把已消解的行删掉；`covered` 行必须指向 attr-acceptance 已有行，别重复建 |
| 引擎可运行性闸红 | 某非负例 `esml check` 有错而台账没登记 ⇒ 补 `engine-example-debt.tsv` 行（owner `engine-debt`、errors 数写实测值）；台账 errors 数与实测不符 ⇒ 引擎或示例变了，台账没跟上，重跑更新；缺引擎仓时本闸打印「跳过」不算红 |

## 6. 备份与恢复

- 本仓是文本 + git；备份 = 远端 tag 与镜像；
- 发布物不可变；恢复旧版用旧 tag，不修改历史；
- 规范网页/PDF 由站点仓构建，重建时以本仓 tag 为准。

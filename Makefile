# 仓内闸门（gate）：八道常驻机判。
#
#   make check            八道都跑，任一失败即非零退出
#   make roots            只跑根矩阵对账（仅标准库，无外部依赖）
#   make examples         只跑示例 ⇄ 规范对账（需要 xmlschema）
#   make selftest         根矩阵的自证（好例 / 坏例）
#   make strict           只跑示例 ⇄ 规范的撤通配判别力闸（--strict，需 xmlschema）
#   make elements         只跑元素覆盖双向闸（仅标准库）
#   make drift            只跑跨仓 XSD 漂移闸（本仓 xsd/ ⇄ 引擎仓 schema/；
#                         缺引擎仓时打印「跳过（引擎仓不在）」并以退出码 0 结束）
#   make attr             只跑属性覆盖双向闸（仅标准库）
#   make engine-examples  只跑引擎×示例可运行性台账闸（需引擎二进制；
#                         缺引擎仓时打印「跳过（引擎仓不在）」并以退出码 0 结束）
#   make spec-elements    只跑 XSD 声明元素 ⇄ SPEC 正文点名闸（仅标准库）
#   make expectations     只跑示例「期望值」台账闸（需引擎二进制；
#                         缺引擎仓时打印「跳过（引擎仓不在）」并以退出码 0 结束）
#
# 八道 `make check` 的固定次序（任一失败即非零退出）：
#   ① roots          → docs/validate_roots.py          （标准库）
#   ② examples       → docs/validate_examples.py       （xmlschema）
#   ③ drift          → tools/check-engine-xsd-parity.py（引擎仓 schema/；缺仓跳过）
#   ④ elements       → tools/check-element-coverage.py （标准库）
#   ⑤ attr           → tools/check-attr-coverage.py    （标准库）
#   ⑥ engine-examples→ tools/check-engine-examples.py  （引擎二进制；缺仓跳过）
#   ⑦ spec-elements→ tools/check-spec-element-coverage.py（标准库）
#   ⑧ expectations   → tools/check-example-expectations.py（引擎二进制；缺仓跳过）
#
# 缺引擎仓时 ③ 与 ⑥ 打印跳过并退出 0，不误红。
#
# 改完 schema 后先 `python3 docs/validate_roots.py sync` 重生成入口层注释里的
# 根矩阵清单，再 `make check`。

PY ?= python3

.PHONY: check roots examples selftest strict elements drift attr engine-examples spec-elements expectations

check:
	@rc=0; \
	$(PY) docs/validate_roots.py || rc=1; \
	$(PY) docs/validate_examples.py || rc=1; \
	$(PY) tools/check-engine-xsd-parity.py || rc=1; \
	$(PY) tools/check-element-coverage.py || rc=1; \
	$(PY) tools/check-attr-coverage.py || rc=1; \
	$(PY) tools/check-engine-examples.py || rc=1; \
	$(PY) tools/check-spec-element-coverage.py || rc=1; \
	$(PY) tools/check-example-expectations.py || rc=1; \
	if [ $$rc -ne 0 ]; then echo; echo "make check: 判红（见上）"; exit 1; fi; \
	echo; echo "make check: 全绿"

roots:
	$(PY) docs/validate_roots.py

examples:
	$(PY) docs/validate_examples.py

selftest:
	$(PY) docs/validate_roots.py selftest

strict:
	$(PY) docs/validate_examples.py --strict

elements:
	$(PY) tools/check-element-coverage.py

drift:
	$(PY) tools/check-engine-xsd-parity.py

attr:
	$(PY) tools/check-attr-coverage.py

engine-examples:
	$(PY) tools/check-engine-examples.py

spec-elements:
	$(PY) tools/check-spec-element-coverage.py

expectations:
	$(PY) tools/check-example-expectations.py

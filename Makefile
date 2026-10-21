# 仓内闸门（gate）：两道常驻机判。
#
#   make check     两道都跑，任一失败即非零退出
#   make roots     只跑根矩阵对账（仅标准库，无外部依赖）
#   make examples  只跑示例 ⇄ 规范对账（需要 xmlschema）
#   make selftest  根矩阵的自证（好例 / 坏例）
#
# 改完 schema 后先 `python3 docs/validate_roots.py sync` 重生成入口层注释里的
# 根矩阵清单，再 `make check`。

PY ?= python3

.PHONY: check roots examples selftest

check:
	@rc=0; \
	$(PY) docs/validate_roots.py || rc=1; \
	$(PY) docs/validate_examples.py || rc=1; \
	if [ $$rc -ne 0 ]; then echo; echo "make check: 判红（见上）"; exit 1; fi; \
	echo; echo "make check: 全绿"

roots:
	$(PY) docs/validate_roots.py

examples:
	$(PY) docs/validate_examples.py

selftest:
	$(PY) docs/validate_roots.py selftest

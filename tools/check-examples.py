#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ESML 规范仓 · 示例 × XSD 一致性门。

为什么要有这个脚本
------------------
`xsd/esml-v1.xsd` 是**入口** schema，但它的内容模型是
`<xs:any processContents="lax"/>` —— lax 的含义是「目标命名空间里**声明过**的元素按声明校验，
**没声明**的原样放过」。所以拿它当唯一判据，136 件示例全部通过，**一片假绿**：
历史上 `<connections>` 写成 `<connect>`、`<modelType>` 当成 `<description>` 这类拼写漂移，
它在入口 schema 下根本照单全收。

本脚本因此对每件示例跑**两道**校验：

  1. `xsd/esml-v1.xsd`            —— 入口（文档形态是不是 ESML）
  2. `xsd/esml-canonical-basic.xsd`（连带 include 的 common / compute）—— 逐元素真校验

第 2 道才是抓漂移的那道。`--vocab` 额外做**逐元素对账**：把示例里用到的元素名与 schema
里声明过的元素名摆在一起列出来，让「同一语义两种名」这种事没法藏在 lax 通配里。

负例（`tools/negatives.tsv`）
--------------------------
规范仓刻意留了一批负例，**它们必须红**。但负例红在哪一层必须写清：

  level=schema    必须被 XSD 拒收；XSD 收下它 ⇒ 判据漏了 ⇒ 红
  level=semantic  必须**通过** XSD（它红在求解层，不在拼写层）；
                  XSD 拒收它 ⇒ 我们把语义负例误判成拼写错 ⇒ 红

没有「未判定」：每件都要落进一层，否则下次复核又得重新猜。

自证（`--self-test`）
--------------------
一个「检查器」如果对任何东西都说 OK，它和没有检查器等价。所以本脚本自带 7 个构造样例
（3 好 4 坏，另加 1 条反向自检）证明它**真的会红**：好件必须判过、坏件必须判红，
任一翻转都算自证失败。

用法
----
    tools/check-examples.py              # 全仓；退出码 0 = 全绿
    tools/check-examples.py --vocab      # 附带逐元素对账表
    tools/check-examples.py --self-test  # 2 好 2 坏自证

依赖：lxml（XSD 校验器）。装法见 README 或 `python3 -m venv .venv && .venv/bin/pip install lxml`。
xmllint 若可用，`--xmllint` 会改用它并保持同样的判据口径。

已知盲区（别把它当没这回事）
--------------------------
`<esml>` 根上挂着 `<xs:anyAttribute processContents="lax"/>` ⇒ **根属性拼错永远抓不到**
（`coordinatee="x"` 也能过）。本门只管元素名与结构，管不到根属性。要收紧根属性得单独一轮：
先给 `coordinate`/`version` 等在用的属性补声明，再摘掉通配。本脚本不假装覆盖它。
"""

import argparse
import collections
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
XSD_DIR = REPO / "xsd"
ENTRY_SCHEMA = XSD_DIR / "esml-v1.xsd"
CANONICAL_SCHEMA = XSD_DIR / "esml-canonical-basic.xsd"
COMPUTE_SCHEMA = XSD_DIR / "esml-canonical-compute.xsd"
PROJECT_SCHEMA = XSD_DIR / "esml-canonical-project.xsd"
NEGATIVES_TSV = Path(__file__).resolve().parent / "negatives.tsv"
ESML_GLOB = "*.esml"

# 校验顺序：`<esml>` 文档走 canonical-basic（它 include 了 common + compute）；
# 其它根各自走对应 schema。判据是「根元素属于哪个 schema 的全局元素集」，
# 不是「哪个 schema 报错信息好看」。
ROOT_OWNER = [
    ("esml", CANONICAL_SCHEMA),
    ("units", CANONICAL_SCHEMA),
    ("variableTypes", CANONICAL_SCHEMA),
    ("portTypes", CANONICAL_SCHEMA),
    ("modelTypes", CANONICAL_SCHEMA),
    ("systems", CANONICAL_SCHEMA),
    ("system", CANONICAL_SCHEMA),
    ("orderedSet", CANONICAL_SCHEMA),
    ("metadata", CANONICAL_SCHEMA),
    ("computeTasks", COMPUTE_SCHEMA),
    ("project", PROJECT_SCHEMA),
]

COMMENTS = re.compile(r"<!--.*?-->", re.S)


# --------------------------------------------------------------------------- 工具后端
def _load_backend(prefer_xmllint):
    """返回 (validate_fn, 后端名)。validate_fn(path, schema_path) -> (ok, 首条错误)。"""
    if prefer_xmllint:
        exe = _which("xmllint")
        if exe:
            return _xmllint_backend(exe), f"xmllint({exe})"
    try:
        from lxml import etree
    except ImportError:
        sys.exit(
            "[check-examples] 需要 lxml。装：python3 -m venv .venv && .venv/bin/pip install lxml\n"
            "               或装 xmllint 后加 --xmllint。"
        )
    return _lxml_backend(etree), "lxml"


def _which(name):
    from shutil import which

    return which(name)


def _lxml_backend(etree):
    cache = {}

    def validate(path, schema_path):
        key = str(schema_path)
        if key not in cache:
            cache[key] = etree.XMLSchema(etree.parse(key))
        schema = cache[key]
        try:
            doc = etree.parse(str(path))
        except etree.XMLSyntaxError as e:
            return False, f"XML 解析失败: {e}"
        ok = schema.validate(doc)
        if ok:
            return True, ""
        err = schema.error_log.last_error
        return False, f"{err.line}:{err.column}: {err.message}"

    return validate


def _xmllint_backend(exe):
    def validate(path, schema_path):
        p = subprocess.run(
            [exe, "--noout", "--schema", str(schema_path), str(path)],
            capture_output=True,
            text=True,
        )
        if p.returncode == 0:
            return True, ""
        lines = [l for l in (p.stderr or "").splitlines() if l.strip() and ".esml" in l]
        return False, lines[0].strip() if lines else (p.stderr or "").strip().splitlines()[-1]

    return validate


# --------------------------------------------------------------------------- 语料
def esml_files():
    out = []
    for p in sorted(REPO.rglob(ESML_GLOB)):
        if ".git" in p.parts or p.parts[0] == "tools":
            continue
        out.append(p)
    return out


def root_tag(path):
    """读根元素名（先剥注释，免得头部示例把正则喂偏）。"""
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = COMMENTS.sub("", raw)
    m = re.search(r"<([A-Za-z_][\w.\-]*)", raw)
    return m.group(1) if m else None


def schema_for_root(root):
    for name, sch in ROOT_OWNER:
        if name == root:
            return sch
    return None


def load_negatives():
    """→ (path -> (level, reason))。清单里每行都必须有三列且 level 合法。"""
    table = {}
    for lineno, line in enumerate(NEGATIVES_TSV.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            sys.exit(f"[check-examples] {NEGATIVES_TSV.name}:{lineno} 必须 3 列（path/level/reason）")
        path, level, reason = parts
        if level not in ("schema", "semantic"):
            sys.exit(
                f"[check-examples] {NEGATIVES_TSV.name}:{lineno} level={level!r} 非法："
                "只许 schema / semantic（「未判定」不是合法状态）"
            )
        if not reason.strip():
            sys.exit(f"[check-examples] {NEGATIVES_TSV.name}:{lineno} reason 为空 —— 没写清它红在哪一层")
        table[path] = (level, reason)
    return table


# --------------------------------------------------------------------------- 逐元素对账
def declared_elements():
    """schema 里声明过的全部元素名（含嵌套的局部元素声明与 ref）。"""
    names = set()
    for f in sorted(XSD_DIR.glob("*.xsd")):
        text = f.read_text(encoding="utf-8")
        for m in re.finditer(r"<xs:element\s+(?:name|ref)=\"([^\"]+)\"", text):
            names.add(m.group(1))
    return names


def used_elements():
    """示例里真正用到的元素名（剥注释后按标签扫）→ 名字 -> {相对路径}。"""
    used = collections.defaultdict(set)
    for p in esml_files():
        raw = COMMENTS.sub("", p.read_text(encoding="utf-8", errors="replace"))
        for m in re.finditer(r"<([A-Za-z_][\w.\-]*)", raw):
            used[m.group(1)].add(str(p.relative_to(REPO)))
    return used


def global_roots(schema_path):
    from xml.etree import ElementTree as ET

    XS = "{http://www.w3.org/2001/XMLSchema}"
    root = ET.parse(schema_path).getroot()
    return [e.get("name") for e in root.findall(f"{XS}element")]


def vocab_report(stream):
    """逐元素对账：入口 schema 与 canonical 的全局元素集必须一致。"""
    declared = declared_elements()
    used = used_elements()
    canon = set(global_roots(CANONICAL_SCHEMA)) | set(global_roots(COMPUTE_SCHEMA)) | set(
        global_roots(PROJECT_SCHEMA)
    )
    entry = set(global_roots(ENTRY_SCHEMA))

    w = stream.write
    w("\n[vocab] 入口 schema 与 canonical 的全局元素对账\n")
    only_entry = sorted(entry - canon)
    only_canon = sorted(canon - entry)
    w(f"  canonical 全局元素 {len(canon):2}: {' '.join(sorted(canon))}\n")
    w(f"  入口   schema 全局元素 {len(entry):2}: {' '.join(sorted(entry))}\n")
    w(f"  只在入口、canonical 没有：{len(only_entry)} → {' '.join(only_entry) or '（无）'}\n")
    w(f"  只在 canonical、入口没有：{len(only_canon)} → {' '.join(only_canon) or '（无）'}\n")

    w("\n[vocab] 示例用到但 schema 未声明的元素名\n")
    w("  （多数落在**设计上的 lax 通配**里 —— 元数据/域类型 wrapper/方法表/枚举容器等；\n")
    w("    这不是漂移，是那些容器刻意开放的。真正要盯的是「入口 schema 收了 canonical 没有的名字」。）\n")
    undeclared = sorted(n for n in used if n not in declared)
    if not undeclared:
        w("  （无）\n")
    for n in undeclared:
        files = sorted(used[n])
        w(f"  {n:24} {len(files):2} 件   例：{files[0]}\n")
    return only_entry, only_canon


# --------------------------------------------------------------------------- 自证
GOOD = {
    "good-connect.esml": """<?xml version="1.0"?>
<esml xmlns="https://www.ai4energy.cn/esml/v1" name="SELF_OK">
  <variableTypes><type name="real" unit="1" default="0.0" role="algebraic"/></variableTypes>
  <modelTypes><modelType name="M" discipline="generic">
    <variables><variable name="y" type="real" role="algebraic"/></variables>
    <equations><equation>y = 1.0</equation></equations>
  </modelType></modelTypes>
  <systems><system name="S">
    <instances><instance name="m" type="M"/></instances>
    <schedule><sequence><continueFor time="0"/></sequence></schedule>
  </system></systems>
</esml>
""",
    "good-connect-esml-v1.esml": """<?xml version="1.0"?>
<esml xmlns="https://www.ai4energy.cn/esml/v1" schema="esml/v1" name="SELF_ENTRY">
  <variableTypes><type name="real" unit="1" default="0.0" role="algebraic"/></variableTypes>
</esml>
""",
}
BAD = {
    # 坏例 1：legacy <connect> —— 入口 schema 会放过（lax），canonical 必须拒收。
    #         这正是本脚本存在的理由：只跑入口 schema 的话它是绿的。
    "bad-legacy-connect.esml": """<?xml version="1.0"?>
<esml xmlns="https://www.ai4energy.cn/esml/v1" name="SELF_BAD1">
  <systems><system name="S">
    <connect from="a.p" to="b.p"/>
    <schedule><sequence><continueFor time="0"/></sequence></schedule>
  </system></systems>
</esml>
""",
    # 坏例 2：<body> 与 <derivative> 并存 —— 违反 xs:choice maxOccurs="1"。
    "bad-body-plus-derivative.esml": """<?xml version="1.0"?>
<esml xmlns="https://www.ai4energy.cn/esml/v1" name="SELF_BAD2">
  <functions><function name="sq">
    <inputs><input name="x"/></inputs>
    <outputs><output name="y"/></outputs>
    <body>x * x</body>
    <derivative mode="analytic"><partial wrt="x">2.0 * x</partial></derivative>
  </function></functions>
</esml>
""",
    # 坏例 3：kebab-case 容器 `<model-types>` —— SPEC §2 明写「kebab-case 不是合法语法」，
    #         入口 schema 照样放过（lax），canonical 必须拒收。
    "bad-kebab-container.esml": """<?xml version="1.0"?>
<esml xmlns="https://www.ai4energy.cn/esml/v1" name="SELF_BAD3">
  <model-types>
    <modelType name="M" discipline="generic">
      <variables><variable name="y" type="real" role="algebraic"/></variables>
      <equations><equation>y = 1.0</equation></equations>
    </modelType>
  </model-types>
</esml>
""",
    # 坏例 4：文档根本身不是合法 ESML 根。
    "bad-root.esml": """<?xml version="1.0"?>
<not-esml-at-all xmlns="https://www.ai4energy.cn/esml/v1" name="SELF_BAD4"/>
""",
}


def self_test(validate, stream):
    """2 好 2 坏：好件必须判过，坏件必须判红。任一翻转 = 自证失败。"""
    import tempfile

    w = stream.write
    results = []
    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        for name, text in sorted(GOOD.items()):
            p = tdir / name
            p.write_text(text, encoding="utf-8")
            ok, err = validate(p, CANONICAL_SCHEMA)
            results.append((name, True, ok, err))
        for name, text in sorted(BAD.items()):
            p = tdir / name
            p.write_text(text, encoding="utf-8")
            ok, err = validate(p, CANONICAL_SCHEMA)
            results.append((name, False, ok, err))

    w("[self-test] 构造样例 3 好 4 坏 + 1 反向自检 —— 证明本检查器真的会红\n")
    failures = 0
    for name, should_pass, ok, err in results:
        verdict = "PASS" if ok == should_pass else "BROKEN"
        if ok != should_pass:
            failures += 1
        want = "应收下" if should_pass else "应拒收"
        got = "收下了" if ok else f"拒收了（{err[:78]}）"
        w(f"  [{verdict}] {name:32} {want} → 实际{got}\n")

    # 反向自检：入口 schema 至少要放过一个坏例，否则说明 canonical 那道根本没在起作用。
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "bad-legacy-connect-entry.esml"
        p.write_text(BAD["bad-legacy-connect.esml"], encoding="utf-8")
        entry_ok, _ = validate(p, ENTRY_SCHEMA)
    if entry_ok:
        w("  [PASS] 反向自检：入口 schema 放过 legacy <connect>（lax 的本性）"
          "⇒ 只跑入口 schema 会假绿，两道校验缺一不可\n")
    else:
        w("  [BROKEN] 反向自检：入口 schema 竟拒收了 legacy <connect> —— "
          "反向自检样例失效，请检查 XSD 是否被改成了严格模式\n")
        failures += 1

    return failures


# --------------------------------------------------------------------------- 主流程
def main(argv=None):
    ap = argparse.ArgumentParser(description="ESML 示例 × XSD 一致性门")
    ap.add_argument("--vocab", action="store_true", help="附带逐元素对账表")
    ap.add_argument("--self-test", action="store_true", help="只跑 2 好 2 坏自证")
    ap.add_argument("--xmllint", action="store_true", help="优先用 xmllint（缺 lxml 时）")
    ap.add_argument("--quiet", action="store_true", help="只报红项")
    args = ap.parse_args(argv)

    validate, backend = _load_backend(args.xmllint)

    if args.self_test:
        bad = self_test(validate, sys.stdout)
        if bad:
            print(f"[self-test] {bad} 项自证失败 —— 检查器本身不可信")
            return 1
        print("[self-test] 全部成立")
        return 0

    negatives = load_negatives()
    files = esml_files()
    red = []
    checked = collections.Counter()

    for p in files:
        rel = str(p.relative_to(REPO))
        # 清单里标 level=schema 的负例**本来就该被拒收**，不进 pass 侧的红项；
        # 它们在下面的负例判定里单独核对（XSD 收下它们才红）。
        if negatives.get(rel, ("", ""))[0] == "schema":
            checked["expected-fail"] += 1
            continue
        root = root_tag(p)
        sch = schema_for_root(root)
        entry_ok, entry_err = validate(p, ENTRY_SCHEMA)
        checked["entry"] += 1
        if not entry_ok:
            red.append((rel, "entry", entry_err))
        if sch is None:
            red.append((rel, "canonical", f"根 <{root}> 不在任何 schema 的全局元素集里"))
            continue
        ok, err = validate(p, sch)
        checked["canonical"] += 1
        if not ok:
            red.append((rel, "canonical", err))

    # ---- 负例判定 ----
    seen = set()
    for rel, (level, reason) in sorted(negatives.items()):
        seen.add(rel)
        p = REPO / rel
        if not p.exists():
            red.append((rel, "manifest", "清单列了它，文件却不在（悬空）"))
            continue
        ok, err = validate(p, CANONICAL_SCHEMA)
        if level == "schema" and ok:
            red.append((rel, "manifest", f"标 level=schema（{reason}），XSD 却收下了 ⇒ 判据漏了"))
        elif level == "semantic" and not ok:
            red.append((rel, "manifest", f"标 level=semantic（{reason}），XSD 却拒收了：{err}"))

    # ---- 未登记的自述负例：文件头自称负例却不在清单里 = 未判定 ----
    for p in files:
        rel = str(p.relative_to(REPO))
        if rel in seen:
            continue
        raw_head = p.read_text(encoding="utf-8", errors="replace")[:4000]
        if re.search(r"负例|预期失败|预期报错", raw_head):
            red.append((rel, "manifest", "文件头自称负例，却不在 tools/negatives.tsv 里（「未判定」不合法）"))

    # ---- 汇总 ----
    if not args.quiet:
        for rel, where, msg in red:
            print(f"  RED  {rel} [{where}] {msg}")

    n_pass_schema = checked["canonical"] - sum(1 for r in red if r[1] == "canonical")
    print(
        f"[check-examples] 后端 {backend} · 示例 {len(files)} 件 · "
        f"入口 {checked['entry'] - sum(1 for r in red if r[1] == 'entry')}/{checked['entry']} 通过 · "
        f"canonical {n_pass_schema}/{checked['canonical']} 通过 · "
        f"预期拒收 {checked['expected-fail']} 件（负例清单标 schema，必须红） · "
        f"负例清单 {len(negatives)} 件（schema "
        f"{sum(1 for v in negatives.values() if v[0] == 'schema')} / semantic "
        f"{sum(1 for v in negatives.values() if v[0] == 'semantic')}） · 违规 {len(red)}"
    )

    if args.vocab:
        vocab_report(sys.stdout)

    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())

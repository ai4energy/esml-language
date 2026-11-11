#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ESML 规范仓 · XSD 元素覆盖双向闸门（W24）。

台账：tools/element-coverage.tsv
   kind  item  verdict  owner  evidence
   kind  值域：element  （方向 A：XSD 声明了、示例没用）
            example  （方向 B：示例用了、XSD 没命名声明）
   verdict 值域：has-example / pending / by-design
   owner  值域：W1 / W3 / W4 / engine-debt
   （有示例的元素**不必登记** ⇒ has-example 行只用来记「已落地」，方向 A 缺示例的元素
     才需要 pending / by-design 行；首版台账如实登记 2026-11-11 当场重算出的差集。）

门做什么（每一条都能机械复核，与属性面 check-attr-acceptance.py 同形）：
  1. **头部计数当场重算**：台账头部「共 N 行」「pending：N 行」必须等于正文实际 ⇒
     对不上就红（rc=1），照抄属性闸的 `check_counts`。
  2. **方向 A（声明 → 示例）**：`xsd/*.xsd` 里每一个**命名** `xs:element`（含嵌套
     局部声明，同名去重）必须在 `**/*.esml`（跳过注释、跳过 `tools/negatives.tsv`
     里**所有**负例——负例本就只用于演示拼写漂移，不算「示例覆盖」）里至少被用一次；
     没有 ⇒ 台账必须有一行 `element/<name>` 且 verdict ∈ {pending, by-design}：
       verdict=pending 且 owner ∈ {W1,W3,W4} ⇒ **警告**（追债中，落地前不红）；
       verdict=by-design ⇒ **警告**（owner 裁决刻意无示例，evidence 写清依据）；
       pending 且 owner=engine-debt ⇒ **红**（必须落地却没登记债主）。
  3. **方向 B（示例 → 声明）**：每个**非负例**示例里用到的元素名，要么在 XSD 里
     命名声明，要么台账有一行 `example/<name>` 且 verdict=by-design（依据写清，
     如 `<metadata>` 子结构不固定 SPEC:65）。缺任一 ⇒ **红**（防「示例偷偷用
     canonical 里没有的东西」）。pending 行**不能**当方向 B 的豁免 —— 用了就是用了，
     要么补声明要么 by-design，不许拿「在办」搪塞。
  4. **台账行与实测差集必须闭合**：台账里登记的每个 name，必须真的落在当天重算的
     差集里（方向 A 的 `element` 行必须「声明且无示例」，方向 B 的 `example` 行必须
     「示例用且未声明」）；反过来差集里的每个 name 也必须有台账行兜着 —— 差集变了
     （补了示例 / 补了声明）台账没跟着改 ⇒ 红。这是「首版台账如实登记」的机判锁。
  5. **`--self-test`**：临时目录造两棵小树——好树（声明元素都有示例、示例都在声明
     内）⇒ 零违规；坏树（故意删一个示例 / 加一个未声明元素）⇒ 必须红。任一翻转 =
     自证失败 ⇒ rc=2。照抄 `check-attr-acceptance.py` 的 `self_test` 结构。
  6. 脚本自身错误（缺表、列数不对、evidence 为空、name 缺尖括号）⇒ rc=2。

用法
----
    tools/check-element-coverage.py              # 双向覆盖 + 台账对账；0 = 零红
    tools/check-element-coverage.py --self-test  # 自证闸门（好树零违规、坏树判红）

依赖：仅标准库（`re` / `glob` / `argparse` / `tempfile`）—— 不需要 lxml / xmlschema
（元素名抽取用正则按标签扫，与 check-examples.py 同口径，故无 venv 也能跑）。
"""

import argparse
import glob
import os
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TSV = Path(__file__).resolve().parent / "element-coverage.tsv"
XSD_GLOB = "xsd/*.xsd"
NEGATIVES_TSV = Path(__file__).resolve().parent / "negatives.tsv"

KINDS = ("element", "example")
VERDICTS = ("has-example", "pending", "by-design")
OWNERS = ("W1", "W3", "W4", "engine-debt")
# 方向 A：pending 且 owner ∈ 这个集合 ⇒ 追债中，警告不红。
WARN_OWNERS = frozenset(("W1", "W3", "W4"))

TAG = re.compile(r"<([A-Za-z_][\w.\-]*)")
COMMENT = re.compile(r"<!--.*?-->", re.S)
DECL_NAME = re.compile(r"<xs:element\s+name=\"([^\"]+)\"")


# --------------------------------------------------------------------------- 台账
def load_tsv(path):
    """→ (rows, declared_total, declared_pending)。

    rows: [{lineno, kind, item, verdict, owner, evidence}]
    头部两行是计数锚：「共 N 行」「pending：N 行」，正文行数对不上 ⇒ 红（check_counts）。
    """
    rows, total, pending = [], None, None
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("#"):
            m = re.match(r"^#\s*共\s*(\d+)\s*行", line)
            if m:
                total = int(m.group(1))
            p = re.match(r"^#\s*pending：(\d+)\s*行", line)
            if p:
                pending = int(p.group(1))
            continue
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 5:
            sys.exit(f"[check-element-coverage] {path.name}:{lineno} 必须 5 列"
                     f"（kind item verdict owner evidence），实际 {len(parts)}")
        kind, item, verdict, owner, evidence = parts
        if not item.startswith("<") or not item.endswith(">"):
            sys.exit(f"[check-element-coverage] {path.name}:{lineno} item 必须带尖括号"
                     f"（<name>），实际 {item!r}")
        rows.append({"lineno": lineno, "kind": kind, "item": item,
                     "verdict": verdict, "owner": owner, "evidence": evidence})
    return rows, total, pending


def load_negatives(path):
    """→ 负例相对路径集合。负例判据照抄 check-examples.py：tools/negatives.tsv 每行第一列。

    方向 A / B 都**跳过所有负例**（schema + semantic）：它们存在是为了演示拼写漂移
    必须被拒收，不是「这个语法点有例子」的证据。component 只活在 schema 负例里 ⇒
    跳过后自然不在方向 B 差集（订单 W24 要求核实的点）。
    """
    out = set()
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 1 and parts[0].strip():
            out.add(parts[0])
    return out


# --------------------------------------------------------------------------- 语料
def strip_comment(text):
    """剥 XML 注释。注释里写的元素名不算「用了」（照抄 check-examples.py 口径）。"""
    return COMMENT.sub("", text)


def declared_elements(xsd_dir):
    """xsd_dir 下全部 *.xsd 里**命名**声明的元素名（含嵌套局部，同名去重）。

    只认 `xs:element name="…"`（声明），不认 `ref=`（引用别人的声明，名字已在别处计过）。
    注释剥掉，免得 schema 注释里的示例标签混进来。
    """
    names = set()
    for f in sorted(glob.glob(os.path.join(str(xsd_dir), "*.xsd"))):
        text = strip_comment(Path(f).read_text(encoding="utf-8"))
        for m in DECL_NAME.finditer(text):
            names.add(m.group(1))
    return names


def used_elements(repo, xsd_dir, negative_files, exclude_repo=None):
    """`**/*.esml`（跳过注释、跳过负例）里**非负例**示例真正用到的元素名集合。

    按标签正则扫（`<name` 后跟空白 / `/` / `>`），与 check-examples.py 的
    `used_elements` 同口径 —— 不需要解析 XML，故无 lxml 也能跑。
    """
    used = set()
    for f in glob.glob(os.path.join(str(repo), "**", "*.esml"), recursive=True):
        if "/.git/" in f:
            continue
        rel = os.path.relpath(f, repo)
        if rel in negative_files:
            continue
        text = strip_comment(Path(f).read_text(encoding="utf-8", errors="replace"))
        for m in TAG.finditer(text):
            used.add(m.group(1))
    return used


# --------------------------------------------------------------------------- 检查
def check_counts(declared, rows):
    """头部「共 N 行」「pending：N 行」必须等于正文实际。→ [(where, msg)]"""
    out = []
    if declared[0] is None:
        out.append((TSV.name, "头部没有写「共 N 行」⇒ 条数无从核对"))
    elif declared[0] != len(rows):
        out.append((TSV.name, f"头部写共 {declared[0]} 行，实际 {len(rows)} 行 ⇒ 台账写错就改台账"))
    actual_pending = sum(1 for r in rows if r["verdict"] == "pending")
    if declared[1] is None:
        out.append((TSV.name, "头部没有写「pending：N 行」⇒ pending 数无从核对"))
    elif declared[1] != actual_pending:
        out.append((TSV.name, f"头部写 pending：{declared[1]} 行，实际 {actual_pending} 行 ⇒ 台账写错就改台账"))
    return out


def check_rows(rows):
    """逐行：kind / verdict / owner 合法、item 有尖括号、evidence 非空。→ [(where, msg)]"""
    out = []
    for r in rows:
        where = f"{TSV.name}:{r['lineno']}"
        if r["kind"] not in KINDS:
            out.append((where, f"kind={r['kind']!r} 非法：只许 {' / '.join(KINDS)}"))
            continue
        if r["verdict"] not in VERDICTS:
            out.append((where, f"verdict={r['verdict']!r} 非法：只许 {' / '.join(VERDICTS)}"))
        if r["owner"] not in OWNERS:
            out.append((where, f"owner={r['owner']!r} 非法：只许 {' / '.join(OWNERS)}"))
        if not r["evidence"].strip():
            out.append((where, "evidence 为空 —— 每行都要写清它凭什么这么判"))
    return out


def _name(item):
    """`<esml>` -> `esml`。"""
    return item[1:-1]


def check_direction_a(rows, declared, used):
    """方向 A：声明了、示例没用（含负例里出现过的也不算数）。→ (red, warn, missing_names)

    missing_names = 当天重算的「声明且无示例」名集合（台账闭合校验用它）。
    """
    red, warn, missing = [], [], set()
    reg_a = {r["item"]: r for r in rows if r["kind"] == "element"}
    for n in sorted(declared - used):
        missing.add(n)
        r = reg_a.get(f"<{n}>")
        if r is None:
            red.append(("direction-A", f"<{n}> 声明了但任何（非负例）示例都没用，台账也没登记 —— 补示例或在台账记一行"))
            continue
        if r["verdict"] == "pending":
            if r["owner"] in WARN_OWNERS:
                warn.append((f"{TSV.name}:{r['lineno']}",
                             f"方向 A 待落地：<{n}> owner={r['owner']}（追债中，警告不红）"))
            else:
                red.append((f"{TSV.name}:{r['lineno']}",
                            f"方向 A：<{n}> verdict=pending owner={r['owner']} —— 必须落地却没记债主 ⇒ 红"))
        elif r["verdict"] == "by-design":
            warn.append((f"{TSV.name}:{r['lineno']}",
                         f"方向 A by-design：<{n}>（刻意无示例，{r['evidence'].strip()[:40]}）"))
        # has-example 行却落在差集里 ⇒ 台账与实测脱节，落到下面的闭合校验里红。
    return red, warn, missing


def check_direction_b(rows, declared, used):
    """方向 B：非负例示例用了、但 XSD 没命名声明。→ (red, warn, undecl_names)

    每一处都得有台账 `example/<n>` 行兜着；verdict 语义与方向 A 同形：
      by-design ⇒ 警告（owner 裁决刻意未声明，evidence 写清依据）；
      pending 且 owner∈{W1,W3,W4} ⇒ **警告**（W20 在办把 anyType 收成真声明，落地前不红）；
      pending 且 owner=engine-debt / has-example ⇒ **红**（用了就是用了，必须有裁决兜底）。
    """
    red, warn = [], []
    undecl = sorted(used - declared)
    reg_b = {r["item"]: r for r in rows if r["kind"] == "example"}
    for n in undecl:
        r = reg_b.get(f"<{n}>")
        if r is None:
            red.append(("direction-B", f"<{n}> 示例在用但 XSD 未命名声明，台账也没登记 —— 补声明或记 by-design"))
        elif r["verdict"] == "by-design":
            warn.append((f"{TSV.name}:{r['lineno']}",
                        f"方向 B by-design：<{n}>（刻意未声明，{r['evidence'].strip()[:40]}）"))
        elif r["verdict"] == "pending" and r["owner"] in WARN_OWNERS:
            warn.append((f"{TSV.name}:{r['lineno']}",
                        f"方向 B 待落地：<{n}> owner={r['owner']}（W20 在办收声明，警告不红）"))
        else:
            red.append((f"{TSV.name}:{r['lineno']}",
                        f"方向 B：<{n}> verdict={r['verdict']!r} owner={r['owner']} —— 用了就是用了，"
                        f"缺 by-design/在办裁决 ⇒ 红"))
    return red, warn, undecl


def check_ledger_closure(rows, missing_a, undecl_b):
    """台账与当天差集闭合：登记的 name 必须真在差集里；差集的 name 必须都有行兜着。

    补了示例/声明后差集会缩，台账不改 ⇒ 红（防止台账腐化成历史遗留）。
    """
    red = []
    reg_a = {r["item"]: r for r in rows if r["kind"] == "element"}
    reg_b = {r["item"]: r for r in rows if r["kind"] == "example"}
    for item, r in sorted(reg_a.items()):
        n = _name(item)
        if n not in missing_a:
            red.append((f"{TSV.name}:{r['lineno']}",
                        f"台账登记 <{n}>（方向 A）但当天它要么有示例、要么根本没声明 ⇒ 台账过时，删行或改 verdict"))
    for item, r in sorted(reg_b.items()):
        n = _name(item)
        if n not in undecl_b:
            red.append((f"{TSV.name}:{r['lineno']}",
                        f"台账登记 <{n}>（方向 B）但当天它要么已声明、要么示例没再用 ⇒ 台账过时，删行"))
    # 差集侧的「缺行」已在 check_direction_a/b 里红，这里不重复。
    return red


# --------------------------------------------------------------------------- 主检查
def run_gate(repo, tsv, xsd_dir, negative_files, stream):
    """对一棵树跑全套检查 → (red, warn)。repo/tsv/xsd_dir 都可指向合成树（自证用）。"""
    rows, total, pending = load_tsv(tsv)
    declared = declared_elements(xsd_dir)
    used = used_elements(repo, xsd_dir, negative_files)
    red, warn = [], []
    red += check_counts((total, pending), rows)
    red += check_rows(rows)
    ra, wa, missing_a = check_direction_a(rows, declared, used)
    red += ra
    warn += wa
    rb, wb, undecl_b = check_direction_b(rows, declared, used)
    red += rb
    warn += wb
    red += check_ledger_closure(rows, missing_a, undecl_b)
    return red, warn, (declared, used, missing_a, undecl_b)


# --------------------------------------------------------------------------- 自证
def self_test(stream):
    """临时目录造两棵小树：好树（声明元素都有示例、示例都在声明内）⇒ 零违规；
    坏树（删一个示例 + 加一个未声明元素、台账没跟上）⇒ 必须红。任一翻转 = 自证失败。"""
    w = stream.write
    failures = 0
    NEG = "N-neg/probe.esml"
    NEG_TSV = f"{NEG}\tschema\t负例占位（自证用）\n"
    DECL = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
            '<xs:element name="alpha"><xs:complexType/></xs:element>'
            '<xs:element name="beta"><xs:complexType/></xs:element></xs:schema>')

    def write_tree(tdir, xsd, esml, tsv_rows, neg=NEG_TSV):
        tdir.mkdir(parents=True, exist_ok=True)
        (tdir / "xsd").mkdir(parents=True, exist_ok=True)
        (tdir / "xsd" / "t.xsd").write_text(xsd, encoding="utf-8")
        for name, text in esml.items():
            p = tdir / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        (tdir / "negatives.tsv").write_text(neg, encoding="utf-8")
        (tdir / "element-coverage.tsv").write_text(tsv_rows, encoding="utf-8")
        return tdir / "element-coverage.tsv"

    def run_on(tree):
        return run_gate(tree, tree / "element-coverage.tsv", tree / "xsd", {NEG}, stream)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # —— 好树：alpha/beta 都有示例、示例都在声明内、台账空（有示例的元素不必登记）⇒ 零违规。
        good = write_tree(root / "good", DECL, {
            "g/a.esml": "<alpha><beta/></alpha>",
        },
            "# 共 0 行\n#\n# pending：0 行\n")
        # —— 坏树：删掉 beta 的示例（a.esml 里没有 <beta>），台账还写着 has-example，
        #         且示例里塞了个未声明的 <ghost> ⇒ 方向 A 闭合红 + 方向 B 红。
        bad = write_tree(root / "bad", DECL, {
            "g/a.esml": "<alpha><ghost/></alpha>",
        },
            "# 共 1 行\n#\n# pending：0 行\n"
            "element\t<beta>\thas-example\tW1\t（示例已删，台账没跟上）\n")

        for label, tree, want_red in (
                ("好树：声明元素都有示例、示例都在声明内", root / "good", False),
                ("坏树：删示例 + 加未声明元素，台账没跟上", root / "bad", True)):
            red, warn, _ = run_on(tree)
            ok = bool(red) == want_red
            w(f"  [{'PASS' if ok else 'BROKEN'}] {label} ⇒ 期望{'判红' if want_red else '零违规'}，"
              f"实际 {len(red)} 红 / {len(warn)} 警告\n")
            for where, msg in red:
                w(f"        {where}: {msg}\n")
            failures += 0 if ok else 1

        # —— 台账计数锚自证：「共 N 行」写错 ⇒ 必须红（check_counts 真在跑）。
        badcount = write_tree(root / "badcount", DECL, {"g/a.esml": "<alpha><beta/></alpha>"},
                              "# 共 5 行\n#\n# pending：0 行\n"
                              "element\t<beta>\thas-example\tW1\t示例已覆盖\n")
        red, _, _ = run_on(root / "badcount")
        ok = any("共 5 行" in msg or "实际 1 行" in msg for _, msg in red)
        w(f"  [{'PASS' if ok else 'BROKEN'}] 台账计数锚：头部「共 5 行」≠ 实际 1 行 ⇒ 期望判红，"
          f"实际 {len(red)} 红\n")
        failures += 0 if ok else 1

        # —— 方向 B by-design 自证：未声明元素若台账记了 by-design ⇒ 不红（豁免真生效）。
        goodby = write_tree(root / "goodby", DECL, {"g/a.esml": "<alpha><beta/><ghost/></alpha>"},
                             "# 共 1 行\n#\n# pending：0 行\n"
                             "example\t<ghost>\tby-design\tW3\t自证：宽松子结构，SPEC:65\n")
        red, _, _ = run_on(root / "goodby")
        ok = not red
        w(f"  [{'PASS' if ok else 'BROKEN'}] 方向 B by-design 豁免：未声明 <ghost> 已登记 by-design ⇒ "
          f"期望零违规，实际 {len(red)} 红\n")
        for where, msg in red:
            w(f"        {where}: {msg}\n")
        failures += 0 if ok else 1
    return failures


# --------------------------------------------------------------------------- 主流程
def main(argv=None):
    ap = argparse.ArgumentParser(description="ESML XSD 元素覆盖双向闸门（W24）")
    ap.add_argument("--self-test", action="store_true", help="自证闸门（好树零违规、坏树判红）")
    ap.add_argument("--quiet", action="store_true", help="只报红项")
    args = ap.parse_args(argv)

    if args.self_test:
        bad = self_test(sys.stdout)
        if bad:
            print(f"[check-element-coverage] {bad} 项自证失败 —— 闸门本身不可信", file=sys.stderr)
            return 2
        print("[check-element-coverage] 自证通过：好树零违规、坏树判红")
        return 0

    if not TSV.exists():
        print(f"[check-element-coverage] 缺表：{TSV} 不存在", file=sys.stderr)
        return 2
    negatives = load_negatives(NEGATIVES_TSV)
    red, warn, stats = run_gate(REPO, TSV, REPO / "xsd", negatives, sys.stdout)
    declared, used, missing_a, undecl_b = stats

    for where, msg in warn:
        print(f"  WARN {where} {msg}")
    if not args.quiet:
        for where, msg in red:
            print(f"  RED  {where} {msg}")

    rows, _, _ = load_tsv(TSV)
    n_pend = sum(1 for r in rows if r["verdict"] == "pending")
    n_bydes = sum(1 for r in rows if r["verdict"] == "by-design")
    print(f"[check-element-coverage] 声明 {len(declared)} 个命名元素 · 非负例示例用到 {len(used)} 个 · "
          f"方向 A 缺示例 {len(missing_a)} · 方向 B 未声明 {len(undecl_b)} · "
          f"台账 {len(rows)} 行（pending {n_pend} / by-design {n_bydes}）· "
          f"违规 {len(red)}（警告 {len(warn)}）")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())

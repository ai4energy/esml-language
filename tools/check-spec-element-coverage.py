#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ESML 规范仓 · XSD 声明元素/属性 ⇄ SPEC 正文点名闸门（W37 + W45）。

台账：tools/spec-element-coverage.tsv
   item       verdict  owner  evidence
   item 格式： 元素 <name>；属性 @name
   verdict 值域：named（已点名，不必登记）/ pending（要补 SPEC 条文）/
                by-design（刻意不写，依据必填）
   owner   值域：W1 / W2 / W3 / W4
   （SPEC 已点名的元素/属性**不必登记** ⇒ 台账只登记差集里的 pending / by-design 行。）

门做什么：
  1. **头部计数当场重算**：台账头部「共 N 行」「pending：N 行」必须等于正文实际 ⇒ 红（rc=1）。
  2. **方向 A（元素声明 → SPEC 点名）**：`xsd/*.xsd` 里每一个**命名** `xs:element`（含嵌套
     局部声明，同名去重）必须在 `SPEC.md` 正文里以 `<名字>` 或 `` `名字` `` 形式出现至少
     一次；没有 ⇒ 台账必须有一行 `<name>` 且 verdict ∈ {pending, by-design}：
       verdict=pending 且 owner ∈ {W1,W2,W3,W4} ⇒ **警告**（追债中，落地前不红）；
       verdict=by-design ⇒ **警告**（owner 裁决刻意不写，evidence 写清依据）。
     差集里无台账行 ⇒ **红**（「声明了 SPEC 没点名、也没人登记 ⇒ 漏了」）。
  3. **方向 B（属性声明 → SPEC 点名，W45）**：`xsd/*.xsd` 里每一个**命名** `xs:attribute`
     （同名去重）必须在 `SPEC.md` 正文里以词边界 `\bname\b` 形式出现至少一次；
     没有 ⇒ 台账必须有一行 `@name` 且 verdict ∈ {pending, by-design}（判据同方向 A）。
  4. **台账行与实测差集必须闭合**（元素 + 属性）：台账里登记的每个 name，必须真的落在
     当天重算的差集里；差集的每个 name 也必须有台账行兜着。差集变了（补了 SPEC 条文）
     台账没跟着改 ⇒ 红（「首版台账如实登记」的机判锁）。
  5. **`--self-test`**：临时目录造树——好树（所有声明元素+属性都在 SPEC 里点名）⇒
     零违规；坏树（SPEC 删掉一个 `<name>` 点名）⇒ 必须红；属性好树（`@gamma` 点名）⇒
     零违规；属性坏树（SPEC 删掉 `gamma` 点名）⇒ 必须红。任一翻转 = 自证失败 ⇒ rc=2。
  6. 脚本自身错误（缺表、列数不对、evidence 为空、item 格式不合法）⇒ rc=2。

用法
----
    tools/check-spec-element-coverage.py              # 方向 A + B 覆盖 + 台账对账；0 = 零红
    tools/check-spec-element-coverage.py --self-test  # 自证闸门（好树零违规、坏树判红）

依赖：仅标准库（`re` / `glob` / `argparse` / `tempfile` / `pathlib`）。
"""

import argparse
import glob
import os
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TSV = Path(__file__).resolve().parent / "spec-element-coverage.tsv"
XSD_GLOB = "xsd/*.xsd"
SPEC_PATH = REPO / "SPEC.md"

VERDICTS = ("named", "pending", "by-design")
OWNERS = ("W1", "W2", "W3", "W4")
WARN_OWNERS = frozenset(OWNERS)  # 所有 owner 的 pending 都警告不红（SPEC 条文追债中）

DECL_NAME  = re.compile(r'<xs:element\s+name="([^"]+)"')
DECL_ATTR  = re.compile(r'<xs:attribute\s+name="([^"]+)"')
COMMENT    = re.compile(r"<!--.*?-->", re.S)


# --------------------------------------------------------------------------- 台账
def load_tsv(path):
    """→ (rows, declared_total, declared_pending)

    rows: [{lineno, item, verdict, owner, evidence}]
    头部两行是计数锚：「共 N 行」「pending：N 行」。
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
        if len(parts) != 4:
            sys.exit(f"[check-spec-element-coverage] {path.name}:{lineno} 必须 4 列"
                     f"（element verdict owner evidence），实际 {len(parts)}")
        item, verdict, owner, evidence = parts
        if not (item.startswith("<") and item.endswith(">")) \
           and not (item.startswith("@") and len(item) > 1):
            sys.exit(f"[check-spec-element-coverage] {path.name}:{lineno} item 必须带尖括号"
                     f"（<name>，元素）或 @前缀（@name，属性），实际 {item!r}")
        rows.append({"lineno": lineno, "item": item, "verdict": verdict,
                     "owner": owner, "evidence": evidence})
    return rows, total, pending


# --------------------------------------------------------------------------- 语料
def strip_comment(text):
    return COMMENT.sub("", text)


def declared_elements(xsd_dir):
    """xsd_dir 下全部 *.xsd 里**命名**声明的元素名（含嵌套局部，同名去重）。"""
    names = set()
    for f in sorted(glob.glob(os.path.join(str(xsd_dir), "*.xsd"))):
        text = strip_comment(Path(f).read_text(encoding="utf-8"))
        for m in DECL_NAME.finditer(text):
            names.add(m.group(1))
    return names


def spec_named_elements(spec_path):
    """SPEC.md 里以 `<name>` 或 `` `name` `` 形式点名的元素名集合。"""
    spec = spec_path.read_text(encoding="utf-8")
    named = set()
    for m in re.finditer(r"<([A-Za-z_][\w.\-]*)(?=[\s/>])", spec):
        named.add(m.group(1))
    for m in re.finditer(r"`([A-Za-z_][\w.\-]*)`", spec):
        named.add(m.group(1))
    return named


def declared_attributes(xsd_dir):
    """xsd_dir 下全部 *.xsd 里**命名**声明的属性名（同名去重）。"""
    names = set()
    for f in sorted(glob.glob(os.path.join(str(xsd_dir), "*.xsd"))):
        text = strip_comment(Path(f).read_text(encoding="utf-8"))
        for m in DECL_ATTR.finditer(text):
            names.add(m.group(1))
    return names


def spec_named_attributes(spec_path):
    """SPEC.md 里以词边界形式点名的属性名集合（判据同元素：`\bname\b` 出现即算）。"""
    spec = spec_path.read_text(encoding="utf-8")
    # 用 spec_named_elements 的两种模式收集所有已点名 token，
    # 再与 declared_attributes 做交集；这里直接返回全 token 集合，
    # 由 check_direction_b 负责取差。
    tokens = set()
    for m in re.finditer(r"[A-Za-z_][\w.\-]*", spec):
        tokens.add(m.group(0))
    return tokens


def _name(item):
    """`<esml>` -> `esml`；`@phase` -> `phase`。"""
    if item.startswith("@"):
        return item[1:]
    return item[1:-1]


def _is_attr_item(item):
    """item 是否为属性行（@name 格式）。"""
    return item.startswith("@")


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
    """逐行：verdict / owner 合法、item 有尖括号、evidence 非空。→ [(where, msg)]"""
    out = []
    for r in rows:
        where = f"{TSV.name}:{r['lineno']}"
        if r["verdict"] not in VERDICTS:
            out.append((where, f"verdict={r['verdict']!r} 非法：只许 {' / '.join(VERDICTS)}"))
        if r["owner"] not in OWNERS:
            out.append((where, f"owner={r['owner']!r} 非法：只许 {' / '.join(OWNERS)}"))
        if not r["evidence"].strip():
            out.append((where, "evidence 为空 —— 每行都要写清它凭什么这么判"))
    return out


def check_direction_a(rows, declared, named):
    """方向 A：XSD 声明了、SPEC 没点名。→ (red, warn, missing_names)

    missing_names = 当天重算的「声明且 SPEC 未点名」名集合（台账闭合校验用它）。
    """
    red, warn, missing = [], [], set()
    reg = {r["item"]: r for r in rows}
    for n in sorted(declared - named):
        missing.add(n)
        r = reg.get(f"<{n}>")
        if r is None:
            red.append(("direction-A",
                         f"<{n}> XSD 声明了但 SPEC 正文没以 <name> 或 `name` 点名，台账也没登记"
                         f" —— 补 SPEC 条文或在台账记一行"))
            continue
        if r["verdict"] == "pending":
            if r["owner"] in WARN_OWNERS:
                warn.append((f"{TSV.name}:{r['lineno']}",
                             f"方向 A 待落地：<{n}> owner={r['owner']}（补 SPEC 条文中，警告不红）"))
            else:
                red.append((f"{TSV.name}:{r['lineno']}",
                            f"方向 A：<{n}> verdict=pending owner={r['owner']} —— 必须补 SPEC 却没记债主 ⇒ 红"))
        elif r["verdict"] == "by-design":
            warn.append((f"{TSV.name}:{r['lineno']}",
                         f"方向 A by-design：<{n}>（刻意不写 SPEC，{r['evidence'].strip()[:40]}）"))
    return red, warn, missing


def check_direction_b(rows, declared, named):
    """方向 B：XSD 属性声明了、SPEC 没点名。→ (red, warn, missing_names)

    missing_names = 当天重算的「声明且 SPEC 未点名」属性名集合。
    判据同方向 A：台账行以 @name 形式登记。
    """
    red, warn, missing = [], [], set()
    reg = {r["item"]: r for r in rows}
    for n in sorted(declared - named):
        missing.add(n)
        r = reg.get(f"@{n}")
        if r is None:
            red.append(("direction-B",
                         f"@{n} XSD 声明了但 SPEC 正文没点名，台账也没登记"
                         f" —— 补 SPEC 条文或在台账记一行"))
            continue
        if r["verdict"] == "pending":
            if r["owner"] in WARN_OWNERS:
                warn.append((f"{TSV.name}:{r['lineno']}",
                             f"方向 B 待落地：@{n} owner={r['owner']}（补 SPEC 条文中，警告不红）"))
            else:
                red.append((f"{TSV.name}:{r['lineno']}",
                            f"方向 B：@{n} verdict=pending owner={r['owner']} —— 必须补 SPEC 却没记债主 ⇒ 红"))
        elif r["verdict"] == "by-design":
            warn.append((f"{TSV.name}:{r['lineno']}",
                         f"方向 B by-design：@{n}（刻意不写 SPEC，{r['evidence'].strip()[:40]}）"))
    return red, warn, missing


def check_ledger_closure(rows, missing):
    """台账与当天差集闭合：登记的 name 必须真在差集里；差集的 name 必须都有行兜着。

    missing 可以是元素差集（方向 A）或属性差集（方向 B）；
    台账行里的 item 格式（<name> 或 @name）决定它属于哪个方向。
    """
    red = []
    reg = {r["item"]: r for r in rows}
    for item, r in sorted(reg.items()):
        n = _name(item)
        # 元素行只对照元素差集，属性行只对照属性差集
        # 调用者已把对应方向的差集传入
        if n not in missing:
            label = f"@{n}" if _is_attr_item(item) else f"<{n}>"
            red.append((f"{TSV.name}:{r['lineno']}",
                         f"台账登记 {label} 但当天 SPEC 已点名（或根本没声明）⇒ 台账过时，删行或改 verdict"))
    return red


# --------------------------------------------------------------------------- 主检查
def run_gate(repo, tsv, xsd_dir, spec_path, stream):
    """对一棵树跑全套检查 → (red, warn, stats)。

    stats = (declared_elements, named_elements, declared_attrs, named_attr_tokens,
             missing_a, missing_b)
    """
    rows, total, pending = load_tsv(tsv)
    declared_el = declared_elements(xsd_dir)
    named_el = spec_named_elements(spec_path)
    declared_at = declared_attributes(xsd_dir)
    named_at_tokens = spec_named_attributes(spec_path)
    # 属性差集：声明了但 SPEC 没以词边界点名的
    named_at = declared_at & named_at_tokens
    missing_b = declared_at - named_at

    red, warn = [], []
    red += check_counts((total, pending), rows)
    red += check_rows(rows)

    # 方向 A：元素
    ra, wa, missing_a = check_direction_a(rows, declared_el, named_el)
    red += ra
    warn += wa

    # 方向 B：属性
    rb, wb, _ = check_direction_b(rows, declared_at, named_at)
    red += rb
    warn += wb

    # 台账闭合：元素行对照元素差集，属性行对照属性差集
    el_rows = [r for r in rows if not _is_attr_item(r["item"])]
    at_rows = [r for r in rows if _is_attr_item(r["item"])]
    red += check_ledger_closure(el_rows, missing_a)
    red += check_ledger_closure(at_rows, missing_b)

    return red, warn, (declared_el, named_el, declared_at, named_at, missing_a, missing_b)


# --------------------------------------------------------------------------- 自证
def self_test(stream):
    """临时目录造两棵小树：好树（所有声明元素都在 SPEC 里点名）⇒ 零违规；
    坏树（SPEC 删掉一个 <name> 点名）⇒ 必须红。任一翻转 = 自证失败。"""
    w = stream.write
    failures = 0
    DECL = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
            '<xs:element name="alpha"><xs:complexType/></xs:element>'
            '<xs:element name="beta"><xs:complexType/'
            '  <xs:attribute name="gamma" type="xs:string"/>'
            '/></xs:element></xs:schema>')
    SPEC_GOOD = "这是规范正文。\n\n`alpha` 和 <beta> 都点名了，`gamma` 属性也点名了。\n"
    SPEC_BAD = "这是规范正文。\n\n`alpha` 点名了，beta 没点名，gamma 没点名。\n"
    TSV_EMPTY = "# 共 0 行\n#\n# pending：0 行\n"
    TSV_ONE = ("# 共 1 行\n#\n# pending：1 行\n"
               "<beta>\tpending\tW2\t自证：SPEC 删了 <beta> 点名，待补条文\n")

    def write_tree(tdir, spec_text, tsv_text):
        tdir.mkdir(parents=True, exist_ok=True)
        (tdir / "xsd").mkdir(parents=True, exist_ok=True)
        (tdir / "xsd" / "t.xsd").write_text(DECL, encoding="utf-8")
        (tdir / "SPEC.md").write_text(spec_text, encoding="utf-8")
        (tdir / "spec-element-coverage.tsv").write_text(tsv_text, encoding="utf-8")
        return tdir / "spec-element-coverage.tsv"

    def run_on(tree):
        return run_gate(tree, tree / "spec-element-coverage.tsv",
                        tree / "xsd", tree / "SPEC.md", stream)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # —— 好树：alpha/beta 都在 SPEC 里点名（`alpha` 和 <beta>），台账空 ⇒ 零违规。
        good_tsv = write_tree(root / "good", SPEC_GOOD, TSV_EMPTY)
        # —— 坏树：SPEC 里删了 <beta> 点名，台账也没登记 ⇒ 方向 A 红。
        bad_tsv = write_tree(root / "bad", SPEC_BAD, TSV_EMPTY)
        # —— 台账兜树：SPEC 删了 <beta>，但台账登记了 pending owner=W2 ⇒ 警告不红。
        pending_tsv = write_tree(root / "pending", SPEC_BAD, TSV_ONE)

        for label, tree, want_red in (
                ("好树：声明元素都在 SPEC 里点名", root / "good", False),
                ("坏树：SPEC 删了 <beta> 点名，台账没登记", root / "bad", True),
                ("台账兜：SPEC 删了 <beta>，台账登记 pending W2", root / "pending", False)):
            red, warn, _ = run_on(tree)
            ok = bool(red) == want_red
            w(f"  [{'PASS' if ok else 'BROKEN'}] {label} ⇒ 期望{'判红' if want_red else '零违规'}，"
              f"实际 {len(red)} 红 / {len(warn)} 警告\n")
            for where, msg in red:
                w(f"        {where}: {msg}\n")
            failures += 0 if ok else 1

        # —— 回归用例：带属性的开标签算点名（防正则回退到只认裸标签）。
        #    SPEC 里 <beta mode="x"/> 必须算 beta 被点名；alpha 用 `alpha` 点名。
        SPEC_ATTR = "这是规范正文。\n\n`alpha` 和 <beta mode=\"x\"/> 都点名了，`gamma` 属性也点名了。\n"
        write_tree(root / "attr", SPEC_ATTR, TSV_EMPTY)
        red, warn, _ = run_on(root / "attr")
        ok = bool(red) is False
        w(f"  [{'PASS' if ok else 'BROKEN'}] 带属性开标签算点名：<beta mode=\"x\"/> ⇒ "
          f"期望零违规，实际 {len(red)} 红 / {len(warn)} 警告\n")
        for where, msg in red:
            w(f"        {where}: {msg}\n")
        failures += 0 if ok else 1

        # —— 台账计数锚自证：「共 N 行」写错 ⇒ 必须红。
        badcount_tsv = write_tree(root / "badcount", SPEC_GOOD,
                                   "# 共 5 行\n#\n# pending：0 行\n"
                                   "<beta>\tby-design\tW2\t自证计数\n")
        red, _, _ = run_on(root / "badcount")
        ok = any("共 5 行" in msg or "实际 1 行" in msg for _, msg in red)
        w(f"  [{'PASS' if ok else 'BROKEN'}] 台账计数锚：头部「共 5 行」≠ 实际 1 行 ⇒ 期望判红，"
          f"实际 {len(red)} 红\n")
        failures += 0 if ok else 1

        # —— 属性方向好树：gamma 在 SPEC 里以词边界形式点名（`gamma`），台账空 ⇒ 零违规。
        #    DECL 里已含 <xs:attribute name="gamma"/>，SPEC_GOOD 已含 `gamma`。
        red, warn, _ = run_on(root / "good")
        # good 树已经验证过方向 A 零违规；方向 B 也应零违规（gamma 被点名）。
        ok = bool(red) is False
        w(f"  [{'PASS' if ok else 'BROKEN'}] 属性方向好树：gamma 在 SPEC 里点名（`gamma`）⇒ "
          f"期望零违规，实际 {len(red)} 红 / {len(warn)} 警告\n")
        for where, msg in red:
            w(f"        {where}: {msg}\n")
        failures += 0 if ok else 1

        # —— 属性方向坏树：SPEC 删了 gamma 点名，台账也没登记 ⇒ 方向 B 红。
        #    复用 bad 树（SPEC_BAD 已删 gamma 点名）。
        red, warn, _ = run_on(root / "bad")
        ok = bool(red) is True
        w(f"  [{'PASS' if ok else 'BROKEN'}] 属性方向坏树：SPEC 删了 gamma 点名，台账没登记 ⇒ "
          f"期望判红，实际 {len(red)} 红\n")
        for where, msg in red:
            w(f"        {where}: {msg}\n")
        failures += 0 if ok else 1
    return failures


# --------------------------------------------------------------------------- 主流程
def main(argv=None):
    ap = argparse.ArgumentParser(description="ESML XSD 声明元素 ⇄ SPEC 正文点名闸门（W37）")
    ap.add_argument("--self-test", action="store_true",
                    help="自证闸门（好树零违规、坏树判红）")
    ap.add_argument("--quiet", action="store_true", help="只报红项")
    args = ap.parse_args(argv)

    if args.self_test:
        bad = self_test(sys.stdout)
        if bad:
            print(f"[check-spec-element-coverage] {bad} 项自证失败 —— 闸门本身不可信",
                  file=sys.stderr)
            return 2
        print("[check-spec-element-coverage] 自证通过：好树零违规、坏树判红")
        return 0

    if not TSV.exists():
        print(f"[check-spec-element-coverage] 缺表：{TSV} 不存在", file=sys.stderr)
        return 2
    if not SPEC_PATH.exists():
        print(f"[check-spec-element-coverage] 缺 SPEC：{SPEC_PATH} 不存在", file=sys.stderr)
        return 2

    red, warn, stats = run_gate(REPO, TSV, REPO / "xsd", SPEC_PATH, sys.stdout)
    declared_el, named_el, declared_at, named_at, missing_a, missing_b = stats

    for where, msg in warn:
        print(f"  WARN {where} {msg}")
    if not args.quiet:
        for where, msg in red:
            print(f"  RED  {where} {msg}")

    rows, _, _ = load_tsv(TSV)
    n_pend = sum(1 for r in rows if r["verdict"] == "pending")
    n_bydes = sum(1 for r in rows if r["verdict"] == "by-design")
    print(f"[check-spec-element-coverage] XSD 声明 {len(declared_el)} 个命名元素 · "
          f"{len(declared_at)} 个命名属性 · "
          f"SPEC 点名 {len(named_el & declared_el)} 个元素 / "
          f"{len(named_at & declared_at)} 个属性 · "
          f"方向 A 缺 {len(missing_a)} · "
          f"方向 B 缺 {len(missing_b)} · "
          f"台账 {len(rows)} 行（pending {n_pend} / by-design {n_bydes}）· "
          f"违规 {len(red)}（警告 {len(warn)}）")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())

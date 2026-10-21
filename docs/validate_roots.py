#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""入口层根清单 ⇄ canonical 全局元素 —— 常驻机判（root matrix gate）。

`xsd/esml-v1.xsd` 是**根合法性闸**：它只管「这份文档的根是不是合法 ESML 根」，
内部结构交给 canonical 层。canonical 层是**唯一真相**（§2「唯一真相 = XSD」）。
于是有一条必须常驻成立的不变量：

    **入口层的根集合 == canonical 层的全局元素集合**

少一个 ⇒ 一份合法的 canonical 文档被入口层判非法（**假拒**）；
多一个 ⇒ 入口层放行一份没有任何 canonical schema 能校验的文档（**假收**，
根合法性闸有洞）。两种偏差都是缺陷，不是风格问题。

本脚本做三道对账：

  1. **入口层根集合 ⇄ canonical 全局元素集合**
     R1（可达）：canonical 的每个全局元素必须也是入口层的根（无例外）。
     R2（无洞）：入口层多出来的根必须逐个登记在 `EXCEPTIONS` 里并写明理由；
                  未登记 ⇒ 判红。已失效的例外登记也判红。
  2. **入口层注释里的根矩阵清单 ⇄ XSD 实际声明**
     `xsd/esml-v1.xsd` 顶部注释里的 `ROOT-MATRIX` 块**由本脚本生成**
     （sync 模式），本脚本逐字复核。谁手改了注释、谁加了全局元素而没重生成，
     都判红 —— 清单不再是「手工转述」。
  3. **SPEC.md §13 的 XSD 分层表 ⇄ XSD 实际声明**
     那张表里「根」一列过去是**手抄**的，已经漂过（整行漏了 `project.xsd`，
     根集合漏了 `<tasks>` / `<metadata>` / `<project>`）。本脚本逐行复核：
     表里的文件集合必须与 `xsd/` 相同，每行的根集合必须与该文件的全局元素相同。

用法：
    python3 docs/validate_roots.py            # 机判 + 报告
    python3 docs/validate_roots.py sync       # 重生成入口层注释里的根矩阵块
    python3 docs/validate_roots.py selftest   # 自证：好例 / 坏例

依赖：**仅标准库**（xml.etree）—— 不依赖 xmlschema，任何环境都能跑。
"""
import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parent.parent

XS = "{http://www.w3.org/2001/XMLSchema}"
ENTRY = "esml-v1.xsd"
CANONICAL_GLOB = "esml-canonical-*.xsd"

BEGIN = "ROOT-MATRIX:BEGIN"
END = "ROOT-MATRIX:END"
INDENT = "     "

# 入口层根 − canonical 全局元素 的**显式例外**。
#
# 例外不是「随手放行」：每一条都要写清理由 + 裁决记录（docs/design/）。
# 机制保留是为了让「以后确实要放宽根集合」变成一次**显式决策**，而不是
# 一次没人看见的 schema 改动。形状：
#
#     "<root>": ("为什么它可以不作为 canonical 全局元素", "docs/design/xxx.md"),
#
# 当前为空 —— 见 docs/design/root-matrix-adjudication.md 的裁定。
EXCEPTIONS: dict = {}

# SPEC.md §13 里那张「XSD 分层文档化」表的表头（用来定位，不依赖行号）。
SPEC_TABLE_HEADER = ("文件", "覆盖", "根", "校验")


# --------------------------------------------------------------------------
# XSD 解析（只用标准库）
# --------------------------------------------------------------------------
def local_globals(path: Path) -> list:
    """文件里**本地声明**的全局元素（`xs:schema` 的直接 `xs:element` 子节点）。"""
    root = ET.parse(path).getroot()
    return [ch.get("name") for ch in root if ch.tag == XS + "element"]


def includes_of(path: Path) -> list:
    """`xs:include` 的 schemaLocation 列表（include 会把被包含者的全局元素并进来）。"""
    root = ET.parse(path).getroot()
    return [ch.get("schemaLocation") for ch in root
            if ch.tag == XS + "include" and ch.get("schemaLocation")]


def effective_globals(xsd_dir: Path, name: str, _seen=None) -> dict:
    """该 schema **实际可用**的全局元素 → {根名: 声明所在文件}。

    = 本地声明 ∪ `xs:include` 链上的全局元素（include 是同一 targetNamespace
    的合并，被包含者声明的根在本文件里同样可用）。
    """
    seen = set() if _seen is None else _seen
    if name in seen:
        return {}
    seen.add(name)
    out = {g: name for g in local_globals(xsd_dir / name)}
    for inc in includes_of(xsd_dir / name):
        for g, src in effective_globals(xsd_dir, inc, seen).items():
            out.setdefault(g, src)
    return out


def build_matrix(repo: Path) -> dict:
    """根矩阵：入口层根 / canonical 全局元素 / 每文件的有效全局元素。"""
    xsd = repo / "xsd"
    entry = {g: ENTRY for g in local_globals(xsd / ENTRY)}
    canon, per_file = {}, {}
    for f in sorted(xsd.glob(CANONICAL_GLOB)):
        eff = effective_globals(xsd, f.name)
        per_file[f.name] = eff
        for g, src in eff.items():
            canon.setdefault(g, src)
    return {
        "entry": entry,
        "canon": canon,
        "per_file": per_file,
        "files": sorted(p.name for p in xsd.glob("*.xsd")),
    }


# --------------------------------------------------------------------------
# 第 1 道：入口层根 ⇄ canonical 全局元素
# --------------------------------------------------------------------------
def check_root_sets(matrix: dict, exceptions: dict) -> list:
    """R1（可达）+ R2（无洞）+ 例外登记的时效性。返回问题列表。"""
    entry, canon = matrix["entry"], matrix["canon"]
    problems = []
    for g in sorted(canon):
        if g not in entry:
            problems.append((
                "R1",
                "canonical 全局元素 `<%s>`（声明于 %s）**不是**入口层的根 —— "
                "入口层比 canonical 更严，一份合法的 canonical 文档会被入口层判非法"
                % (g, canon[g])))
    for g in sorted(entry):
        if g not in canon and g not in exceptions:
            problems.append((
                "R2",
                "入口层根 `<%s>` 在 canonical 层**没有**全局元素对应 —— "
                "入口层比 canonical 更松，这份文档没有任何 canonical schema 能校验它"
                % g))
    for g, (why, where) in sorted(exceptions.items()):
        if g in canon:
            problems.append(("R2", "例外登记 `<%s>` 已失效：canonical 层已有同名全局元素"
                             % g))
        elif g not in entry:
            problems.append(("R2", "例外登记 `<%s>` 已失效：入口层已无此根" % g))
        elif not why or not where:
            problems.append(("R2", "例外登记 `<%s>` 缺少理由或裁决记录" % g))
    return problems


# --------------------------------------------------------------------------
# 第 2 道：入口层注释里的根矩阵块 ⇄ XSD
# --------------------------------------------------------------------------
def render_region(matrix: dict, exceptions: dict) -> list:
    """生成入口层注释里 ROOT-MATRIX 块的内容（逐行）。"""
    entry, canon = matrix["entry"], matrix["canon"]
    roots = sorted(set(entry) | set(canon))
    lines = [
        INDENT + BEGIN,
        INDENT + "根清单 = canonical 层的全局元素（唯一真相 = canonical XSD）。",
        INDENT + "入口层的根集合必须与 canonical 层的全局元素集合**相等**：",
        INDENT + "少一个 ⇒ 合法文档被入口层判非法；多一个 ⇒ 根合法性闸有洞。",
        INDENT + "本块由 `docs/validate_roots.py` 的 sync 模式生成，**勿手工编辑**；",
        INDENT + "`docs/validate_roots.py` 逐字复核本块（漂移即判红）。",
        INDENT + "裁决记录：docs/design/root-matrix-adjudication.md",
        INDENT + "根 | 入口层 | canonical 声明处 | 裁定",
    ]
    for g in roots:
        in_entry = "是" if g in entry else "否"
        where = canon.get(g)
        if g in exceptions and g not in canon:
            why, doc = exceptions[g]
            verdict = "例外：%s（%s）" % (why, doc)
        elif where:
            verdict = "—"
        else:
            verdict = "—"
        lines.append(INDENT + "%s | %s | %s | %s"
                     % (g, in_entry, where or "—", verdict))
    lines.append(INDENT + END)
    return lines


def _manifest_span(lines: list):
    """返回 (begin 行号, end 行号)；找不到标记返回 (None, None)。"""
    i = j = None
    for k, line in enumerate(lines):
        if i is None and BEGIN in line:
            i = k
        if BEGIN in line and END in line:  # 同一行两标记（退化情况）
            return i, i
        if i is not None and j is None and END in line:
            j = k
    return i, j


def check_manifest(repo: Path, matrix: dict, exceptions: dict) -> list:
    """入口层注释里的根矩阵块必须与生成内容逐字一致。"""
    path = repo / "xsd" / ENTRY
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    i, j = _manifest_span(lines)
    if i is None or j is None:
        return [("M1", "入口层 schema 里找不到 %s / %s 标记块" % (BEGIN, END))]
    want = render_region(matrix, exceptions)
    have = lines[i:j + 1]
    if have == want:
        return []
    diff = []
    for k in range(max(len(have), len(want))):
        a = have[k] if k < len(have) else "（缺）"
        b = want[k] if k < len(want) else "（缺）"
        if a != b:
            diff.append("      现有：%s\n      应为：%s" % (a.strip(), b.strip()))
    return [("M1", "入口层注释里的根矩阵清单与 XSD 实际声明不一致（%d 行不同）：\n%s"
             % (len(diff), "\n".join(diff[:8])))]


def sync_manifest(repo: Path, matrix: dict, exceptions: dict) -> bool:
    """把入口层注释里的根矩阵块重生成。返回是否发生了改动。"""
    path = repo / "xsd" / ENTRY
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    i, j = _manifest_span(lines)
    if i is None or j is None:
        raise SystemExit("入口层 schema 里找不到 %s / %s 标记块，无法 sync"
                         % (BEGIN, END))
    new = render_region(matrix, exceptions)
    if lines[i:j + 1] == new:
        return False
    lines[i:j + 1] = new
    out = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    path.write_text(out, encoding="utf-8")
    return True


# --------------------------------------------------------------------------
# 第 3 道：SPEC.md §13 的 XSD 分层表 ⇄ XSD
# --------------------------------------------------------------------------
def _table_rows(spec_text: str) -> list:
    """定位 §13 的 XSD 分层表，返回 [表头, 行, 行, ...]（每行是单元格列表）。"""
    lines = spec_text.splitlines()
    for k, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == len(SPEC_TABLE_HEADER) and tuple(cells) == SPEC_TABLE_HEADER:
            rows = []
            for follow in lines[k + 1:]:
                if not follow.strip().startswith("|"):
                    break
                rows.append([c.strip() for c in follow.strip().strip("|").split("|")])
            return [cells] + rows
    return []


def _root_tokens(cell: str) -> set:
    """根单元格里被点名的元素名（形如 `<esml>`）。"""
    return set(re.findall(r"<([A-Za-z][\w.\-]*)>", cell))


def check_spec_table(repo: Path, matrix: dict) -> list:
    """SPEC §13 的 XSD 分层表：文件集合 + 每行的根集合，必须与 XSD 一致。"""
    spec = repo / "SPEC.md"
    if not spec.exists():
        return [("S1", "找不到 SPEC.md")]
    rows = _table_rows(spec.read_text(encoding="utf-8"))
    if not rows:
        return [("S1", "SPEC.md 里找不到 §13 的「文件 / 覆盖 / 根 / 校验」表")]
    body = rows[1:]
    problems = []

    listed = []
    for cells in body:
        if not cells:
            continue
        names = re.findall(r"`([^`]+)`", cells[0])
        listed.extend(n for n in names if n.endswith(".xsd"))
    for f in matrix["files"]:
        if f not in listed:
            problems.append(("S1", "SPEC §13 的 XSD 分层表**漏了** `xsd/%s` 这一行" % f))
    for f in listed:
        if f not in matrix["files"]:
            problems.append(("S1", "SPEC §13 的 XSD 分层表列了 `xsd/%s`，仓内不存在" % f))

    for cells in body:
        if len(cells) < 3:
            continue
        names = re.findall(r"`([^`]+)`", cells[0])
        fname = next((n for n in names if n.endswith(".xsd")), None)
        if not fname or fname not in matrix["files"]:
            continue
        want = set(matrix["per_file"].get(fname, {}))
        if fname == ENTRY:
            want = set(matrix["entry"])
        have = _root_tokens(cells[2])
        if have != want:
            problems.append((
                "S1",
                "SPEC §13 表 `xsd/%s` 行的「根」一列与 schema 不符："
                "表里 %s，schema 里 %s"
                % (fname,
                   "、".join("`<%s>`" % g for g in sorted(have)) or "（空）",
                   "、".join("`<%s>`" % g for g in sorted(want)) or "（空）")))
    return problems


# --------------------------------------------------------------------------
# 报告
# --------------------------------------------------------------------------
def report(repo: Path, matrix: dict, exceptions: dict) -> bool:
    ok = True
    entry, canon = matrix["entry"], matrix["canon"]

    print("== 1. 入口层根 ⇄ canonical 全局元素 ==")
    by_src = {}
    for g, src in canon.items():
        by_src.setdefault(src, []).append(g)
    print("   canonical 全局元素：%d 个（%s）"
          % (len(canon), " / ".join("%s %d" % (k, len(v)) for k, v in sorted(by_src.items()))))
    print("   入口层根：%d 个" % len(entry))
    only_canon = sorted(set(canon) - set(entry))
    only_entry = sorted(set(entry) - set(canon))
    print("   canonical 有而入口层没有：%s"
          % ("、".join("`<%s>`" % g for g in only_canon) or "无"))
    print("   入口层有而 canonical 没有：%s"
          % ("、".join("`<%s>`" % g for g in only_entry) or "无"))
    p1 = check_root_sets(matrix, exceptions)
    if p1:
        ok = False
        for code, msg in p1:
            print("   [%s] %s" % (code, msg))
    else:
        print("   [OK] 两个集合相等（R1 可达 + R2 无洞），例外登记 %d 条"
              % len(exceptions))

    print("== 2. 入口层注释里的根矩阵清单 ⇄ XSD ==")
    p2 = check_manifest(repo, matrix, exceptions)
    if p2:
        ok = False
        for code, msg in p2:
            print("   [%s] %s" % (code, msg))
    else:
        print("   [OK] ROOT-MATRIX 块与生成内容逐字一致")

    print("== 3. SPEC.md §13 的 XSD 分层表 ⇄ XSD ==")
    p3 = check_spec_table(repo, matrix)
    if p3:
        ok = False
        for code, msg in p3:
            print("   [%s] %s" % (code, msg))
    else:
        print("   [OK] 表内文件集合与每行的「根」集合均与 schema 一致")

    print()
    print("verdict: %s" % ("OK" if ok else "根清单与 canonical 层不一致（见上）"))
    return ok


# --------------------------------------------------------------------------
# 自证：好例 / 坏例
# --------------------------------------------------------------------------
def _write_min_xsd(path: Path, roots: list) -> None:
    body = "\n".join('  <xs:element name="%s"/>' % g for g in roots)
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!--\n'
        + INDENT + BEGIN + "\n"
        + INDENT + END + "\n"
        '-->\n'
        '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"\n'
        '           xmlns:esml="https://www.ai4energy.cn/esml/v1"\n'
        '           targetNamespace="https://www.ai4energy.cn/esml/v1"\n'
        '           elementFormDefault="qualified">\n'
        '%s\n</xs:schema>\n' % body,
        encoding="utf-8")


def _fixture(tmp: Path, entry_roots: list, canon: dict, exceptions: dict = None) -> Path:
    """造一个最小夹具仓：xsd/ 若干 schema + SPEC.md 的 §13 表（都已「自洽」）。"""
    xsd = tmp / "xsd"
    xsd.mkdir(parents=True, exist_ok=True)
    _write_min_xsd(xsd / ENTRY, entry_roots)
    for fname, roots in canon.items():
        _write_min_xsd(xsd / fname, roots)
    rows = []
    for f in [ENTRY] + sorted(canon):
        roots = entry_roots if f == ENTRY else canon[f]
        cell = " ".join("`<%s>`" % g for g in sorted(roots)) or "—"
        rows.append("| `%s` | 覆盖 | %s | lax |" % (f, cell))
    (tmp / "SPEC.md").write_text(
        "# t\n\n## 13 分层\n\n"
        "| 文件 | 覆盖 | 根 | 校验 |\n|---|---|---|---|\n"
        + "\n".join(rows) + "\n", encoding="utf-8")
    # 夹具也要「自洽」：把根矩阵块生成出来
    sync_manifest(tmp, build_matrix(tmp), exceptions or {})
    return tmp


def _clone_repo(repo: Path, dst: Path) -> Path:
    """把仓里机判要看的部分（xsd/ + SPEC.md）克隆一份，供坏例就地破坏。"""
    shutil.copytree(repo / "xsd", dst / "xsd")
    shutil.copy2(repo / "SPEC.md", dst / "SPEC.md")
    return dst


def _drop_root(path: Path, name: str) -> None:
    """从 schema 里删掉一个顶层全局元素声明。"""
    text = path.read_text(encoding="utf-8")
    pat = re.compile(r'\n[ \t]*<xs:element name="%s"(?:\s[^>]*)?>.*?</xs:element>'
                     % re.escape(name), re.S)
    new, n = pat.subn("", text, count=1)
    if n == 0:
        new, n = re.subn(r'\n[ \t]*<xs:element name="%s"[^>]*/>' % re.escape(name),
                         "", text, count=1)
    if n == 0:
        raise SystemExit("夹具里找不到要删的根 <%s>（%s）" % (name, path))
    path.write_text(new, encoding="utf-8")


def _add_root(path: Path, name: str) -> None:
    """给 schema 加一个顶层全局元素声明。"""
    text = path.read_text(encoding="utf-8")
    text = text.replace("</xs:schema>",
                        '  <xs:element name="%s"/>\n</xs:schema>' % name, 1)
    path.write_text(text, encoding="utf-8")


def _break_spec_root_cell(path: Path, fname: str, old: str, new: str) -> None:
    """把 SPEC §13 表里某文件那一行的「根」单元格里一个名字改掉。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    for k, line in enumerate(lines):
        if line.strip().startswith("| `%s`" % fname):
            cells = line.strip().strip("|").split("|")
            if len(cells) >= 3 and old in cells[2]:
                cells[2] = cells[2].replace(old, new, 1)
                lines[k] = "|" + "|".join(cells) + "|"
                path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                return
    raise SystemExit("夹具里找不到 SPEC 表 `%s` 那一行" % fname)


def _run(repo: Path, exceptions: dict) -> list:
    matrix = build_matrix(repo)
    return (check_root_sets(matrix, exceptions)
            + check_manifest(repo, matrix, exceptions)
            + check_spec_table(repo, matrix))


def selftest(repo: Path) -> bool:
    """好例 ≥2、坏例 ≥2：证明这道闸不是摆设。"""
    ok = True
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # ---- 好例 1：本仓当前状态 ----
        p1 = _run(repo, EXCEPTIONS)
        print("   [好例 1] 本仓当前状态（入口层根 = canonical 全局元素）")
        if p1:
            ok = False
            for code, msg in p1:
                print("      %s: %s" % (code, msg))
            print("      → FAIL（%d 个问题）" % len(p1))
        else:
            print("      → PASS（0 个问题）")

        # ---- 好例 2：合成夹具 —— 入口层根 = canonical 全局元素 ----
        fx = _fixture(tmp / "good2", ["a", "b"], {"esml-canonical-x.xsd": ["a", "b"]})
        p2 = _run(fx, {})
        print("   [好例 2] 合成夹具：入口层根 {a,b} = canonical 全局元素 {a,b}")
        if p2:
            ok = False
            for code, msg in p2:
                print("      %s: %s" % (code, msg))
            print("      → FAIL（%d 个问题）" % len(p2))
        else:
            print("      → PASS（0 个问题）")

        # ---- 好例 3：合成夹具 —— 多出来的根已登记为例外 ----
        exc = {"legacy": ("夹具专用的已登记例外", "docs/design/selftest.md")}
        fx = _fixture(tmp / "good3", ["a", "b", "legacy"],
                      {"esml-canonical-x.xsd": ["a", "b"]}, exc)
        p3 = _run(fx, exc)
        print("   [好例 3] 合成夹具：多出的根 `legacy` 已登记为例外")
        if p3:
            ok = False
            for code, msg in p3:
                print("      %s: %s" % (code, msg))
            print("      → FAIL（%d 个问题）" % len(p3))
        else:
            print("      → PASS（0 个问题）")

        # ---- 坏例 1：从入口层删一个根 ----
        clone = _clone_repo(repo, tmp / "bad1")
        victim = "project"
        _drop_root(clone / "xsd" / ENTRY, victim)
        p4 = _run(clone, EXCEPTIONS)
        print("   [坏例 1] 从入口层删掉一个根 `<%s>`（canonical 层仍有）" % victim)
        if not p4:
            ok = False
            print("      → FAIL（本应判红，却通过了）")
        else:
            print("      → 判红（%d 个问题）" % len(p4))
            for code, msg in p4:
                print("      %s: %s" % (code, msg))

        # ---- 坏例 2：给 canonical 层加一个假根 ----
        clone = _clone_repo(repo, tmp / "bad2")
        _add_root(clone / "xsd" / "esml-canonical-compute.xsd", "fakeRoot")
        p5 = _run(clone, EXCEPTIONS)
        print("   [坏例 2] 给 canonical 层加一个假根 `<fakeRoot>`（入口层没有）")
        if not p5:
            ok = False
            print("      → FAIL（本应判红，却通过了）")
        else:
            print("      → 判红（%d 个问题）" % len(p5))
            for code, msg in p5:
                print("      %s: %s" % (code, msg))

        # ---- 坏例 3：入口层加一个未登记的假根 ----
        clone = _clone_repo(repo, tmp / "bad3")
        _add_root(clone / "xsd" / ENTRY, "fakeEntryRoot")
        p6 = _run(clone, EXCEPTIONS)
        print("   [坏例 3] 给入口层加一个未登记的假根 `<fakeEntryRoot>`")
        if not p6:
            ok = False
            print("      → FAIL（本应判红，却通过了）")
        else:
            print("      → 判红（%d 个问题）" % len(p6))
            for code, msg in p6:
                print("      %s: %s" % (code, msg))

        # ---- 坏例 4：手改入口层注释里的清单 ----
        clone = _clone_repo(repo, tmp / "bad4")
        f = clone / "xsd" / ENTRY
        f.write_text(f.read_text(encoding="utf-8").replace(
            INDENT + "esml | 是 |", INDENT + "esml | 否 |", 1), encoding="utf-8")
        p7 = _run(clone, EXCEPTIONS)
        print("   [坏例 4] 手改入口层注释里的根矩阵清单（把 `esml` 标成「否」）")
        if not p7:
            ok = False
            print("      → FAIL（本应判红，却通过了）")
        else:
            print("      → 判红（%d 个问题）" % len(p7))
            for code, msg in p7:
                print("      %s: %s" % (code, msg))

        # ---- 坏例 5：改 SPEC §13 表里的「根」列 ----
        clone = _clone_repo(repo, tmp / "bad5")
        victim = sorted(build_matrix(clone)["entry"])[0]
        _break_spec_root_cell(clone / "SPEC.md", ENTRY,
                              "`<%s>`" % victim, "`<%sX>`" % victim)
        p8 = _run(clone, EXCEPTIONS)
        print("   [坏例 5] 改 SPEC §13 表的「根」列（把 `<%s>` 改成 `<%sX>`）"
              % (victim, victim))
        if not p8:
            ok = False
            print("      → FAIL（本应判红，却通过了）")
        else:
            print("      → 判红（%d 个问题）" % len(p8))
            for code, msg in p8:
                print("      %s: %s" % (code, msg))

    print()
    print("selftest: %s" % ("OK" if ok else "有例子没有按预期判红/判绿"))
    return ok


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="入口层根清单 ⇄ canonical 全局元素 对账机判")
    ap.add_argument("mode", nargs="?", default="check",
                    choices=["check", "sync", "selftest"],
                    help="check=机判（默认）；sync=重生成入口层注释里的根矩阵块；"
                         "selftest=好例/坏例自证")
    args = ap.parse_args()

    if args.mode == "selftest":
        return 0 if selftest(REPO) else 1

    if args.mode == "sync":
        matrix = build_matrix(REPO)
        changed = sync_manifest(REPO, matrix, EXCEPTIONS)
        print("根矩阵块：%s" % ("已重生成" if changed else "本来就是最新的"))
        # sync 后仍要过一遍机判（SPEC 表之类不受 sync 影响）
        return 0 if report(REPO, build_matrix(REPO), EXCEPTIONS) else 1

    matrix = build_matrix(REPO)
    return 0 if report(REPO, matrix, EXCEPTIONS) else 1


if __name__ == "__main__":
    sys.exit(main())

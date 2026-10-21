#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""示例 ⇄ 规范 对账机验（`docs/coverage.md` 的数字来源）。

五道检查：

  1. **XSD 机验**：每份 `.esml` 按根元素路由到仓内 canonical schema 校验。
     README 的规矩是「文件名含 `probe`、或头部注明为负例的文档**预期失败**」
     —— 脚本按同一条规矩分类：负例失败**不算**缺陷，非负例失败才算。
  2. **SPEC → 示例**：SPEC.md 正文里点名的仓内示例路径，逐条核存在性。
  3. **示例 → SPEC**：示例头部是否指名了 SPEC.md 的章节（`§x.y` / `附录 X`），
     并按章节聚合出「每个编号对应哪些示例」——这就是工单要的
     「每个编号的『应当有示例』清单」。
  4. **稀有元素覆盖**：把每份示例用到的 ESML 元素统计出来，频次 ≤3 的
     （即该示例独有的语法点）逐个查 SPEC.md 是否点名；没点名的就是
     「无 SPEC 依据」。
  5. **SPEC.md 的 ```xml 段**：能独立成文档的必须过 schema；其余是子元素片段
     （示例子树），只能算「不可独立机验」。

用法：
    python3 docs/validate_examples.py            # 全量
    python3 docs/validate_examples.py --quiet    # 只出汇总行

依赖：xmlschema（README「校验与运行」一节已写明这是本仓的校验器）。
"""
import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import xmlschema
except ImportError:  # pragma: no cover
    sys.exit("需要 xmlschema：pip install xmlschema")

REPO = Path(__file__).resolve().parent.parent
XSD = REPO / "xsd"
SPEC = REPO / "SPEC.md"
NS = "https://www.ai4energy.cn/esml/v1"

# 根元素 → canonical schema。未列出的根走入口 schema esml-v1.xsd（宽松根闸）。
ROUTE = {
    "esml": "esml-canonical-basic.xsd",
    "project": "esml-canonical-project.xsd",
    "computeTasks": "esml-canonical-compute.xsd",
    "tasks": "esml-canonical-compute.xsd",
}
_cache = {}


def schema(name):
    if name not in _cache:
        _cache[name] = xmlschema.XMLSchema(str(XSD / name))
    return _cache[name]


def examples():
    return sorted(p for p in REPO.rglob("*.esml") if ".git" not in p.parts)


def strip_comments(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return re.sub(r"<\?.*?\?>", "", text, flags=re.S)


def root_of(text):
    m = re.search(r"<\s*([A-Za-z][\w.\-]*)", strip_comments(text))
    return m.group(1) if m else "?"


def is_negative(path, text):
    """README 的规矩：文件名含 probe、或头部注明为负例 ⇒ 预期失败。"""
    if "probe" in path.name:
        return True
    head = "\n".join(text.splitlines()[:25])
    return "负例" in head


def check_xsd(quiet):
    files = examples()
    n_ok = n_neg_fail = n_bad = 0
    bad, neg = [], []
    for p in files:
        rel = str(p.relative_to(REPO))
        text = p.read_text(encoding="utf-8")
        xsd = ROUTE.get(root_of(text), "esml-v1.xsd")
        try:
            schema(xsd).validate(text)
        except Exception as exc:
            reason = next((l.strip() for l in str(exc).splitlines() if "Reason:" in l), "")
            if is_negative(p, text):
                n_neg_fail += 1
                neg.append((rel, reason))
            else:
                n_bad += 1
                bad.append((rel, xsd, reason))
        else:
            n_ok += 1
    print("== 1. XSD 机验 ==")
    print("   示例 %d 件：PASS %d / 负例按预期失败 %d / 非负例失败 %d"
          % (len(files), n_ok, n_neg_fail, n_bad))
    for rel, reason in neg:
        print("   [负例·预期失败] %-46s %s" % (rel, reason))
    for rel, xsd, reason in bad:
        print("   [缺陷]         %-46s %s %s" % (rel, xsd, reason))
    return n_bad == 0


def check_spec_refs(quiet):
    text = SPEC.read_text(encoding="utf-8")
    top = {p.name for p in REPO.iterdir() if p.is_dir() and p.name != ".git"}
    repo = {str(p.relative_to(REPO)) for p in examples()}
    refs = set(re.findall(r"[A-Za-z0-9_./-]*\.esml", text))
    hits = sorted(r for r in refs if r in repo)
    broken = sorted(r for r in refs
                    if "/" in r and r.split("/")[0] in top and r not in repo)
    other = sorted(r for r in refs
                   if r not in repo and r not in broken)
    print("== 2. SPEC.md → 示例 路径对账 ==")
    print("   点名且存在的仓内示例路径：%d 条" % len(hits))
    for r in hits:
        print("     %s" % r)
    print("   指向仓内顶层目录、但文件**不存在**：%d 条 %s" % (len(broken), broken))
    print("   示意路径 / 管线记法（不判对错，列出备查）：%d 条 %s" % (len(other), other))
    return not broken


SECTION_RE = re.compile(r"§\s*([0-9]+(?:\.[0-9]+)*[a-z]?)|附录\s*([A-N])")


def check_cited(quiet):
    """示例头部是否指名规范章节；并按章节聚合出「每个编号的示例清单」。"""
    files = examples()
    cited, uncited = [], []
    per_section = defaultdict(list)
    for p in files:
        head = "\n".join(p.read_text(encoding="utf-8").splitlines()[:25])
        rel = str(p.relative_to(REPO))
        m = SECTION_RE.search(head)
        if m:
            cited.append(rel)
            per_section[m.group(0).replace(" ", "")].append(rel)
        else:
            uncited.append(rel)
    print("== 3. 示例 → SPEC 章节引用 ==")
    print("   头部指名 SPEC 章节：%d / %d" % (len(cited), len(files)))
    for rel in uncited:
        print("     未指名：%s" % rel)
    print("   按章节聚合（= 每个编号的「应当有示例」清单）：%d 个编号"
          % len(per_section))
    for sec in sorted(per_section, key=lambda s: (s.startswith("附录"), s)):
        files_of = per_section[sec]
        print("     %-10s %2d 件  %s"
              % (sec, len(files_of), " ".join(f.split("/")[-1] for f in files_of)))
    return not uncited


def check_rare(quiet):
    text = SPEC.read_text(encoding="utf-8")
    files = examples()
    per, freq = {}, Counter()
    for p in files:
        body = strip_comments(p.read_text(encoding="utf-8"))
        els = list(dict.fromkeys(re.findall(r"<\s*/?\s*([A-Za-z][\w.\-]*)", body)))
        per[str(p.relative_to(REPO))] = els
        freq.update(els)
    unbacked = []
    for rel, els in per.items():
        rare = [e for e in els if freq[e] <= 3]
        un = [e for e in rare
              if not re.search(r"[<`\s(]" + re.escape(e) + r"[>\s`)]", text)]
        if un:
            unbacked.append((rel, un))
    print("== 4. 稀有元素（该示例独有的语法点）在 SPEC.md 的点名情况 ==")
    print("   无 SPEC 依据的示例：%d / %d" % (len(unbacked), len(files)))
    for rel, un in unbacked:
        print("     %-46s %s" % (rel, ", ".join(un)))
    return not unbacked


def check_spec_blocks(quiet):
    """SPEC.md 里 ```xml 段的自足性：能独立成文档的必须过 schema，
    其余是子元素片段（示例子树），只能算「不可独立机验」。"""
    text = SPEC.read_text(encoding="utf-8")
    lines = text.splitlines()
    blocks, i = [], 0
    while i < len(lines):
        if lines[i].strip() == "```xml":
            j = i + 1
            while j < len(lines) and lines[j].strip() != "```":
                j += 1
            blocks.append((i + 2, "\n".join(lines[i + 1:j])))
            i = j
        i += 1
    self_contained, fragments, bad = [], 0, []
    for line, body in blocks:
        m = re.search(r"<\s*([A-Za-z][\w.\-]*)", strip_comments(body))
        root = m.group(1) if m else "?"
        xsd = ROUTE.get(root)
        if xsd is None:
            fragments += 1
            continue
        doc = body if "xmlns=" in body.split("\n")[0] else body.replace(
            "<" + root, '<%s xmlns="%s"' % (root, NS), 1)
        try:
            schema(xsd).validate(doc)
        except Exception as exc:
            reason = next((l.strip() for l in str(exc).splitlines() if "Reason:" in l), "")
            bad.append((line, root, xsd, reason))
        else:
            self_contained.append((line, root, xsd))
    print("== 5. SPEC.md 的 ```xml 段 ==")
    print("   自足文档级（可独立 XSD 校验）：%d 段，全部通过" % len(self_contained))
    for line, root, xsd in self_contained:
        print("     line %-5d <%s> vs %s : PASS" % (line, root, xsd))
    for line, root, xsd, reason in bad:
        print("     line %-5d <%s> vs %s : FAIL %s" % (line, root, xsd, reason))
    print("   子元素片段（示例子树，不可独立机验）：%d 段" % fragments)
    return not bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true", help="只出汇总行")
    args = ap.parse_args()
    ok = True
    ok &= check_xsd(args.quiet)
    ok &= check_spec_refs(args.quiet)
    ok &= check_cited(args.quiet)
    ok &= check_rare(args.quiet)
    ok &= check_spec_blocks(args.quiet)
    print()
    print("verdict: %s" % ("OK" if ok else "有非负例的 XSD 失败 / 有悬空路径 / "
                                         "有示例未指名章节 / 有无 SPEC 依据的示例 / "
                                         "自足示例段校验失败"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

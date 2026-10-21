#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ESML 规范仓 · SPEC ↔ XSD 文档根对账门。

为什么要有这个脚本
------------------
`xsd/esml-v1.xsd`（入口层）的根清单是**手写**的，而 SPEC.md 正文里散着
「什么是文档根」的散文描述。两边一旦漂移，机器是拦不住的：

  * 入口层**多收**一个根（canonical 层根本没有的假根）⇒ 放行一份 canonical
    层必然拒收的文档，**假绿**（历史上 `schedule` / `solutionParameters` /
    `tasks` / `variables` / `domain` 就是这么进来的）。
  * 入口层**漏收**一个根（canonical 层的全局元素没进清单）⇒ 入口层拒收一份
    canonical 层认可的文档，**误拒**（`metadata` / `project` 就是这么丢的）。
  * SPEC 正文把某个元素写成文档根，而 XSD 的根清单里没有它（或反过来）⇒
    规范与 schema 对不上，人读哪边都「有道理」。

本脚本把三个集合摆在一起，机判，不靠人眼对账：

  R_canon  canonical 层（`xsd/esml-canonical-*.xsd`）的**全局** `xs:element`
  R_entry  入口层（`xsd/esml-v1.xsd`）的**全局** `xs:element`
  R_spec   SPEC.md 正文里被描述为**文档根**的元素名

判据（任何一条不成立即红）：

  C1  R_entry ⊆ R_canon   入口层不得多收（假根）
  C2  R_canon ⊆ R_entry   入口层不得漏收（误拒）
  C3  R_spec  ⊆ R_canon   SPEC 不得把 XSD 不认的写法写成文档根
  C4  R_canon ⊆ R_spec    canonical 的全局根 SPEC 不得只字不提

C1/C2 合起来就是「入口层根清单 = canonical 层全局元素集」—— 这条口径写在
`xsd/esml-v1.xsd` 的注释里，本脚本把它变成机器判据。

SPEC 侧的抽取（散文 → 元素名）
----------------------------
SPEC.md 是散文，没有「根清单」字段，只能从正文里抽。抽取规则写死在本文件里，
**规则本身也是可审的**（改动规则 = 改判定口径，必须同步改本段注释与
`docs/design/xsd-spec-parity.md`）：

  R1  根声明行 = 散文行里出现根标记词（`根` / `顶层`）的**行**。
      排除假朋友：`库根`(=libroot)、`根目录`、`根取并集`。
  R2  否定语境 —— 整行排除：出现 `删` / `移除` / `退位` / `不再` / `曾经` /
      `漏根` / `假根` / `旧版` / `历史` 的行，是在讲「改了什么 / 曾经是什么」，
      不是在声明「现在什么是根」。附录 C（修订史）里的
      「删 5 个假根、补 2 个漏根」正是这一类。
  R3  分句否定 —— 子句里出现 `不是文档根` / `非文档根` / `不作为根` /
      `不能作根` 时，该子句里的元素名不算根声明。
  R4  表格 —— 若某张 markdown 表的**表头**含根标记词，则该表的「根」列是
      根声明列，只从那一列抽元素名（不从「覆盖」列抽 —— 那列全是元素名，
      抽了就是噪声）。非根表则整行按 R1 抽。
  R5  元素名来源 —— 行内代码 span `` `...` ``：
        * span 能当 XML 片段解析 ⇒ 取它的**根元素名**（`<orderedSet>…</orderedSet>`
          只算 `orderedSet`，不算里面的 `<element>`）；
        * 解析不了（散文里裸写的 `<project>`）⇒ 取该 span 里**最外层**的标签名；
        * 根声明列里还可以是裸写的 `/` 分隔列表（`units/variableTypes/modelTypes`）。
  R6  示例块 —— ```` ```xml ```` 代码块的**最外层**元素另行单列成
      「SPEC 示例顶层元素」表，并机验它至少在 XSD 里有同名声明
      （示例顶层写了个 XSD 里根本没声明的名字 ⇒ 一定是拼写漂移）。

by-design 登记表
--------------
确有据可查、判为「不改」的分歧登记在 `tools/spec-xsd-bydesign.tsv`：
每行写明 kind（`spec-root` / `entry-root`）、元素名、理由。登记表是**数据**，
不是注释 —— 下一个想改 XSD 的人会先看见它。

自证（`--self-test`）
--------------------
一个「检查器」如果对任何东西都说 OK，它和没有检查器等价。所以本脚本自带
构造样例（**5 好 4 坏**）证明它**真的会红**：好树必须 0 红、坏树必须红，
任一翻转都算自证失败。坏例正是两类历史事故的重演：
人为**删一个根**（漏收）、人为**多一个根**（多收），外加 SPEC 侧的两种
（声明了 XSD 不认的根 / canonical 有根而 SPEC 只字不提）。

用法
----
    tools/check-spec-xsd-parity.py                # 全量对账；退出码 0 = 三方一致
    tools/check-spec-xsd-parity.py --report        # 附带 SPEC 根声明清单与证据行
    tools/check-spec-xsd-parity.py --self-test     # 5 好 4 坏自证

依赖：仅标准库（`xml.etree` / `re` / `argparse`）—— 不需要 lxml / xmllint。
"""

import argparse
import re
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

REPO = Path(__file__).resolve().parent.parent
XSD_DIR = REPO / "xsd"
ENTRY_SCHEMA = XSD_DIR / "esml-v1.xsd"
CANONICAL_GLOB = "esml-canonical-*.xsd"
SPEC_MD = REPO / "SPEC.md"
BYDESIGN_TSV = Path(__file__).resolve().parent / "spec-xsd-bydesign.tsv"

XS = "{http://www.w3.org/2001/XMLSchema}"

# ------------------------------------------------------------------ 根标记与语境
# 「文档根」的强标记词：子句里出现即「这一处在讲文档根」。
STRONG_ROOT_MARKERS = ("文档根", "文档顶层", "根清单", "根元素", "独立根", "顶层声明", "顶层壳")
# 裸「根」：排除假朋友后仍成立 ⇒ 也是强标记。
#   假朋友 = libroot（`libroot 可加库根`）、-L 的「根取并集」、目录意义上的「根」。
#   注意「独立库根」（§13 表：入口 schema 的根 = `<esml>` + 独立库根）**是**根声明，
#   所以只排「可加库根」，不排整个「库根」。
NOT_ROOT_WORDS = ("可加库根", "假根", "漏根", "根目录", "根取", "根并", "根路径")
# 裸「顶层」是弱标记：SPEC 里的「顶层」有两种用法 —— 文档级（「顶层声明」）
# 与成员级（「顶层区段」「顶层 method」「对顶层公开量」）。判定办法看它后面
# 紧跟的词：文档级名词 ⇒ 根声明；成员级名词 ⇒ 不是；别的 ⇒ 弱标记，
# 再看整个子句里有没有成员级词（降级）。
# 注意「顶层」与被点名元素之间常夹一个行内代码 span
# （「顶层 `<solutionParameters>` 段」「顶层 `<recordTypes>` 目录内写 …」），
# 所以判词前要先**去掉代码 span**再看紧跟的词。
WEAK_TOPLEVEL = "顶层"
DOC_LEVEL_NOUNS = ("声明", "壳", "文档", "清单", "元素")
# 成员级语境词：这些词说明「顶层」说的是某个元素的**成员**，不是文档根。
# 「段」「目录」同理：「顶层段」= `<esml>` 的成员段，不是文档根。
MEMBER_SCOPE_WORDS = ("区段", "段", "method", "SET", "实例树", "公开量", "结构", "目录")
# 行级否定：整行不是根声明（讲的是「改了什么」「曾经是什么」）。
LINE_NEGATIONS = (
    "删", "移除", "退位", "不再", "曾经", "漏根", "假根", "旧版", "历史", "过时",
)
# 分句级否定：该子句明说「它不是根」。
CLAUSE_NEGATIONS = ("不是文档根", "非文档根", "不作为根", "不作根", "不能作根", "不是根")

CLAUSE_SEP = "；;。，,\n"

INLINE_CODE = re.compile(r"`([^`]+)`")
BARE_LIST = re.compile(r"([A-Za-z][A-Za-z0-9]*(?:/[A-Za-z][A-Za-z0-9]*)+)")
ELEMENT_NAME = re.compile(r"[a-z][A-Za-z0-9]*")
# 「`<X>` 根」句式：span 后面紧跟「根」⇒ 这个 span 就是被声明的根。
SPAN_FOLLOWED_BY_ROOT = re.compile(r"^\s*根")
# 一段文字开头的行内代码 span（允许 `**` 粗体标记在前）。
FIRST_SPAN = re.compile(r"[*`]*`([^`]+)`")


# ------------------------------------------------------------------ XSD 侧
def global_roots(schema_path):
    """schema 顶层的**全局** `xs:element` 名（只看 xs:schema 的直接子元素）。"""
    root = ET.parse(schema_path).getroot()
    return [e.get("name") for e in root.findall(f"{XS}element") if e.get("name")]


def canonical_roots(xsd_dir):
    """canonical 层全局元素 → {名字: 声明它的文件名}。"""
    out = {}
    for f in sorted(xsd_dir.glob(CANONICAL_GLOB)):
        for n in global_roots(f):
            out[n] = f.name
    return out


def entry_roots(schema_path):
    """入口层全局元素 → {名字: schema 文件名}。"""
    return {n: schema_path.name for n in global_roots(schema_path)}


def declared_element_names(xsd_dir):
    """XSD 里声明过的**全部**元素名（全局 + 局部），用于「示例顶层有没有这个元素」。"""
    names = set()
    for f in sorted(xsd_dir.glob("*.xsd")):
        text = f.read_text(encoding="utf-8")
        for m in re.finditer(r"<xs:element\s+(?:name|ref)=\"([^\"]+)\"", text):
            names.add(m.group(1))
    return names


# ------------------------------------------------------------------ SPEC 侧
def strip_fences(text):
    """去掉围栏代码块的内容，只留散文行。→ [(行号, 行文本)]"""
    out = []
    in_fence = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append((i, line))
    return out


def xml_blocks(text):
    """`` ```xml ```` 围栏块 → [(起始行号, 内容)]。"""
    out = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^\s*```\s*([A-Za-z]*)\s*$", lines[i])
        if not m:
            i += 1
            continue
        lang = m.group(1).lower()
        start = i + 1
        body = []
        j = i + 1
        while j < len(lines) and not lines[j].lstrip().startswith("```"):
            body.append(lines[j])
            j += 1
        if lang == "xml":
            out.append((start, "\n".join(body)))
        i = j + 1
    return out


def outer_tags(span):
    """span 里**最外层**的标签名（嵌套的子标签不算）。"""
    tags = []
    stack = []
    for m in re.finditer(
        r"<\s*(/?)\s*([A-Za-z_][\w.\-]*)\s*((?:\"[^\"]*\"|'[^']*'|[^>\"'])*?)(/?)>", span
    ):
        closing, name, _attrs, selfclose = m.groups()
        if closing:
            if stack:
                stack.pop()
            continue
        if not stack:
            tags.append(name)
        if not selfclose:
            stack.append(name)
    return tags


def mentions_of(span):
    """一个行内代码 span 贡献的元素名：能当 XML 片段解析就取根元素名，
    否则取最外层标签名。"""
    s = span.replace("…", "").replace("...", "")
    s = s.strip()
    if s.startswith("<"):
        try:
            r = ET.fromstring(s)
            return [r.tag.split("}")[-1]]
        except ET.ParseError:
            pass
    return outer_tags(s)


def has_root_marker(text):
    """文本（含根标记词）里是否在讲「根」。用于表头判定。"""
    t = text
    for bad in NOT_ROOT_WORDS:
        t = t.replace(bad, "")
    if any(mk in t for mk in STRONG_ROOT_MARKERS):
        return True
    if WEAK_TOPLEVEL in t and not any(w in t for w in MEMBER_SCOPE_WORDS):
        return True
    return "根" in t


def clause_has_root_marker(clause):
    """一个子句是不是在讲「文档根」。"""
    t = clause
    for bad in NOT_ROOT_WORDS:
        t = t.replace(bad, "")
    if any(mk in t for mk in STRONG_ROOT_MARKERS):
        return True
    if WEAK_TOPLEVEL in t:
        idx = t.find(WEAK_TOPLEVEL)
        after = t[idx + len(WEAK_TOPLEVEL):]
        stripped = after.lstrip()
        # 「顶层」后面**紧跟行内代码 span** ⇒ 它点名的是某个元素
        # （「顶层 `<solutionParameters>` 段」「顶层 `<domains>` 声明 …」），
        # 说的是文档的一个**成员段**，不是文档根。
        # 除非那句是「顶层 `<X>` 根」—— 那时 X 就是根。
        m = FIRST_SPAN.match(stripped)
        if m and not SPAN_FOLLOWED_BY_ROOT.match(stripped[m.end():]):
            return False
        # 判词前先去掉行内代码 span：「顶层 `<X>` 段」的紧跟词是「段」，
        # 不是 span 里的元素名。
        tail = INLINE_CODE.sub(" ", after).lstrip(" *")
        if any(tail.startswith(n) for n in DOC_LEVEL_NOUNS):
            return True
        if any(tail.startswith(n) for n in MEMBER_SCOPE_WORDS):
            return False
        if any(w in t for w in MEMBER_SCOPE_WORDS):
            return False
        return True
    return "根" in t


def is_negated_line(text):
    return any(w in text for w in LINE_NEGATIONS)


def clauses_of(line):
    """把一段文本按子句切开。→ [(子句文本, [(span_text, span)])]

    切分点只取分隔符；行内代码 span 整体归到它**起始位置**所在的子句，
    这样「顶层 | `<esml>` | 根」这种表格行里，标记词与 span 仍在同一子句。
    """
    bounds = {0, len(line)}
    for ch in CLAUSE_SEP:
        for m in re.finditer(re.escape(ch), line):
            bounds.add(m.start())
            bounds.add(m.end())
    pts = sorted(bounds)

    spans = [(m.group(1), m.start(1)) for m in INLINE_CODE.finditer(line)]
    out = []
    for a, b in zip(pts, pts[1:]):
        if a == b:
            continue
        seg = line[a:b]
        inner = [(s, sp) for s, sp in spans if a <= sp < b]
        out.append((seg, inner))
    return out


def extract_root_names(segment, allow_bare_list=False, require_marker=True):
    """从一段文本（散文行或根声明列）里抽元素名 → [名字]。

    * 子句级否定（`不是文档根` 等）⇒ 该子句整句不算；
    * require_marker：子句里必须自带根标记词（根声明列除外 —— 列头「根」
      本身就是标记）；
    * 行内代码 span：能解析成 XML 就取根元素名，否则取最外层标签名；
    * allow_bare_list：额外收 `/` 分隔的裸列表（`units/variableTypes/…`）；
    * **「`<X>` 根」句式独占**：紧跟在「根」前面的那个 span 才是被声明的根，
      同一子句里并列提到的别的名字不算 —— §1.1 标题
      「（`<esml>` 根 · `<metadata>`）」里 `<metadata>` 只是骨架的一项，
      不是「它是根」的声明。
    """
    out = []
    for clause, spans in clauses_of(segment):
        if any(n in clause for n in CLAUSE_NEGATIONS):
            continue
        if require_marker and not clause_has_root_marker(clause):
            continue
        anchored = [
            s for s, pos in spans
            if SPAN_FOLLOWED_BY_ROOT.match(segment[pos + len(s) + 2:])
        ]
        for s in (anchored or [s for s, _ in spans]):
            out.extend(mentions_of(s))
        if allow_bare_list:
            outside = INLINE_CODE.sub(" ", clause)
            for m in BARE_LIST.finditer(outside):
                for part in m.group(1).split("/"):
                    if ELEMENT_NAME.fullmatch(part):
                        out.append(part)
    return out


def table_blocks(prose):
    """把散文行切成 markdown 表格块。→ [[(行号, 行文本)]]"""
    blocks = []
    cur = []
    for lineno, line in prose:
        if line.lstrip().startswith("|"):
            cur.append((lineno, line))
        else:
            if cur:
                blocks.append(cur)
                cur = []
    if cur:
        blocks.append(cur)
    return blocks


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def paragraphs(prose):
    """把散文行按**段落**归并（markdown 味道：空行 / 列表项 / 标题 / 表格行另起段）。

    → [(起始行号, 段落文本)]

    为什么要按段而不是按行：规范里常有「标记词在一行、清单在下一行」的写法
    （如 §13 的文档根清单），按行切会把清单切碎、抽不全。
    """
    out = []
    cur = []
    start = None
    for lineno, line in prose:
        stripped = line.strip()
        new_para = (not stripped) or stripped.startswith(("- ", "* ", "#", "|", ">", "1. "))
        if cur and new_para:
            out.append((start, " ".join(cur)))
            cur = []
        if not stripped:
            continue
        if not cur:
            start = lineno
            cur = [stripped]
        else:
            cur.append(stripped)
    if cur:
        out.append((start, " ".join(cur)))
    return out


def spec_root_declarations(spec_path):
    """SPEC 正文里被描述为**文档根**的元素名 → {名字: [证据行号]}。"""
    text = spec_path.read_text(encoding="utf-8")
    prose = strip_fences(text)

    # 表头含根标记的表 ⇒ 有「根」列，只从那一列抽（不从「覆盖」列抽）。
    root_cols = {}
    for blk in table_blocks(prose):
        if len(blk) < 2:
            continue
        header = split_row(blk[0][1])
        cols = [i for i, c in enumerate(header) if has_root_marker(c)]
        if not cols:
            continue
        for lineno, line in blk[2:]:
            root_cols[lineno] = cols

    out = {}
    for lineno, para in paragraphs(prose):
        if para.lstrip().startswith("|"):
            cells = split_row(para)
            picked = [cells[i] for i in root_cols.get(lineno, []) if i < len(cells)]
            seg = " ".join(picked)
            in_root_table = bool(root_cols.get(lineno))
        else:
            seg = para
            in_root_table = False
        if not seg.strip():
            continue
        if is_negated_line(seg):
            continue
        names = extract_root_names(
            seg, allow_bare_list=in_root_table, require_marker=not in_root_table
        )
        for name in names:
            out.setdefault(name, [])
            if lineno not in out[name]:
                out[name].append(lineno)
    return out


def spec_example_tops(spec_path):
    """SPEC 的 ```` ```xml ```` 示例块的最外层元素 → [(行号, 元素名)]。"""
    text = spec_path.read_text(encoding="utf-8")
    out = []
    for lineno, body in xml_blocks(text):
        s = re.sub(r"<!--.*?-->", "", body, flags=re.S)
        names = outer_tags(s)
        if names:
            out.append((lineno, names[0]))
    return out


# ------------------------------------------------------------------ by-design 登记表
def load_bydesign(path):
    """→ {(kind, name): reason}。kind ∈ {spec-root, entry-root}。"""
    table = {}
    if not path.exists():
        return table
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            sys.exit(f"[parity] {path.name}:{lineno} 必须 3 列（kind/name/reason）")
        kind, name, reason = parts
        if kind not in ("spec-root", "entry-root"):
            sys.exit(f"[parity] {path.name}:{lineno} kind={kind!r} 非法：只许 spec-root / entry-root")
        if not reason.strip():
            sys.exit(f"[parity] {path.name}:{lineno} reason 为空 —— 没写清为什么按设计不改")
        table[(kind, name)] = reason
    return table


# ------------------------------------------------------------------ 对账
def collect(xsd_dir, entry_schema, spec_path):
    return {
        "canon": canonical_roots(xsd_dir),
        "entry": entry_roots(entry_schema),
        "spec": spec_root_declarations(spec_path),
        "examples": spec_example_tops(spec_path),
        "declared": declared_element_names(xsd_dir),
    }


def findings(data, bydesign=None):
    """三方对账 → [(kind, 元素名, 说明)]。kind ∈ C1..C5。"""
    bydesign = bydesign or {}
    canon = set(data["canon"])
    entry = set(data["entry"])
    spec = set(data["spec"])
    out = []

    for n in sorted(entry - canon):
        if ("entry-root", n) in bydesign:
            continue
        out.append(("C1", n, "入口层多收：canonical 层没有这个全局元素 ⇒ 假绿"))
    for n in sorted(canon - entry):
        if ("entry-root", n) in bydesign:
            continue
        out.append(("C2", n, "入口层漏收：canonical 层的全局根没进根清单 ⇒ 误拒"))
    for n in sorted(spec - canon):
        if ("spec-root", n) in bydesign:
            continue
        out.append(("C3", n, "SPEC 把它写成文档根，canonical 层却没有这个全局元素"))
    for n in sorted(canon - spec):
        if ("spec-root", n) in bydesign:
            continue
        out.append(("C4", n, "canonical 层的全局根，SPEC 正文里没被写成文档根"))
    for lineno, name in data["examples"]:
        if name not in data["declared"]:
            out.append(("C5", name, f"SPEC 第 {lineno} 行的示例顶层元素，XSD 里根本没有同名声明"))
    return out


# ------------------------------------------------------------------ 报告
def report(data, fs, bydesign, stream):
    w = stream.write
    canon, entry, spec = data["canon"], data["entry"], data["spec"]

    w("[parity] 三方集合\n")
    w(f"  R_canon  canonical 层全局元素 ({len(canon):2}): {' '.join(sorted(canon))}\n")
    w(f"  R_entry  入口层全局元素     ({len(entry):2}): {' '.join(sorted(entry))}\n")
    w(f"  R_spec   SPEC 文档根声明     ({len(spec):2}): {' '.join(sorted(spec))}\n")

    w("\n[parity] SPEC 根声明的证据行\n")
    for n in sorted(spec):
        w(f"  {n:16} SPEC.md:{','.join(str(x) for x in spec[n])}\n")

    w("\n[parity] SPEC 示例块的最外层元素（信息项：多数是片段，不是文档根）\n")
    for lineno, name in data["examples"]:
        kind = "文档根" if name in canon else "片段"
        w(f"  SPEC.md:{lineno:<5} <{name}>  {kind}\n")

    if bydesign:
        w("\n[parity] by-design 登记（判为「不改」）\n")
        for (kind, name), reason in sorted(bydesign.items()):
            w(f"  {kind:11} {name:16} {reason}\n")


def self_test(stream):
    """5 好 4 坏：好树必须 0 红，坏树必须红。任一翻转 = 自证失败。

    坏例照着历史事故重演：人为删一个根（漏收）、人为多一个根（多收）。
    """
    w = stream.write
    results = []

    def build(tmp, canon_names, entry_names, spec_roots, extra_spec=""):
        xsd = tmp / "xsd"
        xsd.mkdir(parents=True, exist_ok=True)
        canon = xsd / "esml-canonical-basic.xsd"
        canon.write_text(
            '<?xml version="1.0"?>\n'
            '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">\n'
            + "".join(
                f'  <xs:element name="{n}" type="xs:string"/>\n' for n in canon_names
            )
            + "</xs:schema>\n",
            encoding="utf-8",
        )
        entry = xsd / "esml-v1.xsd"
        entry.write_text(
            '<?xml version="1.0"?>\n'
            '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">\n'
            + "".join(
                f'  <xs:element name="{n}" type="xs:string"/>\n' for n in entry_names
            )
            + "</xs:schema>\n",
            encoding="utf-8",
        )
        spec = tmp / "SPEC.md"
        spec.write_text(
            "# 合成规范\n\n"
            "## 1. 根\n\n"
            "文档根声明（顶层）："
            + " / ".join(f"`<{n}>`" for n in spec_roots)
            + "。\n"
            + extra_spec,
            encoding="utf-8",
        )
        return xsd, entry, spec

    cases = [
        # (名字, 应否为绿, canonical 根, 入口根, SPEC 根声明, 追加正文)
        ("好 1：三方一致（2 根）", True,
         ["esml", "units"], ["esml", "units"], ["esml", "units"], ""),
        ("好 2：三方一致（4 根）", True,
         ["esml", "units", "project", "metadata"],
         ["esml", "units", "project", "metadata"],
         ["esml", "units", "project", "metadata"], ""),
        # 好 3：SPEC 明说某元素「不是文档根」⇒ 该名字不得进根声明集。
        #      这条必须是**实的**：把分句否定词表拆掉，它就要变红（见 --self-test 注释）。
        ("好 3：SPEC 明说 <innerShell> 不是文档根", True,
         ["esml", "units"], ["esml", "units"], ["esml", "units"],
         "\n`<innerShell>` 不是文档根，只是 `<esml>` 内的外层壳。\n"),
        # 好 4：成员级「顶层」——「顶层 `<metaSeg>` 声明计算域」说的是 `<esml>` 的
        #      一个**成员段**，不是文档根。这条必须**实的**：把「顶层 + 行内代码
        #      span ⇒ 成员级」这条规则拆掉，`<metaSeg>` 就会漏进根声明集 → C3 变红。
        ("好 4：成员级「顶层」不算文档根", True,
         ["esml", "units"], ["esml", "units"], ["esml", "units"],
         "\n**计算域声明**：顶层 `<metaSeg><domain name/></metaSeg>` 声明计算域。\n"),
        # 好 5：「`<X>` 根」句式独占——并列提到的别的名字不算根声明。
        #      拆掉这条规则，`<metaSeg>` 会漏进根声明集 → C3 变红。
        ("好 5：并列提及不算根声明", True,
         ["esml", "units"], ["esml", "units"], ["esml", "units"],
         "\n### 1.1 文档骨架（`<esml>` 根 · `<metaSeg>`）\n"),
        # ↓ 坏例
        ("坏 1：入口层删了一个根（漏收）", False,
         ["esml", "units"], ["esml"], ["esml", "units"], ""),
        ("坏 2：入口层多了一个根（多收）", False,
         ["esml", "units"], ["esml", "units", "schedule"], ["esml", "units"], ""),
        ("坏 3：SPEC 把 XSD 不认的写成根", False,
         ["esml", "units"], ["esml", "units"], ["esml", "units", "bogusRoot"], ""),
        ("坏 4：canonical 有根而 SPEC 只字不提", False,
         ["esml", "units", "project"], ["esml", "units", "project"], ["esml", "units"], ""),
    ]

    with tempfile.TemporaryDirectory(prefix="esml-parity-selftest-") as td:
        tmp = Path(td)
        for name, should_pass, canon, entry, spec, extra in cases:
            case_dir = tmp / name.replace(" ", "_").replace(":", "_").replace("（", "_").replace("）", "_")
            case_dir.mkdir()
            xsd, entry_path, spec_path = build(case_dir, canon, entry, spec, extra)
            data = collect(xsd, entry_path, spec_path)
            fs = findings(data)
            ok = not fs
            results.append((name, should_pass, ok, fs))

    w("[self-test] 构造样例 5 好 4 坏 —— 证明本检查器真的会红\n")
    failures = 0
    for name, should_pass, ok, fs in results:
        verdict = "PASS" if ok == should_pass else "BROKEN"
        if ok != should_pass:
            failures += 1
        want = "应判绿" if should_pass else "应判红"
        got = "判绿了" if ok else "判红了"
        detail = "" if ok else "（" + "；".join(f"{k}:{n}" for k, n, _ in fs) + "）"
        w(f"  [{verdict}] {name:34} {want} → 实际{got}{detail}\n")

    # 反向自检：故意让 SPEC 声明一个 XSD 不认的根，检查器必须抓到它 ——
    # 若这一条抓不到，说明判定被 by-design 登记表或抽取规则架空了。
    with tempfile.TemporaryDirectory(prefix="esml-parity-reverse-") as td:
        tmp = Path(td)
        xsd, entry_path, spec_path = build(tmp, ["esml"], ["esml"], ["esml", "ghostRoot"])
        fs = findings(collect(xsd, entry_path, spec_path))
    hit = [f for f in fs if f[0] == "C3" and f[1] == "ghostRoot"]
    if hit:
        w("  [PASS] 反向自检：SPEC 凭空声明的根 <ghostRoot> 被 C3 抓到\n")
    else:
        w("  [PASS] 反向自检失效 —— C3 没抓到 <ghostRoot>，抽取规则或登记表被架空了\n")
        failures += 1

    failures += mutation_test(stream)
    return failures


def mutation_test(stream):
    """在**真实树**的副本上做人为变异：删一个根 / 多一个根，必须真的变红。

    合成树的自证证明「判定逻辑会红」；这一段证明「在本仓这棵真树上也会红」——
    抽取规则、登记表、文件路径要是哪一环坏了，这里立刻 BROKEN。
    """
    import shutil

    w = stream.write
    w("\n[self-test] 真实树上的变异测试（人为删一个根 / 多一个根 / SPEC 凭空加一个根）\n")
    failures = 0

    with tempfile.TemporaryDirectory(prefix="esml-parity-mut-") as td:
        root_tmp = Path(td)

        def snapshot(tag):
            d = root_tmp / tag
            d.mkdir()
            shutil.copytree(XSD_DIR, d / "xsd")
            shutil.copy(SPEC_MD, d / "SPEC.md")
            return d

        base_dir = snapshot("base")
        base = findings(
            collect(base_dir / "xsd", base_dir / "xsd" / "esml-v1.xsd", base_dir / "SPEC.md")
        )
        base_set = {(k, n) for k, n, _ in base}

        # 变异 1：入口层删掉一个根（历史事故：漏收）
        victim = "metadata"
        mut_dir = snapshot("mut1")
        entry = mut_dir / "xsd" / "esml-v1.xsd"
        text = entry.read_text(encoding="utf-8")
        new_text, n_sub = re.subn(
            rf'  <xs:element name="{victim}">.*?</xs:element>\n', "", text, count=1, flags=re.S
        )
        entry.write_text(new_text, encoding="utf-8")
        fs = findings(collect(mut_dir / "xsd", entry, mut_dir / "SPEC.md"))
        got = {(k, n) for k, n, _ in fs}
        ok = (n_sub == 1) and (("C2", victim) in got) and base_set <= got
        w(
            f"  [{'PASS' if ok else 'BROKEN'}] 变异 1：入口层删掉 <{victim}>（漏收）"
            f" ⇒ {'变红：' + str(sorted(got - base_set)) if ('C2', victim) in got else '没变红！'}\n"
        )
        if not ok:
            failures += 1

        # 变异 2：入口层多一个根（历史事故：多收）
        mut_dir = snapshot("mut2")
        entry = mut_dir / "xsd" / "esml-v1.xsd"
        text = entry.read_text(encoding="utf-8")
        entry.write_text(
            text.replace(
                "</xs:schema>", '  <xs:element name="ghostRoot" type="xs:string"/>\n\n</xs:schema>'
            ),
            encoding="utf-8",
        )
        fs = findings(collect(mut_dir / "xsd", entry, mut_dir / "SPEC.md"))
        got = {(k, n) for k, n, _ in fs}
        ok = ("C1", "ghostRoot") in got and base_set <= got
        w(
            f"  [{'PASS' if ok else 'BROKEN'}] 变异 2：入口层多一个 <ghostRoot>（多收）"
            f" ⇒ {'变红：' + str(sorted(got - base_set)) if ('C1', 'ghostRoot') in got else '没变红！'}\n"
        )
        if not ok:
            failures += 1

        # 变异 3：SPEC 凭空多一个根声明
        mut_dir = snapshot("mut3")
        spec = mut_dir / "SPEC.md"
        spec.write_text(
            spec.read_text(encoding="utf-8") + "\n文档根：`<ghostRoot>`。\n", encoding="utf-8"
        )
        fs = findings(collect(mut_dir / "xsd", mut_dir / "xsd" / "esml-v1.xsd", spec))
        got = {(k, n) for k, n, _ in fs}
        ok = ("C3", "ghostRoot") in got and base_set <= got
        w(
            f"  [{'PASS' if ok else 'BROKEN'}] 变异 3：SPEC 凭空写一个根 <ghostRoot>"
            f" ⇒ {'变红：' + str(sorted(got - base_set)) if ('C3', 'ghostRoot') in got else '没变红！'}\n"
        )
        if not ok:
            failures += 1

        # 变异 4：canonical 层多一个全局元素而入口层没收（漏收）
        mut_dir = snapshot("mut4")
        canon = mut_dir / "xsd" / "esml-canonical-basic.xsd"
        text = canon.read_text(encoding="utf-8")
        canon.write_text(
            text.replace(
                "</xs:schema>", '  <xs:element name="newGlobal" type="xs:string"/>\n\n</xs:schema>'
            ),
            encoding="utf-8",
        )
        fs = findings(
            collect(mut_dir / "xsd", mut_dir / "xsd" / "esml-v1.xsd", mut_dir / "SPEC.md")
        )
        got = {(k, n) for k, n, _ in fs}
        ok = ("C2", "newGlobal") in got
        w(
            f"  [{'PASS' if ok else 'BROKEN'}] 变异 4：canonical 多一个全局元素而入口层没收"
            f" ⇒ {'变红：' + str(sorted(got - base_set)) if ('C2', 'newGlobal') in got else '没变红！'}\n"
        )
        if not ok:
            failures += 1

    return failures


# ------------------------------------------------------------------ 主流程
def main(argv=None):
    ap = argparse.ArgumentParser(description="ESML SPEC ↔ XSD 文档根对账门")
    ap.add_argument("--report", action="store_true", help="附带 SPEC 根声明清单与证据行")
    ap.add_argument("--self-test", action="store_true", help="只跑 5 好 4 坏自证")
    args = ap.parse_args(argv)

    if args.self_test:
        return 1 if self_test(sys.stdout) else 0

    bydesign = load_bydesign(BYDESIGN_TSV)
    data = collect(XSD_DIR, ENTRY_SCHEMA, SPEC_MD)
    fs = findings(data, bydesign)

    if args.report:
        report(data, fs, bydesign, sys.stdout)

    w = sys.stdout.write
    w("\n[parity] 对账结果\n")
    if not fs:
        w("  三方一致：入口层根清单 = canonical 层全局元素集 = SPEC 文档根声明。0 处差异。\n")
        return 0

    by_kind = {}
    for kind, name, msg in fs:
        by_kind.setdefault(kind, []).append((name, msg))
    labels = {
        "C1": "入口层多收根（假绿）",
        "C2": "入口层漏收根（误拒）",
        "C3": "SPEC 声明了 XSD 不认的文档根",
        "C4": "canonical 有全局根而 SPEC 未写成文档根",
        "C5": "SPEC 示例顶层元素 XSD 未声明",
    }
    for kind in ("C1", "C2", "C3", "C4", "C5"):
        if kind not in by_kind:
            continue
        w(f"  [{kind}] {labels[kind]} —— {len(by_kind[kind])} 处\n")
        for name, msg in by_kind[kind]:
            ev = ""
            if kind in ("C3", "C4") and name in data["spec"]:
                ev = f"（证据 SPEC.md:{','.join(str(x) for x in data['spec'][name])}）"
            w(f"      <{name}>  {msg} {ev}\n")
    w(f"\n[parity] 共 {len(fs)} 处差异。裁决见 docs/design/xsd-spec-parity.md\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())

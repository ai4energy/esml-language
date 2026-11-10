#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""跨仓 XSD 漂移闸：本仓 `xsd/` ⇄ 引擎仓 `$ESML_ENGINE_DIR/schema/`。

比三样，逐组分歧对 `tools/engine-drift.tsv` 台账裁决：

  1. 同名 complexType 的**属性集**（含同名单一元素的匿名内联类型属性集，
     宿主命名 `anon@文件名:来源行`）；
  2. 同名 complexType 的**子元素集**（递归：sequence/choice 里每一层都算，
     同一宿主里重名子元素只计一次）；
  3. **全局根元素集**（schema 直接子元素）。

判据：**每一组实测分歧都必须在 TSV 里有一条对应记录**才不算红。
TSV 里有记录、但实测该分歧已不存在（比如 W1 已把属性补入 / 旧拼写已删）
→ 打印 `[已消解] …（记录可删）`，**退出码不受影响** —— 四单任意次序
合并都不炸。

退出码：`0` 全部分歧已裁决（或引擎仓不在，打印跳过）·
`1` 有未裁决分歧 · `2` 脚本自身错（含自证失败、台账格式错）。

用法：
    python3 tools/check-engine-xsd-parity.py           # 机判（make check 第三道）
    python3 tools/check-engine-xsd-parity.py --report  # 另打印三张实测表
    python3 tools/check-engine-xsd-parity.py --self-test

引擎仓目录：`$ESML_ENGINE_DIR`（缺省 `~/esml-engine-user3`）。
目录不存在时打印「跳过（引擎仓不在）」并以退出码 0 结束：不静默、不误红。

依赖：lxml（与 `docs/validate_examples.py` 同依赖）。
"""
import argparse
import os
import sys
from pathlib import Path

try:
    from lxml import etree
except ImportError:  # pragma: no cover
    sys.exit("需要 lxml：pip install lxml")

XS = "{http://www.w3.org/2001/XMLSchema}"
REPO = Path(__file__).resolve().parent.parent
LANG_XSD = REPO / "xsd"
TSV = REPO / "tools" / "engine-drift.tsv"
TSV_COLS = ("kind", "host", "item", "direction", "依据", "裁决日")
DIRECTIONS = ("engine-wins", "lang-wins", "both-missing", "open")

# 记录 kind → 实测分歧 kind 的对应（root 行实测落在全局元素分歧里）。
_KIND_REAL = {"attr": "attr", "child": "child", "root": "root"}


def norm(s):
    """**仅用于把台账行配到实测分歧**的折叠键：台账以**任一侧拼写**记分歧
    （如引擎侧 `a-part` 对语言侧 `aPart`），按小写去连字符折叠后两者配到同一条。
    ⚠ 折叠**绝不**用于判分歧是否存在——`aPart` 与 `a-part` 都折成 `apart`，
    拿折叠集判存在性会把 kebab/camel 分歧本身吞掉而误判「已消解」
    （存在性判定见 `diff_sides` 的已消解循环：用**原样成员**）。"""
    return s.lower().replace("-", "").replace("_", "")


def engine_dir():
    env = os.environ.get("ESML_ENGINE_DIR")
    return Path(env).expanduser() if env else Path.home() / "esml-engine-user3"


def die_selftest(msg):
    print("[self-test] 自证失败：%s" % msg)
    sys.exit(2)


def die_self(msg):
    print("脚本自身错：%s" % msg)
    sys.exit(2)


def schema_files(root_dir):
    """仓内 schema 全集：含跨文件 include 的可达闭包（本仓与引擎仓都是
    basic/compute → include → common 这一棵树）。"""
    seen, out = set(), []
    stack = sorted(root_dir.glob("*.xsd"))
    while stack:
        f = stack.pop()
        if f in seen or not f.exists():
            continue
        seen.add(f)
        out.append(f)
        try:
            doc = etree.parse(str(f))
        except etree.XMLSyntaxError as exc:
            die_self("解析 %s 失败：%s" % (f, exc))
        for inc in doc.getroot():
            if inc.tag in (XS + "include", XS + "import"):
                loc = inc.get("schemaLocation")
                if loc:
                    stack.append((f.parent / loc).resolve())
    return sorted(seen)


def attr_names(elem):
    """宿主节点**直接声明**的属性名集合（不含 anyAttribute）。
    只取宿主的直接 `xs:attribute` 子元素：嵌套 complexType（如 `<ports>` /
    `<variables>` 的匿名内联）里的属性属于**别的宿主**，按各自宿主比，
    若用 .iter() 会把它们误并进本宿主。"""
    out = set()
    for a in elem:  # 仅直接子元素
        if a.tag == XS + "attribute":
            n = a.get("name")
            if n:
                out.add(n)
    return out


def child_names(elem):
    """宿主内容模型里声明的子元素名（重名去重）。

    只沿 `xs:sequence` / `xs:choice` / `xs:all` 递归；一旦进入
    `xs:element`（其内部是嵌套类型）或 `xs:complexType`（匿名内联），
    便**不再下钻**——那些内部元素属于各自嵌套宿主，按宿主名另比。"""
    out = set()
    CONTAINERS = (XS + "sequence", XS + "choice", XS + "all")

    def walk(node):
        for c in node:
            if c.tag in CONTAINERS:
                walk(c)
            elif c.tag == XS + "element":
                n = c.get("name")
                if n:
                    out.add(n)
            # complexType / element 内部不再下钻

    # 宿主本身（complexType 或 element）的直接内容模型。
    # 全局 / 命名元素宿主：其内容模型在**直接**匿名 complexType 里——那是
    # 宿主自己的类型，须下钻一层（再往内的嵌套宿主仍不下钻）。
    start = elem
    if elem.tag == XS + "element":
        anon = elem.find(XS + "complexType")
        if anon is not None:
            start = anon
    if start.tag in CONTAINERS or start.tag == XS + "complexType" or start.tag == XS + "element":
        walk(start)
    return out


def hosts_of(doc):
    """本文件全部宿主：命名 complexType + 全局元素，均带来源行与内联属性集。
    宿主 = (host名, attrs, children)。匿名内联类型不入宿主表——它们与命名宿主
    在「同宿主不同名」时按各自宿主名（匿名者以 `anon@文件:行` 命名）分别比对。"""
    hosts = {}
    root = doc.getroot()
    for e in root.iter():
        if e.tag != XS + "complexType":
            continue
        name = e.get("name")
        if not name:
            continue  # 匿名内联：其属性集随所在元素/宿主被比
        attrs, children = attr_names(e), child_names(e)
        key = name
        if key in hosts:
            # 同名宿主在 include 闭包里重复（如 common 被两次 include）：
            # 取属性/子元素并集，两侧同规则，不影响集合差。
            prev = hosts[key]
            hosts[key] = (prev[0] | attrs, prev[1] | children)
        else:
            hosts[key] = (attrs, children)
    for el in root:  # 全局元素（schema 直接子元素 = 文档根）
        if el.tag != XS + "element":
            continue
        name = el.get("name")
        if not name:
            continue
        anon = el.find(XS + "complexType")
        attrs = attr_names(anon) if anon is not None else set()
        # 全局元素的子元素集同样含匿名内联部分（如 <esml> 根下的
        # <portTypes> 内联容器）——它**就是**这个根文档的子元素集。
        hosts[name] = (hosts.get(name, (set(), set()))[0] | attrs,
                       hosts.get(name, (set(), set()))[1] | child_names(el))
    return hosts


def anon_singletons(doc, fname):
    """同名单一元素的匿名内联类型属性集：`anon@文件名:nth`。

    「同名单一」= 该元素名在**本文件**里只出现一次（跨 include 闭包重名
    的常见元素如 <partition> 不入此列，它们按宿主名比）。键用「本文件里
    第 nth 个（文档序）带匿名内联 complexType 的同名单一元素」，而非原始
    行号——行号在两侧文件间不稳定（引擎 / 语言仓排版不同），无法作为
    跨仓比对键；nth 计数在两侧各自文件里按同一规则得出，可比。"""
    out = {}
    root = doc.getroot()
    counts = {}
    for e in root.iter(XS + "element"):
        n = e.get("name")
        if n:
            counts[n] = counts.get(n, 0) + 1
    nth = 0
    for e in root.iter(XS + "element"):
        n = e.get("name")
        if not n or counts[n] != 1:
            continue
        if e.find(XS + "complexType") is None:
            continue
        nth += 1
        out["anon@%s:%d" % (fname, nth)] = attr_names(e.find(XS + "complexType"))
    return out


def load_side(root_dir):
    hosts, anons, roots = {}, {}, set()
    for f in schema_files(root_dir):
        doc = etree.parse(str(f))
        h = hosts_of(doc)
        for k, v in h.items():
            if k in hosts:
                prev = hosts[k]
                hosts[k] = (prev[0] | v[0], prev[1] | v[1])
            else:
                hosts[k] = v
        for k, v in anon_singletons(doc, f.name).items():
            if k in anons:
                anons[k] |= v
            else:
                anons[k] = v
        for el in doc.getroot():
            if el.tag == XS + "element" and el.get("name"):
                roots.add(el.get("name"))
    return hosts, anons, roots


def diff_sides(lang, eng, norm_index, report):
    """对两侧结构做三张比对，返回 (未裁决, 已消解, 实测表)。"""
    l_hosts, l_anons, l_roots = lang
    e_hosts, e_anons, e_roots = eng
    undetected, resolved = [], []
    tables = {"attr": {}, "child": {}, "root": {}}

    def check(kind, host, lang_set, eng_set, side_names):
        tables[kind][host] = (sorted(lang_set), sorted(eng_set))
        if lang_set == eng_set:
            return
        for item in sorted(lang_set | eng_set):
            in_l, in_e = item in lang_set, item in eng_set
            if in_l == in_e:
                continue  # 两侧共有：不是分歧
            rec = norm_index.get((kind, host, norm(item)))
            side = ("lang 独有" if in_l else "引擎独有")
            if rec is None:
                undetected.append(("%s 分歧 %s：%s 侧%s，台账无记录"
                                   % (kind, host, item, side)))
            # 台账有记录 ⇔ 已裁决（item 拼写按 norm() 折叠后配到台账行；
            # 存在性本身仍按上方**原样**成员判，见已消解循环）

    # ①② 宿主（命名 complexType + 全局元素）：属性集 / 子元素集
    for host in sorted(set(l_hosts) | set(e_hosts)):
        la, lc = l_hosts.get(host, (set(), set()))
        ea, ec = e_hosts.get(host, (set(), set()))
        check("attr", host, la, ea, ("lang", "engine"))
        check("child", host, lc, ec, ("lang", "engine"))
    # ②续 同名单一元素匿名内联属性集
    for host in sorted(set(l_anons) | set(e_anons)):
        check("attr", host, l_anons.get(host, set()),
              e_anons.get(host, set()), ("lang", "engine"))
    # ③ 全局根元素集
    check("root", "—", l_roots, e_roots, ("lang", "engine"))

    # 台账里「已消解」记录：实测已无此分歧。
    # 判据（**原样成员**，绝不 norm 折叠）：分歧「仍在」⇔ 实测集里存在某个
    # **原样** item x，满足 norm(x)==nitem 且 (x in lang) != (x in eng)。
    # 不能拿 norm() 折叠后的集合判存在性——那样 aPart 与 a-part 都折成 apart、
    # 两侧「都含」apart，kebab/camel 这一分歧本身会被吞掉而恒判「已消解」
    # （正是本次反证出的假阳性）。折叠只用于把**台账行**配到实测分歧。
    for (kind, host, nitem), rec in sorted(norm_index.items()):
        item = nitem  # 归一键，仅用于打印；存在性判定用原样成员
        tkind = _KIND_REAL.get(kind)
        if tkind is None:
            die_self("台账 kind 非法：%r（应为 %s）"
                     % (kind, "/".join(sorted(_KIND_REAL))))
        if tkind == "root":
            lset, eset, host_eff = (tables["root"]["—"][0],
                                     tables["root"]["—"][1], "—")
        else:
            lset, eset = tables[tkind].get(host, ([], []))
            host_eff = host
        live = any(norm(x) == nitem and (x in lset) != (x in eset)
                   for x in set(lset) | set(eset))
        if live:
            continue  # 分歧实测仍在 ⇒ 已裁决（上方 check 已确认有记录）
        resolved.append((tkind, host_eff, item, rec))
    return undetected, resolved, tables


def read_tsv():
    if not TSV.exists():
        die_self("台账缺失：%s" % TSV)
    tsv = {}
    for i, line in enumerate(TSV.read_text(encoding="utf-8").splitlines(), 1):
        if i == 1 and line.split("\t") == list(TSV_COLS):
            continue
        if not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) != 6 or cols[0] not in _KIND_REAL or cols[3] not in DIRECTIONS:
            die_self("台账第 %d 行格式错：%r" % (i, line))
        tsv[(cols[0], cols[1], cols[2])] = (cols[3], cols[4], cols[5])
    # 归一化索引：item 按 norm() 折叠，host 原样（宿主名两侧一致）。
    norm_index = {(k, h, norm(it)): v for (k, h, it), v in tsv.items()}
    return tsv, norm_index


def self_test():
    """好树 0 红 · 坏树（未登记分歧）必红 · 已消解记录不红。失败退出码 2。"""
    from lxml import etree as et
    import tempfile
    xsd_ns = "http://www.w3.org/2001/XMLSchema"

    def write_schema(d, body):
        (d / "s.xsd").write_text(
            '<?xml version="1.0"?>\n'
            '<xs:schema xmlns:xs="%s">%s'
            '<xs:element name="r" type="xs:string"/></xs:schema>\n'
            % (xsd_ns, body),
            encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="esml-parity-selftest-") as td:
        t = Path(td)
        lang, eng = t / "lang", t / "eng"
        # —— 好树：两侧完全一致 + 一条已消解台账记录 ⇒ 0 红
        body_l = ('<xs:complexType name="T"><xs:attribute name="a" type="xs:string"/>'
                 '<xs:sequence><xs:element name="c" type="xs:string"/></xs:sequence>'
                 '</xs:complexType>')
        body_e = body_l
        (lang).mkdir(exist_ok=True)
        (eng).mkdir(exist_ok=True)
        write_schema(lang, body_l)
        write_schema(eng, body_e)
        l_hosts, l_anons, l_roots = load_side(lang)
        e_hosts, e_anons, e_roots = load_side(eng)
        tsv_good = {("attr", "T", "gone"): ("lang-wins", "自证", "2026-01-01")}
        und, res, _ = diff_sides(
            (l_hosts, l_anons, l_roots), (e_hosts, e_anons, e_roots), tsv_good, None)
        if und:
            die_selftest("好树出现未裁决分歧：%s" % und)
        if not res:
            die_selftest("好树未识别出已消解记录")
        # —— 坏树：引擎侧多一个属性，台账未登记 ⇒ 必红
        body_e2 = ('<xs:complexType name="T"><xs:attribute name="a" type="xs:string"/>'
                   '<xs:attribute name="z" type="xs:string"/>'
                   '<xs:sequence><xs:element name="c" type="xs:string"/>'
                   '</xs:sequence></xs:complexType>')
        write_schema(eng, body_e2)
        e_hosts2, _, _ = load_side(eng)
        und2, _, _ = diff_sides(
            (l_hosts, l_anons, l_roots), (e_hosts2, e_anons, e_roots), tsv_good, None)
        if not any("T" in u and "z" in u for u in und2):
            die_selftest("坏树未红：未登记分歧未被检出（%s）" % und2)
        # —— 假阳性护栏：台账记 `a-part`，两侧分别是 `aPart` / `a-part`
        #    （norm 折叠后都是 `apart`）。分歧**实测仍在**，闸门必须判
        #    「分歧仍在」（台账记录匹配上、不报已消解），**不**判未裁决红。
        #    若已消解循环误用 norm 折叠判存在性，会把此分歧吞成「已消解」
        #    而漏红 —— 正是本次反证出的缺陷，故自证必须覆盖。
        write_schema(eng,
                     '<xs:complexType name="T"><xs:attribute name="a-part" type="xs:string"/>'
                     '<xs:sequence><xs:element name="c" type="xs:string"/></xs:sequence>'
                     '</xs:complexType>')  # 引擎侧 T 含 a-part
        write_schema(lang,
                     '<xs:complexType name="T"><xs:attribute name="aPart" type="xs:string"/>'
                     '<xs:sequence><xs:element name="c" type="xs:string"/></xs:sequence>'
                     '</xs:complexType>')  # 语言侧 T 含 aPart
        e_hosts3, e_anons3, e_roots3 = load_side(eng)
        l_hosts3, l_anons3, l_roots3 = load_side(lang)
        tsv_a = {("attr", "T", "a-part"): ("lang-wins", "自证", "2026-01-01")}
        norm_a = {("attr", "T", "apart"): tsv_a[("attr", "T", "a-part")]}
        und3, res3, _ = diff_sides(
            (l_hosts3, l_anons3, l_roots3),
            (e_hosts3, e_anons3, e_roots3), norm_a, None)
        # aPart / a-part 两侧各一个、norm 后同键 apart ⇒ 台账记录 a-part 匹配上：
        # 分歧「已裁决」（不红）。旧实现里 a-part 侧不叫 aPart ⇒ 未裁决红（假漏红
        # 的反面：把已裁决的活分歧报成未裁决）——断言必须 0 未裁决。
        if und3:
            die_selftest("kebab/camel 活分歧未匹配到台账记录（%s）" % und3)
        # 同时绝不能把它报成「已消解」——分歧实测仍在，折叠不得吞掉它。
        if any(r[2] == "apart" for r in res3):
            die_selftest("norm 折叠假阳性：aPart/a-part 活分歧被误判为已消解（%s）" % res3)
    print("[self-test] 好树 0 红 / 坏树（未登记分歧）必红 / 已消解记录不红 / "
          "norm 折叠不吞 kebab-camel 分歧：PASS")


def main():
    ap = argparse.ArgumentParser(description="跨仓 XSD 漂移闸")
    ap.add_argument("--report", action="store_true",
                    help="打印三张实测表（不改变退出码语义）")
    ap.add_argument("--self-test", action="store_true", help="自证后退出")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0

    edir = engine_dir()
    if not (edir / "schema").is_dir() and not edir.is_dir():
        print("跳过（引擎仓不在：%s）" % edir)
        return 0
    schema_dir = edir / "schema"
    if not schema_dir.is_dir():
        schema_dir = edir
    if not list(schema_dir.glob("*.xsd")):
        print("跳过（引擎仓不在：%s 无 *.xsd）" % schema_dir)
        return 0
    tsv, norm_index = read_tsv()
    try:
        lang = load_side(LANG_XSD)
        eng = load_side(schema_dir)
    except SystemExit:
        raise
    except Exception as exc:
        die_self("结构读取失败：%s" % exc)
    undetected, resolved, tables = diff_sides(lang, eng, norm_index, args.report)

    if args.report:
        for kind, title in (("attr", "① 同名 complexType 属性集"),
                           ("child", "② 同名 complexType 子元素集"),
                           ("root", "③ 全局根元素集")):
            print("== %s ==" % title)
            for host in sorted(tables[kind]):
                l, e = tables[kind][host]
                mark = "" if l == e else "  ← 分歧"
                print("   %-34s lang=%s | engine=%s%s" % (host, l, e, mark))
    for kind, host, item, (direction, basis, date) in resolved:
        print("[已消解] %s %s %s（%s；记录可删）" % (kind, host, item, basis))
    if undetected:
        for u in undetected:
            print("[未裁决] %s" % u)
        print("判红：%d 组分歧未在 %s 裁决" % (len(undetected), TSV.relative_to(REPO)))
        return 1
    print("跨仓 XSD 漂移：全部分歧已裁决（台账 %d 条，已消解 %d 条）"
          % (len(tsv), len(resolved)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

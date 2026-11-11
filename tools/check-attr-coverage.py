#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ESML 规范仓 · XSD 属性覆盖双向闸门（W29）+ 方向 C（W47）——W24 元素闸的姊妹闸。

【两张台账的职责（订单要求写死在这里）】
  attr-acceptance.tsv = 「零使用属性的引擎裁决」：`check-attr-acceptance.py`（W5）逐行
      实跑引擎 / 复核 (attr, host) 四元组，verdict ∈ {accepted, rejected-f7, rejected-legacy,
      rejected-ie, no-example}。它是**手建清单**——只复核清单内已有的行，清单本身漏没漏它不知道。
      本闸**只读**它，把它当作「登记来源」：某属性若已有 attr-acceptance 行，就不重复建台账。
  attr-coverage.tsv  = 「完整性对账（不许漏）」：本闸当场重算「声明 ↔ 示例」双向差集，
      保证**明天也不漏**——差集里的每个属性都要么有示例、要么在本台账有行兜着；
      台账行必须与当天差集闭合（补了示例/声明 ⇒ 删行或改 verdict，过时即红）。
      两表不重叠：acceptance 记「引擎怎么裁决」，coverage 记「有没有登记、登记是否还在差集里」。

台账：tools/attr-coverage.tsv
   kind  item(@属性名)  verdict  owner  evidence
   kind  值域：attribute（方向 A：XSD 声明了、非负例示例没用）
           example  （方向 B：非负例示例用了、XSD 没声明、也不在 anyAttribute 宿主上）
   verdict 值域：has-example（已落地，只作记录）/ pending（待落地）/
                by-design（刻意如此，依据写清）/ covered（已有 attr-acceptance 行裁决，
                指向它、本闸不重复建台账）
   owner  值域：W1 / W3 / W4 / engine-debt
   （有示例的属性**不必登记** ⇒ has-example 行只用来记「已落地」。）

门做什么（与元素闸 check-element-coverage.py 同形、同口径）：
  1. **头部计数当场重算**：台账头部「共 N 行」「pending：N 行」必须等于正文实际 ⇒ 红（rc=1）。
  2. **方向 A（声明 → 示例，按属性名）**：`xsd/*.xsd` 里每一个**命名** `xs:attribute`（含嵌套
     局部声明，同名去重）必须在 `**/*.esml`（跳过注释、跳过 `tools/negatives.tsv` 里**所有**
     负例）里至少被写过一次；没有 ⇒ 必须被「兜住」，兜法三选一：
       (i)  台账有一行 `attribute/@name` 且 verdict ∈ {pending, by-design}（语义同元素闸：
            pending 且 owner ∈ {W1,W3,W4} ⇒ 警告；owner=engine-debt ⇒ 红；by-design ⇒ 警告）；
       (ii) 台账有一行 `attribute/@name` 且 verdict=covered（已登记进 attr-acceptance）⇒ 不算缺；
       (iii) attr-acceptance.tsv 里已有该 attr 的行（**读**它当登记来源，不重复建台账）⇒ 不算缺。
     三选一都不满足 ⇒ 红（「声明了没人用、也没人登记 ⇒ 漏了」）。
     **方向 A 只问「属性名出现过没有」**——同名属性落在别的宿主上也不算落地（例：
     `port` 上的 `category=` 不能替 `portVariable` 上的 `category=` 落地）。
  3. **方向 B（示例 → 声明，按宿主判）**：每个**非负例**示例里写的属性名，要么在 XSD 里
     声明过，要么**落在声明了 `xs:anyAttribute` 的宿主上**（宽松放行，by-design），要么台账
     有一行 `example/@name` 且 verdict=by-design。缺任一 ⇒ 红。
     **最小可行判据（误差范围，订单 W29 要求说清）**：属性名是按**宿主元素**判的，而 attr-acceptance
     是按 `(attr, host)` 四元组记的，两者维度不同——所以本闸的方向 B 机判**只做「宿主级 anyAttribute
     宽松放行」**：先扫出 XSD 里每个 `xs:anyAttribute` 所属的**宿主 simpleType/complexType 名**，
     再对每处示例属性用 (host, attr) 反查该宿主是否 anyAttribute。误差范围：
       · 只认**同名**宿主（host 元素名相同 ⇒ 判同一 anyAttribute）；同名多宿主或宿主名在示例里
         有歧义时，**宁松勿错**——判「宽松放行」只豁免方向 B 的红，不会漏判真未声明属性（因为
         未声明属性无论宿主是否 anyAttribute，只要**不在** anyAttribute 宿主上且无 by-design 行，仍红）。
       · `xmlns` 是 XML 命名空间属性，**从不**是 xs:attribute ⇒ 方向 B 里单独按 by-design 放行。
  3.5 **方向 C（accepted → 示例，按宿主+属性，W47 新增）**：`attr-acceptance.tsv` 里每一行
     verdict=accepted（引擎收下、应当有示例）必须在**非负例**示例里找到 `host 元素名` 与
     `attr 名` **同时**出现（跳过注释、跳过 `negatives.tsv` 全部负例）；未落地 ⇒ 必须被
     `attr-coverage.tsv` 一行 `attribute/@attr` 且 verdict=pending 兜住（owner ∈ {W1,W3,W4}
     ⇒ 警告；其它 ⇒ 红，口径照方向 A）。
     **与方向 A 的区别**：A 管「声明 → 示例」（按**属性名**，同名落别处也算落地），C 管
     「accepted → 示例」（按 **(宿主元素名, 属性名)**，同名落别处**不**算）。误差范围：
     宿主按**元素名**匹配，不做类型解析——`<port>` 有两个类型（PortInstanceType 与
     PortMarkType）共用元素名，故 `(port, x)` 落地与否只按元素名判；attr-acceptance 行
     的 host 列即宿主元素名，两表同维度。
  4. **台账行与实测差集必须闭合**：台账登记的每个 @name，必须真落在当天重算的差集里
     （方向 A 的 attribute 行 verdict∈{pending,by-design} 必须「声明且无示例」；covered 行必须
     「声明且无示例且 attr-acceptance 覆盖」；方向 B 的 example 行必须「示例用且未声明且不在
     anyAttribute 宿主」）；反过来差集的每个属性也必须有行或 attr-acceptance 兜着。差集变了台账
     没跟上 ⇒ 红（「首版台账如实登记」的机判锁）。
  5. **`--self-test`**：临时目录造小树——好树（声明属性都有示例或 covered、示例属性都在
     声明/anyAttribute 内、accepted 行已落地）⇒ 零违规；坏树（删一个示例属性 + 加一个未声明
     属性，台账没跟上）⇒ 必须红；方向 C 坏树（accepted 行未落地且台账没兜）⇒ 必须红；
     计数锚错 ⇒ 必须红。任一翻转 = 自证失败 ⇒ rc=2。照抄元素闸的 self_test 结构。
  6. 脚本自身错误（缺表、列数不对、evidence 为空、name 缺 @ 前缀）⇒ rc=2。

用法
----
    tools/check-attr-coverage.py              # 双向覆盖 + 台账对账；0 = 零红
    tools/check-attr-coverage.py --self-test  # 自证闸门（好树零违规、坏树判红）

依赖：仅标准库（`re` / `glob` / `argparse` / `tempfile`）——属性名抽取用正则，与
check-attr-acceptance.py 同口径，故无 lxml / xmlschema / venv 也能跑。
"""

import argparse
import glob
import os
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TSV = Path(__file__).resolve().parent / "attr-coverage.tsv"
XSD_GLOB = "xsd/*.xsd"
NEGATIVES_TSV = Path(__file__).resolve().parent / "negatives.tsv"
ATTR_ACCEPTANCE_TSV = Path(__file__).resolve().parent / "attr-acceptance.tsv"

KINDS = ("attribute", "example")
VERDICTS = ("has-example", "pending", "by-design", "covered")
OWNERS = ("W1", "W3", "W4", "engine-debt")
# 方向 A：pending 且 owner ∈ 这个集合 ⇒ 追债中，警告不红（同元素闸口径）。
WARN_OWNERS = frozenset(("W1", "W3", "W4"))

COMMENT = re.compile(r"<!--.*?-->", re.S)
DECL_ATTR = re.compile(r'<xs:attribute\s+name="([^"]+)"')
# 示例里真实「属性用法」：`name="` 且前面是空白 / 引号 / 斜杠（与 check-attr-acceptance.py
# 的 `[\s"](\w+)="` 同口径，这里把 `/` 也并入前导集，兼容 `/>` 紧邻的属性）。只认 `\w+`，
# 不含点——避免把函数实参 / base64 里的 `x="` 误当属性名。
ATTR_USE = re.compile(r'[\s"/]([A-Za-z_]\w*)="')
# anyAttribute 宿主：`<xs:complexType|simpleType name="H"> … <xs:anyAttribute …/>`（同段内）。
# 按宿主名去重收集；同名 simpleType/complexType 只要任一段带 anyAttribute 就算宽松宿主。
_ANYATTR = re.compile(r'<xs:(complexType|simpleType)\s+name="([^"]+)"[^>]*>(?:(?!</xs:\1>).)*?<xs:anyAttribute\b', re.S)

# 方向 B 里 XML 命名空间属性——永不可能是 xs:attribute，单独 by-design 放行。
_XMLNS_ATTRS = frozenset(("xmlns",))


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
            sys.exit(f"[check-attr-coverage] {path.name}:{lineno} 必须 5 列"
                     f"（kind item verdict owner evidence），实际 {len(parts)}")
        kind, item, verdict, owner, evidence = parts
        if not item.startswith("@"):
            sys.exit(f"[check-attr-coverage] {path.name}:{lineno} item 必须带 @ 前缀"
                      f"（@attr），实际 {item!r}")
        rows.append({"lineno": lineno, "kind": kind, "item": item,
                     "verdict": verdict, "owner": owner, "evidence": evidence})
    return rows, total, pending


def load_negatives(path):
    """→ 负例相对路径集合（tools/negatives.tsv 每行第一列）。方向 A / B 都跳过所有负例。"""
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


def load_attr_acceptance(path):
    """读 attr-acceptance.tsv（W5 的引擎裁决台账）→ 其登记过的 **attr 名集合**。

    只作「登记来源」读，不解析 verdict 语义（verdict 归属 W5 闸）；这里只问「它有没有
    这个属性」——有 ⇒ 本闸方向 A 不重复要求 attr-coverage 行（covered-by）。
    """
    out = set()
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 7 and parts[2].strip():
            out.add(parts[2])
    return out


def load_accepted_rows(path):
    """读 attr-acceptance.tsv → verdict=accepted 的行 [(attr, host, lineno)]。

    方向 C 的登记来源：accepted 表示「引擎收下、**应当有示例**」（attr-acceptance.tsv
    头部注释），落地与否本闸方向 C 当场核。列序：kind(0) name(1) attr(2) host(3)
    verdict(4) owner(5) evidence(6)。
    """
    out = []
    if not path.exists():
        return out
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 7 and parts[4] == "accepted" and parts[2].strip():
            out.append((parts[2], parts[3].strip(), lineno))
    return out


# --------------------------------------------------------------------------- 语料
def strip_comment(text):
    """剥 XML 注释。注释里写的属性名不算「用了」（照抄 check-attr-acceptance / check-examples 口径）。"""
    return COMMENT.sub("", text)


def declared_attrs(xsd_dir):
    """xsd_dir 下全部 *.xsd 里**命名**声明的属性名（含嵌套局部，同名去重）。

    只认 `xs:attribute name="…"`（声明）；注释剥掉，免得 schema 注释里的示例混进来。
    """
    names = set()
    for f in sorted(glob.glob(os.path.join(str(xsd_dir), "*.xsd"))):
        text = strip_comment(Path(f).read_text(encoding="utf-8"))
        for m in DECL_ATTR.finditer(text):
            names.add(m.group(1))
    return names


def anyattribute_hosts(xsd_dir):
    """xsd_dir 下全部 *.xsd 里**声明了 xs:anyAttribute 的宿主名集合**（simpleType/complexType 名）。

    方向 B 的「宽松放行」用：示例里某属性若落在这些宿主上 ⇒ 视为 anyAttribute 接纳，by-design。
    """
    hosts = set()
    for f in sorted(glob.glob(os.path.join(str(xsd_dir), "*.xsd"))):
        text = strip_comment(Path(f).read_text(encoding="utf-8"))
        for m in _ANYATTR.finditer(text):
            hosts.add(m.group(2))
    return hosts


def used_attrs(repo, negative_files):
    """`**/*.esml`（跳过注释、跳过负例）里**非负例**示例真正用到的属性名集合。

    按属性正则扫（`name="` 前导集匹配），与 check-attr-acceptance.py 的 repo_used_attrs
    同口径——不需要解析 XML，故无 lxml 也能跑。
    """
    used = set()
    for f in glob.glob(os.path.join(str(repo), "**", "*.esml"), recursive=True):
        if "/.git/" in f:
            continue
        rel = os.path.relpath(f, repo)
        if rel in negative_files:
            continue
        text = strip_comment(Path(f).read_text(encoding="utf-8", errors="replace"))
        for m in ATTR_USE.finditer(text):
            used.add(m.group(1))
    return used


def host_of_attr(repo, attr, negative_files):
    """扫**非负例**示例，收集属性 `attr` 实际出现的宿主元素名集合。

    方向 B 的 (host, attr) 反查用。宿主 = 该 `attr="` 所在标签的标签名。
    """
    hosts = set()
    tag_open = re.compile(r"<([A-Za-z_][\w.\-]*)([^>]*)>")
    for f in glob.glob(os.path.join(str(repo), "**", "*.esml"), recursive=True):
        if "/.git/" in f:
            continue
        rel = os.path.relpath(f, repo)
        if rel in negative_files:
            continue
        text = strip_comment(Path(f).read_text(encoding="utf-8", errors="replace"))
        for tm in tag_open.finditer(text):
            tagname, attrs = tm.group(1), tm.group(2)
            if re.search(r'[\s"/]%s="' % re.escape(attr), attrs):
                hosts.add(tagname)
    return hosts


def attr_hosts_map(repo, negative_files, attrs):
    """扫**非负例**示例 → {attr 名: 实际出现的宿主元素名集合}（只关心 `attrs` 里的）。

    方向 C 的落地判据用：(host, attr) 是否真在示例里同时出现。宿主 = 该 `attr="` 所在
    标签的标签名——与 attr-acceptance.tsv 的 host 列同维度（都是元素名，不做类型解析）。
    """
    out = {a: set() for a in attrs}
    tag_open = re.compile(r"<([A-Za-z_][\w.\-]*)([^>]*)>")
    for f in glob.glob(os.path.join(str(repo), "**", "*.esml"), recursive=True):
        if "/.git/" in f:
            continue
        rel = os.path.relpath(f, repo)
        if rel in negative_files:
            continue
        text = strip_comment(Path(f).read_text(encoding="utf-8", errors="replace"))
        for tm in tag_open.finditer(text):
            tagname, attrs = tm.group(1), tm.group(2)
            for m in ATTR_USE.finditer(attrs):
                a = m.group(1)
                if a in out:
                    out[a].add(tagname)
    return out


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
    """逐行：kind / verdict / owner 合法、item 有 @ 前缀、evidence 非空。→ [(where, msg)]"""
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
    """`@order` -> `order`。"""
    return item[1:]


def check_direction_a(rows, declared, used, acceptance):
    """方向 A：声明了、非负例示例没用。→ (red, warn, missing_names)

    每个缺示例的属性必须被三选一兜住：台账 attribute 行（pending/by-design/covered）
    或 attr-acceptance 已有行。都不兜 ⇒ 红。missing_names = 当天重算的「声明且无示例」集合。
    """
    red, warn, missing = [], [], set()
    reg_a = {r["item"]: r for r in rows if r["kind"] == "attribute"}
    for n in sorted(declared - used):
        missing.add(n)
        r = reg_a.get(f"@{n}")
        in_acc = n in acceptance
        if r is None:
            if in_acc:
                # 已有 attr-acceptance 行裁决 ⇒ 登记来源在别处，本闸不重复建台账，不算缺。
                warn.append(("attr-acceptance.tsv",
                             f"方向 A 覆盖：@{n} 零示例，已由 attr-acceptance.tsv 裁决（本台账不重复登记）"))
                continue
            red.append(("direction-A",
                         f"@{n} 声明了但任何（非负例）示例都没写，台账与 attr-acceptance 都没登记 "
                         f"—— 补示例 / 记 attr-acceptance / 在本台账记一行"))
            continue
        if r["verdict"] == "covered":
            # 台账显式指向 attr-acceptance；校验它确实覆盖了（防「covered」谎报）。
            if not in_acc:
                red.append((f"{TSV.name}:{r['lineno']}",
                            f"方向 A：@{n} verdict=covered 但 attr-acceptance.tsv 里没有 @{{{n}}} 的行 ⇒ 谎报，删行或改 verdict"))
            # 真覆盖 ⇒ 不红、不警告（登记来源在 attr-acceptance，本闸只核闭合）。
        elif r["verdict"] == "pending":
            if r["owner"] in WARN_OWNERS:
                warn.append((f"{TSV.name}:{r['lineno']}",
                             f"方向 A 待落地：@{n} owner={r['owner']}（追债中，警告不红）"))
            else:
                red.append((f"{TSV.name}:{r['lineno']}",
                            f"方向 A：@{n} verdict=pending owner={r['owner']} —— 必须落地却没记债主 ⇒ 红"))
        elif r["verdict"] == "by-design":
            warn.append((f"{TSV.name}:{r['lineno']}",
                         f"方向 A by-design：@{n}（刻意无示例，{r['evidence'].strip()[:40]}）"))
        # has-example 行却落在差集里 ⇒ 落到下面的闭合校验里红（与元素闸同形）。
    return red, warn, missing


def check_direction_b(rows, declared, used, anyattr_hosts, repo, negative_files):
    """方向 B：非负例示例用了、但 XSD 没声明。→ (red, warn, undecl_names)

    每处未声明属性必须被兜：落在 anyAttribute 宿主上（宽松放行 by-design）、或台账 example 行
    verdict=by-design（/ pending 且 owner∈WARN_OWNERS 在办，警告）。兜不住 ⇒ 红。
    """
    red, warn = [], []
    undecl = sorted(used - declared)
    reg_b = {r["item"]: r for r in rows if r["kind"] == "example"}
    for n in undecl:
        r = reg_b.get(f"@{n}")
        # XML 命名空间属性：永不可能是 xs:attribute，单独 by-design 放行（不必台账兜）。
        if n in _XMLNS_ATTRS:
            warn.append(("direction-B", f"@{n} 是 XML 命名空间属性，非 xs:attribute ⇒ by-design 放行"))
            continue
        # anyAttribute 宿主反查：该属性出现在哪些宿主上？若**全部**宿主都 anyAttribute ⇒ 宽松放行。
        hosts = host_of_attr(repo, n, negative_files)
        loose = bool(hosts) and hosts.issubset(anyattr_hosts)
        if loose:
            warn.append((f"direction-B",
                         f"@{n} 未声明但只出现在 anyAttribute 宿主 {sorted(hosts)} 上 ⇒ 宽松放行（by-design）"))
            continue
        if r is None:
            red.append(("direction-B",
                         f"@{n} 示例在用但 XSD 未声明、也不在 anyAttribute 宿主上，台账也没登记 "
                         f"—— 补声明 / 记 by-design"))
        elif r["verdict"] == "by-design":
            warn.append((f"{TSV.name}:{r['lineno']}",
                         f"方向 B by-design：@{n}（刻意未声明，{r['evidence'].strip()[:40]}）"))
        elif r["verdict"] == "pending" and r["owner"] in WARN_OWNERS:
            warn.append((f"{TSV.name}:{r['lineno']}",
                         f"方向 B 待落地：@{n} owner={r['owner']}（在办收声明，警告不红）"))
        else:
            red.append((f"{TSV.name}:{r['lineno']}",
                        f"方向 B：@{n} verdict={r['verdict']!r} owner={r['owner']} —— 用了就是用了，"
                        f"缺 by-design/在办裁决 ⇒ 红"))
    return red, warn, undecl


def check_direction_c(rows, accepted, attr_hosts):
    """方向 C（W47）：attr-acceptance 的 accepted 行（引擎收下 ⇒ 应当有示例）必须真落地——
    非负例示例里 (host 元素名, attr) 同时出现。未落地 ⇒ 须被 attr-coverage 一行
    `attribute/@attr` 且 verdict=pending 兜住（owner ∈ WARN_OWNERS ⇒ 警告；其它 ⇒ 红，
    口径照方向 A）；无兜 ⇒ 红。→ (red, warn)
    """
    red, warn = [], []
    reg = {r["item"]: r for r in rows if r["kind"] == "attribute"}
    for attr, host, src in sorted(accepted):
        if host in attr_hosts.get(attr, ()):
            continue  # (host, attr) 真在示例里同时出现 ⇒ 已落地
        where = f"attr-acceptance.tsv:{src}"
        r = reg.get(f"@{attr}")
        if r is None:
            red.append(("direction-C",
                         f"accepted @{attr} on <{host}> 在非负例示例里未落地（(host,attr) 没同时出现），"
                         f"attr-coverage 也没登记 —— 补 <{host}> 上的 @{attr} 示例 / 在本台账记一行 pending"))
        elif r["verdict"] == "pending":
            if r["owner"] in WARN_OWNERS:
                warn.append((f"{TSV.name}:{r['lineno']}",
                             f"方向 C 待落地：@{attr} on <{host}> owner={r['owner']}（追债中，警告不红）"))
            else:
                red.append((f"{TSV.name}:{r['lineno']}",
                             f"方向 C：@{attr} on <{host}> verdict=pending owner={r['owner']} —— 必须落地却没记债主 ⇒ 红"))
        else:
            red.append((f"{TSV.name}:{r['lineno']}",
                        f"方向 C：@{attr} on <{host}> 未落地，台账 verdict={r['verdict']!r} —— "
                        f"accepted 行要么补示例、要么记 pending ⇒ 红"))
    return red, warn


def check_ledger_closure(rows, missing_a, undecl_b, acceptance):
    """台账与当天差集闭合：登记的 @name 必须真在差集里；差集的 @name 必须有行（或 acceptance）兜着。

    补了示例/声明后差集会缩，台账不改 ⇒ 红（防台账腐化）。方向 A 的 covered 行还要 attr-acceptance
    真覆盖；has-example 行落在差集里 ⇒ 台账过时。
    """
    red = []
    reg_a = {r["item"]: r for r in rows if r["kind"] == "attribute"}
    reg_b = {r["item"]: r for r in rows if r["kind"] == "example"}
    for item, r in sorted(reg_a.items()):
        n = _name(item)
        if r["verdict"] == "has-example":
            if n not in missing_a:
                # 有示例的元素本就不该登记；落在差集外（有示例了）⇒ 过时。
                red.append((f"{TSV.name}:{r['lineno']}",
                            f"台账登记 @{n}（方向 A has-example）但当天它要么有示例、要么根本没声明 "
                            f"⇒ 台账过时，删行"))
            continue
        # pending / by-design / covered 都要求「声明且无示例」（在差集里）
        if n not in missing_a:
            red.append((f"{TSV.name}:{r['lineno']}",
                        f"台账登记 @{n}（方向 A {r['verdict']}）但当天它要么有示例、要么没声明 ⇒ 过时，删行或改 verdict"))
        elif r["verdict"] == "covered" and n not in acceptance:
            red.append((f"{TSV.name}:{r['lineno']}",
                        f"台账 @{n} verdict=covered 但 attr-acceptance.tsv 没有它 ⇒ 谎报"))
    for item, r in sorted(reg_b.items()):
        n = _name(item)
        if n not in undecl_b:
            red.append((f"{TSV.name}:{r['lineno']}",
                        f"台账登记 @{n}（方向 B）但当天它要么已声明、要么示例没再用 ⇒ 台账过时，删行"))
    # 差集侧的「缺行/缺 acceptance」已在 check_direction_a/b 里红，这里不重复。
    return red


# --------------------------------------------------------------------------- 主检查
def run_gate(repo, tsv, xsd_dir, negative_files, acceptance, stream,
             accepted_rows=None, attr_hosts=None):
    """对一棵树跑全套检查 → (red, warn, stats)。repo/tsv/xsd_dir 可指向合成树（自证用）。

    方向 C 的两个入参默认 None（合成树自证走 A/B 时不跑方向 C）：
      accepted_rows = [(attr, host, lineno), …]（attr-acceptance.tsv 的 accepted 行）
      attr_hosts    = {attr: 非负例示例里实际出现的宿主元素名集合}（attr_hosts_map 的产出）
    """
    rows, total, pending = load_tsv(tsv)
    declared = declared_attrs(xsd_dir)
    used = used_attrs(repo, negative_files)
    anyattr = anyattribute_hosts(xsd_dir)
    red, warn = [], []
    red += check_counts((total, pending), rows)
    red += check_rows(rows)
    ra, wa, missing_a = check_direction_a(rows, declared, used, acceptance)
    red += ra
    warn += wa
    rb, wb, undecl_b = check_direction_b(rows, declared, used, anyattr, repo, negative_files)
    red += rb
    warn += wb
    if accepted_rows is not None and attr_hosts is not None:
        rc_red, rc_warn = check_direction_c(rows, accepted_rows, attr_hosts)
        red += rc_red
        warn += rc_warn
    red += check_ledger_closure(rows, missing_a, undecl_b, acceptance)
    return red, warn, (declared, used, missing_a, undecl_b)


# --------------------------------------------------------------------------- 自证
def self_test(stream):
    """临时目录造小树：好树（声明属性都 covered/有示例、示例属性都在声明/anyAttribute 内）
    ⇒ 零违规；坏树（删一个示例属性 + 加一个未声明属性，台账没跟上）⇒ 必须红；计数锚错 ⇒
    必须红；方向 C 坏树（accepted 行未落地且台账没兜）⇒ 必须红；方向 C 好（accepted 行已
    落地）⇒ 不红。任一翻转 = 自证失败。"""
    w = stream.write
    failures = 0
    NEG = "N-neg/probe.esml"
    NEG_TSV = f"{NEG}\tschema\t负例占位（自证用）\n"
    # 合成 XSD：HostA（带 anyAttribute，宽松宿主）/ HostB（不带，严格宿主）都是**命名**
    # complexType（宿主名 = complexType 名，与真实 XSD 一致）；命名属性 alpha（HostA 上）、
    # beta（HostB 上）。示例元素名也取 HostA / HostB，使 (host, attr) 反查与 anyAttribute 宿主
    # 集合（按 complexType 名收集）对齐。
    DECL = (
        '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
        '<xs:complexType name="HostA">'
        '<xs:attribute name="alpha" type="xs:string" use="optional"/>'
        '<xs:anyAttribute processContents="lax"/>'
        '</xs:complexType>'
        '<xs:complexType name="HostB">'
        '<xs:attribute name="beta" type="xs:string" use="optional"/>'
        '</xs:complexType>'
        '<xs:element name="esml"><xs:complexType/></xs:element>'
        '</xs:schema>')

    def write_tree(tdir, xsd, esml, tsv_rows, acceptance_rows, neg=NEG_TSV):
        tdir.mkdir(parents=True, exist_ok=True)
        (tdir / "xsd").mkdir(parents=True, exist_ok=True)
        (tdir / "xsd" / "t.xsd").write_text(xsd, encoding="utf-8")
        for name, text in esml.items():
            p = tdir / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        (tdir / "negatives.tsv").write_text(neg, encoding="utf-8")
        (tdir / "attr-coverage.tsv").write_text(tsv_rows, encoding="utf-8")
        n_acc = 0 if not acceptance_rows else len(
            [l for l in acceptance_rows.splitlines() if l.strip() and not l.startswith("#")])
        (tdir / "attr-acceptance.tsv").write_text(
            f"# 共 {n_acc} 行\n" + acceptance_rows if acceptance_rows else "# 共 0 行\n",
            encoding="utf-8")
        return tdir / "attr-coverage.tsv"

    def run_on(tree, direction_c=False):
        acc = load_attr_acceptance(tree / "attr-acceptance.tsv")
        kwargs = {}
        if direction_c:
            accepted = load_accepted_rows(tree / "attr-acceptance.tsv")
            kwargs = {"accepted_rows": accepted,
                       "attr_hosts": attr_hosts_map(tree, {NEG}, {a for a, _, _ in accepted})}
        return run_gate(tree, tree / "attr-coverage.tsv", tree / "xsd", {NEG}, acc,
                        stream, **kwargs)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # —— 好树：alpha 有示例（HostA 上），beta 零示例但 attr-acceptance 有行（由 acceptance 兜），
        #    示例里没有未声明属性 ⇒ 零违规。台账 0 行（有示例的、被 acceptance 覆盖的都不必登记）。
        good = write_tree(
            root / "good", DECL,
            {"g/a.esml": '<esml><HostA alpha="x"/></esml>'},
            "# 共 0 行\n#\n# pending：0 行\n",
            "attribute\tXType\tbeta\tHostB\taccepted\tW4\t自证：beta 已有裁决\n")
        # —— 坏树：删掉 alpha 的示例（a.esml 里 HostA 不再带 alpha），并在 HostB 上塞一个**未声明**
        #    属性 ghost ⇒ 方向 A（alpha 无人兜）红 + 方向 B（ghost 未声明且 HostB 非 anyAttribute）红。
        bad = write_tree(
            root / "bad", DECL,
            {"g/a.esml": '<esml><HostB beta="x" ghost="y"/></esml>'},
            "# 共 0 行\n#\n# pending：0 行\n",
            "attribute\tXType\tbeta\tHostB\taccepted\tW4\t自证：beta 已有裁决\n")
        # —— 计数锚：头部「共 5 行」≠ 实际 1 行 ⇒ 必须红。
        badcount = write_tree(
            root / "badcount", DECL,
            {"g/a.esml": '<esml><HostA alpha="x"/></esml>'},
            "# 共 5 行\n#\n# pending：0 行\n"
            "attribute\t@alpha\thas-example\tW1\t自证：计数锚\n",
            "attribute\tXType\tbeta\tHostB\taccepted\tW4\t自证：beta 已有裁决\n")

        for label, tree, want_red in (
                ("好树：声明属性都 covered/有示例、示例属性都在声明/anyAttribute 内", root / "good", False),
                ("坏树：删示例属性 + 加未声明属性，台账没跟上", root / "bad", True)):
            red, warn, _ = run_on(tree)
            ok = bool(red) == want_red
            w(f"  [{'PASS' if ok else 'BROKEN'}] {label} ⇒ 期望{'判红' if want_red else '零违规'}，"
              f"实际 {len(red)} 红 / {len(warn)} 警告\n")
            for where, msg in red:
                w(f"        {where}: {msg}\n")
            failures += 0 if ok else 1

        red, _, _ = run_on(root / "badcount")
        ok = any("共 5 行" in msg or "实际 1 行" in msg for _, msg in red)
        w(f"  [{'PASS' if ok else 'BROKEN'}] 台账计数锚：头部「共 5 行」≠ 实际 1 行 ⇒ 期望判红，"
          f"实际 {len(red)} 红\n")
        failures += 0 if ok else 1

        # —— 方向 B anyAttribute 宽松自证：未声明属性若**只**落在 anyAttribute 宿主上 ⇒ 不红。
        goodloose = write_tree(
            root / "goodloose", DECL,
            {"g/a.esml": '<esml><HostA alpha="x" ghost="y"/></esml>'},
            "# 共 0 行\n#\n# pending：0 行\n",
            "attribute\tXType\tbeta\tHostB\taccepted\tW4\t自证：beta 已有裁决\n")
        red, _, _ = run_on(root / "goodloose")
        ok = not red
        w(f"  [{'PASS' if ok else 'BROKEN'}] 方向 B anyAttribute 宽松：未声明 @ghost 只落在 anyAttribute "
          f"宿主 HostA 上 ⇒ 期望零违规，实际 {len(red)} 红\n")
        for where, msg in red:
            w(f"        {where}: {msg}\n")
        failures += 0 if ok else 1

        # —— 方向 C（W47）：accepted 行必须真落地——(host, attr) 在非负例示例里同时出现。
        #    坏树：attr-acceptance 登 HostB 的 beta 为 accepted，但示例里 beta 没落过 HostB
        #    （HostB 上零属性）且 attr-coverage 台账没兜 ⇒ 必须红（且红源必须是 direction-C）。
        c_bad = write_tree(
            root / "c-bad", DECL,
            {"g/a.esml": '<esml><HostA alpha="x"/></esml>'},
            "# 共 0 行\n#\n# pending：0 行\n",
            "attribute\tXType\tbeta\tHostB\taccepted\tW4\t自证：方向 C 坏树（beta 未落地）\n")
        red, _, _ = run_on(root / "c-bad", direction_c=True)
        ok = bool(red) and any("direction-C" in where or "未落地" in msg
                               for where, msg in red)
        w(f"  [{'PASS' if ok else 'BROKEN'}] 方向 C 坏树：accepted 行（HostB, beta）未落地且台账没兜 "
          f"⇒ 期望判红，实际 {len(red)} 红\n")
        for where, msg in red:
            w(f"        {where}: {msg}\n")
        failures += 0 if ok else 1

        # —— 方向 C 好树：同一行 accepted，但示例里 <HostB beta="y"/> 真落地 ⇒ 零违规
        #    （alpha 在 HostA 上有示例、beta 有裁决且已落地、无未声明属性）。
        c_good = write_tree(
            root / "c-good", DECL,
            {"g/a.esml": '<esml><HostA alpha="x"/><HostB beta="y"/></esml>'},
            "# 共 0 行\n#\n# pending：0 行\n",
            "attribute\tXType\tbeta\tHostB\taccepted\tW4\t自证：方向 C 好树（beta 已落地）\n")
        red, _, _ = run_on(root / "c-good", direction_c=True)
        ok = not red
        w(f"  [{'PASS' if ok else 'BROKEN'}] 方向 C 好树：accepted 行（HostB, beta）已在示例里落地 "
          f"⇒ 期望零违规，实际 {len(red)} 红\n")
        for where, msg in red:
            w(f"        {where}: {msg}\n")
        failures += 0 if ok else 1
    return failures


# --------------------------------------------------------------------------- 主流程
def main(argv=None):
    ap = argparse.ArgumentParser(description="ESML XSD 属性覆盖双向闸门（W29）")
    ap.add_argument("--self-test", action="store_true", help="自证闸门（好树零违规、坏树判红）")
    ap.add_argument("--quiet", action="store_true", help="只报红项")
    args = ap.parse_args(argv)

    if args.self_test:
        bad = self_test(sys.stdout)
        if bad:
            print(f"[check-attr-coverage] {bad} 项自证失败 —— 闸门本身不可信", file=sys.stderr)
            return 2
        print("[check-attr-coverage] 自证通过：好树零违规、坏树判红")
        return 0

    if not TSV.exists():
        print(f"[check-attr-coverage] 缺表：{TSV} 不存在", file=sys.stderr)
        return 2
    negatives = load_negatives(NEGATIVES_TSV)
    acceptance = load_attr_acceptance(ATTR_ACCEPTANCE_TSV)
    accepted_rows = load_accepted_rows(ATTR_ACCEPTANCE_TSV)
    attr_hosts = (attr_hosts_map(REPO, negatives, {a for a, _, _ in accepted_rows})
                  if accepted_rows else None)
    red, warn, stats = run_gate(REPO, TSV, REPO / "xsd", negatives, acceptance, sys.stdout,
                                accepted_rows=accepted_rows, attr_hosts=attr_hosts)
    declared, used, missing_a, undecl_b = stats

    for where, msg in warn:
        print(f"  WARN {where} {msg}")
    if not args.quiet:
        for where, msg in red:
            print(f"  RED  {where} {msg}")

    rows, _, _ = load_tsv(TSV)
    n_pend = sum(1 for r in rows if r["verdict"] == "pending")
    n_bydes = sum(1 for r in rows if r["verdict"] == "by-design")
    n_covered = sum(1 for r in rows if r["verdict"] == "covered")
    n_c_unlanded = sum(1 for a, h, _ in accepted_rows
                       if attr_hosts is not None and h not in attr_hosts.get(a, ()))
    print(f"[check-attr-coverage] 声明 {len(declared)} 个命名属性 · 非负例示例用到 {len(used)} 个 · "
          f"方向 A 零示例 {len(missing_a)} · 方向 B 未声明 {len(undecl_b)} · "
          f"方向 C accepted 未落地 {n_c_unlanded}（accepted 共 {len(accepted_rows)} 行）· "
          f"台账 {len(rows)} 行（pending {n_pend} / by-design {n_bydes} / covered {n_covered}）· "
          f"attr-acceptance 登记 {len(acceptance)} 属性 · "
          f"违规 {len(red)}（警告 {len(warn)}）")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())

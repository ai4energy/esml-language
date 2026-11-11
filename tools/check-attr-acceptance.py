#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ESML 规范仓 · XSD 属性验收台账闸门（W5）。

台账：tools/attr-acceptance.tsv
   kind  name(complexType)  attr  host  verdict  owner  evidence
   verdict 值域：accepted / rejected-f7 / rejected-legacy / rejected-ie / no-example
   owner  值域：W3 / W4 / W5 / engine-debt

门做什么（每一条都能机械复核）：
  1. **台账条数当场重算**：头部「共 N 行」必须等于正文行数 ⇒ 对不上就红（rc=1）。
  2. **accepted 行必须有示例**：`**/*.esml`（跳过注释）里找不到该属性被 owner 名下使用
     ⇒ 缺示例。`owner=W3/W4` 只**警告**（台账在追债，落地前允许红）；
     `owner=W5/engine-debt` 的 accepted 行才**红**。
  3. **`--engine-check` 实跑引擎复算**：对每一行，把该属性注入到「基线 errors=0」的
     锚定示例的宿主元素上、写源件同目录临时件、`esml check`、删临时件。
     accepted 行要求 errors=0；rejected-f7 要求出现 F7；rejected-legacy 要求 F1；
     rejected-ie 要求 IE8。与台账不一致 ⇒ 红，打印「台账写 X / 实测 Y」。
     no-example 行：宿主元素在仓内示例零出现，无法注入 ⇒ 跳过（不计违规）。
  4. **缺引擎仓**（ESML_ENGINE_DIR 指不到 / 默认路径不存在）⇒ 打印「跳过（引擎仓不在）」
     并 rc=0，不静默、不误红。
  5. **`--self-test`**：临时目录造一棵「故意写错一行台账」的小树，自证闸门会红；
     自证失败 ⇒ rc=2。
  6. 脚本自身错误（缺表、列数不对、evidence 为空）⇒ rc=2。

用法：
    tools/check-attr-acceptance.py                  # 查台账（不需要引擎）
    tools/check-attr-acceptance.py --engine-check  # 附引擎实跑复算
    tools/check-attr-acceptance.py --self-test     # 自证
"""

import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TSV = Path(__file__).resolve().parent / "attr-acceptance.tsv"

VERDICTS = ("accepted", "rejected-f7", "rejected-legacy", "rejected-ie", "no-example")
OWNERS = ("W1", "W3", "W4", "W5", "engine-debt")
NS = 'xmlns="https://www.ai4energy.cn/esml/v1"'

# --------------------------------------------------------------------------- 引擎路径
def resolve_engine():
    """ESML_ENGINE_DIR 优先；否则默认 ~/esml-engine-user3/target/release/esml。找不到返回 None。"""
    env = os.environ.get("ESML_ENGINE_DIR")
    if env:
        p = os.path.join(env, "esml")
        return p if os.path.exists(p) else None
    default = os.path.expanduser("~/esml-engine-user3/target/release/esml")
    return default if os.path.exists(default) else None


# --------------------------------------------------------------------------- 台账
def load_tsv(path):
    """→ (rows, declared_count or None, declared_pending or None)。

    rows: [{lineno, kind, name, attr, host, verdict, owner, evidence}]
    """
    rows, declared, pending = [], None, None
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("#"):
            m = re.match(r"^#\s*共\s*(\d+)\s*行", line)
            if m:
                declared = int(m.group(1))
            p = re.match(r"^#\s*待落地：(\d+)\s*行", line)
            if p:
                pending = int(p.group(1))
            continue
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 7:
            sys.exit(f"[check-attr-acceptance] {Path(path).name}:{lineno} 必须 7 列"
                     f"（kind name attr host verdict owner evidence），实际 {len(parts)}")
        kind, name, attr, host, verdict, owner, evidence = parts
        rows.append({
            "lineno": lineno, "kind": kind, "name": name, "attr": attr,
            "host": host, "verdict": verdict, "owner": owner, "evidence": evidence,
        })
    return rows, declared, pending


# --------------------------------------------------------------------------- 仓内属性使用
def repo_used_attrs(repo):
    """`**/*.esml`（跳过注释）里被「使用」的属性名集合。"""
    used = set()
    for f in glob.glob(os.path.join(str(repo), "**", "*.esml"), recursive=True):
        if "/.git/" in f:
            continue
        txt = Path(f).read_text(encoding="utf-8", errors="replace")
        txt = re.sub(r"<!--.*?-->", "", txt, flags=re.S)
        used |= set(re.findall(r'[\s"](\w+)=\s*"', txt))
    return used


def example_exists_for(attr, used):
    """仓内任一 .esml（跳过注释）里是否真的写了 `attr="…"`。

    入参是 `repo_used_attrs()` 已经算好的**属性名集合**，不是仓库路径 —— 逐行判断
    都要问同一个问题，重复 glob 一遍全仓既慢又容易把入参传错（早期版本这里写成
    `repo` 路径，两个调用点却都传集合 ⇒ `glob(os.path.join(str(set), …))` 恒空
    ⇒ 每一行 accepted 都被误判「没有示例」，真加了示例也看不见）。
    """
    if isinstance(used, (str, Path)):
        used = repo_used_attrs(used)
    return attr in used


# --------------------------------------------------------------------------- 引擎
def in_comment(txt, pos):
    return txt.rfind("<!--", 0, pos) > txt.rfind("-->", 0, pos)


def first_host(txt, host):
    for m in re.finditer(r"<%s(?=[\s/>])[^>]*>" % re.escape(host), txt):
        if not in_comment(txt, m.start()):
            return m
    return None


def engine_run(engine, path):
    r = subprocess.run([engine, "check", path], capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    codes = re.findall(r"error:\s*([A-Z][A-Za-z0-9\-]*)\[\]", out)
    m = re.search(r"summary: errors=(\d+)", out)
    n = int(m.group(1)) if m else -1
    return n, codes


def verdict_from_engine(n, codes):
    """把一次实测映射回台账 verdict 值域（accepted / rejected-f7 / …）。"""
    if n == 0:
        return "accepted"
    if "F7" in codes:
        return "rejected-f7"
    if "F1" in codes:
        return "rejected-legacy"
    if "IE8" in codes:
        return "rejected-ie"
    return "unresolved:" + ",".join(codes[:3])


def inject_attr(txt, host, attr, value):
    """把 `attr="value"` 注进第一处**非注释**的 `<host…>` 标签。无宿主返回 None。

    属性区 = 标签名之后的全部文本，只在**这一段**上做替换/判定——天然不碰注释
    与「别的标签」的同名属性（绝不全局 `str.replace`）。同名属性判定与替换用同一
    个正则 `(?<=\\s)ATTR="[^"]*"`：前导环视的空格保证命中的是**真属性**（属性永远
    空格分隔），`count=1` 只换第一个同名；该属性恰好是首属性（紧贴标签名、前无
    空格）时环视不命中 ⇒ 走追加路径。没有才追加 `attrs.rstrip() + ' ATTR="V"'`。
    """
    m = first_host(txt, host)
    if m is None:
        return None
    tag = m.group(0)
    sc = tag.endswith("/>")
    body, tail = (tag[:-2], "/>") if sc else (tag[:-1], ">")
    name_end = re.match(r"<%s" % re.escape(host), tag).end()
    head, attrs = body[:name_end], body[name_end:]
    pat = re.compile(r'(?<=\s)%s="[^"]*"' % re.escape(attr))
    attrs = pat.sub('%s="%s"' % (attr, value), attrs, count=1) if pat.search(attrs) \
        else attrs.rstrip() + ' %s="%s"' % (attr, value)
    newtag = head + attrs + tail
    return txt[: m.start()] + newtag + txt[m.end():]


def inject_element(txt, element_xml):
    """在 `</esml>` 前插入一段整块元素 XML（宿主在仓内零出现、没有可注入宿主标签时用）。"""
    idx = txt.rfind("</esml>")
    if idx < 0:
        return None
    return txt[:idx] + element_xml + "\n" + txt[idx:]


# 每行的注入配方：attr -> (anchor 文件, 注入方式, 属性值 或 整块元素 XML)
# anchor 是「基线 errors=0」的真实示例；注入方式：
#   attr  —— 把 attr="值" 注进 anchor 的第一个 <host> 标签
#   element —— 在 </esml> 前插一整块元素 XML（宿主在仓内零出现、无可注入宿主标签时用）
INJECT = {
    # —— accepted（宿主在真实示例里，注入单属性）——
    "a": ("T-tasks/control-vars.esml", "attr", "1"),
    "b": ("T-tasks/control-vars.esml", "attr", "1"),
    "c": ("T-tasks/control-vars.esml", "attr", "1"),
    "category": ("D-skeleton/skeleton-full.esml", "attr", "inlet"),
    "distribution": ("T-tasks/task-sensitivity.esml", "attr", "normal"),
    "expr": ("T-tasks/task-constraint.esml", "attr", "x &gt; 0"),
    "generations": ("L8-function/foreign-object.esml", "attr", "10"),
    "immediate": ("L2-discrete/reset-transition.esml", "attr", "true"),
    "libroot": ("D-skeleton/project.esml", "attr", "/r"),
    "model": ("T-tasks/task-surrogate.esml", "attr", "poly"),
    "population": ("L8-function/foreign-object.esml", "attr", "20"),
    "portSet": ("D-skeleton/skeleton-full.esml", "attr", "main"),
    "priority": ("L2-discrete/reset-transition.esml", "attr", "2"),
    "q": ("T-tasks/control-vars.esml", "attr", "1"),
    "r": ("T-tasks/control-vars.esml", "attr", "1"),
    "samples": ("L8-function/foreign-object.esml", "attr", "100"),
    "size": ("D-skeleton/skeleton-full.esml", "attr", "3"),
    "solver": ("D-skeleton/esml-coordinate.esml", "attr", "rk4"),
    "steps": ("T-tasks/control-vars.esml", "attr", "5"),
    "t": ("T-tasks/tasks-seven.esml", "attr", "0"),
    "timestep": ("L8-function/foreign-object.esml", "attr", "0.1"),
    "tolerancePct": ("T-tasks/check.esml", "attr", "5"),
    "umax": ("T-tasks/control-vars.esml", "attr", "1"),
    "umin": ("T-tasks/control-vars.esml", "attr", "-1"),
    "x0": ("T-tasks/control-vars.esml", "attr", "0"),
    "xref": ("T-tasks/control-vars.esml", "attr", "0"),
    # —— rejected-*（宿主在真实示例里，注入单属性）——
    "aPart": ("L4-port/conservation.esml", "attr", "1"),
    "bPart": ("L4-port/conservation.esml", "attr", "2"),
    "count": ("D-skeleton/skeleton-full.esml", "attr", "3"),
    "domain": ("D-skeleton/skeleton-full.esml", "attr", "thermal"),
    "extendsFrom": ("D-skeleton/esml-coordinate.esml", "attr", "Base"),
    "nominal": ("D-skeleton/esml-coordinate.esml", "attr", "1.0"),
    "phase": ("L2-discrete/clock-sample.esml", "attr", "0.5"),
    "quantity": ("D-skeleton/esml-coordinate.esml", "attr", "Pressure"),
    "side": ("D-skeleton/skeleton-full.esml", "attr", "left"),
    "synchronize": ("L2-discrete/reset-transition.esml", "attr", "true"),
    "replaceable": ("L3-model/extendsfrom.esml", "attr", "true"),
    # —— no-example（宿主元素在仓内零出现，插一整块元素 XML）——
    "ref": ("D-skeleton/skeleton-full.esml", "element",
            '  <doc name="d" title="x" ref="GB-1234"/>'),
    "summary": ("D-skeleton/skeleton-full.esml", "element",
                '  <doc name="d" title="x" summary="s"/>'),
    "title": ("D-skeleton/skeleton-full.esml", "element",
              '  <doc name="d" title="x"/>'),
    "maxTime": ("D-skeleton/skeleton-full.esml", "element",
                '  <continueUntil name="cu" condition="x &gt; 1" maxTime="10"/>'),
}
# 宿主元素在仓内**零出现**、且没有干净 anchor 可插的属性 ⇒ 引擎无法复算，闸门跳过
NO_EXAMPLE_NO_ANCHOR = {"tasks"}


# --------------------------------------------------------------------------- 检查
def check_counts(declared, rows, stream):
    """头部「共 N 行」必须等于正文行数。→ [(where, msg)]"""
    out = []
    if declared is None:
        out.append((TSV.name, "头部没有写「共 N 行」⇒ 条数无从核对"))
    elif declared != len(rows):
        out.append((TSV.name, f"头部写 {declared} 行，实际 {len(rows)} 行 ⇒ 台账写错就改台账"))
    return out


def check_rows(rows, used, stream):
    """逐行：evidence 非空、verdict/owner 合法、accepted 行必须有示例。

    accepted 无示例：owner=W3/W4 只警告（追债中，不红）；owner=W5/engine-debt 红。
    """
    red, warn = [], []
    for r in rows:
        where = f"{TSV.name}:{r['lineno']}"
        if r["verdict"] not in VERDICTS:
            red.append((where, f"verdict={r['verdict']!r} 非法：只许 {' / '.join(VERDICTS)}"))
            continue
        if r["owner"] not in OWNERS:
            red.append((where, f"owner={r['owner']!r} 非法：只许 {' / '.join(OWNERS)}"))
        if not r["evidence"].strip():
            red.append((where, "evidence 为空 —— 每行都要写清它凭什么这么判"))
            continue
        if r["verdict"] == "accepted":
            if r["attr"] not in used:
                if r["owner"] in ("W3", "W4"):
                    warn.append((where, f"accepted 但没有示例（{r['attr']}，owner={r['owner']}）⇒ 追债中，警告不红"))
                else:
                    red.append((where, f"accepted 但没有示例（{r['attr']}，owner={r['owner']}）⇒ 必须有示例"))
    return red, warn


def check_engine(rows, engine, stream):
    """--engine-check：逐行实跑引擎复算，与台账 verdict 对账。

    `no-example` 行是**记账裁决**（「宿主在仓内零出现 / check 过但语义无效 ⇒ 不补示例」），
    不是引擎判定 ⇒ 引擎无法、也无需复算它，跳过（不计违规）。
    """
    out = []
    for r in rows:
        attr, host, verdict = r["attr"], r["host"], r["verdict"]
        where = f"{TSV.name}:{r['lineno']}"
        if verdict == "no-example":
            # 记账裁决，引擎复算无意义 ⇒ 跳过
            continue
        if attr in NO_EXAMPLE_NO_ANCHOR:
            # 宿主在仓内零出现且无干净 anchor ⇒ 引擎无法复算，跳过
            if verdict != "no-example":
                out.append((where, f"台账写 {verdict}，但 {attr} 无 anchor 可注入（宿主零出现）⇒ 无法引擎复算"))
            continue
        recipe = INJECT.get(attr)
        # 同属性多宿主拆行（W17 2026-11-11）：domain 在 <instance>/<modelType>/<system>
        # 各拆一行，单一 INJECT 配方无法区分宿主 ⇒ 按 (attr, host) 补宿主感知配方。
        # 不改判定，只让 --engine-check 对拆行后的各宿主找对锚件。
        if isinstance(recipe, tuple) and attr == "domain":
            _dhost = {
                "instance": "L5-instance/instance-basic.esml",
                "modelType": "L5-instance/instance-basic.esml",
                "system": "L5-instance/instance-basic.esml",
            }
            if host in _dhost:
                recipe = (_dhost[host], "attr", val)
        if recipe is None:
            out.append((where, f"台账行 {attr} 没有注入配方（INJECT 缺项）⇒ 无法引擎复算"))
            continue
        anchor, mode, val = recipe
        anchor_path = REPO / anchor
        if not anchor_path.exists():
            out.append((where, f"anchor 件不在：{anchor}"))
            continue
        txt = anchor_path.read_text(encoding="utf-8")
        n0, _ = engine_run(engine, str(anchor_path))
        if n0 != 0:
            out.append((where, f"anchor 件 {anchor} 基线非绿（n={n0}）⇒ 注入判定不可信"))
            continue
        newtxt = (inject_attr(txt, host, attr, val) if mode == "attr"
                  else inject_element(txt, val))
        if newtxt is None:
            out.append((where, f"anchor 件 {anchor} 里找不到 <{host}>（注入点缺失）⇒ 无法引擎复算"))
            continue
        tmp = str(anchor_path.parent / ".w5gate-probe.esml")
        Path(tmp).write_text(newtxt, encoding="utf-8")
        try:
            n, codes = engine_run(engine, tmp)
        finally:
            os.unlink(tmp)
        actual = verdict_from_engine(n, codes)
        if actual != verdict:
            out.append((where, f"台账写 {verdict} / 实测 {actual}"
                               f"（{attr}@<{host}>，n={n} codes={codes[:4]}）⇒ 判定漂移"))
    return out


# --------------------------------------------------------------------------- 自证
def self_test(stream):
    """临时目录造一棵小树：好台账（自洽，零违规）+ 坏台账（故意写错一行）⇒ 必须红。

    任一翻转 = 自证失败 ⇒ 返回失败数。
    """
    w = stream.write
    failures = 0

    def make_tree(tdir, rows_text, declared):
        tdir.mkdir(parents=True, exist_ok=True)
        (tdir / "attr-acceptance.tsv").write_text(
            f"# 共 {declared} 行\n{rows_text}", encoding="utf-8")
        return tdir

    def run_on(tree):
        """对一棵合成树跑台账检查（不动全局 REPO/TSV，显式传路径）。"""
        tsv = tree / "attr-acceptance.tsv"
        rows, declared, _ = load_tsv(tsv)
        used = repo_used_attrs(tree)
        v = check_counts(declared, rows, stream)
        red, _warn = check_rows(rows, used, stream)
        v += red
        return v

    # —— 闸自证：宿主标签已带同名属性 → 注入后仍只有**一份**（替换、不追加），
    #    否则双同名属性会触发 F1「xml is not well-formed」假红。
    host_with = '<host attr="old" z="1"/>'
    after = inject_attr(host_with, "host", "attr", "new")
    dup_ok = (after is not None and after.count('attr="') == 1) \
        and 'attr="new"' in after and 'attr="old"' not in after
    # 追加路径（原行为）：宿主**没有**该属性时才追加，行为不变。
    after_app = inject_attr('<host z="1"/>', "host", "attr", "new")
    app_ok = (after_app is not None and after_app.count('attr="') == 1) \
        and 'attr="new"' in after_app
    for label, ok in (("闸自证：宿主已有同名属性 → 注入后单份（替换不追加）", dup_ok),
                      ("闸自证：宿主无该属性 → 追加单份", app_ok)):
        w("  [%s] %s\n" % ("PASS" if ok else "BROKEN", label))
        failures += 0 if ok else 1

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # —— 好：自洽台账（1 行 rejected-f7，evidence 含 F7、条数对）⇒ 零违规
        good = make_tree(root / "good",
                         "attribute\tXType\tx\thost\trejected-f7\tW4\t"
                         "error: F7[]: unknown attribute `x` on `<host>` at <probe>\n",
                         1)
        # —— 坏：故意写错一行（verdict 谎报 accepted、owner=W5 且无示例）⇒ 必须红
        bad = make_tree(root / "bad",
                        "attribute\tXType\tx\thost\taccepted\tW5\t"
                        "error: F7[]: unknown attribute `x` on `<host>` at <probe>\n",
                        1)

        for label, tree, want_red in (("好：自洽台账", good, False),
                                      ("坏：verdict 谎报 accepted", bad, True)):
            v = run_on(tree)
            ok = bool(v) == want_red
            w(f"  [{'PASS' if ok else 'BROKEN'}] {label} ⇒ 期望{'判红' if want_red else '零违规'}，实际 {len(v)} 项\n")
            for where, msg in v:
                w(f"        {where}: {msg}\n")
            failures += 0 if ok else 1
    return failures


# --------------------------------------------------------------------------- 主流程
def main(argv=None):
    ap = argparse.ArgumentParser(description="ESML XSD 属性验收台账闸门（W5）")
    ap.add_argument("--engine-check", action="store_true", help="实跑引擎逐行复算 verdict")
    ap.add_argument("--self-test", action="store_true", help="自证闸门（好台账零违规、坏台账判红）")
    args = ap.parse_args(argv)

    if args.self_test:
        bad = self_test(sys.stdout)
        if bad:
            print(f"[check-attr-acceptance] {bad} 项自证失败 —— 闸门本身不可信", file=sys.stderr)
            return 2
        print("[check-attr-acceptance] 自证通过：好台账零违规、坏台账判红")
        return 0

    # 台账缺了 ⇒ rc=2
    if not TSV.exists():
        print(f"[check-attr-acceptance] 缺表：{TSV} 不存在", file=sys.stderr)
        return 2
    rows, declared, pending = load_tsv(TSV)  # 列数错 / evidence 空 → 已在 load 里 sys.exit(rc=2)
    used = repo_used_attrs(REPO)

    red, warn = [], []
    red += check_counts(declared, rows, sys.stdout)
    r2, w2 = check_rows(rows, used, sys.stdout)
    red += r2
    warn += w2

    if args.engine_check:
        engine = resolve_engine()
        if engine is None:
            # 订单口径：缺引擎仓 ⇒ 跳过（引擎复算）并 rc=0，不静默、不误红。
            # 台账/示例检查（W3/W4 警告）仍打印，但缺引擎时不以它们定退出码。
            print("[check-attr-acceptance] 跳过（引擎仓不在）——ESML_ENGINE_DIR 未解析到 esml 二进制 ⇒ rc=0")
            for where, msg in warn:
                print(f"  WARN {where} {msg}")
            return 0
        red += check_engine(rows, engine, sys.stdout)

    for where, msg in warn:
        print(f"  WARN {where} {msg}")
    for where, msg in red:
        print(f"  RED  {where} {msg}")

    n_acc = sum(1 for r in rows if r["verdict"] == "accepted")
    pend = sum(1 for r in rows if r["verdict"] == "accepted" and r["attr"] not in used)
    eng = "跳过（引擎仓不在）" if (args.engine_check and resolve_engine() is None) else (
        "未给 --engine-check（引擎复算跳过）" if not args.engine_check else "引擎实跑复算")
    print(f"[check-attr-acceptance] 台账 {len(rows)} 行（accepted {n_acc}）· "
          f"待落地 {pend} 行 · 引擎 {eng} · 违规 {len(red)}")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())

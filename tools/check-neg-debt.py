#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ESML 规范仓 · G16 负例债务行对账门。

它管两本台账：

  tools/neg-debt.tsv   —— G16 白名单（引擎仓 `scripts/gate-baselines/corpus-neg.tsv`）
                          落在本仓的 10 行 + 本轮新增 4 行：逐行处置与证据
  tools/negatives.tsv  —— 全仓自述负例清单（`check-examples.py` 也读它）

门做什么（每一条都能机械复核）：
  1. **登记条数当场重算**：两本台账的头部都写着条数，对不上就红
     （台账写错就改台账 —— 条数不是注释里的摆设）。
  2. **逐行核对 neg-debt.tsv**：件在不在、登记没登记、XSD 裁决与 level 是否一致、
     证据行是不是**含该行的错误码**（防止「证据」是一句空话）。
  3. **导数位置判据**：本轮新增的 4 件必须把 token 放在**合法位**
     （`<derivative>` 之内、canonical 拼写），且整件**不写 `<body>`** ——
     于是引擎的 F1 **不可能**归因 body 形态，只能归因位置（缺 `<extern>`）。
     这条是「合法位被拒、拒的是位不是拼写」的机器形式。
  4. **引擎复核**（`--engine PATH`）：实测错误码与台账一致（换码 = 漂移 ⇒ 红），
     且诊断的归因与件形相符：有 `<body>` 的件必须死在 body 形态上，
     没 `<body>` 的件必须死在位置上（"without an `<extern>`"）。
  5. **白名单对账**（`--whitelist PATH`）：台账的 10 行与引擎仓白名单逐行对上，
     且白名单里落在本仓示例目录的行**一条都不许漏**（漏 = 未判定）。

自证（`--self-test`）：2 好 2 坏 + 反向 —— 好件必须判过、坏件必须判红，
任一翻转都算自证失败。

用法：
    tools/check-neg-debt.py                       # 查台账与 XSD（不需要引擎）
    tools/check-neg-debt.py --engine PATH         # 附引擎复核
    tools/check-neg-debt.py --libroot PATH        # 附 -L <libroot>（F12 行要用）
    tools/check-neg-debt.py --whitelist PATH      # 附引擎仓白名单对账
    tools/check-neg-debt.py --self-test           # 2 好 2 坏 + 反向自证

依赖：lxml（XSD 校验器）。装法见 README；xmllint 可用时加 --xmllint。
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
XSD_DIR = REPO / "xsd"
CANONICAL_SCHEMA = XSD_DIR / "esml-canonical-basic.xsd"
NEGATIVES_TSV = Path(__file__).resolve().parent / "negatives.tsv"
NEG_DEBT_TSV = Path(__file__).resolve().parent / "neg-debt.tsv"

# 台账头部写着条数的那一行（两本台账各一个格式）
COUNT_NEG = re.compile(r"^#\s*登记条数：(\d+)\s*件（schema\s*(\d+)\s*/\s*semantic\s*(\d+)）")
COUNT_DEBT = re.compile(r"^#\s*登记条数：(\d+)\s*行")

VERDICTS = ("改件", "转negative", "删孤儿", "新增")

# 导数 token 的 canonical 拼写（= XSD `DerivativeType` 的四个子元素名）
DERIV_TOKENS = ("partial", "derivativeSymbol", "noDerivative", "zeroDerivative")

COMMENTS = re.compile(r"<!--.*?-->", re.S)


# --------------------------------------------------------------------------- 工具后端
def _which(name):
    from shutil import which

    return which(name)


def _lxml_backend():
    try:
        from lxml import etree
    except ImportError:
        sys.exit(
            "[check-neg-debt] 需要 lxml。装：python3 -m venv .venv && .venv/bin/pip install lxml\n"
            "               或装 xmllint 后加 --xmllint。"
        )
    cache = {}

    def validate(path, schema_path=CANONICAL_SCHEMA):
        key = str(schema_path)
        if key not in cache:
            cache[key] = etree.XMLSchema(etree.parse(key))
        schema = cache[key]
        try:
            doc = etree.parse(str(path))
        except etree.XMLSyntaxError as e:
            return False, f"XML 解析失败: {e}"
        if schema.validate(doc):
            return True, ""
        err = schema.error_log.last_error
        return False, f"{err.line}:{err.column}: {err.message}"

    return validate, "lxml"


def _xmllint_backend(exe):
    def validate(path, schema_path=CANONICAL_SCHEMA):
        p = subprocess.run(
            [exe, "--noout", "--schema", str(schema_path), str(path)],
            capture_output=True,
            text=True,
        )
        if p.returncode == 0:
            return True, ""
        lines = [l for l in (p.stderr or "").splitlines() if l.strip() and ".esml" in l]
        return False, lines[0].strip() if lines else (p.stderr or "").strip().splitlines()[-1]

    return validate, f"xmllint({exe})"


def load_backend(prefer_xmllint):
    if prefer_xmllint:
        exe = _which("xmllint")
        if exe:
            return _xmllint_backend(exe)
    return _lxml_backend()


# --------------------------------------------------------------------------- 台账
def load_negatives():
    """→ (登记 {path: (level, reason)}, 头部声明的 (总, schema, semantic) 或 None)"""
    table, declared = {}, None
    for lineno, line in enumerate(NEGATIVES_TSV.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("#"):
            m = COUNT_NEG.match(line)
            if m:
                declared = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            continue
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            sys.exit(f"[check-neg-debt] {NEGATIVES_TSV.name}:{lineno} 必须 3 列（path/level/reason）")
        path, level, reason = parts
        if level not in ("schema", "semantic"):
            sys.exit(f"[check-neg-debt] {NEGATIVES_TSV.name}:{lineno} level={level!r} 非法")
        if not reason.strip():
            sys.exit(f"[check-neg-debt] {NEGATIVES_TSV.name}:{lineno} reason 为空")
        table[path] = (level, reason)
    return table, declared


def load_debt():
    """→ (登记 [行 dict], 头部声明的行数 或 None)"""
    rows, declared = [], None
    for lineno, line in enumerate(NEG_DEBT_TSV.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("#"):
            m = COUNT_DEBT.match(line)
            if m:
                declared = int(m.group(1))
            continue
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 5:
            sys.exit(f"[check-neg-debt] {NEG_DEBT_TSV.name}:{lineno} 必须 5 列（g16_path/code/verdict/repo_path/evidence）")
        g16_path, code, verdict, repo_path, evidence = parts
        rows.append({
            "lineno": lineno,
            "g16_path": g16_path,
            "code": code,
            "verdict": verdict,
            "repo_path": repo_path,
            "evidence": evidence,
        })
    return rows, declared


# --------------------------------------------------------------------------- 件的形状
def derivative_tokens(path):
    """件里 `<derivative>` 的子元素名（canonical 拼写的那几个）。"""
    raw = COMMENTS.sub("", Path(path).read_text(encoding="utf-8", errors="replace"))
    out = []
    for m in re.finditer(r"<derivative\b[^>]*>(.*?)</derivative>", raw, re.S):
        for c in re.finditer(r"<\s*([A-Za-z_][\w.\-]*)", m.group(1)):
            name = c.group(1)
            if name in DERIV_TOKENS:
                out.append(name)
    return out


def body_texts(path):
    """件里每个 `<body>` 的文本。"""
    raw = COMMENTS.sub("", Path(path).read_text(encoding="utf-8", errors="replace"))
    return [m.group(1).strip() for m in re.finditer(r"<body\b[^>]*>(.*?)</body>", raw, re.S)]


def is_equation_body(text):
    """`<body>` 写的是方程（含 `=`）而不是右值表达式。"""
    return "=" in text


# --------------------------------------------------------------------------- 引擎
def engine_check(engine, path, libroot=None):
    """跑一次 `esml check`。→ (rc, 输出文本)"""
    cmd = [engine, "check", str(path)]
    if libroot:
        cmd += ["-L", str(libroot)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def engine_codes(output):
    """从输出里取全部错误码（`error: F1[]: …` → {F1}）。一次 check 可能报多条。"""
    return set(re.findall(r"error:\s*([A-Z][A-Za-z0-9\-]*)\[\]", output))


# --------------------------------------------------------------------------- 检查
def check_ledger(rows, negatives, validate, stream):
    """逐行核对 neg-debt.tsv。→ [(where, msg)]"""
    out = []
    for r in rows:
        where = f"{NEG_DEBT_TSV.name}:{r['lineno']}"
        if r["verdict"] not in VERDICTS:
            out.append((where, f"verdict={r['verdict']!r} 非法：只许 {' / '.join(VERDICTS)}"))
            continue
        if not r["evidence"].strip():
            out.append((where, "evidence 为空 —— 每行都要写清它凭什么这么判"))
            continue
        if r["code"] not in r["evidence"]:
            out.append((where, f"evidence 里没有该行的错误码 {r['code']} —— 证据与码对不上"))
        if r["repo_path"] == "-":
            if r["verdict"] != "删孤儿":
                out.append((where, "repo_path 为 `-`（本仓无对应件）却不是「删孤儿」裁决"))
            continue
        p = REPO / r["repo_path"]
        if not p.exists():
            out.append((where, f"件不在：{r['repo_path']}"))
            continue
        if r["repo_path"] not in negatives:
            out.append((where, f"{r['repo_path']} 未登记进 tools/negatives.tsv（「未判定」不合法）"))
            continue
        level = negatives[r["repo_path"]][0]
        ok, err = validate(p)
        if level == "schema" and ok:
            out.append((where, f"{r['repo_path']} 登记 level=schema，XSD 却收下了 ⇒ 判据漏了"))
        elif level == "semantic" and not ok:
            out.append((where, f"{r['repo_path']} 登记 level=semantic，XSD 却拒收了：{err}"))
    return out


def check_derivative_position(rows, negatives, validate, stream):
    """导数**位置**判据：新增件必须把 token 放在合法位，且整件不写 `<body>`。"""
    out = []
    for r in rows:
        if r["verdict"] != "新增" or r["repo_path"] == "-":
            continue
        where = f"{NEG_DEBT_TSV.name}:{r['lineno']}"
        p = REPO / r["repo_path"]
        if not p.exists():
            continue  # 已在 check_ledger 里报过
        toks = derivative_tokens(p)
        if not toks:
            out.append((where, f"{r['repo_path']} 里找不到 `<derivative>` 内的 canonical token"
                               f"（{', '.join(DERIV_TOKENS)}）⇒ 「合法位」无从谈起"))
            continue
        bodies = body_texts(p)
        if bodies:
            out.append((where, f"{r['repo_path']} 写了 `<body>`（{bodies[0]!r}）⇒ 引擎的 F1 可能"
                               f"归因 body 形态，位置归因被抢走 ⇒ 这件证明不了「位」"))
        ok, err = validate(p)
        if ok:
            out.append((where, f"{r['repo_path']} XSD 竟收下了 ⇒ 位置判据不成立"))
        elif "derivative" not in err:
            out.append((where, f"{r['repo_path']} 的 XSD 报错点不是 `<derivative>`：{err}"))
    return out


def check_engine(rows, negatives, engine, libroot, stream):
    """引擎复核：实测码与台账一致；诊断归因与件形相符。"""
    out = []
    for r in rows:
        if r["repo_path"] == "-":
            continue
        p = REPO / r["repo_path"]
        if not p.exists():
            continue
        rc, output = engine_check(engine, p, libroot)
        codes = engine_codes(output)
        where = f"{NEG_DEBT_TSV.name}:{r['lineno']}"
        if not codes:
            # 没有错误码：要么是绿的，要么是 F12 那类「要 -L 才跑」的审计。
            out.append((where, f"{r['repo_path']} 实测没报错（rc={rc}）⇒ 与登记码 {r['code']} 对不上"
                               f"（F12 这类审计要 -L <libroot> 才跑）"))
            continue
        if r["code"] not in codes:
            out.append((where, f"{r['repo_path']} 实测码 {sorted(codes)} 不含登记码 {r['code']}"
                               f" ⇒ 失败码漂移"))
            continue
        # 归因与件形相符：只有带 `<derivative>` 的件才谈得上「位置 vs body 形态」
        if not derivative_tokens(p):
            continue
        bodies = body_texts(p)
        if bodies and is_equation_body(bodies[0]):
            if "without an <extern>" in output:
                out.append((where, f"{r['repo_path']} 的 `<body>` 是方程写法，引擎却报位置错"
                                   f" ⇒ 归因与件形不符，evidence 该更新"))
        elif "without an <extern>" not in output:
            out.append((where, f"{r['repo_path']} 没有 `<body>`，引擎的诊断却没指向位置"
                               f"（应含 \"without an <extern>\"）⇒ 归因与件形不符"))
    return out


def check_whitelist(rows, whitelist_path, stream):
    """台账的 10 行与引擎仓白名单逐行对上，且白名单落在本仓的行一条不许漏。

    只看白名单里 `examples/syntax/` 开头的行 —— 那是引擎仓里**本仓示例的副本**；
    `tests/fixtures/…` 那些是引擎仓自己的夹具，不归本仓台账管。
    """
    out = []
    wl = {}
    for line in Path(whitelist_path).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].startswith("examples/syntax/"):
            wl[parts[0]] = parts[1]
    ledger = {r["g16_path"]: r for r in rows if not r["g16_path"].startswith("-")}
    for g16_path, code in sorted(wl.items()):
        if g16_path not in ledger:
            out.append(("whitelist", f"白名单行 {g16_path}（{code}）在本仓台账里没有登记 ⇒ 未判定"))
            continue
        if ledger[g16_path]["code"] != code:
            out.append(("whitelist", f"白名单行 {g16_path} 的码 {code} ≠ 台账 {ledger[g16_path]['code']}"))
    for g16_path in sorted(set(ledger) - set(wl)):
        out.append(("whitelist", f"台账登记了 {g16_path}，但白名单里没有这一行（引擎仓删过了？）"))
    return out


def check_counts(neg_declared, negs, debt_declared, rows, stream):
    """登记条数当场重算：头部写的数字必须等于实际行数。"""
    out = []
    if neg_declared is None:
        out.append((NEGATIVES_TSV.name, "头部没有写「登记条数」⇒ 条数无从核对"))
    else:
        total, n_schema, n_sem = neg_declared
        real_total = len(negs)
        real_schema = sum(1 for v in negs.values() if v[0] == "schema")
        real_sem = sum(1 for v in negs.values() if v[0] == "semantic")
        if total != real_total or n_schema != real_schema or n_sem != real_sem:
            out.append((NEGATIVES_TSV.name,
                        f"头部写 {total} 件（schema {n_schema} / semantic {n_sem}），"
                        f"实际 {real_total} 件（schema {real_schema} / semantic {real_sem}）"
                        f" ⇒ 台账写错就改台账"))
    if debt_declared is None:
        out.append((NEG_DEBT_TSV.name, "头部没有写「登记条数」⇒ 条数无从核对"))
    elif debt_declared != len(rows):
        out.append((NEG_DEBT_TSV.name,
                    f"头部写 {debt_declared} 行，实际 {len(rows)} 行 ⇒ 台账写错就改台账"))
    return out


# --------------------------------------------------------------------------- 自证
def _synthetic_repo(tdir, with_body=False):
    """造一棵自洽的小树：1 件负例（XSD 拒收）+ 两本台账。

    with_body=True ⇒ 件里写 `<body>y = x * x</body>`（旧件的形状：
    引擎的 F1 归因 body 形态，位置判据**不**该管它）。
    """
    (tdir / "L1").mkdir(parents=True, exist_ok=True)
    body = "    <body>y = x * x</body>\n" if with_body else ""
    doc = f"""<?xml version="1.0"?>
<esml xmlns="https://www.ai4energy.cn/esml/v1" name="SELF_NEG">
  <functions><function name="sq">
    <inputs><input name="x"/></inputs>
    <outputs><output name="y"/></outputs>
{body}    <derivative mode="analytic"><partial wrt="x">2.0 * x</partial></derivative>
  </function></functions>
</esml>
"""
    (tdir / "L1" / "neg-probe.esml").write_text(doc, encoding="utf-8")
    (tdir / "negatives.tsv").write_text(
        "# 登记条数：1 件（schema 1 / semantic 0）\n"
        "L1/neg-probe.esml\tschema\t自测用负例\n",
        encoding="utf-8",
    )
    (tdir / "neg-debt.tsv").write_text(
        "# 登记条数：1 行\n"
        "-（自测）\tF1\t新增\tL1/neg-probe.esml\t自测：实测码 F1，证据行含 F1\n",
        encoding="utf-8",
    )
    return tdir


def self_test(validate, stream):
    """2 好 2 坏 + 反向：好件必须判过，坏件必须判红。任一翻转 = 自证失败。"""
    import tempfile

    w = stream.write
    failures = 0

    def run(tdir):
        """对一棵合成树跑一遍检查，返回违规列表。"""
        global NEGATIVES_TSV, NEG_DEBT_TSV, REPO
        old = (REPO, NEGATIVES_TSV, NEG_DEBT_TSV)
        REPO = tdir
        NEGATIVES_TSV = tdir / "negatives.tsv"
        NEG_DEBT_TSV = tdir / "neg-debt.tsv"
        try:
            negs, neg_decl = load_negatives()
            rows, debt_decl = load_debt()
            v = check_counts(neg_decl, negs, debt_decl, rows, stream)
            v += check_ledger(rows, negs, validate, stream)
            v += check_derivative_position(rows, negs, validate, stream)
            return v
        finally:
            REPO, NEGATIVES_TSV, NEG_DEBT_TSV = old

    def case(label, tdir, want_red):
        nonlocal failures
        v = run(tdir)
        ok = bool(v) == want_red
        w(f"  [{'PASS' if ok else 'BROKEN'}] {label} ⇒ 期望{'判红' if want_red else '零违规'}，实际 {len(v)} 项\n")
        for where, msg in v:
            w(f"        {where}: {msg}\n")
        failures += 0 if ok else 1

    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)

        # —— 好 1：自洽的新增件（无 `<body>`、token 在合法位、XSD 拒收）⇒ 零违规
        case("好 1：自洽台账 + 自洽新增件", _synthetic_repo(tdir / "good"), want_red=False)

        # —— 好 2：旧件形状（有 `<body>` 方程）登记为转negative ⇒ 位置判据不误伤
        good2 = _synthetic_repo(tdir / "good2", with_body=True)
        (good2 / "neg-debt.tsv").write_text(
            "# 登记条数：1 行\n"
            "-（自测）\tF1\t转negative\tL1/neg-probe.esml\t自测：旧件有 <body>，F1 归因 body 形态，登记码 F1\n",
            encoding="utf-8",
        )
        case("好 2：旧件形状（带 <body>）不受位置判据误伤", good2, want_red=False)

        # —— 坏 1：台账条数谎报 ⇒ 必须红
        bad1 = _synthetic_repo(tdir / "bad1")
        (bad1 / "neg-debt.tsv").write_text(
            "# 登记条数：9 行\n"  # 谎报
            "-（自测）\tF1\t新增\tL1/neg-probe.esml\t自测：实测码 F1，证据行含 F1\n",
            encoding="utf-8",
        )
        case("坏 1：台账条数谎报（写 9 行、实际 1 行）", bad1, want_red=True)

        # —— 坏 2：新增件带了 `<body>` ⇒ 位置归因被抢走 ⇒ 必须红
        bad2 = _synthetic_repo(tdir / "bad2", with_body=True)
        case("坏 2：新增件写了 <body>（位置归因会被抢走）", bad2, want_red=True)

        # —— 坏 3：证据行不含该行的码 ⇒ 必须红
        bad3 = _synthetic_repo(tdir / "bad3")
        (bad3 / "neg-debt.tsv").write_text(
            "# 登记条数：1 行\n"
            "-（自测）\tF1\t新增\tL1/neg-probe.esml\t自测：证据行里没有错误码\n",
            encoding="utf-8",
        )
        case("坏 3：证据行不含登记码", bad3, want_red=True)

        # —— 坏 4：level 倒挂（XSD 拒收却登记 semantic）⇒ 必须红
        bad4 = _synthetic_repo(tdir / "bad4")
        (bad4 / "negatives.tsv").write_text(
            "# 登记条数：1 件（schema 0 / semantic 1）\n"
            "L1/neg-probe.esml\tsemantic\t自测：把被 XSD 拒收的件说成 XSD 收下\n",
            encoding="utf-8",
        )
        case("坏 4：level 倒挂（XSD 拒收却登记 semantic）", bad4, want_red=True)

        # —— 反向自检：token 拼错（不在合法位）必须判红 ——
        #    判据盯的是「canonical token 在合法位」，不是「随便一件坏件」
        rev = _synthetic_repo(tdir / "rev")
        (rev / "L1" / "neg-probe.esml").write_text(
            """<?xml version="1.0"?>
<esml xmlns="https://www.ai4energy.cn/esml/v1" name="SELF_REV">
  <functions><function name="sq">
    <inputs><input name="x"/></inputs>
    <outputs><output name="y"/></outputs>
    <derivative mode="analytic"><partialDerivative wrt="x">2.0 * x</partialDerivative></derivative>
  </function></functions>
</esml>
""",
            encoding="utf-8",
        )
        case("反向自检：token 拼错（非 canonical）⇒ 判红", rev, want_red=True)

    return failures


# --------------------------------------------------------------------------- 主流程
def main(argv=None):
    ap = argparse.ArgumentParser(description="ESML G16 负例债务行对账门")
    ap.add_argument("--self-test", action="store_true", help="只跑 2 好 2 坏 + 反向自证")
    ap.add_argument("--xmllint", action="store_true", help="优先用 xmllint（缺 lxml 时）")
    ap.add_argument("--engine", help="引擎二进制路径（给了才做引擎复核）")
    ap.add_argument("--libroot", help="引擎的 -L <libroot>（F12 审计要它）")
    ap.add_argument("--whitelist", help="引擎仓白名单 corpus-neg.tsv（给了才做白名单对账）")
    ap.add_argument("--quiet", action="store_true", help="只报红项")
    args = ap.parse_args(argv)

    validate, backend = load_backend(args.xmllint)

    if args.self_test:
        bad = self_test(validate, sys.stdout)
        if bad:
            print(f"[check-neg-debt] {bad} 项自证失败 —— 检查器本身不可信")
            return 1
        print("[check-neg-debt] 全部成立")
        return 0

    negatives, neg_declared = load_negatives()
    rows, debt_declared = load_debt()
    red = []

    red += check_counts(neg_declared, negatives, debt_declared, rows, sys.stdout)
    red += check_ledger(rows, negatives, validate, sys.stdout)
    red += check_derivative_position(rows, negatives, validate, sys.stdout)
    if args.engine:
        red += check_engine(rows, negatives, args.engine, args.libroot, sys.stdout)
    if args.whitelist:
        red += check_whitelist(rows, args.whitelist, sys.stdout)

    if not args.quiet:
        for where, msg in red:
            print(f"  RED  {where} {msg}")

    n_schema = sum(1 for v in negatives.values() if v[0] == "schema")
    n_sem = sum(1 for v in negatives.values() if v[0] == "semantic")
    verdicts = {v: sum(1 for r in rows if r["verdict"] == v) for v in VERDICTS}
    engine_note = "未给 --engine（引擎复核跳过）"
    if args.engine:
        engine_note = f"引擎 {args.engine}"
        if args.libroot:
            engine_note += f" -L {args.libroot}"
    wl_note = "未给 --whitelist（白名单对账跳过）" if not args.whitelist else f"白名单 {args.whitelist}"
    print(
        f"[check-neg-debt] 后端 {backend} · 台账 neg-debt.tsv {len(rows)} 行"
        f"（改件 {verdicts['改件']} / 转negative {verdicts['转negative']} / "
        f"删孤儿 {verdicts['删孤儿']} / 新增 {verdicts['新增']}）· "
        f"负例清单 negatives.tsv {len(negatives)} 件（schema {n_schema} / semantic {n_sem}）· "
        f"{engine_note} · {wl_note} · 违规 {len(red)}"
    )
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())

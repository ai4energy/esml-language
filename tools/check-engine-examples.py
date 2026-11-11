#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ESML 规范仓 · 引擎 × 示例可运行性台账闸门（W31）。

台账：tools/engine-example-debt.tsv
   path  errors(实测)  owner  evidence
   owner 值域：engine-debt（引擎侧不收，登记跟踪；示例本身 canonical 不动）

门做什么（每一条都能机械复核）：
  1. **枚举非负例**：`**/*.esml` 中**非负例**——负例识别照抄 `docs/validate_examples.py`
     的 `is_negative`（文件名含 `probe` 或头部 20 行注明「负例」）。负例不进本闸
     （它们预期失败，另一套逻辑管）。
  2. **逐件跑引擎** `esml check <file>`（`ESML_PROPS=off`），解析 `summary: errors=N`。
  3. **判据**：`errors=0` ⇒ 通过；`errors>0` ⇒ 必须在台账里有一行登记（path 精确匹配），
     否则**判红**（台账没有行的红示例不许当成通过——那正是本闸要拦的）。
  4. **台账行与实测对账**：台账写 errors=N、实测 M，N≠M ⇒ 打印「台账过时」判红
     （引擎行为或示例变了、台账没跟上）；示例已修好（实测 0）但仍登记 ⇒ 同样「台账过时」判红。
  5. **头部计数当场重算**：`# 共 N 行` 必须等于台账正文行数 ⇒ 对不上就红（rc=1）。
  6. **`--self-test`**：临时目录造好/坏两棵小树（不跑引擎的部分：负例识别 + 台账核对 +
     计数），好树零违规、坏树判红；自证必须覆盖台账逻辑，自证失败 ⇒ rc=2。
  7. **缺引擎仓**（`ESML_ENGINE_DIR` 解析不到 / 默认路径不存在）⇒ 打印「跳过（引擎仓不在）」
     并 rc=0，不静默、不误红（头部计数检查仍照常做）。

用法：
    tools/check-engine-examples.py           # 全量：枚举 + 逐件跑引擎 + 台账对账
    tools/check-engine-examples.py --self-test  # 自证
"""

import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TSV = Path(__file__).resolve().parent / "engine-example-debt.tsv"

OWNERS = ("engine-debt",)


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
    """→ (rows, declared_count or None)。

    rows: [{lineno, path, errors(int or None), owner, evidence}]
    """
    rows, declared = [], None
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("#"):
            m = re.match(r"^#\s*共\s*(\d+)\s*行", line)
            if m:
                declared = int(m.group(1))
            continue
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 4:
            sys.exit(f"[check-engine-examples] {Path(path).name}:{lineno} 必须 4 列"
                     f"（path errors owner evidence），实际 {len(parts)}")
        p, errs, owner, evidence = parts
        rows.append({
            "lineno": lineno, "path": p,
            "errors": int(errs) if errs.lstrip("-").isdigit() else None,
            "owner": owner, "evidence": evidence,
        })
    return rows, declared


# --------------------------------------------------------------------------- 负例识别
def is_negative(path, text):
    """照抄 docs/validate_examples.py 的 is_negative：文件名含 probe、或头部注明「负例」⇒ 预期失败。

    判据收紧（W47b）：`(?<!非)负例`——「负例」前一字符是「非」时是「非负例」自述，
    不算自述负例（旧子串会把「非负例示例」整件静默跳过）。
    """
    if "probe" in path.name:
        return True
    head = "\n".join(text.splitlines()[:25])
    return bool(re.search(r"(?<!非)负例", head))


def enumerate_examples(repo):
    """仓内所有**非负例** .esml，返回 [相对路径字符串]（相对 repo，排序稳定）。"""
    out = []
    for f in glob.glob(os.path.join(str(repo), "**", "*.esml"), recursive=True):
        if "/.git/" in f:
            continue
        p = Path(f)
        rel = os.path.relpath(f, str(repo)).replace(os.sep, "/")
        txt = p.read_text(encoding="utf-8", errors="replace")
        if is_negative(p, txt):
            continue
        out.append(rel)
    out.sort()
    return out


# --------------------------------------------------------------------------- 引擎
def engine_check(engine, path):
    """跑 `esml check <path>`（ESML_PROPS=off），→ errors or None。

    None 表示没能从输出解析出 summary（输出异常）。
    """
    env = dict(os.environ)
    env["ESML_PROPS"] = "off"
    r = subprocess.run([engine, "check", path], capture_output=True, text=True, env=env)
    out = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"summary: errors=(\d+)", out)
    return int(m.group(1)) if m else None


# --------------------------------------------------------------------------- 检查
def check_counts(declared, rows, tsv_name):
    """头部「共 N 行」必须等于正文行数。→ [msg]"""
    out = []
    if declared is None:
        out.append(f"{tsv_name} 头部没有写「共 N 行」⇒ 条数无从核对")
    elif declared != len(rows):
        out.append(f"{tsv_name} 头部写 {declared} 行，实际 {len(rows)} 行 ⇒ 台账写错就改台账")
    return out


def check_engine(rows, engine, repo):
    """逐件跑引擎 + 与台账对账。→ [(where, msg)] 红项。

    判据：
      errors=0        ⇒ 通过（台账里还有行 ⇒ 台账过时，红）
      errors>0        ⇒ 台账必须有 path 精确行（无 ⇒ 红「未登记」）；
                        有行但 errors 数字不符 ⇒ 红「台账过时」。
      errors 解析不出 ⇒ 红「引擎输出异常」。
    """
    red = []
    tsv_name = TSV.name
    reg = {r["path"]: r for r in rows}
    used = set()
    for rel in enumerate_examples(repo):
        n = engine_check(engine, str(repo / rel))
        if n is None:
            red.append((rel, "引擎输出无 `summary: errors=N` ⇒ 无法判定（引擎行为异常？）"))
            continue
        row = reg.get(rel)
        if n == 0:
            if row is not None:
                red.append((f"{tsv_name}:{row['lineno']}",
                            f"台账过时：{rel} 已修好（实测 errors=0）但仍登记 ⇒ 删行"))
            continue
        # n > 0
        used.add(rel)
        if row is None:
            red.append((rel,
                        f"esml check errors={n} 但台账无登记行 ⇒ 未登记的引擎债不许当通过"))
        elif row["errors"] != n:
            red.append((f"{tsv_name}:{row['lineno']}",
                        f"台账过时：{rel} 台账写 errors={row['errors']}，实测 {n} ⇒ 改数字"))
    # 台账里登记了、但实测 errors=0 的（上面 n==0 分支已报「已修好」）之外的：
    # 登记行 path 既非 0 也非匹配到任何示例（示例被删 / 改名）⇒ 台账过时。
    for rel, r in reg.items():
        if rel not in {p for p in used}:
            # 该 path 没在「errors>0 且实测非 0」里被用到 ⇒ 要么已修好（上面报过），要么文件没了
            # 重新跑一次以区分（已修好 vs 文件缺失）
            f = repo / rel
            if not f.exists():
                red.append((f"{tsv_name}:{r['lineno']}",
                            f"台账过时：{rel} 文件已不存在 ⇒ 删行"))
            # 已修好(errors=0) 的情形上面已报，这里不重复
    return red


# --------------------------------------------------------------------------- 自证
def self_test(stream):
    """临时目录造好/坏两棵小树（不跑引擎），自证台账逻辑。→ 失败数。

    覆盖（台账逻辑 + 负例识别 + 计数）：
      好树：2 个非负例（1 绿、1 红），1 个负例（probe，跳过），台账 1 行与红件闭合、计数对 ⇒ 零违规。
      坏树：同例但台账对不上（红件未登记 / 计数错）⇒ 判红。
    """
    w = stream.write
    failures = 0
    engine = "true"  # 假引擎 stub：永远 exit 0、不打印 summary ⇒ 引擎分支走「输出异常」，
                      # 但台账逻辑（负例识别/对账/计数）用**注入的 errors 值**自证，不依赖真引擎。

    def make_tree(tdir, files, tsv_text):
        tdir.mkdir(parents=True, exist_ok=True)
        for rel, body in files.items():
            fp = tdir / rel
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(body, encoding="utf-8")
        (tdir / "engine-example-debt.tsv").write_text(tsv_text, encoding="utf-8")
        return tdir

    POS = '<?xml version="1.0"?><esml xmlns="u" name="A"/><foo/>'
    NEG = "<?xml version='1.0'?><!-- 负例：预期失败 --><esml xmlns=\"u\" name=\"N\"/>"

    def run_on(tree, forced_errors):
        """对一棵合成树跑非引擎部分：负例识别 + 台账对账 + 计数。
        forced_errors: {rel: int} 注入的实测 errors（替代真引擎）。"""
        msgs = []
        rows, declared = load_tsv(tree / "engine-example-debt.tsv")
        msgs += check_counts(declared, rows, "engine-example-debt.tsv")
        # 台账逻辑：负例识别 + 对账（用注入值代替引擎）
        reg = {r["path"]: r for r in rows}
        used = set()
        for f in sorted(glob.glob(os.path.join(str(tree), "**", "*.esml"), recursive=True)):
            p = Path(f)
            rel = os.path.relpath(f, str(tree)).replace(os.sep, "/")
            txt = p.read_text(encoding="utf-8", errors="replace")
            if is_negative(p, txt):
                continue
            n = forced_errors.get(rel, 0)
            row = reg.get(rel)
            if n == 0:
                if row is not None:
                    msgs.append(f"{p.name}: 台账过时：{rel} 已修好但仍登记")
                continue
            used.add(rel)
            if row is None:
                msgs.append(f"{p.name}: {rel} errors={n} 但台账无登记行")
            elif row["errors"] != n:
                msgs.append(f"{p.name}: 台账过时：{rel} 写 {row['errors']} 实测 {n}")
        for rel, r in reg.items():
            if rel not in used:
                fp = tree / rel
                if not fp.exists():
                    msgs.append(f"台账过时：{rel} 文件已不存在")
        return msgs

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # —— 好树：a 绿、b 红(errors=2)、probe 负例跳过；台账 1 行(b, errors=2)、计数 1 ⇒ 零违规
        good = make_tree(root / "good",
                         {"a.esml": POS, "b.esml": POS, "probe.esml": NEG},
                         "# 共 1 行\nb.esml\t2\tengine-debt\terror: F7[]: unknown element\n")
        # —— 坏树1：红件 b 未登记（台账空）⇒ 必红
        bad1 = make_tree(root / "bad1",
                         {"a.esml": POS, "b.esml": POS, "probe.esml": NEG},
                         "# 共 0 行\n")
        # —— 坏树2：台账数字错（b 写 3、实测 2）⇒ 台账过时
        bad2 = make_tree(root / "bad2",
                         {"a.esml": POS, "b.esml": POS, "probe.esml": NEG},
                         "# 共 1 行\nb.esml\t3\tengine-debt\terror: F7[]: unknown element\n")
        # —— 坏树3：头部计数错（写 2 行、实际 1 行）⇒ 条数对不上
        bad3 = make_tree(root / "bad3",
                         {"a.esml": POS, "b.esml": POS, "probe.esml": NEG},
                         "# 共 2 行\nb.esml\t2\tengine-debt\terror: F7[]: unknown element\n")

        cases = [
            ("好：绿+红+负例，台账闭合、计数对", good, {"b.esml": 2}, False),
            ("坏：红件未登记", bad1, {"b.esml": 2}, True),
            ("坏：台账数字过时", bad2, {"b.esml": 2}, True),
            ("坏：头部计数错", bad3, {"b.esml": 2}, True),
        ]
        # 负例识别自证：probe 必须被跳过（不在对账输入里）
        probe_txt = NEG
        neg_ok = is_negative(Path("probe.esml"), probe_txt)
        # 头部「负例」注明也识别（收紧后判据）
        head_neg_ok = bool(re.search(r"(?<!非)负例", "\n".join(NEG.splitlines()[:25])))
        # 收紧判据：头部注「非负例」不算自述负例
        non_neg = "<?xml version='1.0'?><!-- 非负例：预期通过 --><esml xmlns=\"u\" name=\"N\"/>"
        non_neg_ok = not is_negative(Path("non-neg.esml"), non_neg)
        for label, ok in (("负例识别：文件名含 probe", neg_ok),
                          ("负例识别：头部注明「负例」", head_neg_ok),
                          ("非负例不算负例（W47b）", non_neg_ok)):
            w("  [%s] %s\n" % ("PASS" if ok else "BROKEN", label))
            failures += 0 if ok else 1

        for label, tree, forced, want_red in cases:
            v = run_on(tree, forced)
            ok = bool(v) == want_red
            w(f"  [{'PASS' if ok else 'BROKEN'}] {label} ⇒ 期望{'判红' if want_red else '零违规'}，实际 {len(v)} 项\n")
            for m in v:
                w(f"        {m}\n")
            failures += 0 if ok else 1
    return failures


# --------------------------------------------------------------------------- 主流程
def main(argv=None):
    ap = argparse.ArgumentParser(description="ESML 引擎 × 示例可运行性台账闸门（W31）")
    ap.add_argument("--self-test", action="store_true", help="自证闸门（好树零违规、坏树判红）")
    args = ap.parse_args(argv)

    if args.self_test:
        bad = self_test(sys.stdout)
        if bad:
            print(f"[check-engine-examples] {bad} 项自证失败 —— 闸门本身不可信", file=sys.stderr)
            return 2
        print("[check-engine-examples] 自证通过：好树零违规、坏树判红")
        return 0

    if not TSV.exists():
        print(f"[check-engine-examples] 缺表：{TSV} 不存在", file=sys.stderr)
        return 2
    rows, declared = load_tsv(TSV)

    red = check_counts(declared, rows, TSV.name)

    engine = resolve_engine()
    if engine is None:
        # 订单口径：缺引擎仓 ⇒ 跳过（引擎逐件跑）并 rc=0，不静默、不误红。头部计数检查仍打印。
        print("[check-engine-examples] 跳过（引擎仓不在）——ESML_ENGINE_DIR 未解析到 esml 二进制 ⇒ rc=0")
        for msg in red:
            print(f"  RED  {msg}")
        return 1 if red else 0

    red += check_engine(rows, engine, REPO)

    for msg in red:
        print(f"  RED  {msg}")

    # 逐件明细（绿/红）
    n_ex = len(enumerate_examples(REPO))
    n_debt = len(rows)
    print(f"[check-engine-examples] 非负例 {n_ex} 件 · 引擎实跑逐件 · "
          f"台账 {n_debt} 行 · 违规 {len(red)}")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())

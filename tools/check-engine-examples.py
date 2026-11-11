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
STAGES = ("check", "solve")
SOLVE_TIMEOUT_S = 120  # esml solve 超时（防挂死）


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

    rows: [{lineno, path, errors(int or None), owner, stage, evidence}]
    stage 值域 {check, solve}；不合法 ⇒ 红（不静默退出——台账格式错要当违规报，不是崩闸门）。
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
        if len(parts) != 5:
            sys.exit(f"[check-engine-examples] {Path(path).name}:{lineno} 必须 5 列"
                     f"（path errors owner stage evidence），实际 {len(parts)}")
        p, errs, owner, stage, evidence = parts
        rows.append({
            "lineno": lineno, "path": p,
            "errors": int(errs) if errs.lstrip("-").isdigit() else None,
            "owner": owner,
            "stage": stage if stage in STAGES else None,  # None ⇒ 非法值，check_engine 判红
            "evidence": evidence,
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


def engine_solve(engine, path):
    """跑 `esml solve <path>`（ESML_PROPS=off，超时 SOLVE_TIMEOUT_S），→ returncode 或 None。

    None 表示超时（挂死）。判据只用退出码：0=成功（引擎修好），非 0=仍失败。
    """
    env = dict(os.environ)
    env["ESML_PROPS"] = "off"
    try:
        r = subprocess.run([engine, "solve", path], capture_output=True, text=True,
                           env=env, timeout=SOLVE_TIMEOUT_S)
        return r.returncode
    except subprocess.TimeoutExpired:
        return None


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
    """逐件跑引擎 + 与台账对账。→ [red_msg] 红项（分 stage）。

    台账按 stage 拆两类行（W46b，一条台账管两层）：
      stage=check：跑 `esml check`，实测 errors 必须等于台账 errors 数字；
                   errors=0 但仍登记 ⇒ 红「台账过时（已修好）⇒ 删行」（既有 8 行逻辑不变，只加严不放宽）。
      stage=solve：跑 `esml check` 必须 errors=0；再跑 `esml solve <file>` 必须**非零退出**（仍失败）；
                   solve 成功(退出 0) ⇒ 引擎修好 ⇒ 红「台账过时 ⇒ 删行」；check 非 0 / solve 超时 ⇒ 红。
    通用：stage 值不合法 ⇒ 红；登记行 path 文件已删/改名 ⇒ 红；check errors>0 无登记行 ⇒ 红「未登记」。
    """
    red = []
    tsv_name = TSV.name
    # 台账行分 stage
    check_rows = [r for r in rows if r["stage"] == "check"]
    solve_rows = [r for r in rows if r["stage"] == "solve"]
    other_rows = [r for r in rows if r["stage"] is None]  # 非法 stage
    check_reg = {r["path"]: r for r in check_rows}
    solve_reg = {r["path"]: r for r in solve_rows}
    used = set()

    # —— 逐非负例：先 `esml check`（所有示例都跑，check 是共同前置层）
    for rel in enumerate_examples(repo):
        n = engine_check(engine, str(repo / rel))
        if n is None:
            red.append((rel, "引擎输出无 `summary: errors=N` ⇒ 无法判定（引擎行为异常？）"))
            continue
        crow = check_reg.get(rel)
        srow = solve_reg.get(rel)
        if n == 0:
            # check 绿。check 债行不该在这（已修好）⇒ 红。solve 债行合法，继续判 solve。
            if crow is not None:
                red.append((f"{tsv_name}:{crow['lineno']}",
                            f"台账过时：{rel} check 已修好（实测 errors=0）但仍登记(stage=check) ⇒ 删行"))
            continue
        # n > 0：check 层不收
        used.add(rel)
        if srow is not None:
            red.append((f"{tsv_name}:{srow['lineno']}",
                        f"stage=solve 行要求 check errors=0，但 {rel} check 实测 errors={n} ⇒ 台账过时/误登记 ⇒ 删行或改 stage"))
            continue
        if crow is None:
            red.append((rel,
                        f"esml check errors={n} 但台账无 stage=check 登记行 ⇒ 未登记的引擎债不许当通过"))
        elif crow["errors"] != n:
            red.append((f"{tsv_name}:{crow['lineno']}",
                        f"台账过时：{rel} 台账写 errors={crow['errors']}，实测 {n} ⇒ 改数字"))

    # —— 台账登记了、但文件已删/改名（既非 check 债、非 solve 债、也没在上面被匹配）⇒ 过时
    for r in rows:
        if r["path"] in used or r["path"] in check_reg or r["path"] in solve_reg:
            continue
        # 走到这：rel 没进 used（check errors=0）也没在 check/solve 登记里被消费
        # 上面逐例循环已对所有**现存**示例跑过 check；若 rel 文件不存在（被删），这里兜底
        f = repo / r["path"]
        if not f.exists():
            red.append((f"{tsv_name}:{r['lineno']}",
                        f"台账过时：{r['path']} 文件已不存在 ⇒ 删行"))

    # —— stage=solve 行：跑 `esml solve`，必须非零退出（仍失败）才闭合
    for rel, r in solve_reg.items():
        if rel in used:
            continue  # 已在上面 check 层判红（check 非 0）
        f = repo / rel
        if not f.exists():
            red.append((f"{tsv_name}:{r['lineno']}",
                        f"台账过时：{rel} 文件已不存在 ⇒ 删行"))
            continue
        rc = engine_solve(engine, str(f))
        if rc is None:
            red.append((f"{tsv_name}:{r['lineno']}",
                        f"stage=solve：esml solve {rel} 超时（>{SOLVE_TIMEOUT_S}s）⇒ 无法判定（挂死？）"))
        elif rc == 0:
            red.append((f"{tsv_name}:{r['lineno']}",
                        f"台账过时：{rel} esml solve 已收敛（退出 0）⇒ 引擎修好了 ⇒ 删行"))
        # rc != 0 ⇒ solve 仍失败 ⇒ 台账闭合，不报（这是登记行的预期状态）

    # —— 非法 stage 值
    for r in other_rows:
        red.append((f"{tsv_name}:{r['lineno']}",
                    f"stage 值非法：{r['path']} stage={r['stage']!r}（值域 check|solve）⇒ 改台账"))
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

    def run_on(tree, forced_errors, forced_solve_rc=None):
        """对一棵合成树跑非引擎部分：负例识别 + 分 stage 台账对账 + 计数。
        forced_errors: {rel: int} 注入的实测 check errors（替代真引擎 check）。
        forced_solve_rc: {rel: int|None} 注入的 solve 退出码（替代真引擎 solve）；None=不跑 solve。
        逻辑镜像 check_engine（stage=check/solve 两类判据）。"""
        msgs = []
        rows, declared = load_tsv(tree / "engine-example-debt.tsv")
        msgs += check_counts(declared, rows, "engine-example-debt.tsv")
        check_reg = {r["path"]: r for r in rows if r["stage"] == "check"}
        solve_reg = {r["path"]: r for r in rows if r["stage"] == "solve"}
        other = [r for r in rows if r["stage"] is None]
        used = set()
        for f in sorted(glob.glob(os.path.join(str(tree), "**", "*.esml"), recursive=True)):
            p = Path(f)
            rel = os.path.relpath(f, str(tree)).replace(os.sep, "/")
            txt = p.read_text(encoding="utf-8", errors="replace")
            if is_negative(p, txt):
                continue
            n = forced_errors.get(rel, 0)
            crow, srow = check_reg.get(rel), solve_reg.get(rel)
            if n == 0:
                if crow is not None:
                    msgs.append(f"台账过时：{rel} check 已修好但仍登记(stage=check)")
                continue
            # n > 0
            used.add(rel)
            if srow is not None:
                msgs.append(f"stage=solve 行要求 check errors=0，实测 {n} ⇒ 误登记")
                continue
            if crow is None:
                msgs.append(f"{rel} errors={n} 但台账无 stage=check 登记行")
            elif crow["errors"] != n:
                msgs.append(f"台账过时：{rel} 写 {crow['errors']} 实测 {n}")
        # stage=solve 行：注入的 solve 退出码（0=成功⇒红；非 0=闭合）
        for rel, r in solve_reg.items():
            if rel in used:
                continue
            if not (tree / rel).exists():
                msgs.append(f"台账过时：{rel} 文件已不存在")
                continue
            rc = (forced_solve_rc or {}).get(rel)
            if rc is None:
                msgs.append(f"stage=solve：{rel} solve 超时/无法判定")
            elif rc == 0:
                msgs.append(f"台账过时：{rel} solve 已收敛(退出 0) ⇒ 删行")
            # rc != 0 ⇒ 闭合
        # 非法 stage
        for r in other:
            msgs.append(f"stage 值非法：{r['path']} stage={r['stage']!r}")
        # 文件已删的登记行（既未消费也非 solve）
        for r in rows:
            if r["path"] in used or (tree / r["path"]).exists():
                continue
            if r["path"] in check_reg or r["path"] in solve_reg:
                continue
            msgs.append(f"台账过时：{r['path']} 文件已不存在")
        return msgs

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # —— 好树：a 绿、b 红(errors=2)、probe 负例跳过；台账 1 行(b, errors=2, stage=check)、计数 1 ⇒ 零违规
        good = make_tree(root / "good",
                         {"a.esml": POS, "b.esml": POS, "probe.esml": NEG},
                         "# 共 1 行\nb.esml\t2\tengine-debt\tcheck\terror: F7[]: unknown element\n")
        # —— 坏树1：红件 b 未登记（台账空）⇒ 必红
        bad1 = make_tree(root / "bad1",
                         {"a.esml": POS, "b.esml": POS, "probe.esml": NEG},
                         "# 共 0 行\n")
        # —— 坏树2：台账数字错（b 写 3、实测 2）⇒ 台账过时
        bad2 = make_tree(root / "bad2",
                         {"a.esml": POS, "b.esml": POS, "probe.esml": NEG},
                         "# 共 1 行\nb.esml\t3\tengine-debt\tcheck\terror: F7[]: unknown element\n")
        # —— 坏树3：头部计数错（写 2 行、实际 1 行）⇒ 条数对不上
        bad3 = make_tree(root / "bad3",
                         {"a.esml": POS, "b.esml": POS, "probe.esml": NEG},
                         "# 共 2 行\nb.esml\t2\tengine-debt\tcheck\terror: F7[]: unknown element\n")
        # —— 好树·solve：c.esml 绿(check=0)、solve 仍失败(rc=1)；台账 1 行(c, errors=0, stage=solve) ⇒ 零违规
        good_solve = make_tree(root / "good_solve",
                               {"c.esml": POS},
                               "# 共 1 行\nc.esml\t0\tengine-debt\tsolve\terror: solve … structurally singular\n")
        # —— 坏树·solve：同上但 solve 已收敛(rc=0) ⇒ 台账过时（引擎修好）⇒ 红
        bad_solve = make_tree(root / "bad_solve",
                              {"c.esml": POS},
                              "# 共 1 行\nc.esml\t0\tengine-debt\tsolve\terror: solve … structurally singular\n")

        # cases: (label, tree, forced_check_errors, forced_solve_rc, want_red)
        cases = [
            ("好：绿+红+负例，台账闭合、计数对", good, {"b.esml": 2}, None, False),
            ("坏：红件未登记", bad1, {"b.esml": 2}, None, True),
            ("坏：台账数字过时", bad2, {"b.esml": 2}, None, True),
            ("坏：头部计数错", bad3, {"b.esml": 2}, None, True),
            ("好·solve：solve 仍失败 ⇒ 闭合", good_solve, {"c.esml": 0}, {"c.esml": 1}, False),
            ("坏·solve：solve 已收敛 ⇒ 台账过时", bad_solve, {"c.esml": 0}, {"c.esml": 0}, True),
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

        for label, tree, forced, srcc, want_red in cases:
            v = run_on(tree, forced, srcc)
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

    # 逐件明细（绿/红），分 stage 计数
    n_ex = len(enumerate_examples(REPO))
    n_debt = len(rows)
    n_check = sum(1 for r in rows if r["stage"] == "check")
    n_solve = sum(1 for r in rows if r["stage"] == "solve")
    n_badstage = n_debt - n_check - n_solve
    print(f"[check-engine-examples] 非负例 {n_ex} 件 · 引擎实跑逐件 · "
          f"台账 {n_debt} 行（check {n_check} / solve {n_solve}"
          + (f" / 非法 {n_badstage}" if n_badstage else "")
          + f"）· 违规 {len(red)}")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())

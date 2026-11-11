#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ESML 规范仓 · 示例「期望值」台账闸门（W70，第八道常驻闸）。

台账：tools/example-expectations.tsv
   path  mode(solve|simulate)  steps(N 或 -)  var  value  tol  source(头注|实测)

门做什么（每一条都能机械复核）：
  1. **读台账逐行跑引擎**：`ESML_PROPS=off esml <mode> <file> [--steps N]`——
     `--steps` 放文件路径**之后**（实测 rc=0 形式；放 mode 前或文件前引擎非零退出）。
     每行一次实跑（不合并、不缓存），超时 TIMEOUT_S ⇒ 红（无法判定）。
  2. **解析变量值**：solve 输出行 `  <var>  <科学计数>`（行首缩进两格 + 两个空格 + 数值）；
     simulate 输出先有表头 `t  <var1>  <var2>…`，数据行 `t  v1  v2…`，取 var 列**末条数据行**（末步值）。
     台账 value 与解析值按 tol **绝对差**比对（容差台账写死，不随步数漂移）；
     找不到该变量/解析不出值 ⇒ 红（引擎输出变了，台账没跟上）。
  3. **台账行 = 机器判据本身**：头注期望值与台账不符 ⇒ 台账值必与头注一致（改哪边是人的事，
     双标是红）；台账数字与引擎实测不符 ⇒ 红「台账过时」（引擎修了/示例改了，台账没跟上）。
  4. **头部计数当场重算**：`# 共 N 行` 必须等于台账正文行数 ⇒ 对不上就红（rc=1）。
  5. **缺引擎仓**（`ESML_ENGINE_DIR` 解析不到 / 默认路径不存在）⇒ 打印「跳过（引擎仓不在）」
     并 rc=0（同 check-engine-examples.py 口径），头部计数检查仍照常做。
  6. **`--self-test`**：假引擎 sh stub（按 argv 分发输出，值取 env FAKE_VAL 便于同一 stub 造好/坏两例）
     + 假台账 + 假示例树，覆盖「好行过 / 坏值红 / 缺引擎跳过」三例；自证失败 ⇒ rc=2。

与 engine-example-debt.tsv 的分工：本台账只登记**引擎跑得通**（退出 0）的示例的期望值；
跑不通的（如 L6-connect/port-array.esml，solve 仍 Pantelides DOF 少计失败）在 debt 台账
stage=solve 行登记，不写期望值行——「跑不跑得通」与「跑得通的值对不对」各管各的。
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TSV = Path(__file__).resolve().parent / "example-expectations.tsv"

MODES = ("solve", "simulate")
SOURCES = ("头注", "实测")
TIMEOUT_S = 120  # 单次引擎调用超时（防挂死）

# solve 输出数据行：行首缩进 + 变量路径 + 两个空格 + 科学计数（可带 ± 符号位，也可无符号）
ROW_RE = re.compile(r"^\s+([^ ]+)\s{2,}([-+]?\d[\d.eE+-]*)\s*$")
# simulate 数据行首列：十进制（表头 `t` 不匹配）
DEC_RE = re.compile(r"^-?[0-9]+\.[0-9]+$")


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

    rows: [{lineno, path, mode, steps(int or None), var, value(float), tol(float), source}]
    值域不合法（mode/steps/source）⇒ 记 None 或哨兵 "bad"，主流程判红（格式错当违规报，不崩闸门）。
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
        if len(parts) != 7:
            sys.exit(f"[check-example-expectations] {Path(path).name}:{lineno} 必须 7 列"
                     f"（path mode steps var value tol source），实际 {len(parts)}")
        p, mode, steps, var, value, tol, source = parts
        rows.append({
            "lineno": lineno, "path": p,
            "mode": mode if mode in MODES else None,
            "steps": int(steps) if steps.isdigit() else (None if steps == "-" else "bad"),
            "var": var,
            "value": float(value),
            "tol": float(tol),
            "source": source if source in SOURCES else None,
        })
    return rows, declared


# --------------------------------------------------------------------------- 引擎输出解析
def parse_var_value(output, mode, var):
    """从引擎输出里解析 var 的值。→ float | None。

    solve：行 `  <var>  <科学计数>`，取第一条匹配（稳态，各步同值）。
    simulate：表头行定 var 列下标；数据行 = 首列为十进制 t 的行；取该列**末条**（末步值）。
    """
    lines = output.splitlines()
    if mode == "solve":
        for ln in lines:
            m = ROW_RE.match(ln)
            if m and m.group(1) == var:
                return float(m.group(2))
        return None
    col = None
    for ln in lines:
        if ln.startswith("             "):  # 表头行（对齐缩进）
            toks = ln.split()
            if var in toks:
                col = toks.index(var)
            break
    if col is None:
        return None
    last = None
    for ln in lines:
        toks = ln.split()
        if len(toks) > col and DEC_RE.match(toks[0]):
            try:
                last = float(toks[col])
            except (ValueError, IndexError):
                pass
    return last


def run_engine(engine, mode, steps, path):
    """跑引擎一次。→ (returncode, output) 或 ("timeout", "")。

    注意：`--steps` 放子命令与文件路径**之后**（实测 rc=0 形式：
    `esml simulate <file> --steps N`；放 mode 前或文件前均非零退出）。
    """
    cmd = [engine, mode, path]
    if mode == "simulate":
        cmd += ["--steps", str(steps)]
    env = dict(os.environ)
    env["ESML_PROPS"] = "off"
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=TIMEOUT_S)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return "timeout", ""


# --------------------------------------------------------------------------- 检查
def check_counts(declared, rows, tsv_name):
    """头部「共 N 行」必须等于正文行数。→ [msg]"""
    out = []
    if declared is None:
        out.append(f"{tsv_name} 头部没有写「共 N 行」⇒ 条数无从核对")
    elif declared != len(rows):
        out.append(f"{tsv_name} 头部写 {declared} 行，实际 {len(rows)} 行 ⇒ 台账写错就改台账")
    return out


def check_expectations(rows, engine, repo, tsv_name):
    """逐台账行跑引擎 + 解析 + 比对。→ [red_msg]。"""
    red = []
    for r in rows:
        tag = f"{tsv_name}:{r['lineno']}"
        if r["mode"] is None:
            red.append(f"{tag} mode 值非法：{r['path']} mode={r['mode']!r}（值域 solve|simulate）")
            continue
        if r["source"] is None:
            red.append(f"{tag} source 值非法：{r['path']} source={r['source']!r}（值域 头注|实测）")
        if r["steps"] == "bad":
            red.append(f"{tag} steps 值非法：{r['path']} steps 须为 N（simulate）或 '-'（solve）")
            continue
        if r["mode"] == "solve" and r["steps"] is not None:
            red.append(f"{tag} solve 行 steps 必须 '-'，实际 {r['steps']}")
            continue
        if r["mode"] == "simulate" and r["steps"] is None:
            red.append(f"{tag} simulate 行必须带 steps=N，实际缺失")
            continue
        f = repo / r["path"]
        if not f.exists():
            red.append(f"{tag} 台账过时：{r['path']} 文件已不存在 ⇒ 删行")
            continue
        rc, out = run_engine(engine, r["mode"], r["steps"], str(f))
        if rc == "timeout":
            red.append(f"{tag} {r['path']} 引擎超时（>{TIMEOUT_S}s）⇒ 无法判定（挂死？）")
        elif rc != 0:
            red.append(f"{tag} {r['path']} 引擎退出 {rc} ⇒ 引擎行为变了（跑不通了？）⇒ "
                       f"删行（并登记 engine-example-debt.tsv stage=solve）或改台账")
            continue
        got = parse_var_value(out, r["mode"], r["var"])
        if got is None:
            red.append(f"{tag} {r['path']} 输出里解析不出 {r['var']} ⇒ 引擎输出变了 ⇒ 改台账")
            continue
        if abs(got - r["value"]) > r["tol"]:
            red.append(f"{tag} {r['path']} {r['var']} 台账 {r['value']}，实测 {got}，"
                        f"超出 tol={r['tol']} ⇒ 改台账数字或改头注（不许双标）")
    return red


def run_gate(tsv_path, repo, engine=None):
    """台账对账 + 引擎逐行实跑（engine=None ⇒ 缺引擎分支）。→ (rc, printed_msgs)"""
    rows, declared = load_tsv(tsv_path)
    red = check_counts(declared, rows, tsv_path.name)
    if engine is None:
        red.append("__SKIP__")
        # 缺引擎 ⇒ 跳过：仅当「共 N 行」计数核对通过（red 里只有 __SKIP__ 标记）才 rc=0；
        # 计数本身就错（red 有真红 + __SKIP__）⇒ rc=1（台账写错不因为缺引擎就放过）。
        return (0 if red == ["__SKIP__"] else 1), red
    red += check_expectations(rows, engine, repo, tsv_path.name)
    return (1 if red else 0), red


# --------------------------------------------------------------------------- 自证
FAKE_ENGINE = (
    "#!/bin/sh\n"
    'v="${FAKE_VAL:-0.5000000000e0}"\n'
    "a1=\"$1\"\n"
    'if [ "$a1" = "simulate" ]; then exit 0; fi\n'
    'if [ "$a1" = "solve" ]; then\n'
    "  echo 'system: S (1 unknowns)'\n"
    "  echo \"  m.x  $v\"\n"
    "  exit 0\n"
    "fi\n"
    "exit 1\n"
)


def self_test(stream):
    """假引擎 stub + 假台账 + 假示例树，覆盖三例。→ 失败数。

      好行过：台账 value 与假引擎输出一致 ⇒ 零违规（rc=0）。
      坏值红：台账 value 差超 tol ⇒ 判红（rc=1），消息含「超出 tol」。
      缺引擎跳过：ESML_ENGINE_DIR 指向不存在 ⇒ rc=0 且打印「跳过」（头部计数仍核对）。
    """
    w = stream.write
    failures = 0
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        def make_tree(name, tsv_text):
            """ESML_ENGINE_DIR 语义 = **引擎仓目录**（resolve_engine 拼 <dir>/esml）。"""
            tree = root / name
            (tree / "sub").mkdir(parents=True)
            (tree / "sub" / "a.esml").write_text(
                '<?xml version="1.0"?><esml xmlns="u" name="A"/>', encoding="utf-8")
            (tree / "example-expectations.tsv").write_text(tsv_text, encoding="utf-8")
            ed = tree / "engine"
            ed.mkdir()
            ep = ed / "esml"
            ep.write_text(FAKE_ENGINE, encoding="utf-8")
            ep.chmod(0o755)
            return tree, str(ed)

        good, good_ed = make_tree("good",
                                  "# 共 1 行\nsub/a.esml\tsolve\t-\tm.x\t0.5\t1e-6\t头注\n")
        badval, badval_ed = make_tree("badval",
                                      "# 共 1 行\nsub/a.esml\tsolve\t-\tm.x\t0.9\t1e-6\t头注\n")

        def run(tree, engine_dir, fake_val):
            # resolve_engine() 读 os.environ ⇒ 必须真改进程环境（子进程 env 传不进它）。
            old_env = dict(os.environ)
            os.environ["ESML_ENGINE_DIR"] = engine_dir
            os.environ["FAKE_VAL"] = fake_val
            try:
                engine = resolve_engine()
                rc, red = run_gate(tree / "example-expectations.tsv", tree, engine)
                return rc, red
            finally:
                os.environ.clear()
                os.environ.update(old_env)

        # 好例：零违规 rc=0
        rc, red = run(good, good_ed, "0.5000000000e0")
        ok = (rc == 0 and not red)
        w(f"  [{'PASS' if ok else 'BROKEN'}] 好行过：期望零违规 rc=0，实际 rc={rc}，红项 {len(red)}\n")
        for m in red:
            w(f"        {m}\n")
        failures += 0 if ok else 1

        # 坏值例：rc=1 且报「超出 tol」
        rc, red = run(badval, badval_ed, "0.5000000000e0")
        ok = (rc == 1 and any("超出 tol" in m for m in red))
        w(f"  [{'PASS' if ok else 'BROKEN'}] 坏值红：期望 rc=1 报「超出 tol」，实际 rc={rc}\n")
        for m in red:
            w(f"        {m}\n")
        failures += 0 if ok else 1

        # 缺引擎例：ESML_ENGINE_DIR 指向不存在 ⇒ 跳过 rc=0
        rc, red = run(good, str(root / "no-such-engine"), "0.5000000000e0")
        ok = (rc == 0 and "__SKIP__" in red and not any(m != "__SKIP__" for m in red))
        w(f"  [{'PASS' if ok else 'BROKEN'}] 缺引擎跳过：期望 rc=0 且仅跳过标记，实际 rc={rc}\n")
        for m in red:
            w(f"        {m}\n")
        failures += 0 if ok else 1
    return failures


# --------------------------------------------------------------------------- 主流程
def main(argv=None):
    ap = argparse.ArgumentParser(description="ESML 示例「期望值」台账闸门（W70，第八道常驻闸）")
    ap.add_argument("--self-test", action="store_true", help="自证闸门（好行过 / 坏值红 / 缺引擎跳过）")
    args = ap.parse_args(argv)

    if args.self_test:
        bad = self_test(sys.stdout)
        if bad:
            print(f"[check-example-expectations] {bad} 项自证失败 —— 闸门本身不可信", file=sys.stderr)
            return 2
        print("[check-example-expectations] 自证通过：好行过 / 坏值红 / 缺引擎跳过")
        return 0

    if not TSV.exists():
        print(f"[check-example-expectations] 缺表：{TSV} 不存在", file=sys.stderr)
        return 2

    engine = resolve_engine()
    rc, red = run_gate(TSV, REPO, engine)
    if engine is None:
        # 订单口径：缺引擎仓 ⇒ 跳过 rc=0，不静默、不误红。头部计数检查仍打印。
        print("[check-example-expectations] 跳过（引擎仓不在）——ESML_ENGINE_DIR 未解析到 esml 二进制 ⇒ rc=0")
    else:
        rows, _ = load_tsv(TSV)
        n_ex = len({r["path"] for r in rows})
        print(f"[check-example-expectations] 台账 {len(rows)} 行（{n_ex} 件示例）· 违规 {len(red)}")
    for msg in red:
        if msg == "__SKIP__":
            continue
        print(f"  RED  {msg}")
    return rc


if __name__ == "__main__":
    sys.exit(main())

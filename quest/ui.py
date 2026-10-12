"""터미널 출력 도우미: 색상, 한글 폭을 고려한 표, 진행 바, 말풍선."""
import os
import sys
import unicodedata

# 윈도우 콘솔에서 한글·ANSI 색상이 깨지지 않게
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
if os.name == "nt":
    os.system("")

USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _c(code):
    def f(s):
        return f"\033[{code}m{s}\033[0m" if USE_COLOR else str(s)
    return f


bold = _c("1")
dim = _c("2")
red = _c("31")
green = _c("32")
yellow = _c("33")
blue = _c("34")
magenta = _c("35")
cyan = _c("36")
gold = _c("1;33")


def width(s):
    s = str(s)
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in s)


def pad(s, w):
    s = str(s)
    return s + " " * max(0, w - width(s))


def cut(s, w):
    s = str(s)
    if width(s) <= w:
        return s
    out = ""
    for ch in s:
        if width(out + ch) > w - 1:
            break
        out += ch
    return out + "…"


def fmt_val(v):
    if v is None:
        return "NULL"
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e15:
            return f"{v:.1f}"
        return f"{v:.4f}".rstrip("0").rstrip(".")
    return str(v)


def table(columns, rows, max_rows=20, max_col=24):
    cols = [str(c) for c in columns]
    shown = rows[:max_rows]
    cells = [[cut(fmt_val(v), max_col) for v in r] for r in shown]
    ws = [width(c) for c in cols]
    for r in cells:
        for i, v in enumerate(r):
            ws[i] = max(ws[i], width(v))
    line = "+" + "+".join("-" * (w + 2) for w in ws) + "+"
    out = [line, "| " + " | ".join(bold(pad(c, ws[i])) for i, c in enumerate(cols)) + " |", line]
    for r in cells:
        out.append("| " + " | ".join(pad(v, ws[i]) for i, v in enumerate(r)) + " |")
    out.append(line)
    if len(rows) > max_rows:
        out.append(dim(f"  … 외 {len(rows) - max_rows}행 (총 {len(rows)}행)"))
    else:
        out.append(dim(f"  총 {len(rows)}행"))
    return "\n".join(out)


def bar(done, total, size=20):
    total = max(total, 1)
    filled = int(round(size * done / total))
    return green("█" * filled) + dim("░" * (size - filled))


def box(title, lines, color=cyan):
    inner = max([width(title) + 2] + [width(l) for l in lines] + [40])
    top = color("┌─ ") + bold(title) + color(" " + "─" * (inner - width(title) - 1) + "┐")
    out = [top]
    for l in lines:
        out.append(color("│ ") + pad(l, inner) + color(" │"))
    out.append(color("└" + "─" * (inner + 2) + "┘"))
    return "\n".join(out)


def wrap(text, w=64):
    """한글 폭 기준 줄바꿈."""
    lines = []
    for para in str(text).split("\n"):
        cur = ""
        for word in para.split(" "):
            cand = (cur + " " + word) if cur else word
            if width(cand) > w and cur:
                lines.append(cur)
                cur = word
            else:
                cur = cand
        lines.append(cur)
    return lines


def say(who, text, color=cyan):
    print(color(f"💬 {who}"))
    for l in wrap(text):
        print("   " + l)

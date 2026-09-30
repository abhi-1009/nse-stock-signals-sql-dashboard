"""Quote-aware SQL file splitter + runner (used to execute sql/*.sql on Aiven from Python)."""
import re
from pathlib import Path


def split_statements(text: str) -> list[str]:
    """Split on ';' outside quotes, drop '-- comments', MYSQL_ONLY blocks and USE statements."""
    text = re.sub(r"-- MYSQL_ONLY_START.*?-- MYSQL_ONLY_END", "", text, flags=re.S)
    out, buf, quote, i, n = [], [], None, 0, len(text)
    while i < n:
        ch = text[i]
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"', "`"):
            quote = ch
            buf.append(ch)
        elif ch == "-" and text[i:i + 2] == "--" and (i + 2 >= n or text[i + 2] in " \t\r\n"):
            while i < n and text[i] != "\n":
                i += 1
            continue
        elif ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                out.append(stmt)
            buf = []
        else:
            buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    return [s for s in out if not re.match(r"^USE\b", s, re.I)]


def run_file(conn, path: Path, echo: bool = True):
    """Execute every statement of a .sql file on a DBAPI connection; return SELECT results."""
    results = []
    cur = conn.cursor()
    for stmt in split_statements(path.read_text()):
        cur.execute(stmt)
        if cur.description:
            results.append((stmt[:60].replace("\n", " "), cur.fetchall()))
    conn.commit()
    cur.close()
    if echo:
        print(f"ran {path.name}: {len(results)} result set(s)")
    return results

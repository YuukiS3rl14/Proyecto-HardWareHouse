"""Ejecuta archivos .sql de seed usando la conexión de Django (sin psql)."""
from __future__ import annotations

import re
from pathlib import Path


_SKIP_PREFIXES = ("SET ", "BEGIN", "COMMIT", "ROLLBACK")


def _strip_sql_comments(sql: str) -> str:
    lines = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        lines.append(line)
    return "\n".join(lines)


def iter_sql_statements(sql: str):
    """Divide SQL en sentencias respetando literales entre comillas simples."""
    cleaned = _strip_sql_comments(sql)
    buf: list[str] = []
    in_string = False
    i = 0
    while i < len(cleaned):
        ch = cleaned[i]
        if ch == "'" and not in_string:
            in_string = True
            buf.append(ch)
        elif ch == "'" and in_string:
            if i + 1 < len(cleaned) and cleaned[i + 1] == "'":
                buf.append("''")
                i += 1
            else:
                in_string = False
                buf.append(ch)
        elif ch == ";" and not in_string:
            statement = "".join(buf).strip()
            if statement:
                yield statement
            buf = []
        else:
            buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        yield tail


def load_sql_file(path: Path, cursor) -> int:
    """
    Ejecuta un archivo SQL. Devuelve la cantidad de sentencias ejecutadas.
    """
    if not path.is_file():
        raise FileNotFoundError(path)

    sql = path.read_text(encoding="utf-8")
    executed = 0
    for statement in iter_sql_statements(sql):
        head = re.sub(r"\s+", " ", statement.split("(", 1)[0]).strip().upper()
        if any(head.startswith(prefix) for prefix in _SKIP_PREFIXES):
            continue
        cursor.execute(statement)
        executed += 1
    return executed

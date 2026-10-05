"""Valida el prefijo Conventional Commit. Lo usan el hook commit-msg y el job `prefix` del CI.

python scripts/check_commit_msg.py --file .git/COMMIT_EDITMSG
python scripts/check_commit_msg.py --require-key "feat(fx): cotización MEP [PF-30]"
"""

import argparse
import io
import re
import sys
from collections.abc import Sequence
from pathlib import Path

TYPES = (
    "feat",
    "fix",
    "refactor",
    "perf",
    "test",
    "docs",
    "style",
    "build",
    "ci",
    "chore",
    "revert",
)
PREFIX = re.compile(rf"^(?:{'|'.join(TYPES)})(?:\([a-z0-9-]+\))?!?: \S")
JIRA_KEY = re.compile(r"\[PF-\d+\]")


def subject_from_file(path: Path) -> str:
    """Primera línea con contenido del mensaje, ignorando los comentarios de git."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            return line.strip()
    return ""


def check(subject: str, *, require_key: bool = False) -> str | None:
    """Devuelve el error, o None si el asunto es válido."""
    if not PREFIX.match(subject):
        return (
            f"Prefijo inválido: {subject!r}\n"
            f"  Formato: <tipo>(<scope opcional>): <descripción>\n"
            f"  Tipos: {', '.join(TYPES)}"
        )
    if require_key and not JIRA_KEY.search(subject):
        return f"Falta la key de Jira [PF-<n>]: {subject!r}"
    return None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("subjects", nargs="+", help="asuntos a validar (o archivos con --file)")
    parser.add_argument("--file", action="store_true", help="los argumentos son archivos")
    parser.add_argument("--require-key", action="store_true", help="exige [PF-<n>]")
    args = parser.parse_args(argv)

    subjects = [subject_from_file(Path(s)) for s in args.subjects] if args.file else args.subjects
    errors = [e for s in subjects if (e := check(s, require_key=args.require_key))]
    if isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr.reconfigure(encoding="utf-8")  # en Windows la salida capturada usa cp1252
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

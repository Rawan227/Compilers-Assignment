from __future__ import annotations

import sys
from pathlib import Path

from nfa import NFA


def process_regex(regex: str, out_name: str) -> NFA:
    nfa = NFA.build_regex_nfa(regex)

    if out_name:
        out_base = Path(out_name)
        nfa.save_json(out_base.with_suffix(".nfa.json"))
    return nfa


def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python main.py <regex> [out_base]")
        return 2

    regex = argv[1]
    out_base = argv[2] if len(argv) >= 3 else ""
    process_regex(regex, out_base)

    if not out_base:
        print(NFA.build_regex_nfa(regex).to_json())

    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))

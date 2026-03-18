from __future__ import annotations

import sys
import os
import shutil
from pathlib import Path

from nfa import NFA
from dfa import nfa_to_dfa, minimize_dfa, plot_dfa, save_dfa_json


def process_regex(regex: str, out_name: str) -> NFA:
    nfa = NFA().build_regex_nfa(regex)
    nfa_dict = nfa.to_dict()

    if out_name:
        nfa.save_nfa_to_json(f"{out_name}_nfa.json", ".")
        nfa.plot_nfa(f"{out_name}_nfa.png")
        src = os.path.join("outputs", "nfa", f"{out_name}_nfa.png")
        if os.path.exists(src):
            shutil.move(src, f"{out_name}_nfa.png")

        min_dfa = minimize_dfa(nfa_to_dfa(nfa_dict))
        save_dfa_json(min_dfa, f"{out_name}_dfa.json")
        plot_dfa(min_dfa, f"{out_name}_dfa.png")

    return nfa


def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python main.py <regex> [out_base]")
        return 2

    regex = argv[1]
    out_base = argv[2] if len(argv) >= 3 else ""
    process_regex(regex, out_base)

    if not out_base:
        print(NFA().build_regex_nfa(regex).to_json())

    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
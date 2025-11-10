   


import pathlib
import sys
from typing import Set
from models.model import SolutionSet
from slnprojparse.loghelper import log_debug
from slnprojparse.parsing import _collect_sln_files, discover_solution_set, parse_proj, parse_solution, solution_set_to_json


def parse_from_argv(argv):
    """
    Entry point.

    * If a path to a *.sln* file is given → parse that file.
    * If a path to a directory is given → parse **all** *.sln* files inside it.
    * If no argument is supplied → print usage and exit with code 1.
    """
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("Usage: parse_from_argv(<path-to-sln-or-folder>)", file=sys.stderr)
        return 1
    print("argv[0]::",''.join(argv))
    target = pathlib.Path(''.join(argv)).resolve()
    print("mainentry::{target}",target)
    sln_files = _collect_sln_files(target)

    if not sln_files:
        print(f"[INFO] No .sln files to process under {target}", file=sys.stderr)
        return 0

    solution_set = discover_solution_set(target)

    print(solution_set_to_json(solution_set))

    # Return 0 to indicate success
    return 0

def parse_from_target_path(target:pathlib.Path):
    """
    Entry point.

    * If a path to a *.sln* file is given → parse that file.
    * If a path to a directory is given → parse **all** *.sln* files inside it.
    * If no argument is supplied → print usage and exit with code 1.
    """

    target = pathlib.Path(target).resolve()
    log_debug("mainentry::{target}",target)
    sln_files = _collect_sln_files(target)

    if not sln_files:
        print(f"[INFO] No .sln files to process under {target}", file=sys.stderr)
        return 0

    solution_set = discover_solution_set(target)

    print(solution_set_to_json(solution_set))

    # Return 0 to indicate success
    return 0




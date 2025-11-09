import sys

from slnprojparse.parsing import _collect_sln_files, discover_solution_set, solution_set_to_json
import pathlib

from slnprojparse.loghelper import log_debug


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
    target = pathlib.Path(''.join(argv)).resolve()
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
    Entry point - folder where python is being called.

    * If a path to a *.sln* file is given → parse that file.
    * If a path to a directory is given → parse **all** *.sln* files inside it.
    * If no argument is supplied → print usage and exit with code 1.
    """

    target = pathlib.Path().absolute()
    sln_files = _collect_sln_files(target)

    if not sln_files:
        print(f"[INFO] No .sln files to process under {target}", file=sys.stderr)
        return 0

    solution_set = discover_solution_set(target)
    print(solution_set_to_json(solution_set))

    # Return 0 to indicate success
    return 0


if __name__ == "__main__":
    exec_path=pathlib.Path(__file__).parent.resolve()
    log_debug(exec_path)
    if sys.argv is not None:
        argv = sys.argv[1:]

    if not argv:
        #slnList = list("/home/vertikal/P8/mntSrc.ai/src.dotnet")
        parse_from_target_path(exec_path)
    else:
        parse_from_argv(argv)
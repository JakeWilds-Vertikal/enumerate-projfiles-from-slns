#
"""
Parse VisualStudio solution (*.sln*) files and collect all referenced
project names (e.g. CSProj, VBProj, VcProj, FsProj …).

Features
--------
* Works on any platform (Windows, macOS, Linux) – only the Python standard
  library is required.
* Handles the most common project extensions:
      .csproj, .vbproj, .vcxproj, .fsproj, .vcproj, .proj
* Returns a `list[str]` with the *project name* (file name without extension).
* Optionally validates an **XML** representation of a solution against a
  supplied XSD schema (demonstrates how you could use the schema you mentioned).

Usage
-----
    python parse_sln.py  path/to/MySolution.sln
    # or parse all *.sln files in a folder:
    python parse_sln.py  path/to/folder/

The script prints the collected project names to STDOUT.
"""

 
# --------------------------------------------------------------
#   Updated parsing utilities – they now populate the data model
# --------------------------------------------------------------

import pathlib
import re
import sys
import os
import xml.etree.ElementTree as ET
from typing import List, Dict, Set, Tuple
from .loghelper import log_debug,log_info
from models.model import Language,Solution,Project,CodeFile,SolutionSet,SolutionSchema,ProjectSchema,CodeFileSchema,SolutionSetSchema

# ------------------------------------------------------------------
# * Helpers that turn a plain‑text .sln file into a Solution object
# ------------------------------------------------------------------

_PROJECT_LINE_RE = re.compile(
    r'''
    ^Project\("\{[^}]+\}"\)      # literal Project("{GUID}")
    \s*=\s*
    "(?P<proj_name>[^"]+)"       # display name (may contain spaces)
    \s*,\s*
    "(?P<proj_path>[^"]+)"       # relative path to the .csproj/.vbproj …
    \s*,\s*
    "\{[^}]+\}"                  # the project GUID (ignored)
    ''',
    re.IGNORECASE | re.VERBOSE,
)

# ------------------------------------------------------------------
# * Language detection – maps file‑extensions to the Language Enum
# ------------------------------------------------------------------
_EXTENSION_LANGUAGE_MAP = {
    ".cs":   "CS",
    ".fs":   "FS",
    ".vb":   "VB",
    ".py":   "PY",
    ".java": "JAVA",
    ".js":   "JS",
   # ".csproj": "PROJECT",
   # ".vbproj": "PROJECT"
    # add more extensions as you need them
}


def _detect_language(file_name: str) -> Language:
    """Very small heuristic based on file‑extension."""
    ext = os.path.splitext(file_name)[1].lower()
    return {
        ".cs": Language.CSharp,
        ".fs": Language.FSharp,
        ".vb": Language.VB,
        ".py": Language.Python,
        ".java": Language.Java,
        ".js": Language.JavaScript,
        ".csproj": Language.CSProject,
        ".vbproj": Language.VBProject,
    }.get(ext, Language.Empty)   # fallback – you can change it


def parse_proj(
    proj_path: pathlib.Path,
    visited: Set[pathlib.Path] | None = None,
) -> Tuple[Project, List[Project]]:
    """
    Parse a single *.proj* (csproj, vbproj, …) file.

    Returns
    -------
    Tuple[Project, List[Project]]
        * The fully‑populated ``Project`` instance for *proj_path*.
        * A list of **child** ``Project`` objects that were discovered via
          ``<ProjectReference Include="…"/>``.  These are **not** added to the
          parent automatically – the caller decides whether to nest them or
          keep them flat.
    """
    if visited is None:
        visited = set()
    proj_path=str(proj_path).replace("\\","/")
    proj_path=pathlib.Path(proj_path)
    proj_path = proj_path.resolve()
    if not proj_path.is_file():
        raise FileNotFoundError(f"Project file not found: {proj_path}")

    # ------------------------------------------------------------------
    # * Load the XML (keep namespace because the schema uses it)
    # ------------------------------------------------------------------
    tree = ET.parse(str(proj_path))
    root = tree.getroot()

    # ------------------------------------------------------------------
    # * Determine default namespace (MSBuild uses http://schemas.microsoft.com/developer/msbuild/2003)
    # ------------------------------------------------------------------
    ns_prefix = ""
    ns_map = {}
    if root.tag.startswith("{"):
        ns_uri = root.tag.split("}")[0].strip("{")
        ns_prefix = f"{{{ns_uri}}}"
        ns_map = {"msb": ns_uri}

    # ------------------------------------------------------------------
    # * Gather source files (<Compile Include="…"/> etc.)
    # ------------------------------------------------------------------
    code_files: List[CodeFile] = []
    child_projects: List[Project] = []
    for item in root.findall(f".//{ns_prefix}Compile"):
        inc = item.attrib.get("Include")
        if not inc:
            continue
        src_path = (proj_path.parent / inc).resolve()
        if src_path.is_file():
            _language = _detect_language(src_path.name)
            if _language is Language.CSharp or _language is Language.VB:
                cf = CodeFile(
                    file_name=os.path.basename(src_path),
                    full_path=str(src_path),
                    language=_detect_language(src_path.name),
                )
                code_files.append(cf)
            if _language is Language.CSProject or _language is Language.VBProject:
                prj = Project(
                    file_name=os.path.basename(src_path),
                    full_path=str(src_path), 
                )
                child_projects.append(_process_child_project(prj))

    # ------------------------------------------------------------------
    # * Discover child projects (ProjectReference)
    # ------------------------------------------------------------------
    
    for ref in root.findall(f".//{ns_prefix}ProjectReference"):
        if 'Include' in ref.attrib:
            child_path = (proj_path.parent / ref.attrib["Include"]).resolve()
            # Guard against circular references – we simply ignore already‑visited ones.
            if child_path in visited:
                continue
            visited.add(child_path)
            child_proj, grandchildren = parse_proj(child_path, visited=visited)
            # Nest grandchildren under the child we just created
            child_proj.child_projects.extend(grandchildren)
            child_projects.append(child_proj)

    # ------------------------------------------------------------------
    # * Build the Project dataclass
    # ------------------------------------------------------------------
    project_type="UNKNOWN"
    if "Sdk" in root.attrib:
        if root.attrib["Sdk"] is not None:
            if root.attrib["Sdk"]== "Microsoft.NET.Sdk":
                project_type="dotNET_SDK"
    collected_source_files =  code_files #_collect_source_files(root, ns_prefix, proj_path.parent)
    if len(collected_source_files) < 1 and project_type=="dotNET_SDK":
        collected_source_files=_get_sdk_files(project_type,proj_path.parent)
    proj_file_name = proj_path.name
    proj_folder_path = str(proj_path.parent.resolve())
    proj_full_path = str(proj_path.parent.resolve())
    proj_full_path += "/"
    proj_full_path += proj_file_name
    project = Project(
        full_path=str(proj_full_path),
        project_folder_path=str(proj_folder_path),
        name=proj_path.stem,
        code_files=collected_source_files,
        child_projects=child_projects,
    )
    return project, child_projects

def  _get_sdk_files(project_Type:str, proj_path:pathlib.Path) ->List[pathlib.Path]:
    codeList:List[pathlib.Path] = []

    for cs_file in proj_path.rglob("*.cs"):
        codeList.append(cs_file.resolve())
    for vb_file in proj_path.rglob("*.vb"):
        codeList.append(vb_file.resolve())

    code_files= [
            CodeFile(
                file_name=os.path.basename(cf_path),
                full_path=str(cf_path),
                language=_detect_language(cf_path.name),
            )
            for cf_path in codeList
    ]
    return code_files

# ------------------------------------------------------------------
# * Parse a single project file (csproj, vbproj, …) → Project dataclass
# ------------------------------------------------------------------
def _parse_project_file(proj_path: pathlib.Path) -> Project:
    """
    Build a :class:`Project` instance for *proj_path*.

    The function re‑uses the existing ``parse_proj`` logic that extracts
    every <Compile Include="…"/> element and enriches the result with a
    language identifier.
    """

    # The *name* of the project is the file‑stem (MyApp.csproj → MyApp)
    name = proj_path.stem
    proj_file_name = proj_path.name
    # Use the original ``parse_proj`` implementation to collect raw
    # dictionaries (filename + absolute path) for every <Compile> element.
    rootProj,childProj = parse_proj(proj_path)          # <-- the original helper from the script
    code_files=rootProj.code_files
    child_projects = [_process_child_project(p) for p in childProj]
    log_debug("::code_files::",code_files)
    proj_folder_path = str(proj_path.parent.resolve())
    proj_full_path = str(proj_path.parent.resolve())
    proj_full_path += "/"
    proj_full_path += proj_file_name
    return Project(
        full_path=str(proj_full_path),
        project_folder_path=str(str(proj_folder_path)),
        name=name,
        code_files=code_files, child_projects=child_projects
    )

def _process_child_project(child_project:Project) -> Project:
    log_debug("::child_project::",child_project)
    child_project_folder_path = pathlib.Path(child_project.full_path).parent.resolve()
    child_project.project_folder_path = str(child_project_folder_path)
    return child_project
     
# ------------------------------------------------------------------
# * Parse a .sln file → Solution dataclass (populated with Projects)
# ------------------------------------------------------------------
def _parse_solution_file(sln_path: pathlib.Path) -> Solution:
    """
    Turn a plain‑text ``*.sln`` file into a :class:`Solution` instance.

    * All project paths referenced in the file are resolved to absolute
      paths.
    * For each project we call ``_parse_project_file`` to collect its
      source files.
    * The resulting ``Solution`` contains a list of fully‑populated
      :class:`Project` objects.
    """

    solution_name = sln_path.name
    solution_root = str(sln_path.parent.resolve())

    solution = Solution(
        full_path=solution_root,
        solution_name=solution_name,
        projects=[],
    )

    # Walk the solution line‑by‑line and extract every project reference.
    try:
        with sln_path.open(encoding="utf-8") as fh:
            for line in fh:
                m = _PROJECT_LINE_RE.match(line)
                if not m:
                    continue

                proj_path = pathlib.Path(m.group("proj_path").replace("\\","/"))
                sProj_path = str(proj_path)
                #Check to make sure the ref is to a supported type
                if '.csproj' in sProj_path.lower() or '.vbproj' in sProj_path:
                    # The path stored in the .sln is relative to the .sln location.
                    abs_proj_path = (sln_path.parent / proj_path).resolve()
                
                    # Build a Project object (including its code files)
                    project = _parse_project_file(abs_proj_path)
                    solution.projects.append(project)

    except (OSError, UnicodeDecodeError) as exc:
        log_debug(f"[ERROR] Could not read solution '{sln_path}': {exc}", file=sys.stderr)

    return solution


# ------------------------------------------------------------------
# * Public entry‑point – discover every solution under *start_path*
# ------------------------------------------------------------------
def discover_solution_set(start_path: pathlib.Path) -> SolutionSet:
    """
    Scan *start_path* (recursively) for ``*.sln`` files and return a
    :class:`SolutionSet` that contains fully‑populated :class:`Solution`
    objects.

    The function is the only thing you need to call from user code – it
    returns the top‑level container you asked for.
    """

    start_path = start_path.resolve()
    log_debug(":: start_path ::", start_path)
    solution_set = SolutionSet(start_path=str(start_path.absolute()), solutions=[])

    for sln_file in start_path.rglob("*.sln"):
        solution = _parse_solution_file(sln_file)
        solution_set.solutions.append(solution)

    return solution_set


# ------------------------------------------------------------------
# * Optional: Serialisation to JSON using the generated Marshmallow
#      schemas (just a convenience – not required for the core task)
# ------------------------------------------------------------------
def solution_set_to_json(solution_set: SolutionSet) -> str:
    """
    Serialise a :class:`SolutionSet` to a pretty‑printed JSON string.
    """
    schema = SolutionSetSchema()
    return schema.dumps(solution_set, indent=2)

# ---------------------------------------------------------------------------
#  Command‑line interface
# ---------------------------------------------------------------------------

def _collect_sln_files(target: pathlib.Path) -> List[pathlib.Path]:
    """Return a list of *.sln* files under *target* (file or directory)."""
    if target.is_file() and target.suffix.lower() == ".sln":
        return [target]
    elif target.is_dir():
        log_debug("::target::",target)
        log_debug(sorted(target.rglob("*.sln")))
        return sorted(target.rglob("*.sln"))
    else:
        log_debug(f"[WARN] No .sln file found at {target}", file=sys.stderr)
        return []


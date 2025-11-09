# file: model.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

import marshmallow
import marshmallow_dataclass
from marshmallow import fields


class Language(str, Enum):
    """Allowed programming‑language codes."""
    CSharp = "CS"
    FSharp = "FS"
    VB = "VB"
    Python = "PY"
    Java = "JAVA"
    JavaScript = "JS"
    CSProject="CSPROJECT" #backup for Project ref
    VBProject="VBPROJECT" #backup for Project ref
    Empty="EMPTY"
    # add more as needed

class ProjectType(str, Enum):
    """Known Project Types."""
    SDK = "Microsoft.NET.Sdk"
    LEGPROJ = "Legace PROJ"
    # add more as needed

@dataclass
class CodeFile:
    """A single source‑code file."""
    file_name: str #= field(metadata={"description": "Just the file name, e.g. Program.cs"})
    full_path: str #= field(metadata={"description": "Absolute path including the file name"})
    language: Language #= field(metadata={"description": "Language identifier, e.g. 'CS'"})


@dataclass
class Project:
    """A project that contains many code files."""
    full_path: str # = field(metadata={"description": "Root folder of the project"})
    project_folder_path: str
    name: str # = # field(metadata={"description": "Project name"})
    code_files: List[CodeFile] # = field(
     #   default_factory=list,
     #   metadata={"description": "All source files belonging to the project"},
    #)
    child_projects: List[Project]
    
@dataclass
class Solution:
    """Top‑level solution that groups projects."""
    full_path: str # = fields.Str(metadata={"description": "Root folder of the solution"})
    solution_name: str  # = fields.Str(metadata={"description": "Solution name (e.g. MyApp.sln)"})
    projects: List[Project] # = fields.List[Project](
   #     metadata={"description": "Projects contained in the solution"},
   # )

@dataclass
class SolutionSet:
    """ Top‑level set of solutions based on given start path. """
    start_path: str #= fields.Str(metadata={"description": "Start folder of the solution search"})
    solutions: List[Solution] # = fields.List[Solution](
       # metadata={"description": "Solutions discovered during search of the start_path "},
   # )
# -------------------------------------------------------------------------
# Automatically generate Marshmallow schemas from the dataclasses.
# The generated classes are named <DataclassName>Schema.
SolutionSchema = marshmallow_dataclass.class_schema(Solution)
ProjectSchema = marshmallow_dataclass.class_schema(Project)
CodeFileSchema = marshmallow_dataclass.class_schema(CodeFile)
SolutionSetSchema = marshmallow_dataclass.class_schema(SolutionSet)
# -------------------------------------------------------------------------
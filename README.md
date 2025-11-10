## enumerate-projfiles-from-slns
 

# 📂 Project Discovery Tool [WIP]
A pure‑Python utility that recursively scans a folder for Visual Studio .sln files, parses each solution and its referenced .csproj / .vbproj projects, and builds a rich data model of the whole code‑base.

```

Why?
• Quickly get an inventory of every .NET project in a repo.
• Extract absolute paths of all source files (C#, VB, F# …).
• Export the hierarchy to JSON (or use the native Python objects).
• No external .NET tooling required – works on Linux, macOS, Windows.

```



 Very direct/to-the-point method of enumerating SLN files in order to find CSPROJ files. 

```mermaid

 .SLN    //enumerate SLN files
   │
   └──.CSPROJ / .VBPROJ   //enumerate CSPROJs in SLNs
              │
              └─.cs / .vb     //for each PROJ, enum code files

```

Table of Contents
* <a href="#features">Features</a>
* <a href="#prerequisites">Prerequisites</a>
* Installation
* <a href="#data-model">Data model (dataclasses) </a>
* Command‑line usage
* Programmatic API
* JSON serialisation
* Examples
* Limitations & Gotchas
* <a href="#contributing">Contributing</a>
* License


<br>
<a name="#features"></a>Features 
==================================================================================================== 
<br>|✅	|  Description                                                                            <br>
| 📁 |  Recursive discovery – finds every *.sln under a given start folder. <br>	
| 🗂 |  Solution → Projects → Code files – builds a full hierarchy (SolutionSet → Solution → Project → CodeFile). <br>	
| 🧩 |  Nested project support – child projects referenced inside a project file are resolved and attached.	<br>
| 🛠 |  Cross‑platform – pure Python, no .NET SDK required.	<br>
| 📦 |  Marshmallow schemas – auto‑generated (via marshmallow_dataclass) for easy JSON (de)serialisation.	<br>
| 💡 |  CLI & library – use the script as a command‑line tool or import the functions in your own code.	<br>
| 🔍 |  Language detection – each file is tagged with a Language enum (CS, FS, VB, PY, …).	<br>
| 🧹 |  Graceful error handling – unreadable files are reported, but parsing continues.	<br>
 

<br>

<a name="#prerequisites"></a>Prerequisites
======================================================================================================= 
Python 3.9+ (type‑hints & dataclasses are heavily used).
Standard library only except for the optional JSON serialisation (see below).
If you want the ready‑made JSON output, install:

pip install marshmallow==3.20.1 marshmallow-dataclass==8.5.13

The script will still run without these packages – you just won’t get the solution_set_to_json() helper.

<br>

<a name="#data-model"></a>Data model (dataclasses)
=====================================================================================================
**All core structures live in model.py and are plain @dataclass objects:
=====================================================================================================
|  Class	        | Description                              
| :----------------:|:-------------------------------------------------------------------------------:
| Language (Enum)   | Programming‑language identifier (CS, FS, VB, PY, …).   
| CodeFile	        | file_name, full_path, language.
| Project	        | full_path (project root), name, code_files (list of CodeFile), child_projects (nested Projects).
| Solution	        | full_path (solution folder), solution_name (MyApp.sln), projects (list of Project).
| SolutionSet	    | Top‑level container – start_path and solutions (list of Solution).

#### *Marshmallow schemas are automatically generated:*

SolutionSchema = marshmallow_dataclass.class_schema(Solution)
ProjectSchema  = marshmallow_dataclass.class_schema(Project)
CodeFileSchema = marshmallow_dataclass.class_schema(CodeFile)
SolutionSetSchema = marshmallow_dataclass.class_schema(SolutionSet)

These schemas let you dump/load the objects to/from JSON with full validation.

<br><br>

# <a name="#contributing"></a>Contributing
* Fork the repo.
* Create a feature/bug branch (git checkout -b feat/xyz).
* Run tests (if you add any) with pytest.
* Submit a Pull Request with a clear description of the change.


# Renpy-Compiler

**Status:** Ongoing (Work in progress)

Renpy-Compiler is an ongoing project that implements a complete **AST construction and semantic analysis** pipeline for a Ren’Py-inspired scripting language (RnP). The compiler parses `.rpy`-style scripts and generates an abstract syntax tree (AST) that can be used by a runtime engine to execute and render visual novels.

---

## Features

### 1. Tokenizer
- Processes Ren’Py-style scripts and splits the code into meaningful tokens.
- Identifies keywords, variables, strings, numbers, and built-in constructs.
- Prepares the source code for parsing.

### 2. Parser
- Consumes the tokens to build syntactic structures.
- Recognizes statements like `define`, `image`, `scene`, `show`, `play`, `stop`, `label`, `return`, and more.
- Handles top-level statements and separates label bodies for sequential execution.

### 3. AST Building (in the `parser` module)
- Constructs a fully structured Abstract Syntax Tree (AST) representing the script.
- Supports nodes such as `DefineNode`, `ImageNode`, `SceneNode`, `ShowNode`, `PlayNode`, `StringNode`, `LabelNode`, `ReturnNode`, `StopNode`, etc.
- Tracks variable declarations, symbol usage, and context for semantic analysis.

---

## Project Status

This project is **ongoing**. Current implementation includes:

- Full AST construction from Ren’Py-style files.
- Semantic checks for variable usage and statement validity.
- Support for basic statement execution flow within labels.

Future plans:

- Creation of the 'runtime engine' which will execute and create a visual novel video game from the complete AST object.

---

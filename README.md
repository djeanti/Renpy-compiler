# Renpy-Compiler

**Status:** Ongoing (Work in progress)

Renpy-Compiler is an ongoing project that implements a complete **AST construction and semantic analysis** pipeline for a Ren’Py-inspired scripting language (RnP). The compiler parses `.rpy`-style scripts and generates an abstract syntax tree (AST) that can be used by a runtime engine to execute and render visual novels.

---

## Features

- **AST Construction**
  - Parses Ren’Py-inspired scripts and builds a fully structured AST.
  - Supports nodes such as `DefineNode`, `ImageNode`, `SceneNode`, `ShowNode`, `PlayNode`, `StringNode`, `LabelNode`, `ReturnNode`, `StopNode`, and more.
  
- **Semantic Analysis**
  - Tracks variable declarations and usage.
  - Validates proper usage of images, colors, transforms, layers, transitions, and audio.
  - Ensures statements like `with` follow correct preceding statements (`scene`, `show`, `hide`, `play`).

- **Label & Context Handling**
  - Separates top-level statements and label bodies.
  - Maintains execution context for both global symbols and label-local symbols.
  - Supports runtime-ready AST generation for sequential execution.

---

## Project Status

This project is **ongoing**. Current implementation includes:

- Full AST construction from Ren’Py-style files.
- Semantic checks for variable usage and statement validity.
- Support for basic statement execution flow within labels.

Future plans:

- Complete runtime integration for executing visual novel scripts.
- Advanced features such as conditional branching, loops, and more complex audio/visual effects.

---

## Usage

The project is not yet fully ready for end-user execution, but the AST construction can be demonstrated with example Ren’Py scripts. The code is structured to allow easy extension towards a full runtime engine.

---

## License

This project is open-source and available under the MIT License.

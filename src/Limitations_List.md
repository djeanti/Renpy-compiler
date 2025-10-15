## Current Limitations

- **No Runtime Execution**  
  Only the AST of the renpy file (script) is built; The script cannot yet be executed or rendered as a visual novel.

- **Semantic Analysis Limited to AST Context**  
  The syntax is verified in the Parser module, but semantic analysis for runtime execution has not been implemented yet.
  e.g. Currently we do not raise an error if a variable is used prior to being declared.

- **No Conditional Logic or User Input**  
  Branching, choices, loops, and flags are not supported. The rendered visual novel will only function as a linear storytelling game; the user will not be able to follow different story paths or routes. 

- **Minimal Built-in Feature Support**  
  Only basic layers, transitions, and transforms are recognized.  
  Advanced features of the renpy language (ex: custom transforms) are not supported. 

- **Work in Progress**  
  The compiler is ongoing.  
  Future work includes implementing the runtime engine for script execution.

from Parser import *
from visualnovel import VisualNovelGenerator
from Tokens import __BREAK__TOKEN__
##############################################################################
####### TO MODIFY BY THE USER OF THIS PROJECT (for testing purpose): #########

# Global variables:
TEST_AST_TREE = False # Change to True (and put the other global variables to False) to test MasterParser.parse_renpy_file
TEST_PARSER_METHOD = False # Change to True (and put the other global variables to False) to test any parser_method except MasterParser.parse_label and MasterParser.parse_renpy_file
TEST_VISUAL_NOVEL = True # Change to True (and put the other global variables to False) to generate a visual novel from the renpy script. 

OUTPUT_TEXT_FILE_MASTER_AST = '../output_files_interpreter/master_output_ast.txt' # (Do not change) File where the test converned by 'TEST_MASTER_OR_LABEL = True' will output its result.
OUTPUT_TEXT_FILE_PARSER_AST = '../output_files_interpreter/parser_output_ast.txt' # (Do not change) File where the test converned by 'TEST_PARSER_METHOD = True' will output its result.
FOLDER_VN_DEBUG = '../output_files_VN/' # (Do not change) Folder used by VisualNovelGenerator to outputs debugging files

parse_method = MasterParser.parse_play # ---------> (Used only by 'TEST_PARSER_METHOD') Change the parse method HERE (replace 'parse_define' by any other parser_method)

##############################################################################

# Class used to perfom test on current program

class DEBUG:
    """
    Class made for debugging purpose only during this project.
    """

    def __init__(self, filename):
        self.filename = filename
        self.file_lines = []
        self.file = ""
        self.current_idx = 0
        
    def load_file(self):
        """
        Description
        ---------
        Loads the file, keeping only non-empty, non-comment lines.
        Ignores lines that are empty or start with "# TEST" and appends valid lines to `self.file_lines`.
        Example:
            If the file contains "Line 1" and "# TEST comment", `self.file_lines` will include "Line 1".

        Arguments
        ---------
        None

        Returns
        -------
        None
        """
        with open(self.filename, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("# TEST"):
                    self.file_lines.append(stripped)
        # print("self.file_lines:", self.file_lines)

    def load_file_classic(self):
        """
        Description
        -----------
        Loads the entire file into `self.file`.
        Reads the file specified by `self.filename` and stores its content as a string in `self.file`.

        Arguments
        ---------
        None

        Returns
        -------
        None
        """
        with open(self.filename, 'r') as file:
            self.file = file.read()
     
    def test_parse(self, MAX_TEST_NB, debug=False): 
        """
        Description
        ---------
        Tests the parsing of lines from a file, generating an AST for each line.
        Reads lines from the file up to `MAX_TEST_NB`, tokenizes them, parses the tokens, and stores 
        the resulting Abstract Syntax Tree (AST) in `ast_tree`. Optionally prints tokens if `debug` is True.
        The results are saved to a file specified by `OUTPUT_TEXT_FILE_PARSER_AST`.

        Arguments
        ---------
        MAX_TEST_NB: The maximum number of lines to process.
        debug: If True, prints the list of tokens for each line.

        Returns
        -------
        int: 0 upon successful completion.
        """
        # Works well with any .rpy file inside Tests-Parser except label.rpy and renpy_script_master.rpy
        global parse_method

        self.load_file()
        idx = 1
        list_tokens = []
        if MAX_TEST_NB > len(self.file_lines):
            MAX_TEST_NB = len(self.file_lines)
        if MAX_TEST_NB < 0:
            return
        
        ast_tree = []
        for line in self.file_lines[0:MAX_TEST_NB]:
            tk = RPTokenizer(line)
            token = tk.tokenizer_from_file()
            while token != FILE_EOF:
                list_tokens.append(token)
                token = tk.tokenizer_from_file()
            
            if debug:
                self.print_list_token(list_tokens)
            parser = MasterParser(list_tokens)
            ast_tree.append(parse_method(parser))
        
            # print(f"Test #{idx}: {ast_tree}\n")
            idx += 1
            list_tokens = []

        with open(OUTPUT_TEXT_FILE_PARSER_AST, "w", encoding="utf-8") as f:
            for idx, node in enumerate(ast_tree, start=1):
                f.write(f"Test #{idx}: {repr(node)}\n\n")

        return 0
    
    def print_list_token(self, list_token):
        """
        Description
        -----------
        Prints the tokens from `list_token`, showing their type and value.
        For each token, prints the line number and token type. If the token is a keyword, user token, 
        or built-in, its value is also printed. Newline tokens are handled separately.

        Arguments
        ---------
        list_token: A list of tokens to be printed.

        Returns
        -------
        None
        """
        if not list_token:
            return

        ligne_idx = 1
        printed_line_num = False
        for e in list_token:
            if 'NEWLINE' in e:
                if not printed_line_num:
                    print(f"#{ligne_idx} || NEWLINE")
                else:
                    print("NEWLINE")
                ligne_idx += 1
                printed_line_num = False
                continue

            e_type, e_val = __BREAK__TOKEN__(e)

            if not printed_line_num:
                print(f"#{ligne_idx} || ", end="")
                printed_line_num = True

            if e_type in ['KEYWORD', 'USER', 'BUILTIN']:
                print(f"{e_type}({e_val}) -> ", end="")
            else:
                print(f"{e_type} -> ", end="")
    
    def test_master(self, debug=False):
        """
        Description
        -----------
        Tokenizes the entire file and parses it into an Abstract Syntax Tree (AST).
        Loads the file, tokenizes it using `RPTokenizer`, and parses the tokens with `MasterParser`. 
        Optionally prints tokens if `debug` is True. The resulting AST is saved to a file.

        Arguments
        ---------
        debug: If True, prints the list of tokens.

        Returns
        -------
        int: 0 upon successful completion.
        """
        self.load_file_classic()
        list_tokens = []
        tk = RPTokenizer(self.file)
        token = tk.tokenizer_from_file()
        while token != FILE_EOF:
            list_tokens.append(token)
            token = tk.tokenizer_from_file()
        
        if debug:
            self.print_list_token(list_tokens)
        parser = MasterParser(list_tokens)
        ast_tree = parser.parse_renpy_file()
        
        # Write the AST object inside a file:
        with open(OUTPUT_TEXT_FILE_MASTER_AST, "w", encoding="utf-8") as f:
            f.write(str(ast_tree))

        return 0

    def test_visual_novel(self, debug_=False):
        """
        Description
        -----------
        Generates and outputs a visual novel based on the file.
        Initializes the `VisualNovelGenerator` with the file and optional debug settings, 
        then calls `output_result` to generate and output the visual novel.

        Arguments
        ---------
        debug_: If True, enables debugging and saves debug information to a specified path.

        Returns
        -------
        None
        """
        VN = VisualNovelGenerator(self.filename, debug=debug_, debug_PATH=FOLDER_VN_DEBUG)
        VN.output_result()

# Exemples of PATHS that can be used for TEST_MASTER_OR_LABEL:
PATH_RENPY_SCRIPT1 = "Tests-Parser/renpy_script_master.rpy" # It's possible to choose any other complete renpy script such as the ones located in Tests-RenPy-Scripts folder
PATH_RENPY_SCRIPT2 = "Tests-RenPy-Scripts/Execution-scripts/script1.rpy"

# Exemples of PATHS that can be used for TEST_PARSER_METHOD:
PATH_PARSER_METHOD1 = "Tests-Parser/play.rpy" # It's possible to choose any other complete script located in Tests-Parser folder (except PATH_RENPY_SCRIPT1 and scripts with 'labels' in their names)
PATH_PARSER_METHOD2 = "Tests-Parser/define.rpy" 
PATH_PARSER_METHOD3 = "Tests-Parser/scene.rpy" 
PATH_PARSER_METHOD4 = "Tests-Parser/user.rpy" 
PATH_PARSER_METHOD5 = "Tests-Parser/string.rpy" 

# Exemples of PATH that can be used for TEST_VISUAL_NOVEL:
PATH_RENPY_SCRIPT2 = "Tests-RenPy-Scripts/Execution-scripts/script1.rpy" # Only this one currently 

tester = DEBUG(PATH_RENPY_SCRIPT2) # -> change the argument with the corresponding path 
idx = 0

try:
    if TEST_AST_TREE:
        idx = tester.test_master(debug=False)
    elif TEST_PARSER_METHOD:
        idx = tester.test_parse(5000, debug=False) # We support a maximum of 5000 tokens -> Can be raised if script contains more than 5000 tokens.
    elif TEST_VISUAL_NOVEL:
        idx = tester.test_visual_novel(debug_=True)

    if idx == 0:
        print('No error raised for all the tests')
    else:
        print(f'failed at Test #{idx}')
except Exception as e:
    raise e  

# Note: When using TEST_PARSER_METHOD, please make sure that the Ren'Py file path (RENPY_FILE_LOCATION) and the associated parser method (parse_method) match correctly
# To be further implemented: 
#   hide instruction in the generation of the VN
from Parser import *

##############################################################################
####### TO MODIFY BY THE USER OF THIS PROJECT (for testing purpose): #########

PATH = "Tests-Parser/" # (Do not change) Folder where all renpy file meant for testing are stored.
RENPY_FILE_LOCATION = PATH + "define.rpy" # ---------> Change 'define.rpy' by the renpy file to test (And please also update parse-method below)
parse_method = MasterParser.parse_define # ---------> Change the parse method HERE (replace 'parse_define' by any other parser_method)

TEST_MASTER_OR_LABEL = True # Change to True to test MasterParser.parse_label or MasterParser.parse_renpy_file
TEST_PARSER_METHOD = True # Change to True to test any parser_method except MasterParser.parse_label and MasterParser.parse_renpy_file

OUTPUT_TEXT_FILE_MASTER_AST = 'master_output_ast.txt' # (Do not change) File where the test converned by 'TEST_MASTER_OR_LABEL = True' will output its result.
OUTPUT_TEXT_FILE_PARSER_AST = 'parser_output_ast.txt' # (Do not change) File where the test converned by 'TEST_PARSER_METHOD = True' will output its result.

##############################################################################

 # Utility functions (do not modify):
def TOKEN__TYPE__DEBUG(token_str):
    if token_str == '':
        return False
    if token_str == FILE_EOF:
        return False
    token_type = token_str.split('type')[1].split(', value')[0]
    token_type = token_type[2:len(token_type)-1]
    return token_type

def __GET__VALUE__TOKEN__(token_str):
    if token_str == FILE_EOF:
        return token_str
    value = token_str.split('value')[1]
    value = value[2:len(value)-2]
    return value

def __BREAK__TOKEN__(token_str):
    if token_str == FILE_EOF or (not isinstance(token_str, str)) or (not token_str.startswith('Token(type="')) or ('value="' not in token_str):
        return FILE_EOF, FILE_EOF  # Format invalide → on renvoie un tuple EOF pour signaler une fin anormale (car cette fonction doit tj renvoyer un tuple)
    token_type = token_str.split('type')[1].split(', value')[0]
    token_type = token_type[2:len(token_type)-1]
    value = token_str.split('value')[1]
    value = value[2:len(value)-2]
    return token_type, value

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
        """Load the file by splitting it at each # TEST line."""
        with open(self.filename, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("# TEST"):
                    self.file_lines.append(stripped)
        # print("self.file_lines:", self.file_lines)

    def load_file_classic(self):
        with open(self.filename, 'r') as file:
            self.file = file.read()
     
    def print_list_token(self, list_token):
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

    def test_parse(self, MAX_TEST_NB, debug=False): # Works well with any .rpy file except label.rpy and renpy_script_master.rpy
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
                print(list_tokens)
            parser = MasterParser(list_tokens)
            ast_tree.append(parse_method(parser))
        
            # print(f"Test #{idx}: {ast_tree}\n")
            idx += 1
            list_tokens = []

        with open(OUTPUT_TEXT_FILE_PARSER_AST, "w", encoding="utf-8") as f:
            for idx, node in enumerate(ast_tree, start=1):
                f.write(f"Test #{idx}: {repr(node)}\n\n")

        return 0
   
    def test_master(self, debug=True): # Works only with label.rpy and renpy_script_master.rpy
        global parse_method

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
        ast_tree = parse_method(parser) 
        
        # Write the AST object inside a file:
        with open(OUTPUT_TEXT_FILE_MASTER_AST, "w", encoding="utf-8") as f:
            f.write(str(ast_tree))

        return 0


tester = DEBUG(RENPY_FILE_LOCATION)
idx = 0

try:
    if TEST_MASTER_OR_LABEL:
        idx = tester.test_master(debug=False)
    elif TEST_PARSER_METHOD:
        idx = tester.test_parse(1000, debug=False)

    if idx == 0:
        print('No error raised for all the tests')
    else:
        print(f'failed at Test #{idx}')
except Exception as e:
    # raise e  # ---------> Uncomment this line to re-raise the exception if you want the full traceback fo the error. (Only uncomment if RENPY_FILE_LOCATION and parse_method match correctly)
    print("Error: please make sure the Ren'Py file path (RENPY_FILE_LOCATION) and the associated parser method (parse_method) match correctly.")

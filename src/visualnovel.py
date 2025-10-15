# MODULE that creates a visual novel game from a MasterNode AST (Ongoing).

from Parser import MasterParser
from Tokens import RPTokenizer, __BREAK__TOKEN__
from defs import FILE_EOF
from AST import *
from Error import *

class VisualNovelGenerator():
    def __init__(self, renpy_file, debug=False):
        # Init the game:
        self.debug = debug
        self.file = None
        self.list_tokens = []
        self.tk = None # Tokenizer
        self.parser = None # Parser
        self.ast_tree = None 
        self.symbols_table = {} # Dictionnary initialise during Initialisation Phase (contains all top level ASTnode)
        self.labels_table = {} # Dictionnary initialise during Initialisation Phase (contains all label nodes), key = label name

        # Load all ressources:
        self.step1_loadfile(renpy_file)
        self.step2_tokenizer()
        self.step3_parser()
        self.step4_creategame()
    
    
    def print_list_token(self):
        if not self.list_token:
            return

        ligne_idx = 1
        printed_line_num = False

        for e in self.list_token:
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

    def step1_loadfile(self, renpy_file):
        with open(renpy_file, 'r') as file:
            self.file = file.read()

    def step2_tokenizer(self):
        self.tk = RPTokenizer(self.file)
        token = self.tk.tokenizer_from_file()
        while token != FILE_EOF:
            self.list_tokens.append(token)
            token = self.tk.tokenizer_from_file()

        if self.debug:
            self.print_list_token()

    def step3_parser(self):
        self.parser = MasterParser(self.list_tokens)
        self.ast_tree = self.parser.parse_renpy_file()

    def update_nested_table_image_node(self, table:dict, ast_node: ImageNode, img_path):
        key = table
        for tag in ast_node.image_expression:
            if tag == ast_node.image_expression[-1]:
                if tag not in key: 
                    key[tag] = {}
                    key[tag]['image_path'] = img_path
                else: # tag already exist, meaning we don't want to delete the current value of key[value]
                    key[tag]['image_path'] = img_path # We basically add another key to the dictionnary 'key[tag]'
            else:
                if tag not in key: # We keep increasing the depth of our nested dictionnary
                    key[tag] = {} # Necessary or the next line won't work
                    key = key[tag] # The new key is updated
                else: # We do not want to override an existing key
                    key = key[tag]

    def update_nested_table(self, table:dict, ast_node, args: dict): 
        key = table
        for tag in ast_node.image_expression:
            if tag == ast_node.image_expression[-1]:
                if tag not in key: 
                    key[tag] = {}
                    key[tag]['args'] = args
                else: # tag already exist, meaning we don't want to delete the current value of key[value]
                    key[tag]['args'] = args
            else:
                if tag not in key: 
                    key[tag] = {}
                    key = key[tag]
                else: # We do not want to override an existing key
                    key = key[tag]

    def step4_label_body_initialize(self, label_body):
        """
        'return': self.parse_return,
        'jump': self.parse_jump,
        'USER': self.parse_user
        """
        for ast_node in label_body:
            if isinstance(ast_node, SceneNode): #Ex: scene eileen happy blushing at center with transition 
                if 'scene' not in self.symbols_table:
                    label_body['scene'] = {} # Cannot be None by default or we will have an error
                    label_body['scene']['masternode'] = [] # Useful only for 'with' statement alone in label body

                args = { 
                    'transform': getattr(ast_node, "transform", None),
                    'layer': getattr(ast_node, "layer", None),
                    'transition': getattr(ast_node, "transition", None)
                }
                self.update_nested_table(label_body['scene'], ast_node, args)
                label_body['scene']['masternode'].append(ast_node) 

            elif isinstance(ast_node, ShowNode):  
                if 'show' not in self.symbols_table:
                    label_body['show'] = {} # Cannot be None by default or we will have an error
                    label_body['show']['masternode'] = [] # Useful only for 'with' statement alone in label body
                args = { 
                    'transform': getattr(ast_node, "transform", None),
                    'layer': getattr(ast_node, "layer", None),
                    'transition': getattr(ast_node, "transition", None)
                }
                self.update_nested_table(label_body['show'], ast_node, args)
                label_body['show']['masternode'].append(ast_node) 

            elif isinstance(ast_node, HideNode): #Ex: scene eileen happy blushing at center with transition 
                if 'hide' not in self.symbols_table:
                    label_body['hide'] = {} # Cannot be None by default or we will have an error
                    label_body['hide']['masternode'] = [] # Useful only for 'with' statement alone in label body
                args = { 
                    'layer': getattr(ast_node, "layer", None),
                    'transition': getattr(ast_node, "transition", None)
                }
                self.update_nested_table(label_body['hide'], ast_node, args)
                label_body['show']['masternode'].append(ast_node)

            elif isinstance(ast_node, PlayNode): #Ex: scene eileen happy blushing at center with transition 
                if 'play' not in self.symbols_table:
                    label_body['play'] = [] # Cannot be None by default or we will have an error
                
                label_body['play'].append(ast_node) 

            elif isinstance(ast_node, StopNode): #Ex: scene eileen happy blushing at center with transition 
                if 'stop' not in self.symbols_table:
                    label_body['stop'] = [] # Cannot be None by default or we will have an error

                label_body['stop'].append(ast_node)

            elif isinstance(ast_node, TransitionNode): #Ex: scene eileen happy blushing at center with transition 
                # Must be preceed by 'scene', 'show', 'hide' or 'play'
                last_key_added = list(label_body.keys())[-1]
                if last_key_added not in ['scene', 'show', 'hide', 'play']:
                    raise DetailedError('Runtime error. with statement must be preceed by either scene, show, hide or play statement')

                args = { 
                    'transition': getattr(ast_node, "transition", None)
                }
                self.update_nested_table(label_body[last_key_added], label_body[last_key_added]['masternode'][-1], args)

            elif isinstance(ast_node, StringNode):
                if 'string' not in self.symbols_table:
                    label_body['string'] = [] # Cannot be None by default or we will have an error

                label_body['string'].append(ast_node)

            elif isinstance(ast_node, UserNode):
                if 'user' not in self.symbols_table:
                    self.symbols_table['user'] = {} # Cannot be None by default or we will have an error

                #Attention: todo: usernode est utilisé seul ou par un autre statement dnas un label body ???
                self.symbols_table['user'][ast_node.id] = ast_node.value # Define statement is now considered 'initialised'

    def step4_initialize_master_node(self):
        # Goal: Store all statements in a symbol node and check if a statement (whether inside a label or outside) is used before being initialised
        for ast_node in self.ast_tree:
            if isinstance(ast_node, DefineNode): # We are declaring a variable, no need to check if it's used before initialised 
                if 'define' not in self.symbols_table:
                    self.symbols_table['define'] = {} # Cannot be None by default or we will have an error

                self.symbols_table['define'][ast_node.id] = ast_node.value # Define statement is now considered 'initialised'

            elif isinstance(ast_node, ImageNode): # Ex: ast_node.image_expression = ['eileen', 'happy', 'blushing']
                if 'image' not in self.symbols_table:
                    self.symbols_table['image'] = {} # Cannot be None by default or we will have an error

                img_path = ast_node.get_value() 
                self.update_nested_table_image_node(self.symbols_table['image'], ast_node, img_path) # image statement is now considered 'initialised'

            elif isinstance(ast_node, SceneNode): #Ex: scene eileen happy blushing at center with transition 
                if 'scene' not in self.symbols_table:
                    self.symbols_table['scene'] = {} # Cannot be None by default or we will have an error

                args = { 
                    'transform': getattr(ast_node, "transform", None),
                    'layer': getattr(ast_node, "layer", None),
                    'transition': getattr(ast_node, "transition", None)
                }
                self.update_nested_table(self.symbols_table['scene'], ast_node, args)

            elif isinstance(ast_node, ShowNode):  
                if 'show' not in self.symbols_table:
                    self.symbols_table['show'] = {} # Cannot be None by default or we will have an error
                
                args = { 
                    'transform': getattr(ast_node, "transform", None),
                    'layer': getattr(ast_node, "layer", None),
                    'transition': getattr(ast_node, "transition", None)
                }
                self.update_nested_table(self.symbols_table['show'], ast_node, args)

            elif isinstance(ast_node, HideNode): #Ex: scene eileen happy blushing at center with transition 
                if 'hide' not in self.symbols_table:
                    self.symbols_table['hide'] = {} # Cannot be None by default or we will have an error

                args = { 
                    'layer': getattr(ast_node, "layer", None),
                    'transition': getattr(ast_node, "transition", None)
                }
                self.update_nested_table(self.symbols_table['hide'], ast_node, args)

            elif isinstance(ast_node, PlayNode): #Ex: scene eileen happy blushing at center with transition 
                if 'play' not in self.symbols_table:
                    self.symbols_table['play'] = [] # Cannot be None by default or we will have an error
                
                self.symbols_table['play'].append(ast_node) 

            elif isinstance(ast_node, StopNode): #Ex: scene eileen happy blushing at center with transition 
                if 'stop' not in self.symbols_table:
                    self.symbols_table['stop'] = [] # Cannot be None by default or we will have an error

                self.symbols_table['stop'].append(ast_node)

            elif isinstance(ast_node, LabelNode): #Ex: scene eileen happy blushing at center with transition 
                if 'label' not in self.labels_table:
                    self.labels_table['label'] = {} # Cannot be None by default or we will have an error

                self.labels_table[ast_node.label_name] = {}
                # We need to go through label body to see if anything requires initialisation
                self.step4_label_body_initialize(self.labels_table[ast_node.label_name])


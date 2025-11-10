from Tokens import *
from Error import DetailedError
from defs import *
import re
from AST import *

"""
This module defines all classes and logic related to parsing Ren'Py-like script files.

Parsing is the process of analyzing the script's syntax to ensure it follows
the language rules and converting it into an Abstract Syntax Tree (AST).
The AST is a structured representation of the script that can be later
interpreted or compiled by the engine.

In this project, the parser handles:
- Token validation and syntax enforcement
- Construction of AST nodes (LabelNode, SceneNode, ShowNode, etc.)
- Support for Ren'Py directives such as 'scene', 'show', 'hide', 'play', 'with', etc... (See AST.py for all the ASTnode that are handled)

Each node in the AST corresponds to a syntactic element of the Ren'Py language.
"""

"""
Parsing class hierarchy for Ren'Py files.

- TOOL: methods in RPParser_Test (general utilities)
- BASIC_PARSER: methods in SimpleParser (parsing without dispatch)
- DISPATCH_PARSER: methods in DispatchParser subclasses (parsing via dispatch table)
"""

class RPParser():
    """
    Base class providing TOOL methods for all parser classes.

    TOOL methods are general utilities used by every parser
    methods defined in class that inherits this one.
    """
     
    def __init__(self, list_tokens):
        self.idx = 0 # To browse through all the tokens
        self.list_tokens = list_tokens # Contains the list of tokens (obtained from Tokens module)
        self.EOF = FILE_EOF # Used to indicate when the renpy file is ending.

    def eat_skip_until(self, expected_type, return_type_found = False): # TOOL
        """
        Description
        -----------
        Advance through tokens until `expected_type` is found.

        Arguments
        ---------
        expected_type : str
            The type of token to look for.
        return_type_found [optional] : bool
            If True, return the token type found.

        Returns
        -------
        bool or str
            If return_type_found is False: True if `expected_type` found, False otherwise.
            If return_type_found is True: token type found, whether it matches `expected_type` or not.
        """
        if self.idx < len(self.list_tokens):
            type_found = __GET__TYPE__TOKEN__(self.list_tokens[self.idx])
            if type_found != expected_type: # We didn't find the expected token
                self.idx += 1
                if return_type_found:
                    return type_found
                return False
            else:
                if return_type_found:
                    return type_found
                return True # We found the expected token
        else:
            return self.EOF # End of token list
        
    def eat(self, expected_type="", expected_value=""): # TOOL
        """
        Description
        -----------
        Consume the next token, optionally verifying its type and value.

        Arguments
        ---------
        expected_type : str, optional
            Type of the expected token. If empty string (""), type check is skipped.
        expected_value : str, optional
            Expected value of the token. If empty string (""), value check is skipped.

        Returns
        -------
        str
            The consumed token.

        Raises
        ------
        DetailedError
            If the token type or value does not match expectations.
        """

        if self.idx < len(self.list_tokens):
            token = self.list_tokens[self.idx]
            token_type, token_value = __BREAK__TOKEN__(token)
            # if expected_type == "": # We use this special case to skip until we find expected_type in parse_image. 
            #    self.idx += 1
            #    return __GET__TYPE__TOKEN__(token)
            if token_type != expected_type:
                raise DetailedError(f"Wrong token type. Expected {expected_type} and got {token_type} instead")
            if expected_value != "" and token_value != expected_value: # expected_token_value!= "" is for user defined variable: We don't want to raise an error.
                raise DetailedError(f"Wrong value used for the token: {token_type}. Expected value was {expected_value} instead of {token_value}")
            self.idx += 1
            return token
        else:
            return self.EOF # End of token list
  
    def token_peek(self, return_type=True): # TOOL
        """
        Description
        -----------
        Look at the next token without advancing the index.

        Arguments
        ---------
        return_type : bool, optional
            If True (default), return the token type.
            If False, return the full token.

        Returns
        -------
        str
            Token type if return_type is True, else the full token string.
        """
        if self.idx < len(self.list_tokens):
            if return_type:
                return __GET__TYPE__TOKEN__(self.list_tokens[self.idx]) 
            return self.list_tokens[self.idx]
        else:
            return self.EOF # End of token list
    
    def vomit(self, expected_type): # TOOL
        """
        Description
        -----------
        Safely move the index backward if the current token does not match expected_type.
        Used to "unconsume" a token.

        Arguments
        ---------
        expected_type : str or list
            A single token type or a list of allowed token types.

        Returns
        -------
        bool
            True if current token matches expected_type, False if index was decremented.

        Raises
        ------
        DetailedError
            If argument type is invalid or index is out of range.
        """

        if self.idx >= 0:
            typ = __GET__TYPE__TOKEN__(self.list_tokens[self.idx])
            if isinstance(expected_type, str):
                if typ != expected_type:
                    self.idx -= 1
                    return False
                return True
            elif isinstance(expected_type, list):
                for token_type in expected_type:
                    if typ == token_type:
                        return True
                self.idx -= 1
                return False
            else:
                raise DetailedError(f'Expected list or string as argument')
        else:
            raise DetailedError(f'Index out of range. Coud not decrement index to find {expected_type}. Last item found: {self.list_tokens[self.idx+1]}')

    def eat_optional(self, expected_type): # TOOL
        """
        Description
        -----------
        Consume the next token if it matches expected_type; otherwise, skip.
        Syntax enforcement: optional, does not raise errors if token missing.

        Arguments
        ---------
        expected_type : str
            The type of token that is optional.

        Returns
        -------
        str or bool
            The consumed token if present, False if token was skipped.
        """
        token_type = self.token_peek() 
        if expected_type == token_type: # The token is optional but the user used it anyway -> We consume
            return self.eat(expected_type)
        else: # We don't consume the next token
            return False

    def skip_spaces(self): # TOOL
        """
        Description
        -----------
        Consume all consecutive SPACE tokens.
        Syntax enforcement: optional, does not raise errors if no SPACE tokens.

        Arguments
        ---------
        None

        Returns
        -------
        None
        """
        while self.token_peek() == 'SPACE':
            self.eat_optional('SPACE') # We expect to see a 'SPACE' but it's okay if there isn't
                




class SimpleParser(RPParser): # All method in this class cannot exist inside syntax_handler of dispatch parser (to verify) because they don't return args
    """
    Provides simple parsing methods for parsing without a dispatch table.
    This class inherits all the TOOLS from RPParser

    These methods implement fundamental parsing logic. They serve as the base for
    more complex parsers.
    """

    def __init__(self, list_tokens):
        super().__init__(list_tokens)

    def parse_string(self):
        """
        Description
        -----------
        Verify that the next token respects string syntax.
        Syntax enforcement: Raises DetailedError if token is not a valid STRING.

        Arguments
        ---------
        None

        Returns
        -------
        StringNode
            AST node representing the string value.
        """
        token = self.eat('STRING')
        token_value = __GET__VALUE__TOKEN__(token)
        return StringNode(token_value) 

    def parse_user(self):
        """
        Description
        -----------
        Parse a user-defined identifier token.
        Syntax: USER <user_variable>
        Syntax enforcement: Raises DetailedError if token is not a valid identifier.

        Arguments
        ---------
        None

        Returns
        -------
        UserNode
            AST node representing the user identifier.
        """
        token = self.eat('USER')
        token_value = __GET__VALUE__TOKEN__(token)
        regex_user = r'^[A-Za-z_][A-Za-z0-9_]*$'
        if not re.match(regex_user, token_value):
            raise DetailedError(f"Wrong syntax used for variable: '{token_value}' is not a valid identifier")
        return UserNode(token_value)
    
    def parse_comment(self):
        """
        Description
        -----------
        Consume a comment line. Consume everything until NEWLINE token or end of token list (self.EOF).
        Syntax enforcement: Optional, does not raise errors for comment content.

        Arguments
        ---------
        None

        Returns
        -------
        None
        """
        self.eat('COMMENT')
        val = self.eat_skip_until('NEWLINE')
        while (val != self.EOF and not val):
            val = self.eat_skip_until('NEWLINE')

    def eof_line(self): # BASIC_PARSER (it cannot be DISPATCH_PARSER because every DISPATCH_PARSER use it)
        """
        Description
        -----------
        Handle the end of a line after reading a statement.
        Syntax enforcement: Raises DetailedError for unexpected tokens.

        Arguments
        ---------
        None

        Returns
        -------
        None
        """
        token_type = self.token_peek()
        self.skip_spaces()

        # HANDLING whether we have a COMMENT token or a NEWLINE token
        token_type = self.token_peek()
        if token_type == 'COMMENT':
            self.parse_comment() 
        elif token_type == 'NEWLINE': 
            return
        elif token_type == self.EOF:
            return
        else:
            print('token = ', self.list_tokens[self.idx])
            raise DetailedError(f"Unexpected token: {token_type}")
        
    def parse_jump(self): # BASIC_PARSER
        """
        Description
        -----------
        Parse a 'jump' statement.
        Syntax: jump <label_name>
        Syntax enforcement: Raises DetailedError if invalid token or syntax.

        Arguments
        ---------
        None

        Returns
        -------
        JumpNode
            AST node representing the jump statement.
        """
        self.eat('KEYWORD', 'jump')
        self.skip_spaces()
        
        # HANDLING USER token
        val = self.parse_user()
        self.skip_spaces()
        
        # HANDLING end of line
        self.eof_line()
        return JumpNode(label_name=val)
        
    def parse_return(self): # BASIC_PARSER
        """
        Description
        -----------
        Parse a 'return' statement.
        Syntax: return [value]
            [argument]: argument is optional
        Syntax enforcement: Raises DetailedError if token sequence invalid.

        Arguments
        ---------
        None

        Returns
        -------
        ReturnNode
            AST node representing the return statement with optional value.
        """

        self.eat('KEYWORD', 'return')
        self.skip_spaces()

        # HANDLING the situation where the syntax is done 
        token = self.token_peek(return_type=False)
        if token == self.EOF or __GET__TYPE__TOKEN__(token) == 'NEWLINE' or __GET__TYPE__TOKEN__(token) == 'COMMENT':
            return ReturnNode(value=None)
        
        # HANDLING USER token
        val = self.parse_user()
        self.skip_spaces()
        
        # HANDLING end of line
        self.eof_line()
        return ReturnNode(value=val)
    
    def parse_stop(self): # BASIC_PARSER
        """
        Description
        -----------
        Parse a 'stop' statement for music or sound.
        Syntax: stop [music|sound] [fadeout [duration]]
            [argument]: argument is optional
            arg1|arg2: either arg1 or arg2 is expected
        Syntax enforcement: Raises DetailedError if syntax or values are invalid.

        Arguments
        ---------
        None

        Returns
        -------
        StopNode
            AST node representing the stop statement, with optional audio type and fadeout duration.
        """
        self.eat('KEYWORD', 'stop')
        self.skip_spaces()
        
        # HANDLING the situation where the syntax is done 
        token = self.token_peek(return_type=False)
        if token == self.EOF or __GET__TYPE__TOKEN__(token) == 'NEWLINE' or __GET__TYPE__TOKEN__(token) == 'COMMENT': 
            self.eof_line()
            return StopNode()
        
        # HANDLING whether we have music or sound KEYWORD token
        audio_val = __GET__VALUE__TOKEN__(token)
        if audio_val == 'music':
            self.eat('KEYWORD', 'music')
            self.skip_spaces()
        elif audio_val == 'sound':
            self.eat('KEYWORD', 'sound')
            self.skip_spaces()
        elif audio_val == 'voice':
            self.eat('KEYWORD', 'voice')
            self.skip_spaces()
        else:
            raise DetailedError(f'Stop syntax error. Expected either music or sound or voice but got {audio_val}')
        
        # HANDLING the situation where the syntax is done 
        token = self.token_peek(return_type=False)
        if token == self.EOF or __GET__TYPE__TOKEN__(token) == 'NEWLINE' or __GET__TYPE__TOKEN__(token) == 'COMMENT': 
            self.eof_line()
            return StopNode(audio_type=audio_val)
        
        # HANDLING if we have a fadeout
        effect_val = __GET__VALUE__TOKEN__(token)
        if effect_val != 'fadeout':
            raise DetailedError(f'Stop syntax error. Expected fadeout but got {effect_val}')
        self.eat('BUILTIN', effect_val)
        self.skip_spaces()

        # HANDLING the situation where the syntax is done 
        token = self.token_peek(return_type=False)
        if token == self.EOF or __GET__TYPE__TOKEN__(token) == 'NEWLINE' or __GET__TYPE__TOKEN__(token) == 'COMMENT': 
            self.eof_line()
            return StopNode(audio_type=audio_val, fadeout=2) # 2 sec is default value of fadeout when user does not precise

        # HANDLING duration of fade effect
        duration_val = __GET__VALUE__TOKEN__(token)
        if not re.fullmatch(r'\d+(\.\d+)?', duration_val):
            raise DetailedError('Stop syntax error. Expected a float number for fadeout effect.')
        self.eat('DOT', duration_val)

        # HANDLING end of line
        self.eof_line()
        return StopNode(audio_type=audio_val, fadeout=duration_val)
    
    def parse_function_call(self): # BASIC_PARSER
        """
        Description
        -----------
        Parse a function call expression.
        Syntax: <FUNCTION_NAME>(<ARG1> [<ARG2>, ..., <ARGN>])
            [argument]: argument is optional
        Syntax enforcement: Raises DetailedError if invalid argument type or missing RPAREN.

        Arguments
        ---------
        None

        Returns
        -------
        FunctionCallNode
            AST node representing the function call with arguments and keyword assignments.
        """
        function_token = self.eat('FUNCTION')
        self.eat('LPAREN')
        
        ast_args_list = [] 
        ast_kwargs = []

        # HANDLING all the arguments inside the function (between the parenthesis)
        accepted_types = ['USER', 'STRING', 'COMMA', 'SPACE', 'ASSIGN', 'KEYWORD']
        accepted_values_KEYWORD = ['color', 'image']
        while (self.idx < len(self.list_tokens) and self.token_peek() != 'RPAREN'):
            arg = self.token_peek(return_type=False)
            arg_token_type, arg_token_value = __BREAK__TOKEN__(arg)
            if arg_token_type not in accepted_types:
                raise DetailedError(f"Wrong argument in function call. Expected either {accepted_types} arguments but got {arg_token_type} instead")
            elif arg_token_type == 'KEYWORD' and arg_token_value not in accepted_values_KEYWORD:
                raise DetailedError(f"Wrong argument in function call. Expected {accepted_values_KEYWORD} arguments but got {arg_token_value} instead")
            else: # We are handling an arg or a kwargs
                if arg_token_type == 'USER':
                    ast_args_list.append(self.parse_user())
                elif arg_token_type == 'STRING':
                    ast_args_list.append(self.parse_string())
                elif arg_token_type == 'ASSIGN':
                    ast_kwargs.append(self.parse_assign_local())
                else: # We are not storing this information:
                    self.eat(arg_token_type)
        
        if self.idx >= len(self.list_tokens):
            raise DetailedError(f"Wrong argument in function call. Expected RPAREN but got {self.list_tokens[len(self.list_tokens)-1]} instead.")
        
        # HANDLING end of function syntax
        self.eat('RPAREN')
        self.eof_line()

        return FunctionCallNode(name=__GET__VALUE__TOKEN__(function_token), args=ast_args_list, kwargs=ast_kwargs)
        
    def parse_fadein(self):
        """
        Description
        -----------
        Parse a 'fadein' statement.
        Syntax: fadein <duration>
        Syntax enforcement: Raises DetailedError if duration is missing or invalid.

        Arguments
        ---------
        None

        Returns
        -------
        FadeInNode
            AST node representing the fade-in statement.
        """
        args = {
            'fadein': 2.0, # Default  value if not precised by USER
            'loop': True
        }

        self.eat('BUILTIN', 'fadein')
        self.skip_spaces()

        # HANDLING the situation where the syntax is done 
        token = self.token_peek(return_type=False)
        if token == self.EOF or __GET__TYPE__TOKEN__(token) == 'NEWLINE' or __GET__TYPE__TOKEN__(token) == 'COMMENT':
            return args
        
        # HANDLING fadein or loop
        token_type, token_val = __BREAK__TOKEN__(token)
        if token_val != 'loop' and token_type != 'DOT':
            raise DetailedError(f'Syntax error fadein. Expected either a float or loop but got {token}')
        
        if token_val == 'loop':
            self.eat('KEYWORD', 'loop')
            self.skip_spaces()
            self.eof_line()
            args['loop'] = True
            return args
        
        args['fadein'] = float(token_val)
        self.eat('DOT', token_val)
        self.skip_spaces()
        
        # HANDLING the situation where the syntax is done 
        token = self.token_peek(return_type=False)
        if token == self.EOF or __GET__TYPE__TOKEN__(token) == 'NEWLINE' or __GET__TYPE__TOKEN__(token) == 'COMMENT':
            return args
        
        # HANDLING loop
        self.eat('KEYWORD', 'loop')
        self.skip_spaces()
        self.eof_line()
        args['loop'] = True
        return args

    def parse_play(self): # BASIC_PARSER
        """
        Description
        -----------
        Parse a 'play' statement for music or sound.
        Syntax: play (music|sound|voice) audio_file [fadein [time]] [loop]
            [argument]: optional
            arg1|arg2|arg3: one of these audio types is expected
        Syntax enforcement: Raises DetailedError if syntax or arguments are invalid.

        Tips: 
        music is for background music
        sound is for SFX
        voice is for character's voice

        Arguments
        ---------
        None

        Returns
        -------
        PlayNode
            AST node representing the play statement with optional fade-in duration.
        """
        self.eat('KEYWORD', 'play')
        self.skip_spaces()

        # HANDLING whether we have music, voice or sound
        token_type, token_val = __BREAK__TOKEN__(self.token_peek(return_type=False))
        if token_val not in ['music', 'voice', 'sound']:
            raise DetailedError(f'Syntax error play. Expected music, sound or voice but got {token_val}')
        
        _audio_type = token_val
        self.eat('KEYWORD', token_val)
        self.skip_spaces()

        # HANDLING the audio file (correspond to 'path' in the syntax)
        _audiofile = ""
        token_type, token_val = __BREAK__TOKEN__(self.token_peek(return_type=False))
        if token_type == 'STRING':
            _audiofile = self.parse_string()
        else: # it must be a user token
            _audiofile = self.parse_user()
        self.skip_spaces()
        
        # HANDLING the situation where the syntax is done 
        token = self.token_peek(return_type=False)
        if token == self.EOF or __GET__TYPE__TOKEN__(token) == 'NEWLINE' or __GET__TYPE__TOKEN__(token) == 'COMMENT':
            return PlayNode(audio_type=_audio_type, audio_file=_audiofile)
        
        # HANDLING loop or fadein
        token_type, token_val = __BREAK__TOKEN__(token)

        if token_val != 'fadein' and token_val != 'loop':
            raise DetailedError(f"Syntax error play. Expected fadein or loop but got {token_val}")
        
        if token_val == 'loop':
            self.eat(token_type, token_val)
            self.skip_spaces()
            self.eof_line()
            return PlayNode(audio_type=_audio_type, audio_file=_audiofile, loop=True)
        
        args_fadein = self.parse_fadein()        
        self.eof_line()

        return PlayNode(audio_type=_audio_type, audio_file=_audiofile, fadein=args_fadein.get('fadein', None) ,loop=args_fadein.get('loop', None))

    def parse_assign_global(self): # BASIC_PARSER (not used currently)
        """
        Description
        -----------
        Parse a 'global assignment' statement.
        Syntax: global <identifier> = <expression>
        Syntax enforcement: Raises DetailedError if identifier or expression is missing.

        Arguments
        ---------
        None

        Returns
        -------
        AssignGlobalNode
            AST node representing a global variable assignment.
        """


        LHS = ""
        RHS = ""

        # HANDLING USER token
        # We must decrement self.idx until we see 'USER' or a 'KEYWORD'
        while not self.vomit('USER'): # We accept at most 1 space between USER and ASSIGN tokens
            pass # What if there are two 'USER' tokens before ASSIGN ? The function who calls Assign must verify it it self.

        # Left side of ASSIGN (LHS):
        LHS = self.parse_user()
        
        self.skip_spaces()
        self.eat('ASSIGN')
        self.skip_spaces()
       
        # HANDLING whether we have USER, STRING or FUNCTION token
        token_type = __GET__TYPE__TOKEN__(self.token_peek(return_type=False)) # Important for this to work: we must have ONE instance of the class that contains list_tokens and all the other classes used for the parsing in this project must inherit it
        if token_type == 'USER':
            RHS = self.parse_user()
        elif token_type == 'STRING':
            RHS = self.parse_string()
        elif token_type == 'FUNCTION':
            RHS = self.parse_function_call()
        else:
            raise DetailedError(f"Syntax error. Expected one of the following as an argument: FUNCTION, STRING or USER but got {token_type} instead.")

        return AssignNode(
            LHS = LHS,
            RHS = RHS
        )
    
    def parse_assign_local(self): # assign used inside function call
        """
        Description
        -----------
        Parse a 'local assignment' statement.
        Syntax: <identifier> = <expression>
        Syntax enforcement: Raises DetailedError if identifier or expression is missing.

        Arguments
        ---------
        None

        Returns
        -------
        AssignLocalNode
            AST node representing a local variable assignment.
        """

        LHS = ""
        RHS = ""

        # HANDLING color or image 
        # We must decrement self.idx until we see 'color' or a 'image'
        expected_token = ['KEYWORD', 'USER']
        while not self.vomit(expected_token): # We accept at most 1 space between USER and ASSIGN tokens
            pass # What if there are two 'USER' tokens before ASSIGN ? The function who calls Assign must verify it it self.
        typ, val = __BREAK__TOKEN__(self.token_peek(return_type=False))

        # HANDLING left side of ASSIGN (LHS):
        backup_LHS_value = val
        if typ == 'USER':
            LHS = self.parse_user()
        elif typ == 'KEYWORD':
            if val != 'color' and val != 'image':
                raise DetailedError('Error function assign local. Expected either color or image.')
            self.eat('KEYWORD', val)
            LHS = KeywordNode(val)
        
        self.skip_spaces()
        self.eat('ASSIGN')
        self.skip_spaces()
        
        # HANDLING RHS depending on what we obtained in LHS
        token_type, token_value = __BREAK__TOKEN__(self.token_peek(return_type=False)) # Important for this to work: we must have ONE instance of the class that contains list_tokens and all the other classes used for the parsing in this project must inherit it
        if token_type != 'STRING' and token_type != 'USER':
            raise DetailedError(f"Syntax error. Expected one of the following as an argument: STRING or USER but got {token_type} instead.")

        if backup_LHS_value == 'color':
            RHS = self.parse_string()
        elif backup_LHS_value == 'image':
            if token_type == 'USER':
                RHS = self.parse_user()
            else:
                RHS = self.parse_string()

        
        return AssignNode(
            LHS = LHS,
            RHS = RHS
        )

    def parse_image(self): # BASIC_PARSER
        """
        Description
        -----------
        Parse an 'image' statement defining a scene image.
        Syntax: image <identifier> [as <alias>] = <path>
            [argument]: argument is optional
        Syntax enforcement: Raises DetailedError if syntax, alias, or path are invalid.

        Tips:
        An image identifier contains at least one USER token: the first token is the 
        main name, and any subsequent tokens are optional tags for variants. 

        Arguments
        ---------
        None

        Returns
        -------
        ImageNode
            AST node representing the image declaration with optional alias.
        """
        self.eat('KEYWORD', 'image')
        self.skip_spaces()

        # HANDLING syntax 'image_expression -> n * SPACE'
        img_expression = []
        # Browsing through the line until 'ASSIGN':
        """token_type = self.eat()
        while (token_type != self.EOF and token_type != 'ASSIGN'):
            if token_type == 'USER':
                self.vomit('USER') # We decrement self.idx because we already read it
                img_expression.append(self.parse_user())
            token_type = self.eat()
        self.vomit('ASSIGN') # We need to decrement again self.idx because we used self.eat"""
        
        token_type = self.eat_skip_until('ASSIGN', return_type_found=True)
        while (token_type != self.EOF and token_type != 'ASSIGN'):
            if token_type == 'USER':
                self.vomit('USER') # We already ate 'USER' so we need to decrement self.idx before calling parse_user
                img_expression.append(self.parse_user())
            token_type = self.eat_skip_until('ASSIGN', return_type_found=True)

        if len(img_expression) == 0:
            raise DetailedError('Syntax error for parse_image. Expected at least one USER token.')
        
        self.eat('ASSIGN')
        self.skip_spaces()
        
        # HANDLING string or user node:
        token = self.token_peek(return_type=False)
        token_type = __GET__TYPE__TOKEN__(token)
        
        if token_type != 'USER' and token_type != 'STRING':
            print('type = ', token_type)
            raise DetailedError('Syntax error image. Expected STRING or USER.')
        
        if token_type == 'STRING':
            path = self.parse_string()
            self.skip_spaces()
            self.eof_line()
            return ImageNode(image_expression=img_expression, string_path=path)
        
        path = self.parse_user()
        self.skip_spaces()
        self.eof_line()
        return ImageNode(image_expression=img_expression, user_var=path)
    







class DispatchParser(SimpleParser): # Must inherit SimpleParser later on
    """
    Parser class using dispatch tables to handle more complex parser methods.

    DispatchParser implements a recursive dispatch table system for parsing Ren’Py-style syntax.
    Children dispatch parsers handle a keyword or token type, optionally take an 'args' dictionary, 
    perform parsing, and update 'args' before returning it to the parent parser.
    Parent dispatch parsers handle top-level constructs and return fully-formed AST nodes.
    """

    def __init__(self, list_tokens):
        super().__init__(list_tokens)

    def _get_parser(self, _syntax_handler: dict): 
        """
        Description
        -----------
        Retrieves the appropriate parser method from a dispatch table based on the next token in the input stream.
        Looks for a match using either the token type or the token value. Raises a DetailedError if no match is found.

        Arguments
        ---------
        _syntax_handler: dict
            A dictionary mapping token types or values to corresponding parser methods.

        Returns
        -------
        callable
            The parser method corresponding to the next token.
        """
        parse_method = ""
        dispatch_idx = [key for key in _syntax_handler]
        token_peek = self.token_peek(return_type=False)
        key_type, key_value = __BREAK__TOKEN__(token_peek)
        if key_type in dispatch_idx:
            parse_method = _syntax_handler[key_type]
        elif key_value in dispatch_idx:
            parse_method = _syntax_handler[key_value]
        else:
            raise DetailedError(f"Syntax error. Expected one of the following as an argument: {dispatch_idx} but got {token_peek} instead.")
        return parse_method

    def update_args(self, syntax_handler, args, key=""): 
        """
        Description
        -----------
        Updates the `args` dictionary by invoking the parser method retrieved from `syntax_handler`.  
        The method distinguishes between two types of parser methods:
        - If the parser method is bound to `SimpleParser`, it is called without arguments and its result is stored in `args` under the given key.
        - If the parser method is a `DispatchParser`, it is called with `args` and expected to return an updated dictionary.
        - Raises a `DetailedError` if the parser method is neither type.

        Arguments
        ---------
        syntax_handler: dict
            Dispatch table mapping token types or values to parser methods.

        args: dict
            The current dictionary of arguments to update.

        key: str, optional
            The key under which to store the result when calling a `SimpleParser` method. Default is an empty string.

        Returns
        -------
        dict
            The updated `args` dictionary.
        """
        parser_method = self._get_parser(syntax_handler)

        # HANDLE SimpleParser
        if hasattr(parser_method, "__self__") and isinstance(parser_method.__self__, SimpleParser):
            args[key] = parser_method()
            return args

        # HANDLE DispatchParser
        if isinstance(parser_method, DispatchParser):
            return parser_method(args)

        # HANDLE neither
        raise DetailedError( # On est pas censé arrivé ici
            f"Parser method attendu: SimpleParser ou DispatchParser. "
            f"Type reçu: {type(parser_method)}. Méthode: {parser_method}"
        )

    def update_args_simpleparser(self, syntax_handler, args, key="", check_with_type=False): 
        """
        Description
        -----------
        Updates the `args` dictionary by calling a `SimpleParser` method retrieved from `syntax_handler`.  
        Typically used by dispatch parser methods that expect only `SimpleParser` methods in their syntax handler.

        Arguments
        ---------
        syntax_handler: dict
            Dispatch table mapping token types or values to parser methods.

        args: dict
            The current dictionary of arguments to update.

        key: str, optional
            The key under which to store the result of the `SimpleParser` method. Default is an empty string.

        check_with_type: bool, optional
            If True, `_get_parser` will prioritize matching the token type when selecting the parser method. Default is False.

        Returns
        -------
        dict
            The updated `args` dictionary.
        """
        parser_method = self._get_parser(syntax_handler, check_with_type)
        args[key] = parser_method()
        return args
    
    def _dispatch(self, _args, _syntax_handler: dict):
        """
        Description
        -----------
        Performs a dispatch based on the next token for 'children' dispatch parser methods.  
        Checks the next token's type and value against the provided `_syntax_handler` dispatch table.  
        Calls the corresponding parser method from `_syntax_handler` with `_args`.  
        Raises `DetailedError` if no matching key is found in the dispatch table.

        Arguments
        ---------
        _args: dict
            Dictionary of arguments to pass to the selected parser method.

        _syntax_handler: dict
            Dispatch table mapping token types or values to parser methods.

        Returns
        -------
        dict
            The updated arguments dictionary after the dispatched parser method has been applied.
        """
        dispatch_idx = [key for key in _syntax_handler]
        token_peek = self.token_peek(return_type=False)
        key_type, key_value = __BREAK__TOKEN__(token_peek)
        if key_type in dispatch_idx:
            args = _syntax_handler[key_type](_args)
        elif key_value in dispatch_idx:
            args = _syntax_handler[key_value](_args)
        else:
            raise DetailedError(f"Scene syntax error. Expected one of the following as an argument: {dispatch_idx} but got {token_peek} instead.")

        return args
    
    def parse_define(self):
        """
        Description
        -----------
        Parses a `define` statement of the form `define <USER> = <expression>`.  
        The right-hand side `<expression>` can be:
        - A STRING (e.g., `"Eileen"`)
        - A USER (variable, e.g., `True`, `None`, `my_var`)
        - A FUNCTION call (e.g., `Character("Eileen", color="#fff")`)

        Arguments
        ---------
        None

        Returns
        -------
        DefineNode
            AST node representing the `define` statement, containing:
            - `id`: the user-defined identifier
            - `value`: the parsed expression on the right-hand side
        """

        self.eat('KEYWORD', 'define')
        self.skip_spaces()
        id_define = self.parse_user() # Must be the same as ast_assign.__getattribute__("LHS")
        self.skip_spaces()
        self.eat('ASSIGN', '=')
        self.skip_spaces()

        args_define = {
            'id': id_define,
            'value': None
        }

        # HANDLING expression on RHS of assign using a dispatch table:
        syntax_handler = { # We use a dispatch_table instead of if/else if imbriqués
            "STRING": self.parse_string,
            "USER": self.parse_user,
            "FUNCTION": self.parse_function_call
        }

        args_define = self.update_args(syntax_handler, args_define, 'value')
        self.eof_line()

        return DefineNode(id=args_define.get('id', None), value=args_define.get('value', None))

    def parse_with(self, args=None):
        """
        Description
        -----------
        Parses a `with` statement that specifies a transition.  
        The syntax handled is:

            with <transition>

        Where `<transition>` can be:
        - A BUILTIN token (predefined transition)
        - A USER-defined identifier

        Arguments
        ---------
        args: dict, optional
            Dictionary to update with the parsed transition under the key `'transition'`.  
            If not provided, the method returns only the parsed transition AST node.

        Returns
        -------
        TransitionNode or dict
            - If `args` is provided: the updated `args` dictionary containing the parsed transition.
            - If `args` is None: the `TransitionNode` representing the parsed transition.
        """
        transition_ast = ""
        # HANDLING the syntax 'with -> n * SPACE'
        self.eat('KEYWORD', 'with')
        self.skip_spaces()
        
        # HANDLING the syntax 'transition -> n * SPACE' # transition can be defined by user or a BUILTIN token 
        token_type, token_value = __BREAK__TOKEN__(self.token_peek(return_type=False))
        if token_type == 'BUILTIN':
            transition_ast = TransitionNode(transition_name=token_value)
            self.eat('BUILTIN', token_value)
        elif token_type == 'USER':
            transition_value = self.parse_user()
            transition_ast = TransitionNode(transition_name=transition_value)

        self.skip_spaces()
        self.eof_line()

        # UPDATING args
        if args is not None:
            args['transition'] = transition_ast
            return args
        else:
            return transition_ast 
            
    def parse_onlayer(self, args):
        """
        Description
        -----------
        Parses an `onlayer` statement, which assigns a layer to an element and optionally handles a transition.  
        The syntax handled is:

            onlayer <layer>
            onlayer <layer> with <transition>

        Where `<layer>` can be:
        - The BUILTIN layer `'master'`
        - A USER-defined layer identifier

        The method also optionally handles a `with` clause to specify a transition using a dispatch table.

        Arguments
        ---------
        args: dict
            Dictionary of arguments to update. The parsed layer is stored under the key `'layer'`.  
            If a `with` transition is present, it will also be added under the key `'transition'`.

        Returns
        -------
        dict
            The updated `args` dictionary containing:
            - `'layer'`: the parsed `LayerNode`
            - `'transition'` (optional): the parsed `TransitionNode` if a `with` clause was present
        """
        # HANDLING the syntax 'onlayer -> n * SPACE'
        self.eat('KEYWORD', 'onlayer')
        self.skip_spaces()
        
        # HANDLING the syntax 'layer': The user used either a renpy keyword (only 'master' is accepted for this project) or his own custom named layer
        layer_ast = LayerNode(layer_name='master')
        token_value = __GET__VALUE__TOKEN__(self.token_peek(return_type=False))
        if token_value != 'master': 
            layer_ast = self.parse_user()
        else: 
            self.eat('BUILTIN', token_value)
        
        # HANDLING the syntax 'n * SPACE'
        self.skip_spaces()
        
        # UPDATING args
        args['layer'] = layer_ast

        # HANDLING next token:
        token = self.token_peek(return_type=False)
        if token == self.EOF or __GET__TYPE__TOKEN__(token) == 'NEWLINE' or __GET__TYPE__TOKEN__(token) == 'COMMENT': 
            self.eof_line()
            return args
        
        # HANDLING 'at', 'onlayer' or 'with' using a dispatch table:
        syntax_handler = { # We use a dispatch_table instead of if/else if imbriqués
            "with": self.parse_with
        }

        args = self._dispatch(args, syntax_handler)
        
        return args
    
    def parse_transform(self, args):
        """
        Description
        -----------
        Parses a `transform` statement that specifies a positioning or transformation for a scene element.  
        The syntax handled includes:

            scene <image_expression> at <transform>
            scene <image_expression> at <transform> with <transition>
            scene <image_expression> at <transform> onlayer <layer> [with <transition>]

        Where `<transform>` can be one of the following BUILTIN values:
            'center', 'left', 'right', 'top', 'bottom', 'offscreenleft', 'offscreenright',
            'topleft', 'topright', 'bottomleft', 'bottomright'

        The method also optionally handles `with` or `onlayer` clauses using a dispatch table.

        Arguments
        ---------
        args: dict
            Dictionary of arguments to update. The parsed transform is stored under the key `'transform'`.  
            Additional keys such as `'layer'` or `'transition'` may be added if corresponding clauses are present.

        Returns
        -------
        dict
            The updated `args` dictionary containing:
            - `'transform'`: the parsed `TransformNode`
            - `'layer'` (optional): if an `onlayer` clause was present
            - `'transition'` (optional): if a `with` clause was present
        """
        # HANDLING the syntax 'at -> n * SPACE'
        self.eat('KEYWORD', 'at')
        self.skip_spaces()

        # HANDLING the syntax 'transform -> n * SPACE'
        acceptable_transform = ['center', 'left', 'right', 'top', 'bottom', 'offscreenleft', 'offscreenright', 'topleft', 'topright', 'bottomleft', 'bottomright']
        token = self.token_peek(return_type=False)
        token_value = __GET__VALUE__TOKEN__(token)
        if token_value not in acceptable_transform:
            raise DetailedError(f'Scene syntax error. Expected an argument among: {acceptable_transform}')
        # Note: si __GET__VALUE__TOKEN__ peut raise Error, on perd de l'information
        self.eat('BUILTIN', token_value)
        transform_ast = TransformNode(transform_name = token_value)
        self.skip_spaces()

        # UPDATING args
        args['transform'] = transform_ast

        # HANDLING whether the statement is done or not:
        token = self.token_peek(return_type=False)
        if token == self.EOF or __GET__TYPE__TOKEN__(token) == 'NEWLINE' or __GET__TYPE__TOKEN__(token) == 'COMMENT': 
            self.eof_line() 
            return args
        
        # HANDLING 'with', or 'onlayer' using a dispatch table:
        syntax_handler = { # We use a dispatch_table instead of if/else if imbriqués
            "with": self.parse_with,
            "onlayer": self.parse_onlayer
        }

        args = self._dispatch(args, syntax_handler)

        return args
    
    def parse_image_expression(self, args):
        """
        Description
        -----------
        Parses an image expression in a scene statement.  
        The possible syntax is:

            scene <image_expression> [at <transform>] [onlayer <layer>] [with <transition>]

        Where:
        - `<image_expression>` is one or more USER tokens representing the image or variable
        - `<transform>` is a transform (parsed via `parse_transform`)
        - `<layer>` is a layer (parsed via `parse_onlayer`)
        - `<transition>` is a transition (parsed via `parse_with`)

        The method handles all relevant dispatch keywords: `at`, `onlayer`, `with`.

        Arguments
        ---------
        args: dict
            Dictionary of arguments to update. Parsed components are stored under:
            - `'image_expression'`: list of parsed USER tokens
            - `'transform'`, `'layer'`, `'transition'`: optional, depending on clauses present

        Returns
        -------
        dict
            The updated `args` dictionary containing the parsed image expression and any optional clauses.
        """
        token = self.token_peek(return_type=False)
        token_type, token_value = __BREAK__TOKEN__(token) 

        # HANDLING syntax 'image_expression -> n * SPACE'
        stopping_values = ['\n', 'at', 'onlayer', 'with']
        img_expression = []
        while (token != self.EOF and token_type != 'COMMENT' and token_value not in stopping_values):
            if token_type == 'USER':
                img_expression.append(self.parse_user())
            elif token_type == 'SPACE': 
                self.eat('SPACE')
            else:
                raise DetailedError(f'Scene syntax error. Expected either USER token or SPACE token and got {token} instead')
            token = self.token_peek(return_type=False)
            # print("token = ", token)
            token_type, token_value = __BREAK__TOKEN__(token)
        
        # UPDATING args
        args['image_expression'] = img_expression

        # HANDLING next token, if it's EOF or NEWLINE we return the current args for parent function (parse_scene):
        if token == self.EOF or __GET__TYPE__TOKEN__(token) == 'NEWLINE' or __GET__TYPE__TOKEN__(token) == 'COMMENT': 
            self.eof_line()
            return args
        
        # HANDLING 'at', 'onlayer' or 'with' using a dispatch table:
        syntax_handler = { # We use a dispatch_table instead of if/else if imbriqués
            "at": self.parse_transform,
            "onlayer": self.parse_onlayer,
            "with": self.parse_with
        }

        args = self._dispatch(args, syntax_handler)

        return args
    



class SceneParser(DispatchParser):
    """Specific class to handle scene keyword with dispatch table (parent parser)"""
    def __init__(self, list_tokens):
        super().__init__(list_tokens)
    
    def parse_scene(self): # ok but develop the children handler
        """
        Description
        -----------
        Parses a `scene` statement, handling multiple syntactic variations through recursive dispatch tables.  
        The possible syntax is:

            scene [<image_expression>] [at <transform>] [onlayer <layer>] [with <transition>]

        Where:
        - `<image_expression>`: one or more USER tokens representing the image or variable
        - `<transform>`: a transform (parsed via `parse_transform`)
        - `<layer>`: a layer (parsed via `parse_onlayer`)
        - `<transition>`: a transition (parsed via `parse_with`)

        This method handles the initial cases (scene alone or followed by `image_expression`, `with`, or `onlayer`) and delegates more complex clauses to appropriate parser methods via dispatch tables.

        Arguments
        ---------
        None

        Returns
        -------
        SceneNode
            AST node representing the parsed scene, containing optional fields:
            - `image_expression`: list of USER tokens or None
            - `transform`: parsed `TransformNode` or None
            - `layer`: parsed `LayerNode` or None
            - `transition`: parsed `TransitionNode` or None
        """

        # mot-clé
        self.eat('KEYWORD', 'scene')
        # self.eat('SPACE') # Minimum one space? Wrong, we could also have a NEWLINE
        self.skip_spaces() 

        # HANDLING the situation where 'scene' is not followed by any other argument accepted by the renpy syntax 
        token = self.token_peek(return_type=False)
        if token == self.EOF or __GET__TYPE__TOKEN__(token) == 'NEWLINE' or __GET__TYPE__TOKEN__(token) == 'COMMENT': 
            return SceneNode() # syntax corresponds to 'scene' only
        
        # We will build the arguments of SceneNode with all the dispatch handler. We start from here:
        args = {
            'image_expression': None, 
            'transform': None, 
            'layer': None, 
            'transition': None
        }

        # Use a dispatch table like a real compiler:
        syntax_handler = { # We use a dispatch_table instead of if/else if imbriqués
            "USER": self.parse_image_expression,  
            "at": self.parse_transform,
            "onlayer": self.parse_onlayer,
            "with": self.parse_with
        }

        args = self._dispatch(args, syntax_handler)
        
        return SceneNode(
            image_expression = args.get('image_expression', None),
            transform = args.get('transform', None),
            layer = args.get('layer', None),
            transition = args.get('transition', None) 
        )

class ShowParser(DispatchParser):
    """Specific class to handler show keyword with dispatch tables (parent handler)"""
    def __init__(self, list_tokens):
        super().__init__(list_tokens)
    
    def parse_show(self): # ok but develop the children handler
        """
        Description
        -----------
        Parses a `show` statement, handling multiple syntactic variations through recursive dispatch tables.  
        The possible syntax is:

            show [<image_expression>] [at <transform>] [onlayer <layer>] [with <transition>]

        Where:
        - `<image_expression>`: one or more USER tokens representing the image or variable
        - `<transform>`: a transform (parsed via `parse_transform`)
        - `<layer>`: a layer (parsed via `parse_onlayer`)
        - `<transition>`: a transition (parsed via `parse_with`)

        This method handles the initial cases (`show` alone or followed by `image_expression`, `with`, or `onlayer`) and delegates more complex clauses to the appropriate parser methods via dispatch tables.

        Arguments
        ---------
        None

        Returns
        -------
        ShowNode
            AST node representing the parsed show statement, containing optional fields:
            - `image_expression`: list of USER tokens or None
            - `transform`: parsed `TransformNode` or None
            - `layer`: parsed `LayerNode` or None
            - `transition`: parsed `TransitionNode` or None
        """
        # mot-clé
        self.eat('KEYWORD', 'show')
        self.skip_spaces() 

        # HANDLING the situation where 'scene' is not followed by any other argument accepted by the renpy syntax 
        token = self.token_peek(return_type=False)
        if token == self.EOF or __GET__TYPE__TOKEN__(token) == 'NEWLINE' or __GET__TYPE__TOKEN__(token) == 'COMMENT': 
            return ShowNode() # syntax corresponds to 'show' only
        
        # We will build the arguments of SceneNode with all the dispatch handler. We start from here:
        args = {
            'image_expression': None, 
            'transform': None, 
            'layer': None, 
            'transition': None
        }

        # Use a dispatch table like a real compiler:
        syntax_handler = { # We use a dispatch_table instead of if/else if imbriqués
            "USER": self.parse_image_expression,  
            "at": self.parse_transform,
            "onlayer": self.parse_onlayer,
            "with": self.parse_with
        }

        args = self._dispatch(args, syntax_handler)

        # print("args = ", args)
        # remove self.eof_line() from all dispatcher and call it here just once ?
        return ShowNode(
            image_expression = args.get('image_expression', None),
            transform = args.get('transform', None),
            layer = args.get('layer', None),
            transition = args.get('transition', None) 
        )

class HideParser(DispatchParser):
    """Specific class to handler hide keyword with dispatch tables (parent handler)"""
    def __init__(self, list_tokens):
        super().__init__(list_tokens)

    def parse_hide(self):
        """
        Description
        -----------
        Parses a `hide` statement, handling multiple syntactic variations through recursive dispatch tables.  
        The possible syntax is:

            hide [<image_expression>] [onlayer <layer>] [with <transition>]

        Where:
        - `<image_expression>`: one or more USER tokens representing the image or variable
        - `<layer>`: a layer (parsed via `parse_onlayer`)
        - `<transition>`: a transition (parsed via `parse_with`)

        This method handles the initial cases (`hide` alone or followed by `image_expression`, `with`, or `onlayer`) and delegates more complex clauses to the appropriate parser methods via dispatch tables.

        Arguments
        ---------
        None

        Returns
        -------
        HideNode
            AST node representing the parsed hide statement, containing optional fields:
            - `image_expression`: list of USER tokens or None
            - `layer`: parsed `LayerNode` or None
            - `transition`: parsed `TransitionNode` or None
        """
        # mot-clé
        self.eat('KEYWORD', 'hide')
        self.skip_spaces() 

        # HANDLING the situation where 'scene' is not followed by any other argument accepted by the renpy syntax 
        token = self.token_peek(return_type=False)
        if token == self.EOF or __GET__TYPE__TOKEN__(token) == 'NEWLINE' or __GET__TYPE__TOKEN__(token) == 'COMMENT': 
            return HideNode() # syntax corresponds to 'show' only
        
        # We will build the arguments of SceneNode with all the dispatch handler. We start from here:
        args = {
            'image_expression': None, 
            'layer': None, 
            'transition': None
        }

        # Use a dispatch table like a real compiler:
        syntax_handler = { # We use a dispatch_table instead of if/else if imbriqués
            "USER": self.parse_image_expression,  
            "onlayer": self.parse_onlayer,
            "with": self.parse_with
        }

        args = self._dispatch(args, syntax_handler)

        # print("args = ", args)
        # remove self.eof_line() from all dispatcher and call it here just once ?
        return HideNode(
            image_expression = args.get('image_expression', None),
            layer = args.get('layer', None),
            transition = args.get('transition', None) 
        )



class LabelParser(SceneParser, ShowParser, HideParser):
    """Specific class to handler label keyword with dispatch tables (parent handler)"""
    def __init__(self, list_tokens):
        super().__init__(list_tokens)

    def parse_dialogue(self):
        # If we read a USER token inside label body: we expect to read a dialogue.
        # dialogue is something like e "Hello, I am Eileen and I am talking" where 'e' was declared with 'define' and 'Character' statements
        # We can also have Character('Eileen') "Hello I am eileen" even if it's less common
        token_type, token_value =  __BREAK__TOKEN__(self.token_peek(return_type=False))

        ast_speaker = ""
        if token_type == 'FUNCTION' and 'Character(' in token_value:
            ast_speaker = self.parse_function_call()
        else:
            ast_speaker = self.parse_user()
        self.skip_spaces()
        ast_string = self.parse_string()

        return DialogueNode(speaker=ast_speaker, text=ast_string)


    def check_body_token(self):
        """
        Description
        -----------
        Checks the next token at the beginning of a line inside a label body and dispatches to the appropriate parser method.  
        Acceptable tokens include: `scene`, `show`, `hide`, `play`, `stop`, `with`, `jump`, `return`, `STRING`, `COMMENT`, `USER`.

        Arguments
        ---------
        None

        Returns
        -------
        ASTNode
            The AST node returned by the corresponding parser method for the current token.
        """
        syntax_handler = { 
            'scene': self.parse_scene,
            'show': self.parse_show,
            'hide': self.parse_hide,
            'play': self.parse_play,
            'with': self.parse_with,
            'stop': self.parse_stop,
            'STRING': self.parse_string,
            'COMMENT': self.parse_comment,
            'return': self.parse_return,
            'jump': self.parse_jump,
            'USER': self.parse_dialogue
            # 'DOLLARS': self.parse_dollars, # Not implemented
        }

        parse_method = self._get_parser(syntax_handler)
        ast_object = parse_method()
        self.eof_line()

        return ast_object

    def check_end_label(self, INDENTATION):
        # Verify all the possible condition telling us the label has ended whenever we read a NEWLINE during parse_label

        # Tokens that can appear at the top level, outside any label are listed inside top_level_starter_token_values. 
        # These tokens represent the first element of a top-level statement:
        # - 'define', 'image', 'color' → global definitions
        # - 'label', 'master'         → label or layer definitions
        # - '$'                       → inline Python statements
        # - '#'                       → comments
        # - '\n'                      → blank lines / statement separators

        # Current token is NEWLINE token
        indent_cpt = 0
        token = self.token_peek(return_type=False)
        tk_type = __GET__TYPE__TOKEN__(token)
        while token != self.EOF and tk_type in ['NEWLINE', 'SPACE']:
            while self.token_peek() == 'NEWLINE': # We may have multiple NEWLINE tokens
                indent_cpt = 0
                self.eat_optional('NEWLINE')

            while self.token_peek() == 'SPACE': # We may have more space but they are optional
                self.eat_optional('SPACE')
                indent_cpt += 1
            
            while self.token_peek() == 'COMMENT':
                self.parse_comment()

            token = self.token_peek(return_type=False)
            tk_type = __GET__TYPE__TOKEN__(token)
        
        if indent_cpt == INDENTATION:
            return False
        else:
            if token == self.EOF: # No need to check indentation for a comment
                return True 
            elif indent_cpt == 0: # We check the first non-SPACE and non-NEWLINE token at the beginning of a line
                if __GET__VALUE__TOKEN__(token) in TOPLEVEL_TOKENS_VALUES or __GET__TYPE__TOKEN__(token) in TOPLEVEL_TOKENS_VALUES:
                    return True
                else: # We only accept certain tokens values/types as top level token as defined by TOPLEVEL_TOKENS_VALUES
                    raise DetailedError('Syntax error for label. Unexpected token declared outside all labels')
            else: # The indentation does not match what we expected.
                raise DetailedError('Syntax error for label. Each line in label body must have the same indent')
       
    def parse_label(self):# We only eat NEWLINE HERE !!!!!
        """
        Description
        -----------
        Parses a label definition and its body.  
        The syntax handled is:

            label <label_name>:
                <body_statements>
                return|jump

        Where `<body_statements>` can include any valid tokens parsed by `check_body_token` (scene, show, hide, play, etc.).  
        The method enforces consistent indentation for all lines in the label body.  
        The label must end with a `return` or `jump` statement.

        Arguments
        ---------
        None

        Returns
        -------
        LabelNode
            AST node representing the parsed label, containing:
            - `label`: the name of the label
            - `body`: a list of AST nodes representing the statements inside the label
        """
        self.eat('KEYWORD', 'label')
        self.skip_spaces() 

        # HANDLING whether it's the starting point of the game 'label start' or not
        token_value = __GET__VALUE__TOKEN__(self.token_peek(return_type=False))
        if token_value != 'start':  # It must be a USER token
            label_name = self.parse_user()
        else:
            self.eat('KEYWORD', token_value)
            label_name = KeywordNode(token_value)
        self.eat('COLON')
        self.skip_spaces()
        self.eof_line()
        while self.token_peek() == 'NEWLINE':
            self.eat_optional('NEWLINE')

        # HANDLING body of the label
        # Body begins: (we can have pretty much anything we want that is inside TOKENS or a user variable)
        # We count the amount of SPACE before next command: this gives us the indentation that MUST be respected after a NEWLINE token
        IDENT_NB = 0  # We request that the indentation is at least one space
        while self.token_peek() == 'SPACE': # We may have more space but they are optional
            self.eat_optional('SPACE')
            IDENT_NB += 1
        
        if IDENT_NB == 0:
            raise DetailedError('Syntax error label. Identation inside label body must be at least one SPACE.')
        body_ast = []
        token = self.token_peek(return_type=False)
        tk_type, tk_val = __BREAK__TOKEN__(token)

        while (token!= self.EOF and tk_val != 'label' and tk_val != 'return'):
            if tk_type == 'NEWLINE':
                if self.check_end_label(IDENT_NB): # We check if the label is ending
                    return LabelNode(label=label_name, body=body_ast)
            else:
                ast = self.check_body_token()
                if ast is not None:
                    body_ast.append(ast)
            token = self.token_peek(return_type=False)
            tk_type, tk_val = __BREAK__TOKEN__(token)
        
        # if token == self.EOF:
        #    raise DetailedError('Syntax error for label. expected return or jump.')
        
        # HANDLING either return of jump (these two are optional)
        if __GET__VALUE__TOKEN__(self.token_peek(return_type=False)) in ['return', 'jump']:
            body_ast.append(self.check_body_token()) # obtain return or jump
        self.eof_line()

        return LabelNode(label=label_name, body=body_ast)
    


class MasterParser(LabelParser):
    """Class that create the final AST tree object for the game
    
    Tips:
    A renpy file in this project is considered to be structured by labels and top-level lines.
    We call Top-level lines statements written outside of any label such as `define`, `image`, 
    `play`.
    # They must appear before any label that uses them. Lines between labels
    # are only available to labels defined after them. Lines after all labels
    # are valid but unused if no label references them.

    """
    

    def __init__(self, list_tokens):
        super().__init__(list_tokens)

    def parse_toplevel_statement(self):
        syntax_handler = { # USER token not allowed (must be preceded by DOLLAR token)
            'define': self.parse_define,
            'image': self.parse_image,
            'scene': self.parse_scene,
            'show': self.parse_show,
            'hide': self.parse_hide,
            'play': self.parse_play,
            'stop': self.parse_stop,
            'COMMENT': self.parse_comment,
            'label': self.parse_label
            # 'DOLLARS': self.parse_dollars, # Not implemented
        }

        parse_method = self._get_parser(syntax_handler)
        ast_object = parse_method()


        return ast_object

    def parse_renpy_file(self):
        """
        Structure of AST:
        List according to order you read renpy file.
        Linkage resolution not done here.
        """
        ast_master = []

        # Program starts with 'label start' or we have an error (I impose this condition) -> Normally the error is raised during runtime, actually it's the same for all the error raised in this document but i don't care cause these methods will be run during runtime in fact.
        found_label_start = False
        for token in self.list_tokens:
            token_value = __GET__VALUE__TOKEN__(token)
            if token_value == 'start':
                found_label_start = True
        
        if not found_label_start:
            raise DetailedError('Syntax error. Renpy script must contain an entry-point: label start')
        
        # HANDLING the entire renpy file:
        token = self.token_peek(return_type=False)
        token_type, token_value = __BREAK__TOKEN__(token)
        while(token!= self.EOF):
            if token_type == 'NEWLINE' or token_type == 'SPACE':
                self.eat(token_type)
            else: # HANDLE all other scenarios
                ast_tree = self.parse_toplevel_statement()
                if ast_tree is not None:
                    ast_master.append(ast_tree)
            token = self.token_peek(return_type=False)
            token_type, token_value = __BREAK__TOKEN__(token)

        return MasterNode(children=ast_master)


# Top-level lines are statements written outside of any label, they are defined
# inside TOPLEVEL_TOKENS_VALUES global variable.
# They must appear before any label that uses them. Lines between labels
# are only available to labels defined after them. Lines after all labels
# are valid but unused if no label references them.



# END OF MODULE PARSER
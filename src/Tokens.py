from Error import DetailedError
from defs import *
from AST import *
import re

class RPTokenizer():
    """Handles tokenization of a renpy script."""
    def __init__(self, renpy_file): # renpy_file is the renpy script
        self.TOKENS = TOKENS
        self.renpy_file = renpy_file
        self.idx = 0 # To navigate letter by letter in the file 

    @staticmethod
    def __BREAK__TOKEN__(token_str):
        """
        Extracts the type and value from a token string.

        Args:
            token_str (str): Token in the format 'Token(type="...", value="...")'

        Returns:
            tuple: (token_type, token_value), or (FILE_EOF, FILE_EOF) if the token is invalid
        """
        if token_str == FILE_EOF or (not isinstance(token_str, str)) or (not token_str.startswith('Token(type="')) or ('value="' not in token_str):
            return FILE_EOF, FILE_EOF  # Return EOF tuple for abnormal cases
        token_type = token_str.split('type')[1].split(', value')[0]
        token_type = token_type[2:len(token_type)-1]
        value = token_str.split('value')[1]
        value = value[2:len(value)-2]
        return token_type, value
    
    @staticmethod
    def __GET__TYPE__TOKEN__(token_str):
        """
        Extracts only the type from a token string.

        Args:
            token_str (str): Token in the format 'Token(type="...", value="...")'

        Returns:
            str: Token type, or FILE_EOF if the token is EOF
        """
        if token_str == FILE_EOF:
            return token_str
        token_type = token_str.split('type')[1].split(', value')[0]
        token_type = token_type[2:len(token_type)-1]
        return token_type

    @staticmethod
    def __GET__VALUE__TOKEN__(token_str):
        """
        Extracts only the value from a token string.

        Args:
            token_str (str): Token in the format 'Token(type="...", value="...")'

        Returns:
            str: Token value, or FILE_EOF if the token is EOF
        """
        if token_str == FILE_EOF:
            return token_str
        value = token_str.split('value')[1]
        value = value[2:len(value)-2]
        return value
    
    @staticmethod
    def __TOKEN__(token_type, word_or_letter):
        """
        Constructs a token string from type and value.

        Args:
            token_type (str): Type of the token
            word_or_letter (str): Value of the token

        Returns:
            str: Formatted token string in the format 'Token(type="...", value="...")'
        """
        return f"Token(type=\"{token_type}\", value=\"{word_or_letter}\")"
    
    def word_is_token(self, word): 
        """
        Checks if a given word matches a predefined token and returns the token string if it does.

        Args:
            word (str): Word written by the user in the script.

        Returns:
            str or bool: Token string in the format 'Token(type="...", value="...")' if the word is a token; 
                        False otherwise.
        """
        for key in TOKENS:
            for elem_list in TOKENS[key]:
                if word == elem_list:
                    return self.__TOKEN__(key, word)
        return False
    
    def char_is_token(self, word): 
        return self.word_is_token(word)
    
    def get_token_comment(self):
        """
        Reads characters from the current position until the end of the line to create a COMMENT token.

        Returns:
            str: Token string in the format 'Token(type="COMMENT", value="...")' containing the comment text.
        """
        token_value = ''
        while (self.idx < len(self.renpy_file) and self.renpy_file[self.idx] != '\n'):
            token_value += self.renpy_file[self.idx]
            self.idx += 1
        return self.__TOKEN__('COMMENT', token_value)
    
    def get_token_float(self):
        """
        Reads a floating-point number around the current '.' character and returns it as a DOT token.

        Returns:
            str: Token string in the format 'Token(type="DOT", value=...)' containing the float value.

        Raises:
            ValueError: If the parsed number does not match a valid float format (digits.digits).
        """
        # Current character reads '.', word does not contian anything either so we can safely return the float number found
        integer = "" # partie entiere
        decimal = "" # partie decimale
        dot_idx = self.idx

        j = dot_idx - 1
        while (j >= 0 and self.renpy_file[j].isdigit()):
            j -= 1
        integer = self.renpy_file[j + 1: dot_idx]

        j = dot_idx + 1
        while (j < len(self.renpy_file) and self.renpy_file[j].isdigit()):
            j += 1
        decimal = self.renpy_file[dot_idx + 1: j]

        token_value = integer + '.' + decimal

        if not re.fullmatch(r'\d+\.\d+', token_value):
            raise ValueError(f"Invalid fadeout number format: {token_value}")
    
        # UPDATE self.idx to not keep reading '.' character
        self.idx = j
        token_value = float(token_value)
        return self.__TOKEN__('DOT', token_value)

    def get_string_token(self, word):
        string_literal = self.renpy_file[self.idx] # Store the quote character
        word += self.renpy_file[self.idx]
        self.idx+=1 # Move past the opening quote
        while (self.idx < len(self.renpy_file)):
            if self.renpy_file[self.idx] == string_literal and self.renpy_file[self.idx - 1] != "\\": 
                # End of string detected, not escaped
                word += self.renpy_file[self.idx]
                self.idx += 1 # Consume closing quote
                return self.__TOKEN__('STRING', word) # Complete string token
            else:
                # Accumulate characters inside the string
                word += self.renpy_file[self.idx]
                self.idx += 1
        # If loop ends without finding closing quote
        raise DetailedError("Unterminated string literal")
    
    def tokenizer_from_file(self):
        """
        Tokenizer for a subset of the Ren'Py scripting language.
        - Recognizes keywords, symbols, identifiers, and string literals.
        - Uses a character-by-character scan with a word accumulator.
        - Differentiates between language keywords and user-defined variables.
        - Reports syntax errors for malformed string literals.
        """
        word = "" # Accumulator for multi-character tokens (keywords, identifiers, variables), e.g., "define" or "my_var"
        while (self.idx < len(self.renpy_file)): 
            token_char = self.char_is_token(self.renpy_file[self.idx]) # Checks if the current character is a known single-character token, e.g., '=' or '('
            token_word = self.word_is_token(word) # Checks if the accumulated word matches a keyword from TOKENS, e.g., "define" or "label"
            
            if token_word != False:
                # Case 1: Keyword detected
                # Example: word="define" → token_word is 'Token(type="KEYWORD", value="define")'
                # At this point, we need to check the next character to ensure the syntax is valid 
                if token_char != False:
                    # If the next character is itself a token (like '(' for a function call), return keyword token immediately
                    return token_word
                else: 
                    # The next character is not a known single-character token
                    # We must ensure it is allowed in Renpy syntax (letter, digit, or underscore for USER tokens)
                    if not re.match(r'[A-Za-z0-9_]', self.renpy_file[self.idx]):
                        raise DetailedError(f'Syntax error while creating token. The character """{self.renpy_file[self.idx]}""" is not accepted by Renpy language.')
            else:
                if token_char != False: 
                    # Case 2: Single-character token detected (e.g., '=', '(', ':', ')', ' ')
                    if self.renpy_file[self.idx] == '"' or self.renpy_file[self.idx] == "'": 
                        return self.get_string_token(word) # Special handling for string literals
                    
                    if self.renpy_file[self.idx] == '.':
                        # Could be a float, e.g., "fadeout 2.0"
                        return self.get_token_float() # This method updates self.idx appropriately
                    
                    if word != '': 
                        # Case 2b: USER-defined identifier detected
                        # Example: variable name like "player_health"
                        return self.__TOKEN__('USER', word) # No idx increment needed: current character is already processed
                    
                    if self.renpy_file[self.idx] == '#': # Start of comment
                        return self.get_token_comment() # This method reads until newline and updates self.idx
                    
                    # Case 2c: Regular single-character token
                    self.idx += 1 # Move past the current character before returning (If we don't, we will read it again at the next call of this method)
                    return token_char 
                else:
                    # The current character is neither a known keyword nor a single-character token
                    # It must be part of a USER token (letter, number, underscore). Otherwise we raise an error.
                    if not re.match(r'[A-Za-z0-9_]', self.renpy_file[self.idx]):
                        raise DetailedError(f'Syntax error while creating token. The following character is not accepted by Renpy language: {self.renpy_file[self.idx]}')
            
            # Case 3: No token detected yet → accumulate character into current word
            word += self.renpy_file[self.idx] # Increment here because we want to process the next character in the next iteration
            self.idx += 1 
        
        # End-of-file handling
        if word != "": 
            # Case 4: EOF reached but accumulated word exists → flush as token
            token_word = self.word_is_token(word)
            if token_word != False:
                return token_word # Already a keyword
            else:
                return self.__TOKEN__('USER', word) # It's a USER token
        else:
            # Case 5: End of file is reached
            return FILE_EOF

# ==============================
#  Expose static utility methods (to be used easily by other module)
# ==============================

__BREAK__TOKEN__ = RPTokenizer.__BREAK__TOKEN__
__GET__TYPE__TOKEN__ = RPTokenizer.__GET__TYPE__TOKEN__
__GET__VALUE__TOKEN__ = RPTokenizer.__GET__VALUE__TOKEN__

__all__ = [
    "RPTokenizer",
    "__BREAK__TOKEN__",
    "__GET__TYPE__TOKEN__",
    "__GET__VALUE__TOKEN__",
]








# END OF MODULE TOKENS
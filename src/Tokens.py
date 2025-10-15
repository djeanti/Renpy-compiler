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
        """
        tokenizer_from_file(renpy_file: .rpy file) -> Token()
        
        Algorithm is defined by the following rules below:
            RULE # 1: Similarly to how a compiler would do his job, we move forward character by character with a pointer (self.idx) and gradually build/accumulate a word inside the variable labeled 'word'.

            At the beginning, we start by checking if word contains a token with the condition 'token_word != False' before checking if the current character is a token. 
            The reason is explained through the exemple below.
                Exemple: We want to analyse 'define e'
                    We accumulate the 6 first characters inside the variable word: 'd', 'e', 'f', 'i', 'n', 'e'. 
                    When word = 'define', our pointer (self.idx) points toward the space character meaning renpy_file[self.idx] = ' '.
                    If we check for single character token before checking for multiple-character token, this method will return the token for the space we found.
                    But we will skip the keyword 'define' stored inside word. 
            
            We can deduce the second rule of the algorithm: 
            RULE # 2: The algorithm prioritize finding multiple-character token over single character token. 

            Regarding the logic of handling the pointer. If we find a single-character token, meaning that the condition 'token_char != False' is True, we increment
            self.idx before returning the pointer. If we don't increment the pointer, then, the next time tokenizer_from_file will be called, we will directly check if the current character (which has not changed) is a Token and return the same Token over and over again.
            However, if we find a multiple-character token, we do not increment self.idx before returning the token. The reason for that can be explained with the exemple below:
                Exemple : We want to analyse the following renpy line 'define e'
                    When the condition 'token_word != False' is True, we know that word = 'define' and we also know that renpy_file[self.idx] = ' '
                    If we increment self.idx before returning token_word, the next time we call this method, the pointer will point at the character 'e'.
                    We would have skip over the space character.

            We can deduce the second rule of the algorithm: 
            RULE # 3: In general, the pointer must be incremented after accumulating a character inside word or right before returning a single-character token

            Thanks to the rules above we can deduce the following structure for the algorithm:
            while (self.idx < len(renpy_file)):
                token_char = self.char_is_token(renpy_file[self.idx])
                token_word = self.word_is_token(word) 

                if token_word != False: 
                    return token_word

                if token_char != False: 
                    self.idx += 1
                    return token_char

                word += renpy_file[self.idx]
                self.idx += 1

            However, this structure is still flawed, we cannot catch user defined  (we will be calling such variable USER token for the latter part of the explanation). 
            For instance, in the following renpy line "define e = Character('Eileen')", we won't be able to catch the variable 'e' created by the user. 
            The reason is simple: our current logic only recognizes predefined tokens. We are able to recognise predefined tokens thanks to a global variable
            called TOKENS, which is a dictionary that contains all the non-user-defined keywords in the Ren’Py language that we need for this project. 
            
            This means we are able to distinguish between an actual variable created by the user (USER Token) and a keyword from the Ren’Py syntax (A Token created with TOKENS).
            For the following explanation we will assume that the user write perfectly syntax Renpy's lines of code in the renpy file we are analysing to create tokens.
            This will make the analysis much easier. (We will analyse syntax errors in the next step of our mini compiler, using: the parser)

            So, with the TOKENS dictionnary and the current structure above, we can intuitively try to identify USER Token in the else conditions of 
            'token_word != False' and of 'token_char != False' (we will be calling these conditions 'token_word test' and 'token_char test' in the latter part of 
            the explanation to make it easier to explain). The intuitive structure is shown below:

            if token_word != False: # token_word test
                return token_word
            else:
                # Here, we return a USER Token

            if token_char != False: # token_char test
                self.idx += 1
                return token_char
            else:
                # Here, we return a USER Token

            word += renpy_file[self.idx]
            self.idx += 1

            However, if we do this. We can run into some problems with a code like « e = 5 »
            At first, when the method is called, we check if word = '' is a token → the answer is always no. This means that we would enter the else branch 
            of the token_word test every time we call the method and generate a USER token, so it doesn’t work at all. 

            If we remove the else branch of 'token_word != False' but keep the else branch of 'token_char != False', then when we will evaluate 'e', the 
            first character, and we can finally return it as a USER Token. 
            However, when we return ‘e’ as a USER Token, we don’t know yet whether the user defined variable ‘e’ continues or if the next character is 
            a single-character token (ex: a space) that we can find inside the TOKENS dictionnary. If it’s the latter, we are safe. 
            But if the user defined variable is longer than one character, as in « define varuser = 5 », we will never be able to return ‘varuser’. 
            Instead, we will stop at the first character of ‘varuser’, ‘v’ and return it as a USER Token. So we still have a problem.

            This means that the structure of the code presented above does not allow us to 'accumulate' a complete user defined variable.
            So the real challenge is to determine the stopping condition that tells us when we can safely check whether the accumulated characters inside 
            the variable 'word' forms a user-defined variable, and we need to ensure that this works for both single-character and multi-character 
            user-defined variables!

            However, we do have a clue regarding the stopping condition: Before, we didn’t know whether the next character would belong to the user-defined 
            variable or if it was a single-character token. But we do know one thing: a user-defined variable, regardless of its length, is always followed 
            by a single-character token in correctly written Ren’Py code. Usually, this is a space, but it could also be a newline '\n', an assignment 
            symbol'=', or other single-character tokens.
            
            The key idea is this: if the current character is a single-character token, there is a chance that 'word' — in which we accumulate all previous 
            characters that failed both the token_word and token_char tests — contains a user-defined variable. However, we must make sure to accumulate all the 
            characters of the user defined variable before reaching this stopping condition. This is why we need a different nested structure, as shown below: 

            if token_word != False:
                return token_word
            else:
                if token_char != False :
                    self.idx += 1 # explained by rule 2
                    return token_char

            word += renpy_file[self.idx] # accumulation of the word if we didn’t find anything.
            self.idx+=1 # explained by rule 2

            Thanks to this new structure, we can accumulate a user-defined variable without returning it immediately when we detect a character that is not 
            in the TOKENS dictionary, unlike the previous approach. There is just one last piece missing: when we reach the stopping condition 
            (finding a single-character token), we must check whether 'word' is empty or not. If word is not empty, it means that the accumulated sequence 
            is not a keyword in TOKENS and is followed by a single-character token. At this point, we can safely say that we have caught a complete 
            user-defined variable.  

            The advantage of this method is that it allows us to correctly capture user-defined variables of any length. 
            Important : for this method to work we must only handle non user defined variable with the TOKEN dictionnary.


            Finally, we need to handle a special situation: STRING tokens, basically any accumulation of characters that begins with " and ends with " 
            or that begins with ' and ends with '
            To handle this specific situation we used a 'brute' approach. We accumulate all the characters inside word as soon as we read 
            the single character token " or ' and we keep doing so until we see the corresponding ending character. If we don't find it, we raise
            an exception.

            This gives us our final algorithm below. 
            
            Side note: char_is_token and  word_is_token are exactly the same function so why are their name different even though their code is the same? 
            The reason is: To add more clarity to this method. Which is helpful if this method needs to be modified six months later in the future for instance.
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
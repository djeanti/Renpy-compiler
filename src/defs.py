FILE_EOF = 2376537

FPS = 60

# We can declare a user variable with the following: define, image, color
# We must check that the variable was previously declared in the following: define (right side of assign token), scene, show, hide, with, label (name), return, jump
TOKENS = {
            'KEYWORD': ['define', 'scene', 'show', 'hide', 'play', 'stop', 'with', 'label', 'start', 'return', 'jump', 'image', 'onlayer', 'at', 'loop', 'music', 'sound', 'voice', 'color'],
                        # which parse method should i implement? start/return/jump should be added inside parse_label ---> TO DO
            'BUILTIN': [
                        # Layer: (implemented and used in parse_scene)
                        'master', 

                        # Transitions: (implemented and used in parse_scene)
                        'none', 'fade', 'slide', 'slideleft', 'slideright', 'movein', 'dissolve', 

                        # Transforms (implemented and used in parse_scene):
                        'center', 
                        'left', 
                        'right',
                        'top',
                        'bottom',	
                        'offscreenleft',	
                        'offscreenright',	
                        'topleft',
                        'topright',	
                        'bottomleft',	
                        'bottomright',
                        
                        # Music:
                        'fadein',
                        'fadeout'],
            'STRING' : ['"', "'"],
            'FUNCTION' : ['Character'],
            'ASSIGN' : ['='],
            'COLON' : [':'],
            'COMMA' : [','],
            'LPAREN' : ['('],
            'RPAREN' : [')'],
            'DOT' : ['.'],
            'COMMENT' : ['#'],
            'NEWLINE' : ['\n'],
            # 'DOLLARS': ['$'], -> not handled
            'SPACE' : [' ']
        }



TOPLEVEL_TOKENS_VALUES = [ # NEWLINE is not included here but handled inside parser methods
    'define',
    'image',
    'scene',
    'show',
    'hide',
    'play',
    'stop',
    'DOLLAR',      # Python assignment / expression
    'COMMENT',      # comments
    'label'   # label definitions
]

   

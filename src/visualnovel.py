# TODO: correct error in self.parse_scene (at doesnt work)


# MODULE that creates a visual novel game from a MasterNode AST.
import sys
import os
from Parser import MasterParser
from Tokens import RPTokenizer, __BREAK__TOKEN__
from defs import FILE_EOF
from AST import *
from Error import *
from Textbox import *
import copy
from defs import FPS

class StateMachine():
    """
    A class to create a visual novel video game from a dictionnary (ast tree) using the pygame library.
    """
    def __init__(self, symbol_table:dict, label_table:dict, ast_tree, path_to_renpyf):
        self.path_to_renpyfile = path_to_renpyf
        self.symbol_table = symbol_table
        self.label_table = label_table
        self.ast_tree = ast_tree
        self.clear_color = (30, 30, 30)
        
        self.state_machine = {}
        self.audio_tracking = {
            'voice': '',
            'sound': ''
        } # Used by stop instruction in renpy (it's hard to keep track of the all the audio with only self.state_machine)
        self.transition_ongoing = False # Set to True whenever any transition animation if ongoing and used to prevent skipping to next self.idx until transition is finished
        
        self.idx = 0 # To navigate inside self.state_machine
        self.layer_order_statements = ['master'] # Contains list of all layers created from start to finish of the script
         
    def pretty_dict(self, d: dict, parent_key=None):
        """
        Description
        -----------
        Return a formatted string representation of a nested dictionary, with indentation

        Arguments
        ---------
        d : The dictionary to format.
        parent_key (optional): The key of the parent dictionary, used to add an end-of-key comment.

        Returns
        -------
        str: A formatted, indented string representing the nested dictionary.
        """
        lines = ["{"]
        for k, v in d.items():
            key_str = repr(k)
            if isinstance(v, dict):
                nested = self.pretty_dict(v, parent_key=k)
                nested = textwrap.indent(nested, "  ")
                lines.append(f"  {key_str}: {nested},")
            else:
                lines.append(f"  {key_str}: {repr(v)},")
        lines.append("}" + (f"  # end of {repr(parent_key)}" if parent_key is not None else ""))
        return "\n\n".join(lines)

    def get_nested_img(self, list_of_tags:list):
        """
        Description
        -----------
        Retrieve the image path from a nested dictionary structure using a list of tags.

        Arguments
        ---------
        list_of_tags : A list of keys representing the path through the nested dictionary.

        Returns
        -------
        str: The value corresponding to the final tag in the nested dictionary, typically the image path.
        """
        nested_dict = self.symbol_table['image']
        for tag in list_of_tags:
            nested_dict = nested_dict[tag]
        return next(iter(nested_dict.values()))
    
    def load_image(self, img_path): # Only load image we need to save some ressources
        """
        Description
        -----------
        Load an image from the specified path and return a Pygame surface with transparency.
        Exits the program if the image cannot be loaded.

        Arguments
        ---------
        img_path : The relative path to the image file.

        Returns
        -------
        pygame.Surface: A Pygame surface object containing the loaded image with transparency.
        """
        image_surface = ""
        path = os.path.dirname(self.path_to_renpyfile) + '/' + img_path[1:-1]
        try:
            image_surface = pygame.image.load(path).convert_alpha()  # convert_alpha() pour gérer la transparence
        except:
            print(f'Runtime execution error. Cannot load file {path}')
            pygame.quit()
            sys.exit()
        return image_surface
    
    def get_scenenode_img(self, node):
        """
        Description
        -----------
        Retrieve and load the image associated with a scene node.
        Supports both direct string paths and user-defined tokens, returning a Pygame surface.

        Arguments
        ---------
        node : The scene node containing an image expression.

        Returns
        -------
        pygame.Surface: A Pygame surface object containing the loaded image.
        """
        img_token = self.get_nested_img(node.image_expression) # Get the image to load from the tags
        image_surface = ""
        if isinstance(img_token, StringNode):
            img_path = img_token.value
            image_surface = self.load_image(img_path)
        else: # img_token is expected to be a UserToken (refer to parse_image to see all the syntax handled)
            img_path_token = self.get_user_value(img_token)
            if not isinstance(img_path_token, StringNode): # could be a usertoken, no ?
                raise DetailedError(f"Runtime execution error. Expected a string but got {img_path_token} instead")
            img_path = img_path_token.value
            # We need to fetch actual value of this variable (which could also be another variable...)
            image_surface = self.load_image(img_path)
            # print('img path = ', img_path)
        return image_surface
    
    def get_position_from_size(self, obj_size, transform, screen_size, debug=False):
        """
        Description
        -----------
        Compute the top-left position of an object on the screen based on its size,
        the screen size, and a specified alignment or transformation keyword.

        Arguments
        ---------
        obj_size : Width and height of the object (iw, ih).
        transform : Alignment or transformation keyword (e.g., 'center', 'topright', 'offscreenleft').
        screen_size : Width and height of the screen (sw, sh).
        debug : If True, prints debug information about the transform and computed position.

        Returns
        -------
        tuple of int: The (x, y) coordinates of the object's top-left corner on the screen.
        """
        sw, sh = screen_size
        iw, ih = obj_size  # largeur/hauteur de ton "objet"

        positions = {
            "topleft": (0, 0),
            "topright": (sw - iw, 0),
            "bottomleft": (0, sh - ih),
            "bottomright": (sw - iw, sh - ih),
            "center": ((sw - iw) // 2, (sh - ih) // 2),
            "left": (0, (sh - ih) // 2),
            "right": (sw - iw, (sh - ih) // 2),
            "top": ((sw - iw) // 2, 0),
            "bottom": ((sw - iw) // 2, sh - ih),
            "offscreenleft": (-iw, (sh - ih) // 2),
            "offscreenright": (sw, (sh - ih) // 2),
        }

        if debug:
            print('transform found: ', transform, end = "")
            print(' and pos found: ', positions.get(transform, (0, 0)))

        return positions.get(transform, (0, 0))

    def clear_layer(self, layer_to_clear, chainblock):
        """
        Description
        -----------
        Remove all objects from a specific layer in a Ren'Py scene.

        Arguments
        ---------
        layer_to_clear : The name of the layer to remove objects from.
        objects : A list of scene objects, each represented as a dictionary with potential 'layer' keys.

        Returns
        -------
        list of dict: The updated list with objects from the specified layer removed.
        """
        for obj in chainblock:
            if 'layer' in obj and obj['layer'] == layer_to_clear:
                chainblock.remove(obj)
        return chainblock
        
    def break_img_object(self, dict_):
        """
        Description
        -----------
        Extract key attributes from an image object dictionary in a Ren'Py scene.

        Arguments
        ---------
        dict_ : The dictionary representing an image object with keys 'layer', 'image', 'pos', and 'transition'.

        Returns
        -------
        tuple: A tuple containing (layer, image, pos, transition) extracted from the dictionary.
        """
        return dict_['layer'], dict_['image'], dict_['pos'], dict_['transition']
    
    def break_txt_object(self, dict_):
        """
        Description
        -----------
        Extract key attributes from a text object dictionary in a Ren'Py scene.

        Arguments
        ---------
        dict_ : The dictionary representing a text object with keys 'character' and 'text'.

        Returns
        -------
        tuple: A tuple containing (character, text) extracted from the dictionary.
        """
        return dict_['character'], dict_['text'], dict_['color']
    
    def scale_image_to_wind(self, image, window_size):
        """
        Description
        -----------
        Scale a Pygame image surface to fit the given window size.

        Arguments
        ---------
        image : The image surface to scale.
        window_size : The target size (width, height) for scaling.

        Returns
        -------
        pygame.Surface: The scaled image surface.
        """
        scaled_image = pygame.transform.scale(image, window_size)
        return scaled_image

    def init_img_dict(self):
        """
        Description
        -----------
        Initialize a dictionary representing a drawable image object for Pygame with default values.

        Arguments
        ---------
        None

        Returns
        -------
        dict: Dictionary with default keys for image, position, layer, and transition settings.
        """
        return {
            'tag': None, # To identify the image (only used by ShowNode)
            'type': None, # Either show or scene
            'layer': None,
            'image': None,
            'pos': None,
            'transition': {
                'type': None,
                'duration': 1,
                'animate': False, # When True, we must execute the animation for a specific duration (not necessarily 'duration' key)
                'pos_anim': (0, 0), # Used by slide type of transition, stores 
                'last_pos': (0, 0), # start pos for movin transition is always the final pos of previous show statement associated with same tag
                'elapsed': 0 # For linear interpolation for smooth animation in general 
            }
        }
    
    def init_txt_dict(self): 
        """
        Description
        -----------
        Initialize a dictionary representing a drawable dialogue object for Pygame with default values.

        Arguments
        ---------
        None

        Returns
        -------
        dict: Dictionary with the content of the dialogue and the name of the character speaking.
        """
        return {
            'character': None,
            'color': '#000000', # Default color is Black
            'text': None
        }
    
    def init_audio_dict(self): 
        """
        Description
        -----------
        Initialize a dictionary representing an audio object for Pygame with default values.

        Arguments
        ---------
        None

        Returns
        -------
        dict: Dictionary with the content of the audio object.
        """
        return {
            'music': { # play only once by default, loop attribute can make it play indefinitely.
                'canal': False, # If False, the music is not playing currently
                'file': '',
                'loop': False # By default we de not loop the music
            }, 
            'sound': { # stops automatically when next dialogue is loaded (user clicked to display the next scene). Never loops.
                'canal': False, # If False, the sound is not playing currently
                'file': ''
            }, 
            'voice': { # stops automatically when new dialogue is loaded
                'canal': False, # If False, the voice is not playing currently
                'file': ''
            } 
        }
                    
    def get_label(self, label_name):
        """
        Description
        -----------
        Retrieve a label node and its next label from the AST by name.

        Arguments
        ---------
        label_name : The name of the label to search for.

        Returns
        -------
        tuple: A tuple (LabelNode, next_label_name) if found, otherwise (None, None).
        """
        for node in self.ast_tree: 
            if isinstance(node, LabelNode):
                if isinstance(node.label_name, KeywordNode) and node.label_name.value == label_name:
                # print(node.get_next_label())
                    return node, node.get_next_label()
                elif isinstance(node.label_name, UserNode) and node.label_name.name == label_name:
                    return node, node.get_next_label()

        return None, None

    def get_user_value(self, user_token):
        """
        Description
        -----------
        Recursively resolves a user-defined token to its final value.
        
        If the token refers to another user-defined token, the method continues
        to follow the chain of references until a non-UserNode value is found.
        
        Arguments
        ---------
        user_token: The user-defined token to resolve.
        
        Returns
        -------
        The final non-UserNode value associated with the user_token.
        """
        # We need to keep looking until we find the actual value associated to user_token
        # As long as the value we find is a User token we keep searching and return the value once found
        token = self.symbol_table['define'][user_token]
        while True:
            # print('token: ', token)
            if not isinstance(token, UserNode):
                return token
            token = self.symbol_table['define'][token]

    def get_labels_order(self):
        """
        Description
        -----------
        Builds and returns the ordered list of label nodes to execute.

        Starting from the 'start' label, this method follows each subsequent
        label reference (via jump instruction in renpy) to determine
        the execution sequence of labels.

        Arguments
        ---------
        None

        Returns
        -------
        list: Ordered list of label nodes representing execution flow.
        """
        # returns list of labels to execute in order
        label_order = []
        label_order_name = ['start']
        jump = "" # contains next label name
        label_node, next_label_name = self.get_label('start')
        
        while next_label_name != None and label_node!= None:
            label_order.append(label_node)
            label_order_name.append(next_label_name)
            label_node, next_label_name = self.get_label(next_label_name)

        if label_node != None:
            label_order.append(label_node)
            
        return label_order

    def remove_img_obj(self, tag, chainblock):
        """
        Description
        -----------
        Removes an image object from a given chainblock by its tag.

        Searches through the chainblock for an object with the specified tag,
        removes it if found, and returns the updated chainblock along with
        the position of the removed object.

        Arguments
        ---------
        tag: The tag identifying the image object to remove.
        chainblock: The list of objects currently in the chainblock.

        Returns
        -------
        tuple: (updated_chainblock, obj_pos)
            - updated_chainblock: The chainblock after removal.
            - obj_pos: The position of the removed object, or (0, 0) if not found.
        """
        obj_pos = (0, 0) # contains position of object below
        for obj in chainblock:
            if 'tag' in obj and obj['tag'] == tag:
                # print('obj tag found = ', obj)
                obj_pos = obj['pos']
                chainblock.remove(obj)
        return chainblock, obj_pos

    def pretty_list(self, liste):
        """
        Description
        -----------
        Displays the contents of a list in a formatted and readable way.

        Each element is printed with an index label for clarity,
        enclosed between "BEGIN DISPLAYING" and "END DISPLAYING" markers.

        Arguments
        ---------
        liste: The list to display.

        Returns
        -------
        None
        """
        print('\nBEGIN DISPLAYING ###########:')
        idx = 1
        for elem in liste:
            name = f'Elem {idx}#'
            print(f"{name}: {elem}")
            idx += 1

        print('END DISPLAYING ###########:\n')

    def remove_text_chainblock(self, chainblock):
        """
        Description
        -----------
        Removes all text-related objects from the given chainblock.

        Iterates through the chainblock and removes any element 
        containing the key 'text'.

        Arguments
        ---------
        chainblock: List of scene objects.

        Returns
        -------
        list: The updated chainblock with text objects removed.
        """
        for obj in chainblock:
            if 'text' in obj:
                chainblock.remove(obj)
        return chainblock

    def isolate_chainblock_state(self, chainblock):
        """
        Description
        -----------
        Creates a deep, isolated copy of the given chainblock to prevent shared references.

        Explanation:
            When assigning `self.state_machine[self.idx] = chainblock`, Python only stores
            a reference to the same list. Any later modification to `chainblock` will 
            automatically affect previously stored states in `self.state_machine`.

            This method ensures each saved state is independent by manually copying 
            each element and duplicating non-serializable objects such as Pygame Surfaces.

        Arguments
        ---------
        chainblock: List of scene objects representing the current visual/audio state.

        Returns
        -------
        list: A new list containing deep copies of all objects in the chainblock.
        """
        isolated = []

        for elem in chainblock:
            # Superficial copy of the dictionary
            new_elem = elem.copy()

            # If the element contains a Pygame Surface, we create a true independent copy.
            if 'image' in elem and isinstance(elem['image'], pygame.Surface):
                new_elem['image'] = elem['image'].copy()  # Copie indépendante en VRAM

            if 'sfx' in elem and isinstance(elem['sfx'], pygame.Surface): # For music, sound et voice
                new_elem['sfx'] = elem['sfx'].copy()  # Independent copy to VRAM

            # If there are any other non-serializable objects, we can handle them here.
            # Ex: if 'music' in elem and hasattr(elem['music'], 'copy'): ...

            isolated.append(new_elem)
        return isolated
    
    def search_tag_chainblock(self, tag, chainblock):
        """
        Description
        -----------
        Checks whether a given tag exists within the chainblock.

        Iterates through all objects and returns True if an object contains
        a 'tag' field that matches or includes the given tag.

        Arguments
        ---------
        tag: The tag to search for.
        chainblock: List of objects representing the current scene state.

        Returns
        -------
        bool: True if the tag is found in any object, otherwise False.
        """
        for obj in chainblock:
            if ('tag' in obj) and (obj['tag'] is not None) and (tag in obj['tag']):
                return True
        return False
    
    def display_with_transition(self, surface: pygame.display, img:pygame.image, pos:tuple, transition:dict):
        """
        Description
        -----------
        Displays an image on the given Pygame surface with an optional transition effect.

        Supports multiple transition types such as fade, slide, movein, and dissolve. 
        Each transition gradually modifies the image’s appearance or position over time 
        according to the specified duration and animation parameters.

        Arguments
        ---------
        surface: The surface to draw the image on.
        img: The image to display.
        pos: The target position (x, y) where the image should appear.
        transition: A dictionary describing the transition behavior.

        Returns
        -------
        dict: Updated transition dictionary reflecting the current animation state.
        """
        if transition is not None:
            if transition['type'] == 'fade':
                # Beginning / continuing transition
                alpha_value = img.get_alpha()
                if not transition['animate']: 
                    self.transition_ongoing = True
                    img.set_alpha(0)
                    transition['animate'] = True # Begin animation
                else:
                    if alpha_value < 255:
                        incr = 255 / (FPS * int(transition['duration']))
                        speed_factor = 2 # to match actual duration in transition['duration']
                        incr = incr * speed_factor
                        img.set_alpha(alpha_value + int(incr)) 
                    else: 
                        self.transition_ongoing = False
                        transition['type'] = 'none' # We only do the animation once when going forward (rollback animation is not permitted)

            elif transition['type'] == 'slide' or transition['type'] == 'slideright':
                # Slide from right to desired position
                if not transition['animate']:
                    self.transition_ongoing = True
                    start_pos = self.get_position_from_size(img.get_size(), 'offscreenright', surface.get_size())
                    transition['pos_anim'] = (start_pos[0], pos[1])
                    transition['start_pos'] = start_pos[0]  # store fixed start x
                    transition['animate'] = True  # Begin animation
                    transition['elapsed'] = 0
                else:
                    # Increment the elapsed time
                    transition['elapsed'] += 1 / FPS
                    t = min(transition['elapsed'] / transition['duration'], 1.0)  # normalized 0..1

                    # Smooth ease-out
                    t_smooth = 1 - (1 - t) ** 2

                    # Interpolate using fixed start position
                    start_x = transition['start_pos']
                    end_x = pos[0]
                    new_x = start_x + (end_x - start_x) * t_smooth
                    transition['pos_anim'] = (new_x, pos[1])

                    # Check if animation is complete
                    if t >= 1.0:
                        self.transition_ongoing = False
                        transition['type'] = 'none'
                        transition['pos_anim'] = pos  # snap exactly to final position

                surface.blit(img, transition['pos_anim'])
                return transition

            elif transition['type'] == 'slideleft':
                # Slide from left to desired position
                if not transition['animate']:
                    self.transition_ongoing = True
                    start_pos = self.get_position_from_size(img.get_size(), 'offscreenleft', surface.get_size())
                    transition['pos_anim'] = (start_pos[0], pos[1])
                    transition['start_pos'] = start_pos[0]  # store fixed start x
                    transition['animate'] = True  # Begin animation
                    transition['elapsed'] = 0
                else:
                    # Increment the elapsed time
                    transition['elapsed'] += 1 / FPS
                    t = min(transition['elapsed'] / transition['duration'], 1.0)  # normalized 0..1

                    # Smooth ease-out
                    t_smooth = 1 - (1 - t) ** 2

                    # Interpolate using fixed start position
                    start_x = transition['start_pos']
                    end_x = pos[0]
                    new_x = start_x + (end_x - start_x) * t_smooth
                    transition['pos_anim'] = (new_x, pos[1])

                    # Check if animation is complete
                    if t >= 1.0:
                        self.transition_ongoing = False
                        transition['type'] = 'none'
                        transition['pos_anim'] = pos  # snap exactly to final position

                surface.blit(img, transition['pos_anim'])
                return transition

            elif transition['type'] == 'movein' and transition['last_pos'] != False:
                # Slide from last known position to desired position
                if not transition['animate']:
                    self.transition_ongoing = True
                    transition['pos_anim'] = transition['last_pos']  # start pos
                    transition['start_pos'] = transition['last_pos'][0]  # store fixed start x
                    transition['animate'] = True  # begin animation
                    transition['elapsed'] = 0
                else:
                    # Increment elapsed time
                    transition['elapsed'] += 1 / FPS
                    t = min(transition['elapsed'] / transition['duration'], 1.0)  # normalized 0..1

                    # Smooth ease-out interpolation
                    t_smooth = 1 - (1 - t) ** 2

                    # Compute new position
                    start_x = transition['start_pos']
                    end_x = pos[0]
                    new_x = start_x + (end_x - start_x) * t_smooth
                    transition['pos_anim'] = (new_x, pos[1])

                    # Check if animation is complete
                    if t >= 1.0:
                        self.transition_ongoing = False
                        transition['type'] = 'none'
                        transition['pos_anim'] = pos  # snap exactly to final position

                surface.blit(img, transition['pos_anim'])
                return transition
             
            elif transition['type'] == 'dissolve': 
                # Dissolve = fade between invisible and visible (similar to fade)
                alpha_value = img.get_alpha()

                if not transition['animate']:
                    self.transition_ongoing = True
                    img.set_alpha(0)
                    transition['animate'] = True  # Begin animation
                else:
                    if alpha_value < 255:
                        incr = 255 / (FPS * int(transition['duration']))
                        speed_factor = 2 # to match actual duration in transition['duration']
                        incr = incr * speed_factor
                        img.set_alpha(alpha_value + int(incr))  # to make the animation fluid and progressive
                    else:
                        self.transition_ongoing = False
                        transition['type'] = 'none'  # animation is finished

        surface.blit(img, pos)
        return transition
        
    def load_audio(self, audio_path, use_canal = True):
        """
        Description
        -----------
        Load an audio from the specified path and return a Pygame sound object.
        Exits the program if the audio cannot be loaded.

        Arguments
        ---------
        audio_path : The relative path to the audio file.
        use_canal: Decides whether we use pygame.mixer.sound or pygame.mixer.music to load audio

        Returns
        -------
        pygame.mixer.Sound: A Pygame sound object containing the loaded audio.
        """
        canal = ""
        path = os.path.dirname(self.path_to_renpyfile) + '/' + audio_path[1:-1]
        try:
            if use_canal:
                canal = pygame.mixer.Sound(path)  
            else:
                pygame.mixer.music.load(path) # returns None
        except:
            print(f'Runtime execution error. Cannot load audio file {path}')
            pygame.quit()
            sys.exit()
        return canal
    
    def handle_audio(self, audio:dict):
        """
        Description
        -----------
        Manages audio playback and stopping audio (music, voice, sound).
        
        Plays music, sound, or voice based on the given dictionary. Stops all audio or specific channels 
        (music, voice, sound) with optional fadeout. 

        fadein when music|sound|voice starts is not handled.

        Arguments
        ---------
        audio: Dictionary containing information regarding 'music', 'voice', 'sound', 'stop' renpy instructions.

        Returns
        -------
        None
        """
        # We are not handling the fadein for sound or voice
        if 'music' in audio or 'sound' in audio or 'voice' in audio:
            if audio['music']['file'] != '':
                if audio['music']['canal'] == False:
                    self.load_audio(audio['music']['file'], use_canal=False)
                    pygame.mixer.music.set_volume(0.1)  # 10% du volume maximum
                    audio['music']['canal'] = True
                    if audio['music']['loop']:
                        pygame.mixer.music.play(loops=-1)  # We play it in loops
                    else:
                        pygame.mixer.music.play() # We play it once only

            elif audio['voice']['file'] != '':
                if audio['voice']['canal'] == False:
                    # load audio
                    audio['voice']['canal'] = self.load_audio(audio['voice']['file']) # We use Sound because we can create multiple canals, it's easier to handle compared to music
                    self.audio_tracking['voice'] = audio['voice']['canal']
                    audio['voice']['canal'].play()  # We play it once only

            elif audio['sound']['file'] != '':
                if audio['sound']['canal'] == False:
                    # load audio
                    audio['sound']['canal'] = self.load_audio(audio['sound']['file']) # We use Sound because we can create multiple canals, it's easier to handle compared to music
                    self.audio_tracking['sound'] = audio['sound']['canal']
                    audio['sound']['canal'].play()  # We play it once only

        else: # Stop
            if audio['stop'] == "": # scenario 1: 'stop'
                # We must stop all channels (voice, music and sound)
                pygame.mixer.stop()
                pygame.mixer.music.stop()

            # scenario 2: 'stop music' or 'stop sound' or 'stop voice' <=> 'stop music|sound|voice' 
            # scenario 3: 'stop music|sound|voice fadeout X'
            else: # scenario 2 or scenario 3
                # Get specific music, sound or voice
                if audio['fadeout'] == -1: # no fadeout:
                    if audio['stop'] in ['voice', 'sound']:
                        self.audio_tracking['sound'][audio['stop']].stop()
                    else: # music
                        pygame.mixer.music.stop()
                else:
                    fadeout_ms = int(float(audio['fadeout']) * 1000) # in milliseconds
                    if audio['stop'] in ['voice', 'sound']:
                        self.audio_tracking[audio['stop']].fadeout(fadeout_ms)
                    else: # music
                        pygame.mixer.music.fadeout(fadeout_ms)

    def clear_audio(self):
        """
        Description
        -----------
        Stops all audio playback (sound and voice) in the game.

        This function is intended to be called when transitioning to the next piece of dialogue. 
        It ensures that any ongoing sound effects or voice lines are stopped automatically, 
        without affecting the background music.

        Arguments
        ---------
        None

        Returns
        -------
        None
        """
        # When getting to next dialogue sound and voice must be stop automatically but not music
        pygame.mixer.stop()

    def display_state(self, surface, texbox: TextBox, pos_textbox):
        """
        Description
        -----------
        Renders the current state of the scene onto the given surface, including images and text.

        Images are drawn according to the layer order and with their associated transitions.
        Text objects are rendered using the provided TextBox at the specified position.
        This function is typically called once per frame in the main loop.

        Arguments
        ---------
        surface: The surface to render the scene on.
        texbox: The text box object used to render dialogue text.
        pos_textbox: The position (x, y) to draw the text box.

        Returns:
            None
        """
        # This function is called at each frame of the main loop (which helps us a lot for transitions as they also must be updated at each frame)
        # First we display all the images with pygame:
        chainblock = self.state_machine[self.idx]
        for z_index in self.layer_order_statements: # order of layers
            for obj in chainblock: # obj = key 
                # print('obj', obj)
                if 'image' in obj:
                    layer, img, pos, transition_dict = self.break_img_object(obj)
                    if layer == z_index:
                        transition_dict = self.display_with_transition(surface, img, pos, transition_dict)
                        # update self.state_machine with new transition status:
                        obj['transition'] = transition_dict

        # raise DetailedError('debug')
        # Then we display the dialogue:
        for obj in chainblock:
            if 'text' in obj:
                speaker, text, color = self.break_txt_object(obj)
                # print('text = ', text)
                texbox.complex_draw(surface, pos_textbox, text=text, speaker=speaker, color=color)
                
        # raise DetailedError('debug2 error raised right over there')
        # Then we handle the audio:
        for obj in chainblock:
            if 'music' in obj or 'sound' in obj or 'voice' in obj or 'stop' in obj:
                self.handle_audio(obj)

    def get_dialogue_speaker(self, node):
        """
        Retrieves the speaker's name from the dialogue node.
        
        Resolves the speaker to a string by checking for various types of nodes
        (UserNode, FunctionCallNode, StringNode). Returns the speaker's name 
        after extracting the appropriate value.

        Arguments
        ---------
        node: The dialogue node containing the speaker information.

        Returns
        -------
        str: The speaker's name as a string.
        """
        speaker = node.speaker
        color = None
        if isinstance(speaker, UserNode):
            speaker = self.get_user_value(speaker)

        if isinstance(speaker, FunctionCallNode):
            speaker, color = speaker.get_character_name()
            if isinstance(speaker, UserNode):
                speaker = self.get_user_value(speaker)             

        if isinstance(speaker, StringNode):
            speaker = speaker.value[1:-1]
        
        return speaker, color # Here, speaker is not a UserNode
        
    def create_state_machine(self, screen_size):
        """
        Description
        -----------
        Creates a state machine that processes labels, dialogue, and scene nodes, 
        then organizes and prepares data for rendering in the game.

        This function iterates through the labels, processes different node types (such as dialogue, scene, and show),
        and constructs a list of actions (`chainblock`) that will be executed sequentially. Each action (such as 
        displaying text or images) is associated with transitions, transformations, and layers to control how they 
        are rendered during gameplay.

        It also handles scaling of images and checks if a tag (for images) already exists to avoid duplicates.

        Arguments
        ---------
        screen_size : The size of the screen (width, height) to adjust image sizes and positions accordingly.

        Returns
        -------
        None
            The state machine is constructed in place and does not return any value.
        """
        labels_order = self.get_labels_order()
        chainblock = [] # list of pygame commands to show between two user actions 
        self.idx = 0
        for label_body in labels_order:
            for node in label_body:
                # print('node = ', node)
                if isinstance(node, StringNode) or isinstance(node, DialogueNode):
                    txt_display = self.init_txt_dict()
                    if isinstance(node, DialogueNode):
                        speaker, color = self.get_dialogue_speaker(node)
                        txt_display['character'] = speaker
                        txt_display['text'] = node.text.value[1:-1]
                        if color is not None:
                            txt_display['color'] = color
                    else: # It's a string 
                        txt_display['character'] = ""
                        txt_display['text'] = node.value[1:-1]

                    # print('name = ', txt_display['text'])
                    self.remove_text_chainblock(chainblock) # We keep the images (scene and show but we remove the text)

                    chainblock.append(txt_display)
                    self.state_machine[self.idx] = self.isolate_chainblock_state(chainblock)
                    self.idx += 1

                elif isinstance(node, PlayNode):
                    # We should play either a background music, character's voice or a sound (SFX)
                    audio_obj = self.init_audio_dict()
                    audio_value = node.audio_file
                    if isinstance(audio_value, UserNode):
                        audio_value = self.get_user_value(audio_value)
                    # At this point audio_value is a StringNode necessarily
                    audio_value = audio_value.value

                    # print('audio_value = ', audio_value)

                    if node.audio_type == 'music':
                        audio_obj['music']['file'] = audio_value
                        audio_obj['music']['loop'] = node.loop
                    else:
                        audio_obj[node.audio_type]['file'] = audio_value

                    chainblock.append(audio_obj)

                elif isinstance(node, StopNode):
                    audio_value = ""
                    audio_fadeout = -1

                    if node.audio_type is not None:
                        audio_value = node.audio_type # audio_value must be a KeywordNode

                    if node.fadeout is not None:
                        audio_fadeout = node.fadeout

                    stop_obj = {
                        'stop': audio_value,
                        'fadeout': audio_fadeout
                    }

                    chainblock.append(stop_obj)

                elif isinstance(node, SceneNode):
                    img_display = self.init_img_dict()
                    image_surface = self.get_scenenode_img(node)
                    if image_surface.get_size() != screen_size: # we do this only because it's a background ---->>> NEED TO BE AN OPTION IN GUI WIND LATER
                        testing_scale = screen_size 
                        image_surface = self.scale_image_to_wind(image_surface, testing_scale)

                    transform = node.transform.transform_name if node.transform is not None else 'topleft'
                    transition = node.transition.transition if node.transition is not None else 'none'
                    if isinstance(node.layer, LayerNode):
                        layer = node.layer.layer_name if node.layer is not None else 'master'
                    else: # node.layer must be a UserNode
                        layer = node.layer.name if node.layer is not None else 'master'

                    img_display['type'] = 'scene' if isinstance(node, SceneNode) else 'scene'
                    img_display['image'] = image_surface
                    img_display['pos'] = self.get_position_from_size(image_surface.get_size(), transform, screen_size)
                    img_display['layer'] = layer
                    img_display['transition'] = {
                        'type': transition,
                        'duration': 2, # default duration in second (we don't handle custom transition so it's always 1 sec)
                        'animate': False,
                        'pos_anim': (0, 0)
                    }
                    
                    # Before updating chainblock we check if layer already exist or not:
                    if layer not in self.layer_order_statements: # to keep a trace of order of inline-declaration of layers
                        self.layer_order_statements.append(layer)
                    else: # layer already exist: we must clear all image on the current layer
                        self.clear_layer(layer, chainblock)

                    chainblock.append(img_display)

                    # print()

                elif isinstance(node, ShowNode):
                    img_display = self.init_img_dict()
                    image_surface = self.get_scenenode_img(node)
                    if image_surface.get_size() != screen_size: # we do this only because it's a background ---->>> NEED TO BE AN OPTION IN GUI WIND LATER
                        image_surface = scale_img(image_surface, desired_width=500)

                    transform = node.transform.transform_name if node.transform is not None else 'center'
                    transition = node.transition.transition if node.transition is not None else 'none'
                    tag = node.image_expression[0] # first elem only
                    if isinstance(node.layer, LayerNode):
                        layer = node.layer.layer_name if node.layer is not None else 'master'
                    else: # node.layer must be a UserNode
                        layer = node.layer.name if node.layer is not None else 'master'

                    img_display['type'] = 'show' if isinstance(node, ShowNode) else 'show'
                    img_display['image'] = image_surface
                    img_display['pos'] = self.get_position_from_size(image_surface.get_size(), transform, screen_size)
                    img_display['layer'] = layer
                    img_display['transition'] = {
                        'type': transition,
                        'duration': 2, # default duration in second (we don't handle custom transition so it's always 1 sec)
                        'animate': False,
                        'pos_anim': (0, 0), # Cannot be None to prevent error in display_with_transition
                        'last_pos': False, # This is to prevent from wrong usage of movein (ex: if we use a movein transition on the first show statement of the game)
                        'elapsed': 0 # for linear interpolation
                    }
                    img_display['tag'] = tag.name

                    # Before updating chainblock we check if layer already exist or not:
                    if layer not in self.layer_order_statements: # to keep a trace of order of inline-declaration of layers
                        self.layer_order_statements.append(layer)

                    # Checking if tag already exist and is used                
                    if self.search_tag_chainblock(tag.name, chainblock): # Already exist, image must be cleared
                        chainblock, last_pos = self.remove_img_obj(tag.name, chainblock)
                        if img_display['transition']['type'] == 'movein' and last_pos != img_display['pos']: # only useful for movein transition
                            # If img_display['transition']['pos'] == last_pos there is no point to the movein animation transition
                            img_display['transition']['last_pos'] = last_pos
                        # print('removed: ', tag)

                    chainblock.append(img_display)
       
    def generate_VN(self, debug=False):
        """
        Description
        -----------
        Initializes and runs the visual novel game loop using Pygame, displaying nodes and transitions.

        This function sets up the Pygame window, initializes the state machine, and handles user input
        to navigate through the game states (represented by the `state_machine`). It processes `KEYDOWN`
        events for left and right arrow keys to navigate through the visual novel, updates the screen based
        on the current state, and handles transitions between game elements (such as text and images).

        It also displays a gradient textbox at the bottom of the screen and updates the display each frame.

        Arguments
        ---------
        None

        Returns
        -------
        None
            This function runs an interactive loop, updating the display and responding to user input in real-time.
        """
        pygame.init()
        pygame.mixer.init() # for music
        WIDTH = 1200
        HEIGHT = 800
        screen_size = (WIDTH, HEIGHT) # sw, sh (WINDOW size)
        screen = pygame.display.set_mode(screen_size) 
        pygame.display.set_caption("Test")
        clock = pygame.time.Clock()

        # pygame.mixer.music.load("Tests-RenPy-Scripts\Execution-scripts\musics-test\E.S-Posthumus-Unstoppable.mp3")
        # pygame.mixer.music.play()

        # Textbox and gradient:
        c1 = (173, 216, 230, 240)  # Light blue
        c2 = (135, 206, 250, 200)  # Sky blue
        gradient =  Gradient(c1, c2)  
        container_surface = TextBox(WIDTH, 200, gr=gradient)
        container_surface.resize(WIDTH, 200, offset_x=30, offset_y=10, gr=gradient, flip_gradient=False)        

        self.create_state_machine(screen_size)
        
        self.idx = 0 
        if debug:
            print('\n\n########### DEBUGGING VISUAL NOVEL BEGIN ##################\n')
            print("current chainblock: ", end ="")
        self.pretty_list(self.state_machine[self.idx])
        running = True  
        pos_textbox = (0, HEIGHT - 200)
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        if self.idx < len(self.state_machine) - 1:
                            if debug:
                                print('pressed key right')
                            if not self.transition_ongoing: # We wait for transition to finish
                                self.clear_audio()
                                self.idx += 1
                                if debug:
                                    print("current chainblock: ", end ="")
                                self.pretty_list(self.state_machine[self.idx])
                            else:
                                if debug:
                                    print('transition ongoing - cannot pass to next state')
                    elif event.key == pygame.K_LEFT:
                        if self.idx > 0:                                
                            self.idx -= 1
                            if debug:
                                print('pressed key left')
                                print("current chainblock: ", end ="")
                            self.pretty_list(self.state_machine[self.idx])

            screen.fill(self.clear_color)
            self.display_state(screen, container_surface, pos_textbox)
            pygame.display.flip()
            clock.tick(FPS)  
            # break

        pygame.quit()
        sys.exit()   
    
class VisualNovelGenerator():
    def __init__(self, renpy_file, debug=False, debug_PATH=''):
        # Init the game:
        self.path_to_renpyfile = renpy_file # Used much later (during runtime execution)
        self.debug = debug
        self.file = None
        self.list_tokens = []
        self.tk = None # Tokenizer
        self.parser = None # Parser
        self.ast_tree = None 
        self.symbols_table = {} # Dictionnary initialise during Initialisation Phase (contains all top level ASTnode)
        self.labels_table = {} # Dictionnary initialise during Initialisation Phase (contains all label nodes), key = label name
        self.state_machine = {} # State machine for runtime game
        self.idx_state = 0 # To navigate inside state_machine
        
        # Load all ressources:
        self.step1_loadfile(renpy_file)
        self.step2_tokenizer()
        self.step3_parser()
        self.step4_initialize_master_node()

        if debug: 
            self.output_result(debug_PATH)

        self.step5_runtime()
        
    def output_result(self, debug_PATH):
        """
        Description
        -----------
        Writes the AST, symbols table, and labels table to text files for analysis.

        This function outputs the following files in the `outputs_file` directory:
        - `output_ast.txt`: The string representation of the AST.
        - `symbols_table.txt`: A formatted version of the symbols table.
        - `labels_table.txt`: A formatted version of the labels table.

        Arguments
        ---------
        None

        Returns
        -------
        None
        """
        with open(debug_PATH+"output_ast.txt", "w", encoding="utf-8") as f: # MasterNode is written in a file
            f.write(str(self.ast_tree))

        res = self.pretty_dict(self.symbols_table)
        with open(debug_PATH+"symbols_table.txt", "w", encoding="utf-8") as f: # We write all the labels in a file
            f.write(str(res))

        res = self.pretty_dict(self.labels_table)
        with open(debug_PATH+"labels_table.txt", "w", encoding="utf-8") as f: # We write all the top level definitions outisde labels in a file
            f.write(str(res))
        
    def pretty_dict(self, d: dict, parent_key=None):
        """
        Description
        -----------
        Formats and displays a nested dictionary with indentation and end-of-key markers.

        This function recursively formats a dictionary into a readable string, adding 
        indentation for nested dictionaries and appending 'end of <key>' after each 
        nested dictionary.

        Arguments
        ---------
        d : The dictionary to format.
        parent_key : The key of the current level (used for the 'end of' marker).

        Returns
        -------
        str: A formatted string representing the dictionary with proper indentation and end markers.
        """
        lines = ["{"]
        for k, v in d.items():
            key_str = repr(k)
            if isinstance(v, dict):
                nested = self.pretty_dict(v, parent_key=k)
                nested = textwrap.indent(nested, "  ")
                lines.append(f"  {key_str}: {nested},\n")
            else:
                lines.append(f"  {key_str}: {repr(v)},\n")
        lines.append("}" + (f"  # end of {repr(parent_key)}" if parent_key is not None else ""))
        return "\n".join(lines)

    def print_list_token(self):
        """
        Formats and displays a nested dictionary with indentation and end-of-key markers.

        This function recursively formats a dictionary into a readable string, adding 
        indentation for nested dictionaries and appending 'end of <key>' after each 
        nested dictionary.

        Arguments
        ---------
        d : The dictionary to format.
        parent_key : The key of the current level (used for the 'end of' marker).

        Returns
        -------
        str
            A formatted string representing the dictionary with proper indentation and end markers.
        """
        if not self.list_tokens:
            return

        ligne_idx = 1
        printed_line_num = False

        for e in self.list_tokens:
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
        """
        Description
        -----------
        Loads the contents of a Ren'Py script file into memory.

        This function opens the specified Ren'Py script file, reads its contents, 
        and stores the content in the `self.file` attribute.

        Arguments
        ---------
        renpy_file : The path to the Ren'Py script file to be loaded.

        Returns
        -------
        None
        """
        with open(renpy_file, 'r', encoding="utf-8") as file:
            self.file = file.read()

    def step2_tokenizer(self):
        """
        Description
        -----------
        Tokenizes the loaded Ren'Py script and stores the tokens found in a list.

        This function uses the `RPTokenizer` to tokenize the contents of the loaded 
        Ren'Py script file, storing the tokens in `self.list_tokens`. The tokenization 
        process continues until the end of the file is reached.

        If debugging is enabled, it prints all the tokens found.

        Arguments
        ---------
        None

        Returns
        -------
        None
        """
        self.tk = RPTokenizer(self.file)
        token = self.tk.tokenizer_from_file()
        while token != FILE_EOF:
            self.list_tokens.append(token)
            token = self.tk.tokenizer_from_file()

        if self.debug:
            print('\n\n########### PRINTING ALL THE TOKENS FOUND ##################\n')
            self.print_list_token()
            print('\n########### END OF TOKENS FOUND ##################\n')
            print()
            print()

    def step3_parser(self):
        """
        Description
        -----------
        Parses the tokenized Ren'Py script into an Abstract Syntax Tree (AST).

        This function uses the `MasterParser` to parse the list of tokens and 
        generates an AST representing the structure of the Ren'Py script. The resulting 
        AST is stored in `self.ast_tree`.

        Arguments
        ---------
        None

        Returns
        -------
        None
        """
        self.parser = MasterParser(self.list_tokens)
        self.ast_tree = self.parser.parse_renpy_file()

    def update_nested_table_image_node(self, table:dict, ast_node: ImageNode, img_path):
        """
        Description
        -----------
        Updates a nested table with the image path from an ImageNode.

        This function navigates through the `table` (a nested dictionary) using the tags 
        from the `ast_node.image_expression`, and adds or updates the image path for 
        the final tag. If a tag already exists, the image path is updated without overwriting 
        any existing data at higher levels in the nested structure.

        Arguments
        ---------
        table : The nested dictionary to update with the image path.
        ast_node : The AST node containing the image expression and image path.
        img_path : The path of the image to store in the nested table.

        Returns
        -------
        None
        """
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
        """
        Description
        -----------
        Updates a nested table with arguments from an AST node.

        This function navigates through the `table` (a nested dictionary) using the tags 
        from the `ast_node.image_expression`, and adds or updates the arguments for the 
        final tag. If a tag already exists, the arguments are updated without overwriting 
        any existing data at higher levels in the nested structure.

        The difference with update_nested_table_image_node is the type of information 
        we want to store at the end of the nested dictionnary.

        Arguments
        ---------
        table : The nested dictionary to update with the arguments.
        ast_node : The AST node containing the image expression and associated data.
        args : A dictionary of arguments to be stored in the nested table.

        Returns
        -------
        None
        """
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
    
    def verify_prior_declaration(self, ast_node):
        """
        Description
        -----------
        Verifies that all variables used in the given AST node are declared beforehand.

        This function verifies that all variables, image tags, and functions used in the provided AST node 
        have been declared beforehand. It checks the following types of nodes:

        - `DefineNode`: Ensures that any variables or functions defined within the node are previously declared in the symbol table.
        - `SceneNode`, `ShowNode`, and `HideNode`: Verifies that any tags (such as image tags) used in these nodes exist in the symbol table.
        - `TransitionNode`: Checks that the transition variable, if used, is declared.
        - `ReturnNode`: Verifies that any variable or function returned in the node is declared.
        - `JumpNode`: Ensures that the label being jumped to exists.
        - `DialogueNode`: Verifies that the speaker or any variables used in the dialogue have been declared.

        If any tag, variable, or function is used before being declared, a runtime error is raised, 
        indicating that the user who wrote the script made a mistake.

        Arguments
        ---------
        ast_node : The AST node to verify, which can be a `DefineNode`, `SceneNode`, `HideNode`, or `ShowNode`.

        Returns
        -------
        None
        """
        # Used by define node, scene node, hide node and show node and more to verify if tags used by these statement were declared or not.
        if isinstance(ast_node, DefineNode):
            if isinstance(ast_node.value, UserNode):
                if str(ast_node.value) not in [str(key) for key in self.symbols_table['define']]:
                    raise DetailedError(f'Runtime error with the statement {ast_node}. Cannot use a variable that had not been declared. Variable: {ast_node.value}')
            elif isinstance(ast_node.value, FunctionCallNode):
                user_node_list = ast_node.value.get_user_tokens()
                for user_token in user_node_list:
                    if str(user_token) not in [str(key) for key in self.symbols_table['define']]:
                        raise DetailedError(f'Runtime error with the statement {ast_node}. Cannot use a variable that had not been declared. Variable: {user_token}')

        elif isinstance(ast_node, SceneNode) or isinstance(ast_node, ShowNode) or isinstance(ast_node, HideNode):
            # First of all, we check for image_expression:
            if self.symbols_table['image'] is None:
                raise DetailedError(f'Runtime Error with the statement {ast_node}. Cannot use tags {ast_node.get_full_name()} that are not declared.')
            key = self.symbols_table['image'] # key is what we already studied
            try:
                for tag in ast_node.image_expression: # ast_node is what we are studying 
                    key = key[tag] 
                if 'image_path' not in key:
                    raise DetailedError(f'Runtime error with the statement {ast_node}. Tried to use a non-existent image tag: {ast_node.get_full_name()}')
            except:
                raise DetailedError(f'Runtime Error with the statement {ast_node}. Tried to use a non-existent image tag: {ast_node.get_full_name()}')

            # Then, we check for transition:
            # In this project custom transition declaration is not handled yet (define my_fade = Fade(2.0)). 

            # Finally, we check for layer: Custom layer are not declared with 'define' keyword, they are
            # declared during inline usage of SceneNode / ShowNode 
            # or HideNode and we never raise errors for them in this project. 
            
    
        elif isinstance(ast_node, TransitionNode):
            if isinstance(ast_node.transition, UserNode):
                if str(ast_node.transition.name) not in [str(key) for key in self.symbols_table['define']]:
                    raise DetailedError(f'Runtime error with the statement {ast_node}. Cannot use a variable that had not been declared. Variable: {ast_node.transition.name}')
            
        elif isinstance(ast_node, ReturnNode):
            if isinstance(ast_node.value, UserNode): 
                if str(ast_node.value) not in [str(key) for key in self.symbols_table['define']]:
                    raise DetailedError(f'Runtime error with the statement {ast_node}. Cannot use a variable that had not been declared. Variable: {ast_node.value}')

        elif isinstance(ast_node, JumpNode):
            # Getting all the label name that exist (not just the ones that have been stored in self.labels_table)
            if not isinstance(ast_node.label_name, UserNode): # We don't verify when label_name = 'start' keyword
                return
            all_label_names = []
            for node in self.ast_tree:
                if isinstance(node, LabelNode) and isinstance(node.label_name, UserNode): # ast_node is necessarily a UserNode
                    all_label_names.append(str(node.label_name.name))
            if str(ast_node.label_name.name) not in all_label_names:
                raise DetailedError(f'Runtime error with the statement {ast_node}. Cannot use a variable that had not been declared. Variable: {ast_node.label_name}')
    
        elif isinstance(ast_node, DialogueNode):
            if isinstance(ast_node.speaker, UserNode):
                if str(ast_node.speaker) not in [str(key) for key in self.symbols_table['define']]:
                    raise DetailedError(f'Runtime error with the statement {ast_node}. Cannot use a variable that had not been declared. Variable: {ast_node.speaker}')
            elif isinstance(ast_node.speaker, FunctionCallNode):
                user_node_list = ast_node.speaker.get_user_tokens()
                for user_token in user_node_list:
                    if str(user_token) not in [str(key) for key in self.symbols_table['define']]:
                        raise DetailedError(f'Runtime error with the statement {ast_node}. Cannot use a variable that had not been declared. Variable: {user_token}')

    def step4_label_body_initialize(self, ast_label_body: LabelNode):
        """
        Description
        -----------
        Initializes the body of a label, verifying and organizing various AST nodes into their respective categories 
        (e.g., 'scene', 'show', 'hide', 'play', 'dialogue', etc.) within the `labels_table` for further processing.

        This function performs the following tasks:

        - Ensures that the label name has not been used previously in the `labels_table`.
        - Iterates through the AST nodes associated with the label body, verifying prior declarations for each node.
        - Categorizes and stores nodes like `SceneNode`, `ShowNode`, `HideNode`, `PlayNode`, `StopNode`, `TransitionNode`, 
        `ReturnNode`, `JumpNode`, `DialogueNode`, and `StringNode` into their corresponding sections in the label's body.
        - Each section (e.g., 'scene', 'show', 'hide') is populated with a list of relevant AST nodes, and the proper arguments 
        (such as transform, layer, transition) are extracted and stored.
        - Ensures that the `with` statement, if present, is placed correctly, as it must follow certain other node types 
        (such as `scene`, `show`, or `hide`).

        Arguments:
        ----------
        ast_label_body: The AST node representing the label body to be initialized.

        Returns
        -------
        None
        """
        last_node_added = "" # Required only for 'with'
        # Check if label name has not already been used:
        if ast_label_body.label_name in self.labels_table:
            raise DetailedError(f'Runtime error. Cannot use a label name twice: {ast_label_body.label_name}')
        self.labels_table[ast_label_body.label_name] = {}
        label_body = self.labels_table[ast_label_body.label_name]
        for ast_node in ast_label_body:
            if isinstance(ast_node, SceneNode): #Ex: scene eileen happy blushing at center with transition 
                if 'scene' not in label_body:
                    label_body['scene'] = {} # Cannot be None by default or we will have an error
                    label_body['scene']['masternode'] = [] # Useful only for 'with' statement alone in label body

                self.verify_prior_declaration(ast_node)
                args = { 
                    'transform': getattr(ast_node, "transform", None),
                    'layer': getattr(ast_node, "layer", None),
                    'transition': getattr(ast_node, "transition", None)
                }
                self.update_nested_table(label_body['scene'], ast_node, args)
                label_body['scene']['masternode'].append(ast_node) 

            elif isinstance(ast_node, ShowNode):  
                if 'show' not in label_body:
                    label_body['show'] = {} # Cannot be None by default or we will have an error
                    label_body['show']['masternode'] = [] # Useful only for 'with' statement alone in label body
                
                self.verify_prior_declaration(ast_node)
                args = { 
                    'transform': getattr(ast_node, "transform", None),
                    'layer': getattr(ast_node, "layer", None),
                    'transition': getattr(ast_node, "transition", None)
                }
                self.update_nested_table(label_body['show'], ast_node, args)
                label_body['show']['masternode'].append(ast_node) 

            elif isinstance(ast_node, HideNode): #Ex: scene eileen happy blushing at center with transition 
                if 'hide' not in label_body:
                    label_body['hide'] = {} # Cannot be None by default or we will have an error
                    label_body['hide']['masternode'] = [] # Useful only for 'with' statement alone in label body
                
                self.verify_prior_declaration(ast_node)
                args = { 
                    'layer': getattr(ast_node, "layer", None),
                    'transition': getattr(ast_node, "transition", None)
                }
                self.update_nested_table(label_body['hide'], ast_node, args)
                label_body['hide']['masternode'].append(ast_node)

            elif isinstance(ast_node, PlayNode):
                if 'play' not in label_body:
                    label_body['play'] = [] # Cannot be None by default or we will have an error
                
                args = { 
                    'audio_type': getattr(ast_node, "audio_type", None),
                    'audio_file': getattr(ast_node, "audio_file", None),
                    'fadein': getattr(ast_node, "fadein", None),
                    'loop': getattr(ast_node, "loop", None)
                }
                label_body['play'].append(args) 

            elif isinstance(ast_node, StopNode): 
                if 'stop' not in label_body:
                    label_body['stop'] = [] # Cannot be None by default or we will have an error

                label_body['stop'].append(ast_node)

            elif isinstance(ast_node, TransitionNode):  
                # Must be preceed by 'scene', 'show', 'hide'
                node_type = ""
                if isinstance(last_node_added, SceneNode):
                    node_type = "scene"
                elif isinstance(last_node_added, ShowNode):
                    node_type = "show"
                elif isinstance(last_node_added, HideNode):
                    node_type = "hide"
                if node_type == "":
                    raise DetailedError(f'Runtime error. with statement {ast_node} must be preceed by either scene, show, hide statement instead of {last_node_added}')

                self.verify_prior_declaration(ast_node)
                args = {}
                if node_type != 'hide':
                    args = { 
                        'transform': getattr(label_body[node_type]['masternode'][-1], "transform", None),
                        'layer': getattr(label_body[node_type]['masternode'][-1], "layer", None),
                        'transition': getattr(ast_node, "transition", None)
                    }
                else:
                    args = { 
                        'layer': getattr(label_body['hide']['masternode'][-1], "layer", None),
                        'transition': getattr(ast_node, "transition", None)
                    }
                self.update_nested_table(label_body[node_type], label_body[node_type]['masternode'][-1], args)

            elif isinstance(ast_node, StringNode):
                if 'string' not in label_body:
                    label_body['string'] = [] # Cannot be None by default or we will have an error

                label_body['string'].append(ast_node)

            elif isinstance(ast_node, ReturnNode):
                if 'return' not in label_body:
                    label_body['return'] = [] # Cannot be None by default or we will have an error

                self.verify_prior_declaration(ast_node)
                label_body['return'].append(ast_node.value) 

            elif isinstance(ast_node, JumpNode):
                if 'jump' not in label_body:
                    label_body['jump'] = [] # Cannot be None by default or we will have an error

                self.verify_prior_declaration(ast_node)
                label_body['jump'].append(ast_node.label_name) 

            elif isinstance(ast_node, DialogueNode):
                if 'dialogue' not in label_body:
                    label_body['dialogue'] = [] # Cannot be None by default or we will have an error

                self.verify_prior_declaration(ast_node)
                label_body['dialogue'].append(ast_node)

            last_node_added = ast_node
          
    def step4_initialize_master_node(self):
        """
        Description
        -----------
        Initializes the master node by processing the AST tree and storing the corresponding statements in the symbol table.

        This function performs the following tasks:

        - Iterates through the AST tree to process various types of nodes (`DefineNode`, `ImageNode`, `SceneNode`, `ShowNode`, `HideNode`, 
        `PlayNode`, `StopNode`, `LabelNode`).
        - For each node, it verifies prior declarations using the `verify_prior_declaration` method to ensure that any referenced tags, 
        variables, or functions have been declared before use.
        - Adds each processed node to the relevant section of the `symbols_table`:
        - `DefineNode`: Stores the variable or function definition.
        - `ImageNode`: Stores image expressions.
        - `SceneNode`, `ShowNode`, `HideNode`: Stores scene-related data, including transformation, layer, and transition attributes.
        - `PlayNode`, `StopNode`: Stores play and stop instructions.
        - `LabelNode`: Processes labels and delegates further initialization to the `step4_label_body_initialize` method for label body processing.
        
        Arguments:
        ----------
        None

        Returns
        -------
        None
        """

        # Goal: Store all statements in a symbol node and check if a statement (whether inside a label or outside) is used before being initialised
        for ast_node in self.ast_tree:
            if isinstance(ast_node, DefineNode): # We are declaring a variable, no need to check if it's used before initialised 
                if 'define' not in self.symbols_table:
                    self.symbols_table['define'] = {} # Cannot be None by default or we will have an error

                # Before adding to symbols_table we check if the USER tokens used on right side of ASSIGN ('=') are declared or not. 
                # ast_node can be either a FunctionNode, User token or a string (we don't check if it's a string)
                self.verify_prior_declaration(ast_node)

                # We add it to symbols_table
                self.symbols_table['define'][ast_node.id] = ast_node.value # Define statement is now considered 'initialised'

            elif isinstance(ast_node, ImageNode): # Ex: ast_node.image_expression = ['eileen', 'happy', 'blushing']
                if 'image' not in self.symbols_table:
                    self.symbols_table['image'] = {} # Cannot be None by default or we will have an error

                img_path = ast_node.get_value() 
                self.update_nested_table_image_node(self.symbols_table['image'], ast_node, img_path) # image statement is now considered 'initialised'

            elif isinstance(ast_node, SceneNode): #Ex: scene eileen happy blushing at center with transition 
                if 'scene' not in self.symbols_table:
                    self.symbols_table['scene'] = {} # Cannot be None by default or we will have an error

                # Before adding to symbols_table we check if the tags used used are declared or not. 
                self.verify_prior_declaration(ast_node)

                # We add it to symbols_table
                args = { 
                    'transform': getattr(ast_node, "transform", None),
                    'layer': getattr(ast_node, "layer", None),
                    'transition': getattr(ast_node, "transition", None)
                }

                # Regarding transition, to simplify this project we simply don't handle them.
                self.update_nested_table(self.symbols_table['scene'], ast_node, args)

            elif isinstance(ast_node, ShowNode):  
                if 'show' not in self.symbols_table:
                    self.symbols_table['show'] = {} # Cannot be None by default or we will have an error
                
                # Before adding to symbols_table we check if the tags used used are declared or not. 
                self.verify_prior_declaration(ast_node)

                # We add it to symbols_table
                args = { 
                    'transform': getattr(ast_node, "transform", None),
                    'layer': getattr(ast_node, "layer", None),
                    'transition': getattr(ast_node, "transition", None)
                }
                self.update_nested_table(self.symbols_table['show'], ast_node, args)

            elif isinstance(ast_node, HideNode): #Ex: scene eileen happy blushing at center with transition 
                if 'hide' not in self.symbols_table:
                    self.symbols_table['hide'] = {} # Cannot be None by default or we will have an error

                # Before adding to symbols_table we check if the tags used used are declared or not. 
                self.verify_prior_declaration(ast_node)

                # We add it to symbols_table
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
                # We need to go through label body to see if anything requires initialisation
                self.step4_label_body_initialize(ast_node)

    def step5_runtime(self):
        """
        Description
        -----------
        Runs the visual novel by initializing the state machine and generating the game.

        This function performs the following tasks:
        - Initializes a `StateMachine` using the current `symbols_table`, `labels_table`, `ast_tree`, and the path to the Ren'Py file.
        - Calls the `generate_VN` method of the `StateMachine` to start the execution of the visual novel.
        - The `generate_VN` method is responsible for processing and rendering the visual novel, including the handling of debug mode if enabled.

        Arguments:
        ----------
        None

        Returns
        -------
        None
        """
        sM = StateMachine(self.symbols_table, self.labels_table, self.ast_tree, self.path_to_renpyfile)
        sM.generate_VN(debug=self.debug)
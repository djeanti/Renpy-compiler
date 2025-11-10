# Module that contains all AST structure I need for this project
import textwrap
from Error import DetailedError

# Base Node
class ASTNode:
    """Base class for all AST nodes."""
    pass

class LabelNode(ASTNode):
    """
    Custom AST node used to store information from a label statement in Ren'Py language.

    Attributes:
        label_name: The identifier of the label (e.g., 'start').
        body: List of AST nodes representing the statements inside the label.
    """
    def __init__(self, label, body=None):
        self.label_name = label              
        self.body = body or []               

    def get_next_label(self):
        """Return the name of the next label found in the first JumpNode of the body."""
        for node in self.body:
            if isinstance(node, JumpNode):
                if isinstance(node.label_name, KeywordNode):
                    return node.label_name.value
                else:
                    return node.label_name.name

    def __iter__(self):
        """Allow iteration over the node's children."""
        return iter(self.body)

    def __len__(self):
        """Return the number of child nodes."""
        return len(self.body)

    def __getitem__(self, index):
        """Allow index access like a list."""
        return self.body[index]
    
    def __repr__(self):
        """Return a readable string representation of the LabelNode."""
        body_repr = ",\n".join([repr(x) for x in self.body])
        body_repr = textwrap.indent(body_repr, "      ")
        return (
            "LabelNode(\n"
            f"  name = {repr(self.label_name)},\n"
            f"  body = [\n{body_repr}\n  ]\n"
            ")"
        )


class DefineNode(ASTNode):
    """
    Custom AST node used to store information from a define statement in Ren'Py language.

    Attributes:
        id: The identifier being defined.
        value: The value assigned to the identifier.
    """
    def __init__(self, id, value):
        self.id = id 
        self.value = value

    def __repr__(self):
        """Return a readable string representation of the DefineNode."""
        value_repr = repr(self.value)
        value_repr = textwrap.indent(value_repr, "    ")
        return (
            "DefineNode(\n"
            f"  id = {repr(self.id)},\n"
            f"  value = \n{value_repr}\n"
            ")"
        )

class ImageNode(ASTNode):
    """
    Custom AST node used to store information from an image statement in Ren'Py language.

    Attributes:
        image_expression: List containing the image name and optional tags (e.g., ['eileen', 'happy']).
        path: Optional explicit path to the image file.
        user_var: Optional variable referencing the image path.
    """
    def __init__(self, image_expression, string_path = None, user_var = None):
        self.image_expression = image_expression  # [img_name, tag1, tag2, ...]
        self.path = string_path or None
        self.user_var = user_var or None
    
    def get_value(self):
        """Return the image path, or the user variable referencing it if no direct path exists."""
        if self.path is not None:
            return self.path
        return self.user_var
    
    def __repr__(self, indent=2):
        """Return a readable string representation of the ImageNode."""
        indent_str = ' ' * indent
        expr_repr = '[' + ', '.join(repr(e) for e in self.image_expression) + ']'
        path_repr = ""
        if self.path is not None:
            path_repr = self.path.__repr__(indent=0) if hasattr(self.path, '__repr__') else repr(self.path)
        else:
            path_repr = self.user_var.__repr__(indent=0) if hasattr(self.user_var, '__repr__') else repr(self.user_var)
        return (
            f"ImageNode(\n"
            f"{indent_str}image_expression = {expr_repr},\n"
            f"{indent_str}path = {path_repr}\n"
            f")"
        )

class SceneNode(ASTNode):
    """
    Custom AST node used to store information from a scene statement in Ren'Py language.

    Attributes:
        image_expression: List containing the image name and optional tags (e.g., ['eileen', 'happy']).
        layer: Optional additional layer.
        transform: Optional transform applied to the image (e.g., 'left', 'right').
        transition: Optional transition effect applied to the image (e.g., 'fade').
    """
    def __init__(self, image_expression=None, transform=None, layer=None, transition=None):
        self.image_expression = image_expression or []  # [img_name, tag1, tag2, ...]
        self.transform = transform
        self.layer = layer
        self.transition = transition

    def get_full_name(self):
        """Return a string representing the full name of the image (e.g., 'img_name tag1 tag2') """
        full_nm = "<< "
        for tag in self.image_expression:
            full_nm += str(tag.name) + " "
        return full_nm[:-1] + " >>"
    
    def __repr__(self, indent=2):
        """Return a readable string representation of the SceneNode."""
        indent_str = ' ' * indent

        # image_expression is a list
        img_repr = "[" + ", ".join(
            t.__repr__(indent=0) if hasattr(t, '__repr__') else repr(t)
            for t in self.image_expression
        ) + "]"

        # transform
        if isinstance(self.transform, ASTNode):
            trans_repr = self.transform.__repr__(indent)
        elif self.transform is not None:
            trans_repr = repr(self.transform)
        else:
            trans_repr = "None"

        # layer
        if isinstance(self.layer, ASTNode):
            layer_repr = self.layer.__repr__(indent)
        elif self.layer is not None:
            layer_repr = repr(self.layer)
        else:
            layer_repr = "None"

        # transition
        if isinstance(self.transition, ASTNode):
            tran_repr = self.transition.__repr__(indent)
        elif self.transition is not None:
            tran_repr = repr(self.transition)
        else:
            tran_repr = "None"

        return (
            f"{self.__class__.__name__}(\n"
            f"{indent_str}image_expression = {img_repr},\n"
            f"{indent_str}transform = {trans_repr},\n"
            f"{indent_str}layer = {layer_repr},\n"
            f"{indent_str}transition = {tran_repr}\n"
            f")"
        )

class ShowNode(ASTNode):
    """
    Custom AST node used to store information from a show statement in Ren'Py language.

    Attributes:
        image_expression: List containing the image name and optional tags (e.g., ['eileen', 'happy']).
        layer: Optional additional layer.
        transform: Optional transform applied to the image (e.g., 'left', 'right').
        transition: Optional transition effect applied to the image (e.g., 'fade').
    """
    def __init__(self, image_expression=None, transform=None, layer=None, transition=None):
        self.image_expression = image_expression or []  # [img_name, tag1, tag2, ...]
        self.transform = transform
        self.layer = layer
        self.transition = transition

    def get_full_name(self):
        """Return a string representing the full name of the image (e.g., 'img_name tag1 tag2') """
        full_nm = "<< "
        for tag in self.image_expression:
            full_nm += str(tag.name) + " "
        return full_nm[:-1] + " >>"
    
    def __repr__(self, indent=2):
        """Return a readable string representation of the ShowNode."""
        indent_str = ' ' * indent

        # image_expression is a list
        img_repr = "[" + ", ".join(
            t.__repr__(indent=0) if hasattr(t, '__repr__') else repr(t)
            for t in self.image_expression
        ) + "]"

        # transform
        if isinstance(self.transform, ASTNode):
            trans_repr = self.transform.__repr__(indent)
        elif self.transform is not None:
            trans_repr = repr(self.transform)
        else:
            trans_repr = "None"

        # layer
        if isinstance(self.layer, ASTNode):
            layer_repr = self.layer.__repr__(indent)
        elif self.layer is not None:
            layer_repr = repr(self.layer)
        else:
            layer_repr = "None"

        # transition
        if isinstance(self.transition, ASTNode):
            tran_repr = self.transition.__repr__(indent)
        elif self.transition is not None:
            tran_repr = repr(self.transition)
        else:
            tran_repr = "None"

        return (
            f"{self.__class__.__name__}(\n"
            f"{indent_str}image_expression = {img_repr},\n"
            f"{indent_str}transform = {trans_repr},\n"
            f"{indent_str}layer = {layer_repr},\n"
            f"{indent_str}transition = {tran_repr}\n"
            f")"
        )
    
class HideNode(ASTNode):
    """
    Custom AST node used to store information from a hide statement in Ren'Py language.

    Attributes:
        image_expression: List containing the image name and optional tags (e.g., ['eileen', 'happy']).
        layer: Optional additional layer.
        transition: Optional transition effect (e.g., 'fade', 'dissolve').
    """
    def __init__(self, image_expression=None, layer=None, transition=None):
        self.image_expression = image_expression or []  
        self.layer = layer
        self.transition = transition

    def get_full_name(self):
        """Return a string representing the full name of the image (e.g., 'img_name tag1 tag2') """
        full_nm = "<< "
        for tag in self.image_expression:
            full_nm += str(tag.name) + " "
        return full_nm[:-1] + " >>"
    
    def __repr__(self, indent=2):
        """Return a readable string representation of the HideNode."""
        indent_str = ' ' * indent

        img_repr = "[" + ", ".join(
            t.__repr__(indent=0) if hasattr(t, '__repr__') else repr(t)
            for t in self.image_expression
        ) + "]"

        layer_repr = self.layer.__repr__(indent=indent) if self.layer else "None"
        tran_repr = self.transition.__repr__(indent=indent) if self.transition else "None"

        return (
            f"{self.__class__.__name__}(\n"
            f"{indent_str}image_expression = {img_repr},\n"
            f"{indent_str}layer = {layer_repr},\n"
            f"{indent_str}transition = {tran_repr}\n"
            f")"
        )

class KeywordNode(ASTNode):
    """
    Custom AST node used to store information from a keyword in Ren'Py language.

    Attribute:
        value: The keyword string (e.g., 'start').
    """

    def __init__(self, value):
        self.value = value
    
    def __iter__(self):
        """Allow iteration over the node's children."""
        return iter(self.value)
    
    def __repr__(self, indent=0):
        """Return a readable string representation of the KeywordNode."""
        ind = ' ' * 0
        return f"{ind}KeywordNode(value={self.value!r})"
    
class TransformNode(ASTNode):
    """
    Custom AST node used to store information regarding a transform applied to an image.

    Attribute:
        transform_name: The name of the transform (e.g., 'left', 'center').
    """
    def __init__(self, transform_name):
        self.transform_name = transform_name

    def __repr__(self, indent=5):
        """Return a readable string representation of the TransformNode."""
        indent_str = ' ' * indent
        return (
            f"TransformNode(\n"
            f"{indent_str}  transform_name = {repr(self.transform_name)}\n"
            f"{indent_str})"
        )

class FunctionCallNode(ASTNode):
    """
    Custom AST node used to store functions in Renpy.

    Attributes:
        name: The name of the function being called.
        args: Positional arguments for the function call (list of ASTNodes).
        kwargs: Keyword arguments for the function call (list of ASTNode).
    """
    def __init__(self, name, args=None, kwargs=None):
        self.name = name
        self.args = args if args else []
        self.kwargs = kwargs if kwargs else []

    def get_character_name(self):
        """
        Returns the first instance of StringNode (=character name) or UserNode (reference to character name) + color of associated character if it exist 
        when the function used is 'Character'
        """
        if self.name != 'Character':
            return None
        
        speaker = ""
        # Specific only to 'Character' function in renpy:
        for elem in self.args:
            if isinstance(elem, UserNode):
                speaker = elem
            elif isinstance(elem, StringNode):
                speaker = elem.value[1:-1] # returns the first string node
            
        # Try to find color among kwargs
        color = None
        for elem in self.kwargs:
            if isinstance(elem, AssignNode) and isinstance(elem.LHS, KeywordNode) and elem.LHS.value == 'color':
                if isinstance(elem.RHS, StringNode):
                    color = elem.RHS.value[1:-1]
                else:
                    raise DetailedError(f'Error in AST.py. Expected StringNode as RHS for color argument but got {elem.RHS} instead')
                
        return speaker, color
    
        
    def get_user_tokens(self):
        """
        Collect all UserNode instances in args and kwargs of this FunctionCallNode
        """
        user_tokens_list = []

        for elem in self.args:
            if isinstance(elem, UserNode):
                user_tokens_list.append(elem)
                
        for elem in self.kwargs:
            if isinstance(elem, AssignNode):
                if isinstance(elem.RHS, UserNode): # Only RHS of ASSIGN in kwargs contains UserNode, LHS is a keyword
                    user_tokens_list.append(elem.RHS)
                elif isinstance(elem, UserNode):
                    user_tokens_list.append(elem)

        return user_tokens_list

    def __repr__(self, indent=0):
        """Return a readable string representation of the FunctionCallNode."""
        ind = ' ' * indent
        s = f"{ind}FunctionCallNode(\n"

        # name indenté d'un niveau
        s += f"{ind}    name = {self.name!r},\n"

        # args sur une seule ligne
        args_repr = ", ".join(arg.__repr__(0) for arg in self.args)
        s += f"{ind}    args = [{args_repr}],\n"

        # kwargs
        # kwargs (if it's now a list)
        s += f"{ind}    kwargs = [\n"
        for kwarg in self.kwargs:
            kwarg_repr = kwarg.__repr__(indent + 8) if hasattr(kwarg, "__repr__") else repr(kwarg)
            s += f"{textwrap.indent(kwarg_repr, ' ' * (indent + 8))},\n"
        s += f"{ind}    ]\n"

        s += f"{ind})"
        return s

class AssignNode(ASTNode):
    """
    Custom AST node used to store instructions using '=' in Renpy.

    Attributes:
        LHS: The left-hand side of the assignment.
        RHS: The right-hand side of the assignment.
    """
    def __init__(self, LHS, RHS):
        self.LHS = LHS
        self.RHS = RHS

    def __getattribute__(self, name):
        return super().__getattribute__(name)
    
    def __repr__(self, indent=2):
        """Return a readable string representation of the AssignNode."""
        indent_str = ' ' * indent
        return (f'AssignNode(\n'
                f'{indent_str}LHS = {self.LHS.__repr__(indent + 2)},\n'
                f'{indent_str}RHS = {self.RHS.__repr__(indent + 2)}\n'
                f')')

class DialogueNode(ASTNode):
    """
    Custom AST node used to store a dialogue in Renpy.

    Attributes:
        speaker: The character or speaker of the dialogue (can be None for narration).
        text: The string content of the dialogue.
    """
    def __init__(self, speaker, text):
        self.speaker = speaker  # Can be a UserNode, or a function call node (Character)
        self.text = text        # StringNode
        
    def __getattribute__(self, name):
        return super().__getattribute__(name)

    def __repr__(self, indent=2):
        """Return a readable string representation of the DialogueNode."""
        indent_str = ' ' * indent
        return (f"DialogueNode(\n"
                f"{indent_str}speaker = {repr(self.speaker)},\n"
                f"{indent_str}text = {repr(self.text)}\n"
                f")")

class PlayNode(ASTNode):
    """
    Custom AST node used to store information regarding the 'play' instruction in Renpy.

    Attributes:
        audio_type: Type of audio ('music', 'sound', or 'voice').
        audio_file: The audio file or variable reference. 
        fadein: Optional fade-in duration in seconds.
        loop: Whether the audio should loop continuously.
    """
    def __init__(self, audio_type, audio_file, fadein=None, loop=False):
        self.audio_type = audio_type      # 'music', 'sound', 'voice'
        self.audio_file = audio_file      
        self.fadein = fadein              
        self.loop = loop                  

    def __repr__(self, indent=2):
        """Return a readable string representation of the PlayNode."""
        indent_str = ' ' * indent
        audio_file_repr = (
            self.audio_file.__repr__(indent=0)
            if hasattr(self.audio_file, '__repr__') else repr(self.audio_file)
        )
        fadein_repr = repr(self.fadein) if self.fadein is not None else "None"
        loop_repr = repr(self.loop)

        return (
            f"PlayNode(\n"
            f"{indent_str}audio_type = '{self.audio_type}',\n"
            f"{indent_str}audio_file = {audio_file_repr},\n"
            f"{indent_str}fadein = {fadein_repr},\n"
            f"{indent_str}loop = {loop_repr}\n"
            f")"
        )

class StopNode(ASTNode):
    """
    Custom AST node used to store information regarding the 'stop' instruction in Renpy.

    Attributes:
        audio_type: Type of audio to stop ('music', 'sound', or 'voice').
        fadeout: Optional fade-out duration in seconds.
    """
    def __init__(self, audio_type=None, fadeout=None):
        self.audio_type = audio_type  # 'music', 'sound', 'voice' or neither of these
        self.fadeout = fadeout        # float or None

    def __repr__(self, indent=2):
        """Return a readable string representation of the StopNode."""
        indent_str = ' ' * indent
        fadeout_repr = repr(self.fadeout) if self.fadeout is not None else "None"
        return (
            f"StopNode(\n"
            f"{indent_str}audio_type = '{self.audio_type}',\n"
            f"{indent_str}fadeout = {fadeout_repr}\n"
            f")"
        )

class ReturnNode(ASTNode):
    """
    Custom AST node used to store information regarding the 'return' instruction in Renpy.

    Attributes:
        value: Optional value or expression being returned.
    """
    def __init__(self, value=None):
        self.value = value  # None or UserNode

    def __repr__(self, indent=2):        
        """Return a readable string representation of the ReturnNode."""
        indent_str = ' ' * indent
        value_repr = (
            self.value.__repr__(indent=0) 
            if hasattr(self.value, '__repr__') else repr(self.value)
        ) if self.value is not None else "None"
        return (
            f"ReturnNode(\n"
            f"{indent_str}value = {value_repr}\n"
            f")"
        )

class JumpNode(ASTNode):
    """
    Custom AST node used to store information regarding the 'jump' instruction in Renpy.

    Attributes:
        label_name: The target label to jump to
    """
    def __init__(self, label_name):
        self.label_name = label_name  # USER token or IdentifierNode

    def __repr__(self, indent=2):
        """Return a readable string representation of the JumpNode."""
        indent_str = ' ' * indent
        label_repr = (
            self.label_name.__repr__(indent=0) 
            if hasattr(self.label_name, '__repr__') else repr(self.label_name)
        )
        return (
            f"JumpNode(\n"
            f"{indent_str}label_name = {label_repr}\n"
            f")"
        )

class TransitionNode(ASTNode):
    """
    Custom AST node used to store information regarding a transition in Renpy.

    Attributes:
        transition_name: The name of the transition (e.g., 'fade').
    """
    def __init__(self, transition_name):
        self.transition = transition_name 

    def __repr__(self, indent=2):
        """Return a readable string representation of the TransitionNode."""
        indent_str = ' ' * indent
        return (
            f"TransitionNode(\n"
            f"{indent_str}  transition_name = {repr(self.transition)}\n"
            f"{indent_str})"
        )
    
class LayerNode(ASTNode):
    """
    Custom AST node used to store information regarding a layer in Renpy.

    Attributes:
        layer_name: The name of the layer where content is shown.
    """
    def __init__(self, layer_name):
        self.layer_name = layer_name  

    def __repr__(self, indent=2):
        """Return a readable string representation of the LayerNode."""
        indent_str = ' ' * indent
        return (
            f"LayerNode(\n"
            f"{indent_str}  layer_name = {repr(self.layer_name)}\n"
            f"{indent_str})"
        )

class StringNode(ASTNode):
    """
    Custom AST node used to store information regarding a StringNode in Renpy.

    Attributes:
        value: The string value.
    """
    def __init__(self, value):
        self.value = value

    def __repr__(self, indent=0):
        """Return a readable string representation of the StringNode."""
        ind = ' ' * 0
        return f"{ind}StringNode(value={self.value!r})"

class UserNode(ASTNode):
    """
    Custom AST node used to store information regarding a user variable in Renpy.

    Attributes:
        name: The name of the identifier.
    """
    def __init__(self, name):
        self.name = name

    def __iter__(self):
        """Allow iteration over the node's children."""
        return iter(self.name)
    
    def __eq__(self, other):
        """Check equality with another UserNode based on the 'name' attribute."""
        if isinstance(other, UserNode):
            return self.name == other.name
        return False
    
    def __hash__(self):
        """Return a hash value based on the 'name' attribute for use in sets or dict keys."""
        return hash(self.name)
    
    def __repr__(self, indent=0):
        """Return a readable string representation of the UserNode."""
        ind = ' ' * 0
        return f"{ind}UserNode(name={self.name!r})"
    
class MasterNode(ASTNode):
    """
    Represents the root of the AST for a Ren'Py script.

    This node contains a list of child AST nodes of any type, 
    allowing the tree to represent the entire script hierarchy.

    Attributes:
        children: A list of all the nodes found in the renpy script.
    """
    def __init__(self, children=None):
        self.children = children or []

    def __iter__(self):
        """Allow iteration over the node's children."""
        return iter(self.children)

    def __len__(self):
        """Return the number of child nodes."""
        return len(self.children)

    def __getitem__(self, index):
        """Allow index access like a list."""
        return self.children[index]
    
    def __repr__(self):
        """Return a readable string representation of the MasterNode."""
        inner = "\n".join(
            textwrap.indent(repr(child), "  ") for child in self.children
        )
        return f"MasterNode(\n{inner}\n)"









# Module that contains all AST structure I need for this project
import textwrap

# Base Node
class ASTNode:
    """Base class for all AST nodes."""
    pass

class LabelNode(ASTNode):
    """
    Represents a label node in a Ren'Py AST.

    Attributes:
        label_name (str): The identifier of the label (e.g., 'start').
        body (list[ASTNode]): List of AST nodes representing the statements inside the label.
    """
    def __init__(self, label, body=None):
        self.label_name = label              
        self.body = body or []               

    def __repr__(self):
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
    Represents a variable or constant definition in a Ren'Py AST.

    Attributes:
        id: The identifier being defined (can be a string or ASTNode).
        value: The value assigned to the identifier (can be any ASTNode or literal).
    """
    def __init__(self, id, value):
        self.id = id 
        self.value = value

    def __repr__(self):
        value_repr = repr(self.value)
        # réindente toute la représentation du value pour l'aligner
        value_repr = textwrap.indent(value_repr, "    ")

        return (
            "DefineNode(\n"
            f"  id = {repr(self.id)},\n"
            f"  value = \n{value_repr}\n"
            ")"
        )

class ImageNode(ASTNode):
    """
    Represents an image declaration in a Ren'Py AST.

    Attributes:
        image_expression (list): List containing the image name and optional tags (e.g., ['eileen', 'happy']).
        path (StringNode or None): Optional explicit path to the image file.
        user_var (UserNode or None): Optional variable referencing the image path.
    """
    def __init__(self, image_expression, string_path = None, user_var = None):
        self.image_expression = image_expression  # [img_name, tag1, tag2, ...]
        self.path = string_path or None
        self.user_var = user_var or None
    
    def get_value(self):
        if self.path is not None:
            return self.path
        return self.user_var
    
    def __repr__(self, indent=2):
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
    Represents a `scene` instruction in a Ren'Py AST.

    Attributes:
        background (UserNode or StringNode): The main background for the scene.
        layer (UserNode): Optional additional layer.
        transform (IdentifierNode or None): Optional transform applied to the background (e.g., 'left', 'truecenter').
        transition (IdentifierNode or None): Optional transition effect (e.g., 'fade', 'dissolve').
    """
    def __init__(self, image_expression=None, transform=None, layer=None, transition=None):
        self.image_expression = image_expression or []  # list of strings / IdentifierNodes !!!!! First element is ALWAYS the 'name' and the others are 'tags'
        self.transform = transform
        self.layer = layer
        self.transition = transition

    def __repr__(self, indent=2):
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

class ShowNode(SceneNode):
    """
    Represents a 'show' statement in Ren'Py.
    Inherits everything from SceneNode because the syntax is identical.
    """
    def __init__(self, image_expression=None, transform=None, layer=None, transition=None):
        super().__init__(image_expression, transform, layer, transition)

class HideNode(ASTNode):
    """
    Represents a `hide` instruction in a Ren'Py AST.

    Attributes:
        background (UserNode or StringNode): The main background for the scene.
        layer (UserNode): Optional additional layer.
        transition (IdentifierNode or None): Optional transition effect (e.g., 'fade', 'dissolve').
    """
    def __init__(self, image_expression=None, layer=None, transition=None):
        self.image_expression = image_expression or []  # list of USER tokens
        self.layer = layer
        self.transition = transition

    def __repr__(self, indent=2):
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
    Represents a keyword in a Ren'Py AST.

    Attributes:
        value (str): The keyword string (e.g., 'define', 'scene').
    """

    def __init__(self, value):
        self.value = value
    
    def __repr__(self, indent=0):
        ind = ' ' * 0
        return f"{ind}KeywordNode(value={self.value!r})"
    
class TransformNode(ASTNode):
    """
    Represents a transform applied to a scene or image in a Ren'Py AST. Impossible to create custom transform (with 'define')

    Attributes:
        transform_name (can only be BUILTIN token): The name of the transform (e.g., 'left', 'center', or a custom transform).
    """
    def __init__(self, transform_name):
        self.transform_name = transform_name  # str or IdentifierNode

    def __repr__(self, indent=5):
        indent_str = ' ' * indent
        return (
            f"TransformNode(\n"
            f"{indent_str}  transform_name = {repr(self.transform_name)}\n"
            f"{indent_str})"
        )

class FunctionCallNode(ASTNode):
    """
    Represents a function or method call in a Ren'Py AST.

    Attributes:
        name (str): The name of the function being called.
        args (list): Positional arguments for the function call (list of ASTNodes or literals).
        kwargs (dict): Keyword arguments for the function call (mapping from str to ASTNode or literal).
    """
    def __init__(self, name, args=None, kwargs=None):
        self.name = name
        self.args = args if args else []
        self.kwargs = kwargs if kwargs else []

    def __repr__(self, indent=0):
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
    Represents an assignment operation in a Ren'Py AST.

    Attributes:
        LHS: The left-hand side of the assignment (typically a variable or target node).
        RHS: The right-hand side of the assignment (expression or value node).
    """
    def __init__(self, LHS, RHS):
        self.LHS = LHS
        self.RHS = RHS

    def __getattribute__(self, name):
        return super().__getattribute__(name)
    
    def __repr__(self, indent=2):
        indent_str = ' ' * indent
        return (f'AssignNode(\n'
                f'{indent_str}LHS = {self.LHS.__repr__(indent + 2)},\n'
                f'{indent_str}RHS = {self.RHS.__repr__(indent + 2)}\n'
                f')')

class PlayNode(ASTNode):
    """
    Represents an audio playback instruction in a Ren'Py AST.

    Attributes:
        audio_type (str): Type of audio ('music', 'sound', or 'voice').
        audio_file (str or IdentifierNode): The audio file or variable reference.
        fadein (float or None): Optional fade-in duration in seconds.
        loop (bool): Whether the audio should loop continuously.
    """
    def __init__(self, audio_type, audio_file, fadein=None, loop=False):
        self.audio_type = audio_type      # 'music', 'sound', 'voice'
        self.audio_file = audio_file      # USER token or IdentifierNode
        self.fadein = fadein              # float or None
        self.loop = loop                  # bool

    def __repr__(self, indent=2):
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
    Represents an audio stop instruction in a Ren'Py AST.

    Attributes:
        audio_type (str): Type of audio to stop ('music', 'sound', or 'voice').
        fadeout (float or None): Optional fade-out duration in seconds.
    """
    def __init__(self, audio_type, fadeout=None):
        self.audio_type = audio_type  # 'music', 'sound', 'voice'
        self.fadeout = fadeout        # float or None

    def __repr__(self, indent=2):
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
    Represents a return statement in a Ren'Py AST.

    Attributes:
        value: Optional value or expression being returned (None, a USER token, or an ASTNode).
    """
    def __init__(self, value=None):
        self.value = value  # None or USER token / expression

    def __repr__(self, indent=2):
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
    Represents a jump statement in a Ren'Py AST, directing execution to another label.

    Attributes:
        label_name: The target label to jump to (USER token or IdentifierNode).
    """
    def __init__(self, label_name):
        self.label_name = label_name  # USER token or IdentifierNode

    def __repr__(self, indent=2):
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
    Represents a transition effect in a Ren'Py AST. Also possible to create custom transition (with 'define') but they are stored as USER token.

    Attributes:
        transition_name (can only be a BUILTIN token): The name of the transition (e.g., 'fade', 'dissolve').
    """
    def __init__(self, transition_name):
        self.transition_name = transition_name  # str or IdentifierNode

    def __repr__(self, indent=2):
        indent_str = ' ' * indent
        # Add extra 2 spaces for inner content
        return (
            f"TransitionNode(\n"
            f"{indent_str}  transition_name = {repr(self.transition_name)}\n"
            f"{indent_str})"
        )
    
class LayerNode(ASTNode):
    """
    Represents a display layer in a Ren'Py AST. Also possible to create custom layer (with 'define') but they are stored as USER token.

    Attributes:
        layer_name (can only be BUILTIN token): The name of the layer where content is shown.
    """
    def __init__(self, layer_name):
        self.layer_name = layer_name  # str or IdentifierNode

    def __repr__(self, indent=2):
        indent_str = ' ' * indent
        # Add extra 2 spaces for inner content
        return (
            f"LayerNode(\n"
            f"{indent_str}  layer_name = {repr(self.layer_name)}\n"
            f"{indent_str})"
        )

class StringNode(ASTNode):
    """
    Represents a string literal in a Ren'Py AST.

    Attributes:
        value (str): The string value.
    """
    def __init__(self, value):
        self.value = value

    def __repr__(self, indent=0):
        ind = ' ' * 0
        return f"{ind}StringNode(value={self.value!r})"

class UserNode(ASTNode):
    """
    Represents a user-defined identifier in a Ren'Py AST.

    Attributes:
        name (str): The name of the identifier.
    """
    def __init__(self, name):
        self.name = name

    def __repr__(self, indent=0):
        ind = ' ' * 0
        return f"{ind}UserNode(name={self.name!r})"
    
class MasterNode(ASTNode):
    """
    Represents the root of the AST for a Ren'Py script.

    This node contains a list of child AST nodes of any type, 
    allowing the tree to represent the entire script hierarchy.

    Attributes:
        children (list[ASTNode]): The top-level statements or nodes in the script.
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
        inner = "\n".join(
            textwrap.indent(repr(child), "  ") for child in self.children
        )
        return f"MasterNode(\n{inner}\n)"
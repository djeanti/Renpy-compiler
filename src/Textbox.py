import pygame 
import re

def is_rgba(value):# Returns if value is a tuple of 4 values.
    """
    Description
    -----------
    Returns True if the value is a tuple containing 4 integers, each representing a color channel
    (Red, Green, Blue, Alpha), where each integer is between 0 and 255.

    Arguments
    ---------
    value: The value to check.

    Returns
    -------
    bool: True if value is a tuple of 4 integers, each in the range [0, 255], otherwise False.
    """
    return (
        isinstance(value, tuple) and
        len(value) == 4 and
        all(isinstance(c, int) and 0 <= c <= 255 for c in value)
    )

def scale_img(img:pygame.image, desired_width=0, desired_height=0):
    """
    Description
    -----------
    Scales the given image to the desired width and height while maintaining the aspect ratio 
    if one of the dimensions is set to 0. If both dimensions are provided, the image is scaled 
    to the exact size (aspect ratio may not be preserved).

    Arguments
    ---------
    img (pygame.image): The image to be scaled.
    desired_width (int, optional): The target width of the image. Defaults to 0.
    desired_height (int, optional): The target height of the image. Defaults to 0.

    Returns
    -------
    pygame.image: The scaled image.
    """
    # returns the scaled image. To keep ratio either desired_width must be 0 or desired_height must be 0
    if desired_height == 0 and desired_width == 0:
        return img
    elif desired_height != 0 and desired_width != 0: # Ratio is not necessarily kept
        return pygame.transform.scale(img, (desired_width, desired_height))
    elif desired_height == 0 and desired_width != 0: # Ratio is kept
        scale_ratio = img.get_width() / img.get_height()
        return pygame.transform.scale(img, (desired_width, int(desired_width / scale_ratio)))
    elif desired_height != 0 and desired_width == 0: # Ratio is kept
        scale_ratio = img.get_width() / img.get_height()
        return pygame.transform.scale(img, (int(desired_height / scale_ratio), desired_height))

class Gradient():
    """Class to create a Gradient color used in Textbox"""
    def __init__(self, color1, color2):
        if not is_rgba(color1) or not is_rgba(color2): # protection
            return 
        self.gradient_color1 = color1
        self.gradient_color2 = color2

    def create_vertical_gradient(self, width, height, flip:bool=False):
        """
        Description
        -----------
        Creates a vertical gradient surface where the color transitions from the top color to 
        the bottom color (or vice versa if `flip` is True). The gradient is drawn line by line 
        across the height of the surface.

        Arguments
        ---------
        width: The width of the gradient surface.
        height: The height of the gradient surface.
        flip (optional): If True, the gradient's color direction is flipped (i.e., 
                                the bottom color becomes the top color). Defaults to False.

        Returns
        -------
        pygame.Surface: A surface containing the vertical gradient.
        """
        top_color = self.gradient_color1
        bottom_color = self.gradient_color2
        if flip:
            top_color = self.gradient_color2
            bottom_color = self.gradient_color1
        gradient = pygame.Surface((width, height), pygame.SRCALPHA)
        for y in range(height):
            ratio = y / height
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            a = int(top_color[3] * (1 - ratio) + bottom_color[3] * ratio)
            pygame.draw.line(gradient, (r, g, b, a), (0, y), (width, y))
        return gradient
        
class TextBox(): 
    """Class for the textbox in game"""

    def __init__(self, width=0, height=0, color = (255, 100, 100, 220), offset_x = 10, offset_y=0, gr: Gradient | None = None, flip_gradient: bool=False):
        self.resize(width, height, color, offset_x, offset_y, gr, flip_gradient)

    def resize(self, width=0, height=0, color = (255, 0, 0, 220), offset_x = 10, offset_y=0, gr: Gradient | None = None, flip_gradient: bool=False): # On rescale self.image
        """
        Description
        -----------

        Resizes the textbox surface and applies a customizable gradient or tint to it. The function
        scales a frame image to match the specified width and height, and optionally applies a gradient
        or color tint for styling.

        Arguments
        ---------
        width (optional): The new width of the textbox. Defaults to 0.
        height (optional): The new height of the textbox. Defaults to 0.
        color (optional): A tuple representing the RGBA color to apply as a tint. Defaults to (255, 0, 0, 220).
        offset_x (optional): The horizontal offset used to adjust the position of the elements inside the textbox. Defaults to 10.
        offset_y (optional): The vertical offset used to adjust the position of the elements inside the textbox. Defaults to 0.
        gr (optional): A `Gradient` object for generating a gradient effect between two colors. Defaults to None.
        flip_gradient (optional): If True, the gradient is flipped vertically. Defaults to False.

        Returns
        -------
        None: This function modifies the instance variable `self.textbox` to the resized surface.
        """
        # protection
        if width <= 0 or height <= 0:
            return
        
        # Surface displayed on screen in the main loop:
        self.textbox = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Store basic attributes:
        self.width = width
        self.height = height
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.base_color = color
        self.gr_class = gr

        # Using a frame to give the textbox a stylized look
        if not hasattr(TextBox, "_panel_img"):
            TextBox._panel_img = pygame.image.load(r"../img/panel-031.png").convert_alpha()
        self.panel = TextBox._panel_img
        
        panel_w, panel_h = self.panel.get_size()
        texbox_img = self.panel

        # Split the frame into three parts to preserve its proportions when scaling
        texbox_left = texbox_img.subsurface(pygame.Rect(0, 0, panel_w // 3, panel_h))
        texbox_middle = texbox_img.subsurface(pygame.Rect(panel_w // 3, 0, panel_w // 3, panel_h))
        texbox_right = pygame.transform.flip(texbox_left, flip_x = True, flip_y = False)
        
        # Scaling each of the new surfaces dynamically (meaning that the textbox must adapt to window's current width)
        texbox_left = pygame.transform.smoothscale(texbox_left, (self.width//24, self.height - 2*self.offset_y)) 
        texbox_right = pygame.transform.smoothscale(texbox_right, (self.width//24, self.height - 2*self.offset_y)) 
        texbox_middle = pygame.transform.smoothscale(texbox_middle, (self.width - self.width//12 - 2 * self.offset_x, self.height - 2 * self.offset_y))

        # Gradient (gradient effect between two color) or Tint (1 single color)
        if gr is None:
            # We can't recolor the frame with Surface.fill() (it would disregard the frame), so we apply a tint instead
            tint_left = pygame.Surface(texbox_left.get_size(), pygame.SRCALPHA) # textbox_right est une copie de textbox_left donc pas besoin de tint
            tint_middle = pygame.Surface(texbox_middle.get_size(), pygame.SRCALPHA)
            tint_left.fill(self.base_color)  # couleur avec alpha
            tint_middle.fill(self.base_color)
                # Application of the tint below:
            texbox_left.blit(tint_left, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
            texbox_right.blit(tint_left, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
            texbox_middle.blit(tint_middle, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        else:
            gradient = gr.create_vertical_gradient(self.width, self.height, flip_gradient)
            texbox_left.blit(gradient, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
            texbox_right.blit(gradient, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
            texbox_middle.blit(gradient, (0,0), special_flags=pygame.BLEND_RGBA_MULT)

        # Blitting the three elements inside the image we will display
        self.textbox.blit(texbox_left, (self.offset_x, 0))     
        self.textbox.blit(texbox_middle, (self.width//24 + self.offset_x, 0))  
        self.textbox.blit(texbox_right, (self.width - self.width//24 - self.offset_x, 0))

    def draw(self, screen, pos=None):
        """
        Description
        -----------
        Draws the textbox on screen
        
        Arguments
        ---------
        None

        Returns
        -------
        None
        """
        if pos is None:
            pos = (0,0)
        screen.blit(self.textbox, pos)

    def complex_draw(self, screen, pos_textbox=None, text: str = None, speaker: str = None, font: pygame.font.Font | None = None, color: tuple = (0, 0, 0)):
        """
        Draws a textbox on the screen with optional speaker name and text wrapping.
        This function handles dynamic text wrapping, including new lines, text centering, and optionally displaying 
        a speaker's name above the textbox.

        Arguments:
        ---------
            screen: The screen or surface where the textbox and text will be drawn.
            pos_textbox (optional): The (x, y) position to place the textbox on the screen. Defaults to (0, 0).
            text (optional): The text to be displayed inside the textbox. If None, no text will be drawn.
            speaker (optional): The name of the speaker to be displayed above the textbox. If None, no speaker is displayed.
            font (optional): The font to be used for drawing the text. If None, the default font will be used.
            color (optional): The color of the text and speaker name, as an (R, G, B) tuple. Defaults to black (0, 0, 0).

        Returns:
        -------
            None: This function modifies the screen by drawing the textbox, speaker, and text onto it.
        """
        if pos_textbox is None:
            pos_textbox = (0, 0)

        # Blit the textbox itself
        screen.blit(self.textbox, pos_textbox)

        # Use default font if none provided
        if font is None:
            font = pygame.font.SysFont(None, 30)

        # Draw speaker if provided
        if speaker:
            font = pygame.font.SysFont(None, 40)
            speaker = speaker.capitalize()
            speaker_offset_x = 90
            speaker_offset_y = 25
            speaker_surf = font.render(speaker, True, color)
            speaker_pos = (pos_textbox[0] + speaker_offset_x, pos_textbox[1] + speaker_offset_y)
            screen.blit(speaker_surf, speaker_pos)
            font = pygame.font.SysFont(None, 30)

        if text is None:
            return  # No text to draw

        # Maximum width for text inside textbox
        max_width = self.width - 2 * self.offset_x

        # Normalize newlines - replace \\n with \n first
        text = text.replace("\\n", "\n")
        
        # Replace any combination of spaces and newlines with proper newlines
        # This handles: '\n \n', '\n  \n', '\n\n', '  \n  ', etc.
        text = re.sub(r'[ \t]*\n[ \t]*', '\n', text)
        
        # Now split by newlines to get paragraphs (empty strings represent blank lines)
        paragraphs = text.split("\n")

        # Initialize the list of lines
        lines = []

        for paragraph in paragraphs:
            # Strip only leading/trailing spaces from the paragraph
            paragraph = paragraph.strip()
            
            if paragraph == "":
                # Empty paragraph = blank line in output
                lines.append("")
            else:
                # Process this paragraph with word wrapping
                words = paragraph.split()
                current_line = ""
                
                for word in words:
                    # Try adding this word to the current line
                    test_line = current_line + (" " if current_line else "") + word
                    
                    if font.size(test_line)[0] <= max_width - 120:
                        # Word fits, add it to current line
                        current_line = test_line
                    else:
                        # Word doesn't fit, save current line and start new one
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                
                # Don't forget the last line of this paragraph
                if current_line:
                    lines.append(current_line)

        # Total height of text block
        line_height = font.get_linesize()
        total_height = line_height * len(lines)

        # Starting y position to vertically center the text in the textbox
        start_y = pos_textbox[1] + (self.height - total_height) // 2

        # Draw each line centered
        for i, line in enumerate(lines):
            if line == "":
                continue  # Skip empty lines (but they still take up space in the layout)
            text_surf = font.render(line, True, color)
            text_x = pos_textbox[0] + (self.width - text_surf.get_width()) // 2
            text_y = start_y + i * line_height
            screen.blit(text_surf, (text_x, text_y))
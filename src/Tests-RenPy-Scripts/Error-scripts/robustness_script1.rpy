# Top-level definitions
define e = Character("Eileen", color="#f0f")
define j = Character("John", color="#fff")
define v = Character("Villain", color="#f00")
image bg room = "room.png"
image bg park = "park.png"
image e happy = "e_happy.png"
image e sad = "e_sad.png"
image j happy = "j_happy.png"
image j sad = "j_sad.png"
image v angry = "v_angry.png"

# Start label
label start:
    scene bg room
    show e happy at center
    show j happy at left
    with fade
    play music "bgm.mp3" fadein 1.0 loop
    "The story begins."
    
    # Intentional error: showing image not defined
    show e happy at right
    # Error: 'e neutral' image not defined
    # Fix: define image e neutral = "e_neutral.png"

    jump middle

# Middle label
label middle:
    hide j happy
    show j sad at bottomright
    with dissolve
    "John looks sad now."
    
    # Intentional error: jump to missing label
    jump ending
    # Error: 'missing_label' does not exist
    # Fix: create label missing_label: before jump
    return

# Ending label
label ending:
    hide e happy
    hide j sad
    stop music fadeout 2.0
    "The story ends here."
    return

# Additional Python code with error:
# $ var_user = 5 
# Error: we don't handle '$' 
# Fix: add a show statement on magic_layer first, or add_layer in init

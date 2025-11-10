# Top-level definitions
define e = Character("Eileen", color="#f0f")
define j = Character("John", color="#fff")
define v = Character("Villain", color="#f00")
image bg street = "street.png"
image e happy = "e_happy.png"
image e neutral = "e_neutral.png"
image j happy = "j_happy.png"
image j neutral = "j_neutral.png"
image v angry = "v_angry.png"

# Start label
label start:
    scene bg street
    show e happy at left
    show j happy at right
    with fade
    play music "theme.mp3" fadein 0.5 loop
    "Eileen and John are on the street."

    # Intentional error: invalid image
    # show v neutral at center
    # Error: 'v neutral' image not defined
    # Fix: define image v neutral = "v_neutral.png"

    # Intentional error: invalid symbol usedused
    # $ x = undefined_var + 1

    jump middle

# Middle label
label middle:
    hide e happy
    show e neutral at bottomleft
    with dissolve
    "Eileen calms down."
    
    # Intentional error: invalid jump
    # jump nowhere
    # Error: 'nowhere' label does not exist
    # Fix: create label nowhere:

    return

# Ending label
label ending:
    hide j happy
    hide e neutral
    stop music fadeout 2.0
    "The street scene ends."
    return
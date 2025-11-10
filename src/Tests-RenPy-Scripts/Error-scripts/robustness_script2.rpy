# Top-level definitions
define hero = Character("Hero", color="#00f")
define villain = Character("Villain", color="#f00")
image bg castle = "castle.png"
image hero ready = "hero_ready.png"
image villain angry = "villain_angry.png"

# Start label
label start:
    scene bg castle
    show hero ready at center
    show villain angry at topleft
    with slide
    play music "battle.mp3" fadein 1.0 loop
    "The hero faces the villain in the castle."

    show hero ready onlayer unknown_layer

    jump encounter

# Encounter label
label encounter:
    show villain angry at center
    with dissolve
    # Intentional error: with statement alone must be preceeded by scene, show or hide statement
    # with sparkle
    # Error: 'sparkle' transition not defined

    "The battle begins!"
    
    return

# Ending label
label end:
    hide hero ready
    hide villain angry
    stop music fadeout 1.0
    return

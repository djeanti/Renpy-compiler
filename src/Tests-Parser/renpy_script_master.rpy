# Top-level definitions
define e = Character("Eileen")
define j = Character("John", image="img.png", color="#fff")
image bg room = "room.png"
image e happy = "e_happy.png"
image j neutral = "j_neutral.png"

# Label start
label start:
    scene bg room
    show e happy
    show j neutral
    with slidein
    play music "bgm.mp3" fadein 1.0 loop

    "Hello! Welcome to our story."

# Middle label
label middle:
    "This is the middle scene."
    show e happy at left
    "Eileen is on the left now."
    return

# Ending label
label ending:
    stop music fadeout 2.0
    "The story ends here."
    return

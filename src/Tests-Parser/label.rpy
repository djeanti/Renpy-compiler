label start:

    # Scene examples
    scene bg_forest
    scene hero_idle at center
    scene bg_city onlayer master
    scene hero_walk at left onlayer master with fade

    # Show / Hide
    show hero_idle
    show hero_walk at right
    hide hero_idle
    hide hero_walk

    # Play / Stop
    play music "bgm_theme.ogg"
    play sound "sfx_click.ogg" loop
    stop music

    # With transition
    with fade

    # Strings (narration)
    "Welcome to the forest."
    "The hero is ready to move."

 # Comments
    # This is a comment
    # Another comment

    # Jump / Return
    jump showow_ddjjd
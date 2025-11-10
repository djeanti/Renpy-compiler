define var_useless1 = 'Eileen'
define var_useless2 = var_useless1
define eileen = Character(var_useless2, color="#4b1630")
define john = Character("John", color="#19572a")

define bgm_romance_varUseless0 = "musics-test/E.S-Posthumus-Unstoppable.ogg"
define bgm_romance_varUseless1 = bgm_romance_varUseless0
define bgm_romance_varUseless2 = bgm_romance_varUseless1
define bgm_romance_varUseless3 = bgm_romance_varUseless2

define eileen_voice1 = "musics-test/eileen_voice1.mp3"
define eileen_voice2 = "musics-test/eileen_voice2.mp3"
define eileen_voice3 = "musics-test/eileen_voice3.mp3"
define eileen_voice4 = "musics-test/eileen_voice4.mp3"
define eileen_voice5 = "musics-test/eileen_voice5.mp3"
define eileen_voice6 = "musics-test/eileen_voice6.mp3"
define eileen_voice7 = "musics-test/eileen_voice7.mp3"
define eileen_voice8 = "musics-test/eileen_voice8.mp3"
define eileen_voice9 = "musics-test/eileen_voice9.mp3"

define john_voice1 = "musics-test/john_voice1.mp3"
define john_voice2 = "musics-test/john_voice2.mp3"
define john_voice3 = "musics-test/john_voice3.mp3"
define john_voice4 = "musics-test/john_voice4.mp3"
define john_voice5 = "musics-test/john_voice5.mp3"
define john_voice6 = "musics-test/john_voice6.mp3"

define bgm_romance = bgm_romance_varUseless2
define bell = "music.mp3"

image bg library = "images-test/bg_library.jpg"       
image bg street night = "images-test/bg_street_night.jpg"        

image eileen happy = "images-test/eileen_happy.png"         
image eileen surprised = "images-test/eileen_suprised.png"  
image eileen smug = "images-test/eileen_smug.png" 
image eileen blushing = "images-test/eileen_blushing.png"

image john neutral = "images-test/john_neutral.png"         
image john happy = "images-test/john_smiling.png"         
image john bigsmile = "images-test/john_bigsmile.png"         

label start:
    "Welcome to this simple Renpy interpreter. Use only the right arrow key to advance through the story of this short visual novel about love, and the left arrow key to go back and revisit previous scenes. Enjoy the experience! The credentials will be revealed at the end of the story.\n\n Press right key to begin!"
    play music bgm_romance fadein 1.0
    scene bg library with fade 
    show eileen happy at center with fade
    show john happy at right with dissolve

    play voice eileen_voice1
    # stop voice fadeout 1.0 # value of fadeout must always be a float, integer not supported
    eileen "John! what are you doing here?"     
    play voice john_voice1                                      
    john "I am looking for a book."

    show eileen happy with dissolve
    play voice eileen_voice2
    eileen "I didn’t know you were a library kind of guy"

    show john bigsmile at right
    play voice john_voice2
    john "I’m not, usually. But it’s peaceful here... and it’s always better when you’re around."

    show eileen blushing at left with movein
    play voice eileen_voice3
    eileen "You really don’t hold back with the compliments, do you?"

    play voice eileen_voice4
    show eileen happy at left with movein
    show john happy at right
    eileen "By the way, you left your key in the classroom earlier. Better grab it before someone freaks out when they get home."
    play voice john_voice3
    john "Ah, right. I won't forget them this time. Thanks for reminding me."

    jump street_scene

label street_scene:
    scene bg street night with fade
    # play music bgm_romance fadein 1.0
    show john happy at right
    play voice john_voice4
    john "Eileen! Wait!"
    play voice eileen_voice5
    show eileen surprised at center
    eileen "John? My gosh, it's so late! What are you doing out here? I thought you were already home!"

    show john bigsmile at right
    play voice john_voice5
    john "I can’t keep pretending it anymore... I like you, Eileen!"

    show eileen blushing at left with movein
    play voice eileen_voice6
    eileen "Oh, John… I didn’t expect this. I… I don’t know what to say."

    play voice eileen_voice7
    eileen "You’re a very very good friend, but… I don’t feel the same."

    show john neutral at right
    play voice john_voice6
    john "... For real?"

    show eileen happy at left
    play voice eileen_voice8
    eileen "Yeah, for real, John. I think it’s best this way."

    play voice eileen_voice9
    eileen "But don't worry, we're still friends!"
    # play sound bell
    stop music fadeout 2.0
    "The street fell silent, but John heard the pain in his heart. Yet, even in silence, there’s a lesson waiting for us to find. Be kind to yourself and to others."
    "The music and images used in this project does not belong to me. Character images were generated with the framework Character Creator made by Sutemo. This is a non-commercial project.\n Thank you for using my RenPy interpreter!"
    return

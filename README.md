# mtrixrain
## Couple of python3 scripts to make it rain

theone.py creates a matrix rain on a command prompt. --cipher command feeds some messages that can be embeded into the rain for fun

There are four versions of the file. All of them read and create the buffer to display on the screen the same way. 

The difference is in rendering. 

# asyncio/theone.py:

On Windows requires the python curses library 'pip install windows-curses'. I used version 2.3.0

python --cipher "FollowTheWhiteRabbit Neo Trinity"  --password "SomeGimmickPassword"

This renders a colored rain on the command prompt using ncurses. Is able to automatically detect console dimensions, and is very smooth. 

# ncurses/theone.py:

On Windows requires the python curses library 'pip install windows-curses'. I used version 2.3.0

python --cipher "FollowTheWhiteRabbit Neo Trinity" 

This renders a colored rain on the command prompt using ncurses. Is able to automatically detect console dimensions, and is very smooth. 


# color/theone.py 

Requires termcolor library on Windows and Linux 'pip install termcolor'. I used version 1.1.0. 

This renders a colored rain. However, relies on windows and linux clear screen commands to refresh the screen. 

Rendering is done by clearing the screen and displaying a string buffer to stdout. 

Warning: The rain is jerky and creates flashes. 

This also requires caller to provide the dimensions of the console. On windows, this can be obtained by right clicking the console title and looking for width and height in layout. 

python theone.py --width 346 --height 88 --cipher "FollowTheWhite
Rabbit Neo Trinity Morpheus Dorothy Kansas"


# nocolor/theone.py:

Requires no library in linux or windows. This renders a black and white rain. 

Rendering is done by clearing the screen and displaying a string buffer to stdout. 

Warning: The rain is jerky and creates flashes. 

This also requires caller to provide the dimensions of the console. On windows, this can be obtained by right clicking the console title and looking for width and height in layout. 

python theone.py --width 346 --height 88 --cipher "FollowTheWhite
Rabbit Neo Trinity Morpheus Dorothy Kansas"






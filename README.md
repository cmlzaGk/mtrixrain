# mtrixrain
## Couple of python3 scripts to make it rain


# theone_ncurses.py

Requires python curses library. 

On Windows requires the python curses library 'pip install windows-curses'. I used version 2.3.0

python theone_ncurses.py  --password "SomeGimmickPassword"

# theone.py:

This requires no third party library. 

However, it requires user to set width and height manually through command parameters

This can be obtained by right clicking the terminal title, select properties, layout and Window Size. 

python theone.py --width 111 --height 28

If terminal supports VT100 escape sequences then vt100 can be used 

python theone.py --width 111 --height 28 --vt100 --color


## Disregard the sub-folders. They are different versions I was trying.


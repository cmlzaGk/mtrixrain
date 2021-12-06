# mtrixrain
## Couple of python3 scripts to make it rain


# theone_ncurses.py

Requires Python3. 

Windows - requires the python curses library 'pip install windows-curses'. I used version 2.3.0
Linux - no third party requirements

python theone_ncurses.py  --password "SomeGimmickPassword"

This [Video](https://www.youtube.com/watch?v=uJwc8n0OnQE) shows a sample output captured on Windows cmd.

# theone.py:

Requires Python3. 

Windows and Linux - no third party requirements

However, it requires user to set width and height manually through command parameters

This can be obtained by right clicking the terminal title, select properties, layout and Window Size. 

python theone.py --width 111 --height 28

If terminal supports VT100 escape sequences then vt100 can be used 

python theone.py --width 111 --height 28 --vt100 --color




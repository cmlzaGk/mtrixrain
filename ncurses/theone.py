##### Author: Rishi Maker
##### 
import argparse
import os
import random
import sys
import time
import curses

# Gets overwritten by argument parser
WIDTH = 130
HEIGHT = 36

def set_global_height_width(height, width):
    global HEIGHT, WIDTH
    HEIGHT, WIDTH = height, width

### https://stackoverflow.com/questions/1477294/generate-random-utf-8-string-in-python
### Useful trick to generate a unicode alphabet set
### saved globally in Alphabet

include_ranges = [
    ( 0x0023, 0x0026 ),
    ( 0x0028, 0x007E ),
    ( 0x00A1, 0x00AC ),
    ( 0x00AE, 0x00FF ),
    ( 0x0100, 0x017F ),
    ( 0x0180, 0x024F ),
    ( 0x2C60, 0x2C7F ),
    ( 0x16A0, 0x16F0 ),
    ( 0x0370, 0x0377 ),
    ( 0x037A, 0x037E ),
    ( 0x0384, 0x038A ),
    ( 0x038C, 0x038C ),
]


ALPHABETS = [
    chr(code_point) for current_range in include_ranges
        for code_point in range(current_range[0], current_range[1] + 1)
]

def get_random_unicode(length):
    return (''.join([random.choice(ALPHABETS) for i in range(length)]))

class MessageGenerator:
    '''
        Helper class to create messages that are shown on screen vertifically
    '''
    def __init__(self, ciphers):
        self.ciphers = ciphers.split()
        self.ciphermessages = [''.join(reversed(x)) for x in self.ciphers]
        #self.ciphermessages = self.ciphers

    def get_random_cipher(self):
        return random.choice(self.ciphermessages)

    def generate_message(self, length):
        ''' generates a random message of atleast len length '''
        return get_random_unicode(length) if 1 < random.randint(0,100) else (get_random_unicode(length) + self.get_random_cipher() +  get_random_unicode(length))


class MessageChannel:
    '''
        A MessageChannel is basically a vertical line on the screen and the class is able to send endlessmessages if scrolled
        self._message is the buffer that contains messages from the matrix
        0 to self._idx is the part of the _message that has scrolled off the screen
        self._idx to HEIGHT is displayed on the screen 
        when self._idx reaches HEIGHT the self._message is moved left, self._idx is reset and new messages from the matrix are queued
    '''
    def __init__(self, messagegenerator):
        self._message = None
        self._idx = 0
        self.messagegenerator = messagegenerator
        self._populate_message(' ' * HEIGHT)

    def _populate_message(self, head):
        ''' 
            get new messages from the matrix. Most of the times the messages contain blanks
        '''
        self._idx = 0 
        self._message = head
        while len(self._message) <= 2 * HEIGHT:
            self._message += (self.messagegenerator.generate_message(random.randint(1,HEIGHT)) if 20 > random.randint(0,100) else ' ' * random.randint(0, HEIGHT))

    def scroll(self):
        '''
           scroll a character 
        '''
        self._idx += 1
        if self._idx >= HEIGHT:
            self._populate_message(self._message[self._idx:])

    @property
    def message(self):
        return self._message[self._idx:]

class ChannelMessageDrainer:
    '''
        An iterator to read a channel message one character at a time without scrolling
        It has a special property that tells if the last character is part of a cipher message from the matrix
    '''
    def __init__(self, channel):
        self._channel = channel
        self._message = None

    def __iter__(self):
        self._message = self._channel.message
        self._idx=0
        self._superencodedtill = -1
        return self

    def is_part_of_cipher_message(self):
        return self._idx <= self._superencodedtill

    def __next__(self):
        '''
            returns the next character from the matrix channel
        '''
        # has a bug .. is ineffecient and does not handle cases where one of the search messages is a prefix of another
        for superencoded in self._channel.messagegenerator.ciphermessages:
            if(self._message[self._idx:].startswith(superencoded)):
                self._superencodedtill = self._idx + len(superencoded)

        s = self._message[self._idx]
        self._idx += 1
        return s

class Matrix:
    def __init__(self, messagegenerator):
        self._channels = [MessageChannel(messagegenerator) for i in range(WIDTH)]
        self._drainers = [ChannelMessageDrainer(ch) for ch in self._channels]

    def get_screen_and_scroll(self):
        '''
            Create a string object that represents whats displayed on the screen
            each line is made up of characters of respective channel for the position
            reverse the string at the end to create an effect that messages are scrolling down

            if something is part of a ciphermessage, append '!' to it
            ! is never part of the matrix channel messages
            The caller removes ! and handles color coding based on positions of !
        '''
        s = ''
        drainers = [iter(d) for d in self._drainers]
        for h in range(HEIGHT):
            for d in drainers:
                s += next(d)
                if d.is_part_of_cipher_message():
                    s += '!'
            s += '\n'
        for ch in self._channels:
            # dont scroll every channel, this creates an effect of different vertical speeds
            if 60 > random.randint(0,100):
                ch.scroll()
        return ''.join(reversed(s))

def main(stdscr, args):

    stdscr.clear()
    height, width = stdscr.getmaxyx()

    if args.width is not None:
        width = args.width
    if args.height is not None:
        height = args.height

    height, width = height-2, width-1

    set_global_height_width(height, width)

    sys.stderr.write('dimensions = {}\n'.format(stdscr.getmaxyx()))
    sys.stderr.write('HEIGHT = {} WIDTH = {} \n'.format(HEIGHT, WIDTH))

    cipher = args.cipher

    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)


    mg = MessageGenerator(cipher)
    matrix = Matrix(mg)

    for i in range(500):
        stdscr.move(0,0)
        matrix_screen = matrix.get_screen_and_scroll()
        if False:
            dm = matrix_screen.replace('!','')
            stdscr.addstr(0, 0, dm, curses.color_pair(1))
            stdscr.refresh()
        else:
            dm = matrix_screen.split('!')
            for xm in dm:
                x,y =  stdscr.getyx()
                head, tail = xm[:1], xm[1:]

                stdscr.addstr(x, y, head, curses.color_pair(2) | curses.A_BOLD )
                x,y =  stdscr.getyx()
                stdscr.addstr(x, y, tail, curses.color_pair(1) | curses.A_BOLD)
                stdscr.refresh()
        time.sleep(0.008)
    curses.endwin()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Matrix Rain')
    parser.add_argument('--width', metavar='Width', type=int, required=False, help='the width of screen. Look for Window Size in CMD Layout Properties')
    parser.add_argument('--height', metavar='Height', type=int, required = False, help='the height of screen. Look for Window Size in CMD Layout Properties')
    parser.add_argument('--cipher', metavar='Cipher', type=str, required = True, help='white space seperate list of words to encode into matrix')
    args = parser.parse_args()

    curses.wrapper(main, args)

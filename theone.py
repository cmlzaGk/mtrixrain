#
# Author: Rishi Maker
#
import argparse
import os
import random
import sys
import time

# Gets overwritten by argument parser
WIDTH = 130
HEIGHT = 36

CLEAR_COMMAND = 'cls' if os.name == 'nt' else 'clear -x'

### https://stackoverflow.com/questions/1477294/generate-random-utf-8-string-in-python
### Useful trick to generate a unicode alphabet set
### saved globally in Alphabet

include_ranges = [
    ( 0x00A1, 0x00AC ),
    ( 0x00AE, 0x00FF ),
    ( 0x0100, 0x017F ),
    ( 0x0180, 0x024F ),
    ( 0x2C60, 0x2C7F ),
    ( 0x0370, 0x0377 ),
    ( 0x037A, 0x037E ),
    ( 0x0384, 0x038A ),
    ( 0x038C, 0x038C )
]

#include_ranges = [ ( 0x3041, 0x3096) ]

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
        return random.choice(self.ciphermessages) if len(self.ciphermessages) else ''

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

class Matrix:
    def __init__(self, messagegenerator):
        self._channels = [MessageChannel(messagegenerator) for i in range(WIDTH)]

    def get_screen_and_scroll(self, showcolor):
        '''
            Create a string object that represents whats displayed on the screen
            each line is made up of characters of respective channel for the position
            reverse the string at the end to create an effect that messages are scrolling down
        '''
        s = ''
        drainers = [iter(ch.message) for ch in self._channels]
        #keep a buffer of whether the last message was a space
        lastmessage = [None for ch in self._channels]
        for h in range(HEIGHT):
            for idx,d in enumerate(drainers):
                message = next(d)
                if showcolor and lastmessage[idx] and lastmessage[idx].isspace() and not message.isspace():
                    s += 'm29[\033{}m69[\033'.format(message)
                else:
                    s += message
                lastmessage[idx] = message
            s += '\n'
        for ch in self._channels:
            # dont scroll every channel, this creates an effect of different vertical speeds
            if 60 > random.randint(0,100):
                ch.scroll()
        return ''.join(reversed(s))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Matrix Rain')
    parser.add_argument('--width', metavar='Width', type=int, required=True, help='the width of screen. Look for Window Size in CMD Layout Properties')
    parser.add_argument('--height', metavar='Height', type=int, required = True, help='the height of screen. Look for Window Size in CMD Layout Properties')
    parser.add_argument('--cipher', metavar='Cipher', type=str, required = False, help='white space seperate list of words to encode into matrix')
    parser.add_argument('--vt100', dest='vt100', required=False, action='store_true', help="Use VT100 codes")
    parser.add_argument('--color', dest='color', required=False, action='store_true', help="Print Colored Rain (Only works with --vt100)")

    args = parser.parse_args()
    WIDTH = args.width - 1
    HEIGHT = args.height - 2
    cipher = args.cipher or ''
    vt100 = args.vt100 or False
    usecolor = args.color or False


    mg = MessageGenerator(cipher)
    matrix = Matrix(mg)
    while True:
        matrix_screen = matrix.get_screen_and_scroll(vt100 and usecolor)
        if vt100:
            sys.stdout.write("\033[H\033[J{}".format(matrix_screen))
        else:
            os.system(CLEAR_COMMAND)
            sys.stdout.write(matrix_screen)
        sys.stdout.flush()
        time.sleep(.1)

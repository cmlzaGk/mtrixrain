#
# Author: Rishi Maker
#
import argparse
import asyncio 
import curses
import sys

from collections import deque
from curses import wrapper, init_pair
from enum import Flag, auto
from random import randint, choice

RENDER_DELAY = 0.04
CHANNEL_DELAY = 0.08
FAST_CHANNEL_DELAY = 0.0001


class EncodingAttr(Flag):
    '''
        Properties that an encoded character can have.
        Some are set from Matrix, Some are processed by MessageChannel
        These Properties dictatate how the Encoded character is rendered.
    '''
    HEAD = auto() 
    CIPHER = auto()
    DANGER = auto()
    NORMAL = auto()

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


#########################
### Blame: https://www.oreilly.com/library/view/python-cookbook/0596001673/ch05s19.html
### Added Async support
#########################
class RingBuffer:
    """ class that implements a not-yet-full buffer """
    def __init__(self,size_max):
        self.max = size_max
        self.data = []
        self.cur = None
        self._lock = asyncio.Lock()

    class __Full:
        """ class that implements a full buffer """
        async def append(self, x):
            """ Append an element overwriting the oldest one. """
            async with self._lock:
                self.data[self.cur] = x
                self.cur = (self.cur+1) % self.max

        async def get(self):
            """ return list of elements in correct order """
            async with self._lock:
                return self.data[self.cur:]+self.data[:self.cur]

        async def peek(self):
            """ return last element from the RingBuffer """
            async with self._lock:
                last = self.max-1 if self.cur == 0  else self.cur - 1
                return self.data[last]


    async def append(self,x):
        """append an element at the end of the buffer"""
        async with self._lock:
            self.data.append(x)
            self.cur = self.cur + 1 if self.cur is not None else 0
            if len(self.data) == self.max:
                self.cur = 0
                # Permanently change self's class from non-full to full
                self.__class__ = self.__Full

    async def get(self):
        """ Return a list of elements from the oldest to the newest. """
        async with self._lock:
            return self.data.copy()

    async def peek(self):
        """ 
            return last element from the RingBuffer 
        """
        async with self._lock:
            return self.data[self.cur] if self.cur is not None else None


class MessageGenerator:
    '''
        This class generates random characters. 
        It randomly encodes the ciphers in the characters
        density is a value between 0 to 100 which determines how much of the message is characters vs space

        A message is made up tuple of (UnicodeCharacter, Attributes).
    '''
    def __init__(self, ciphers, density):
        self.ciphers = ciphers.split() if ciphers else []
        self.ciphermessages = [''.join(reversed(x)) for x in self.ciphers]
        self.density = density
        #self.ciphermessages = self.ciphers

    def _new_random_cipher(self):
        return [(c, EncodingAttr.CIPHER) for c in choice(self.ciphermessages)] if len(self.ciphermessages) else []

    @staticmethod
    def new_random_unicode(length):
        b = [(choice(ALPHABETS), EncodingAttr.NORMAL) for i in range(length)]
        if 0 == randint(0,50):
            problem_id = randint(0,len(b)-1)
            b[problem_id] = b[problem_id][0], EncodingAttr.DANGER
        return b

    def new_space_message(self, length):
        return [(' ', EncodingAttr.NORMAL) for i in range(length)]

    def new_message(self, channelid, length):
        ''' generates a random message of *around* len length. '''

        buff = []
        while len(buff) <= length:
            buff.extend(MessageGenerator.new_random_unicode(randint(1, length)) if self.density > randint(0,100) else self.new_space_message(randint(1,length)))
            # generate ciphers maybe
            if 1 >= randint(0,1000):
                buff.extend(self._new_random_cipher())
                buff.extend(MessageGenerator.new_random_unicode(randint(1, int(length/3))))
        return buff

class MatrixChannel:
    '''
        A Matrix Channel represents a vertical line on the screen. 
        The main job of this class is to deque a vertical channel into a Circular buffer that renderer can pick up 

        The main difference functionally between theone.py and theone_ncurses.py is that the channel can go faster than render.
        This allows for fast moving vertical channels.
        In effect if renderer is slow, it becomes lossy.
    '''
    def __init__(self, channelid, generator, renderer):
        self._channelid = channelid
        self._length = renderer.height
        self.generator = generator
        self.renderer = renderer
        self._q = deque(generator.new_space_message(randint(0,self._length)))
        self._buf = RingBuffer(self._length)

    @property
    def channelid(self):
        return self._channelid

    @property
    async def buf(self):
        return await self._buf.get()

    async def process(self):
        channeldelay = None
        while True:
            if len(self._q) == 0:
                self._q.extend(self.generator.new_message(self._channelid, self._length))


            # if the last character was a space and the current character is not
            prev_message = await self._buf.peek()

            (message, attr) = self._q.popleft()

            if len(self._q) == 0:
                self._q.extend(self.generator.new_message(self._channelid, self._length))
            
            next_message = self._q[0] if len(self._q) else None 
            
            if prev_message and prev_message[0].isspace() and next_message and not next_message[0].isspace() and not message.isspace():
                attr |= EncodingAttr.HEAD

            if channeldelay is None or attr & EncodingAttr.HEAD:
                if 0 == randint(0,20):
                    # This will randomly send a super fast message
                    channeldelay = FAST_CHANNEL_DELAY
                else:
                    channeldelay = CHANNEL_DELAY
            await asyncio.sleep(channeldelay)

            await self._buf.append((message, attr))

class MatrixChannelRenderer:
    '''
        the job of this class is to periodically grab all the channels' buffer and display on screen
    '''

    _instance = None

    @staticmethod
    def get_instance(stdscr, args):
        ''' Factory for Singleton '''
        if MatrixChannelRenderer._instance == None:
            MatrixChannelRenderer(stdscr, args)
        return MatrixChannelRenderer._instance

    def __init__(self, stdscr, args):
        if self._instance != None:
            raise Exception('Singleton class. Use factory method')
        else:
            MatrixChannelRenderer._instance = self

        self.stdscr = stdscr
        self._channels = []

        self.stdscr.clear()
        self.stdscr.nodelay(True)

        height, width = self.stdscr.getmaxyx()
        self.height, self.width = args.height or height-2, args.width or width-1
        curses.curs_set(False)
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

    async def splash_screen(self, gimmick_password):
        try_password = [' ' for m in gimmick_password]
        self.stdscr.clear()
        for i in range(1000):
            for i in range(len(try_password)):
                try_password[i] = choice(ALPHABETS) if try_password[i] != gimmick_password[i] else try_password[i]
                try_password[i] = gimmick_password[i] if 0 == randint(0,100) else try_password[i]

            try_password_s = ''.join(try_password)
            self.stdscr.addstr(0, 0, 'Enter Password: {}'.format(try_password_s), curses.color_pair(1))
            self.stdscr.refresh()
            if try_password_s == gimmick_password:
                break
            await asyncio.sleep(0.01)

        self.stdscr.addstr(0, 0, 'Enter Password: {}'.format(gimmick_password), curses.color_pair(1))
        self.stdscr.refresh()
        await asyncio.sleep(2)
        for i in range(6):
            self.stdscr.clear()
            self.stdscr.addstr(0, 0, 'Access Granted. Connecting to The Matrix {}'.format('.' * i), curses.color_pair(1))
            self.stdscr.refresh()
            await asyncio.sleep(0.5)
        self.stdscr.clear()
        self.stdscr.addstr('Connection established. Standby for feed.', curses.color_pair(1))
        self.stdscr.refresh()
        await asyncio.sleep(2)
        self.stdscr.clear()
        
    def register_channel(self, channel):
        self._channels.append(channel)

    async def render(self):
        render_delay = RENDER_DELAY
        while True:
            for ch in self._channels:
                self.render_channel(ch.channelid, await ch.buf)
            curses.curs_set(False)
            self.stdscr.refresh()
            await asyncio.sleep(render_delay)
            ch_ord = self.stdscr.getch()
            if ch_ord > 0 and 'q' == chr(ch_ord):
                break

    def render_channel(self, channelid, buf):
        for idx, (message, attributes) in enumerate(buf):
            y = len(buf) - idx
            x = channelid
            color = curses.color_pair(1) 
            if attributes & EncodingAttr.HEAD:
                color = curses.color_pair(3) 
            if attributes & EncodingAttr.CIPHER:
                color = curses.color_pair(2)
            if attributes & EncodingAttr.DANGER:
                color = curses.color_pair(4) 
                message = ' ' if 0 == randint(0,1) else message
            color |= curses.A_BOLD
            self.stdscr.addstr(y, x, message, color)

async def main(stdscr, args):

    r = MatrixChannelRenderer.get_instance(stdscr, args)
    m = MessageGenerator(args.cipher, args.density or 10)
    await r.splash_screen(args.password)
    channels = [MatrixChannel(i, m, r) for i in range(r.width)]
    for ch in channels:
        r.register_channel(ch)
    asynclist = [ch.process() for ch in channels] + [r.render()]
    done, pending = await asyncio.wait([asyncio.create_task(t) for t in asynclist], return_when=asyncio.FIRST_COMPLETED)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Matrix Rain')
    parser.add_argument('--width', metavar='Width', type=int, required=False, help='the width of screen. Look for Window Size in CMD Layout Properties')
    parser.add_argument('--height', metavar='Height', type=int, required = False, help='the height of screen. Look for Window Size in CMD Layout Properties')
    parser.add_argument('--cipher', metavar='Cipher', type=str, required = False, help='white space seperate list of words to encode into matrix')
    parser.add_argument('--password', metavar='Password', type=str, required = True, help='Password to connect to the matrix.')
    parser.add_argument('--density', metavar='Density', type=int, required = False, help='Density of the characters vs spaces. ideal is between 10 and 30')
    args = parser.parse_args()
    asyncio.run(curses.wrapper(main, args))

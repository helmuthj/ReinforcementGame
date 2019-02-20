# TODO: Remove the stupid hard-coded numbers: What is "5", what is "9"...
# TODO: In a way, the Visualizer needs to know the size of the board -> couple with Games.py?


class TicTacToeVisualizer:
    def __init__(self, Nb, Np):
        self._screen = None  # a "curses" screen as created by wrapper() in curses module
        self._Nb = Nb       # number of lines reserved for board
        self._Np = Np       # number of lines reserved for messages to players
        self._board_strs = [''] * self._Nb
        self._message_strs = [''] * self._Np
        self._symbols = ['o', 'x', '-']
        self._boardstate = None
        self._nextLine = 0

    @property
    def screen(self):
        return self._screen

    @screen.setter
    def screen(self, scr):
        self._screen = scr
        self._screen.clear()

    # I don't think this is needed ...
    def refresh(self):
        # draw board
        for (idx, line) in enumerate(self._board_strs):
            self._screen.addstr(5+idx, 5, line)

        # show messages
        for (idx, line) in enumerate(self._message_strs):
            self._screen.addstr(5+self._Nb+idx+1, 5, line)

        self._screen.refresh()

    def getPlayerLine(self):
        if self._nextLine < self._Np:
            freeLine = self._nextLine
            self._nextLine += 1
            return freeLine
        else:
            raise Exception('Not enough space for all the lines you want to write.')

    def putMessage(self, message_str, idx):
        self._message_strs[idx] = message_str
        self._screen.addstr(5 + self._Nb + idx + 1, 5, message_str)
        self._screen.refresh()

    def requestInput(self, message_str, idx):
        self.putMessage(message_str, idx)
        ascii_code = self._screen.getch()
        return chr(ascii_code)

    def visualizeState(self, state):
        self._boardstate = state
        lines = []
        line = ''
        for idx in range(6, 9):
            line += self._symbols[self._boardstate[idx]]
        lines.append(line)
        line = ''
        for idx in range(3, 6):
            line += self._symbols[self._boardstate[idx]]
        lines.append(line)
        line = ''
        for idx in range(0, 3):
            line += self._symbols[self._boardstate[idx]]
        lines.append(line)

        self._board_strs = lines

        self.putBoard()

    def putBoard(self):
        for (idx, line) in enumerate(self._board_strs):
            self._screen.addstr(5+idx, 5, line)

        self._screen.refresh()

    def clear(self):
        self._screen.clear()


# TODO: In a way, the Visualizer needs to know the size of the board -> couple with Games.py?
class VierGewinntVisualizer:
    def __init__(self, Nb, Np):
        self._screen = None  # a "curses" screen as created by wrapper() in curses module
        self._Nb = Nb       # number of lines reserved for board
        self._Np = Np       # number of lines reserved for messages to players
        self._board_strs = [''] * self._Nb
        self._message_strs = [''] * self._Np
        self._symbols = ['o', 'x', '-']
        self._boardstate = None
        self._nextLine = 0

    @property
    def screen(self):
        return self._screen

    @screen.setter
    def screen(self, scr):
        self._screen = scr
        self._screen.clear()

    # I don't think this is needed ...
    def refresh(self):
        # draw board
        NROWS = 4
        for (idx, line) in enumerate(self._board_strs):
            self._screen.addstr(NROWS+2+idx, NROWS+2, line)

        # show messages
        for (idx, line) in enumerate(self._message_strs):
            self._screen.addstr(NROWS+2+self._Nb+idx+1, NROWS+2, line)

        self._screen.refresh()

    def getPlayerLine(self):
        if self._nextLine < self._Np:
            freeLine = self._nextLine
            self._nextLine += 1
            return freeLine
        else:
            raise Exception('Not enough space for all the lines you want to write.')

    def putMessage(self, message_str, idx):
        NROWS = 4
        self._message_strs[idx] = message_str
        self._screen.addstr(NROWS+2 + self._Nb + idx + 1, NROWS+2, message_str)
        self._screen.refresh()

    def requestInput(self, message_str, idx):
        self.putMessage(message_str, idx)
        ascii_code = self._screen.getch()
        return chr(ascii_code)

    def visualizeState(self, state):
        self._boardstate = state
        NROWS = 4
        NCOLS = 5
        lines = []
        # plot from top to bottom: higher idxrow comes first
        for idxrow in range(NROWS - 1, -1, -1):
            line = ''
            for idxcol in range(0, NCOLS):
                line += self._symbols[self._boardstate[idxrow][idxcol]]
            lines.append(line)

        self._board_strs = lines

        self.putBoard()

    def putBoard(self):
        NROWS = 4
        for (idx, line) in enumerate(self._board_strs):
            self._screen.addstr(NROWS+2+idx, NROWS+2, line)

        self._screen.refresh()

    def clear(self):
        self._screen.clear()


import sys
import time
from curses import wrapper

class Board:
    def __init__(self):
        self.winners = ((0, 1, 2), (3, 4, 5), (6, 7, 8),
                        (0, 3, 6), (1, 4, 7), (2, 5, 8),
                        (0, 4, 8), (6, 4, 2))
        self._boardstate = [2, 2, 2, 2, 2, 2, 2, 2, 2]  # 0: marked by Pl0, 1: marked by Pl1, 2: empty
        self._status = -2  # -2: not ready, -1: ready/running, 0: player1 wins, 1: player1 wins, 2: draw
        self._whosturn = 0
        self._players = []

    def setplayers(self, players):
        self._players = players
        self._status = -1

    def play(self):
        while self._status == -1:
            self._players[self._whosturn].turn()

    def returnState(self):
        return self._boardstate

    def placeMove(self, move):
        if move < 1 or move > 9:
            return False
        else:
            if move < 4:
                move += 6
            elif move > 6:
                move -= 6
            if self._boardstate[move - 1] != 2:
                # illegal move
                return False
            else:
                # legal move: change state and analyze
                self._boardstate[move - 1] = self._whosturn
                self.checkwon()
                self.checkdraw()
                # give turn to next player in cycle
                self._whosturn = (self._whosturn + 1) % 2
                return True

    def checkwon(self):
        for line in self.winners:
            ref = self._boardstate[line[0]]
            if ref == self._boardstate[line[1]] and ref == self._boardstate[line[2]] and ref != 2:
                # it seems that player ref just made a winning move: log and send a reward of 1.0
                # should I check here if the winner is the one who just made the last move?
                self._status = ref
                reward = 1
                self._players[ref].visualizeState()
                self._players[ref].sendReward(reward)

    def checkdraw(self):
        if self._status == -1:
            if sum(bs != 2 for bs in self._boardstate) == 9:
                # this is a draw: log and send both players a reward of 0.5
                self._status = 2
                reward = 0.5
                self._players[self._whosturn].visualizeState()
                for player in self._players:
                    player.sendReward(reward)


class HumanPlayerInterface:

    def __init__(self, somename, someboard, somescreen):
        self._name = somename
        self._board = someboard
        self._screen = somescreen
        self._boardstate = []  # only inspect the state if asked to move
        self._symbols = ['o', 'x', '-']
        self._reward = 0
        self._playerNumber = self._screen.getPlayerLine()

    def turn(self):
        # when asked to make a move, ask for the state, analyze it, decide, return move
        self._boardstate = self._board.returnState()
        self.visualizeState()
        validmove = False
        while not validmove:
            move = int(self._screen.requestInput(self._name + ' zieht: ', self._playerNumber))
            validmove = self._board.placeMove(move)


    # sendReward() is needed, because a reward is not only given to the player who wins (which is apparent
    # right after his winning move) but also to the other player in case of a draw.
    # This means the reward can not be returned by placeMove(), which would be the more obvious choice.
    # I still don't like the current solution.
    def sendReward(self, reward):
        self._reward = reward
        # this is where the learning or logging should be triggered
        if reward == 1:
            self._screen.putMessage('Oh, ich (' + self._name + ') habe gewonnen!\n', self._playerNumber)
        elif reward == 0.5:
            self._screen.putMessage('Hm, ich (' + self._name + ') habe ein Unentschieden geholt!\n', self._playerNumber)

    def visualizeState(self):
        lines = []
        line = ''
        for (idx, cell) in enumerate(self._boardstate):
            line += self._symbols[cell]
            # new line every third cell
            if (idx+1) % 3 == 0:
                lines.append(line)
                line = ''

        self._screen.putBoard(lines)


class GameScreen:
    def __init__(self, stdscr, Nb, Np):
        self._screen = stdscr
        self._Nb = Nb       # number of lines reserved for board
        self._Np = Np       # number of lines reserved for messages to players
        self._board_strs = [''] * self._Nb
        self._message_strs = [''] * self._Np
        self._screen.clear()
        self._nextLine = 0

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
        if(self._nextLine < self._Np):
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

    def putBoard(self, board_strs):
        self._board_strs = board_strs
        for (idx, line) in enumerate(self._board_strs):
            self._screen.addstr(5+idx, 5, line)

        self._screen.refresh()


def cursesgame(scr):
    gs = GameScreen(scr, 3, 2)
    b = Board()
    hpls = [HumanPlayerInterface('Birte', b, gs), HumanPlayerInterface('Jo', b, gs)]
    b.setplayers(hpls)
    b.play()
    time.sleep(10)


wrapper(cursesgame)


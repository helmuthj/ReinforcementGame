import time
import random
import pickle
import os
import numpy
from curses import wrapper
import matplotlib.pyplot as plt


class Board:

    # class-level constants for rewards
    R_INVALID = 0
    R_DEFEAT = 1
    R_DEFAULT = 2
    R_DRAW = 2.5
    R_WIN = 8

    # class-level board constants
    MARKED_PL0 = 0
    MARKED_PL1 = 1
    UNMARKED = 2

    # class level game status constant
    NOT_READY = -2
    READY = -1
    WIN_PL0 = 0
    WIN_PL1 = 1
    DRAW = 2

    def __init__(self):
        self.winners = ((0, 1, 2), (3, 4, 5), (6, 7, 8),
                        (0, 3, 6), (1, 4, 7), (2, 5, 8),
                        (0, 4, 8), (6, 4, 2))
        self._boardstate = [Board.UNMARKED]*9
        self._status = Board.NOT_READY
        self._whosturn = None
        self._players = None

    def setplayers(self, players):
        self._players = players
        self._whosturn = 0
        self._status = Board.READY

    def reset(self):
        self._boardstate = [Board.UNMARKED]*9
        self._whosturn = 0
        self._status = Board.READY

    def play(self):
        while self._status == Board.READY:
            while 1:
                move = self._players[self._whosturn].turn()
                if self.placeMove(move):
                    break
                else:
                    self._players[self._whosturn].sendReward(Board.R_INVALID, None)

            self.checkwon()
            self.checkdraw()
            self.checkRewards()
            # give turn to next player in cycle
            self._whosturn = (self._whosturn + 1) % 2

        # When the game is finished, let the players do "clean up" operations
        for player in self._players:
            player.finalize()

    def checkRewards(self):
        # TODO: think about cleaning this up a bit: what are the assumptions?
        if self._status == Board.READY:
            # the board is in "ready" state, i.e. nobody has won yet:
            # Send the previous player a reward; the current player has to wait for
            # his reward because his move might turn out to be a bad one
            otherplayer = (self._whosturn + 1) % 2
            self._players[otherplayer].sendReward(Board.R_DEFAULT, tuple(self._boardstate))
        elif self._status == Board.WIN_PL0 or self._status == Board.WIN_PL1:
            # there is a winner, i.e. the current player's move was a winning move
            winner = self._status
            loser = (winner + 1) % 2
            self._players[winner].sendReward(Board.R_WIN, None)
            self._players[loser].sendReward(Board.R_DEFEAT, None)
        elif self._status == Board.DRAW:
            self._players[0].sendReward(Board.R_DRAW, None)
            self._players[1].sendReward(Board.R_DRAW, None)

    def returnState(self):
        return tuple(self._boardstate)

    def placeMove(self, move):
        if move < 1 or move > 9:
            return False
        else:
            if self._boardstate[move - 1] != Board.UNMARKED:
                # illegal move
                return False
            else:
                # legal move: change state
                self._boardstate[move - 1] = self._whosturn
                return True

    def checkwon(self):
        for line in self.winners:
            player = self._boardstate[line[0]]
            if player == self._boardstate[line[1]] and player == self._boardstate[line[2]] and player != Board.UNMARKED:
                # it seems that player on the checked line just made a winning move
                self._status = player

    def checkdraw(self):
        if self._status == Board.READY:
            if all(bs != Board.UNMARKED for bs in self._boardstate):
                # this is a draw: log
                self._status = Board.DRAW


class HumanPlayerInterface:

    def __init__(self, somename, someboard, somescreen):
        self._name = somename
        self._board = someboard
        self._screen = somescreen
        self._boardstate = None
        self._symbols = ['o', 'x', '-']
        self._reward = None
        self._playerNumber = self._screen.getPlayerLine()

    def turn(self):
        # when asked to make a move, ask for the state, analyze it, decide, return move
        self._boardstate = self._board.returnState()
        self.visualizeState()
        while 1:
            try:
                move = int(self._screen.requestInput(self._name + ' zieht: ', self._playerNumber))
                break
            except ValueError:
                pass
        return move

    def sendReward(self, reward, resultingState):
        self._reward = reward

    def finalize(self):
        self._boardstate = self._board.returnState()
        self.visualizeState()
        if self._reward == self._board.R_WIN:
            self._screen.putMessage('Oh, ich (' + self._name + ') habe gewonnen!\n', self._playerNumber)
        elif self._reward == self._board.R_DRAW:
            self._screen.putMessage('Hm, ich (' + self._name + ') habe ein Unentschieden geholt!\n', self._playerNumber)
        elif self._reward == self._board.R_DEFEAT:
            self._screen.putMessage('Mist, ich (' + self._name + ') habe verloren!\n', self._playerNumber)

    def visualizeState(self):
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

        self._screen.putBoard(lines)


class DumbAI:

    def __init__(self, somename, someboard, experienceFile=None):
        self._name = somename
        self._board = someboard
        self._experienceFile = experienceFile
        self._game = []
        self._boardstate = None
        self._action = None

    def turn(self):
        # when asked to make a move, ask for the state, make smart bet, return move, store state and action
        self._boardstate = self._board.returnState()
        self._action = self.chooseAction(None)
        return self._action

    def chooseAction(self, forbiddenmoves):
        return random.randint(1, 9)

    def sendReward(self, reward, resultingState):
        experience = (self._boardstate, self._action, reward, resultingState)
        self._game.append(experience)

    def finalize(self):
        if self._experienceFile is not None:
            # store game's history for future use (e.g. batch learning)
            with open(self._experienceFile, 'ab') as f:
                    pickle.dump(self._game, f)
        # reset
        self._game = []
        self._boardstate = None
        self._action = None


class SmartAI(DumbAI):

    def __init__(self, somename, someboard, experienceFile, ql, curiosity=1.0):
        DumbAI.__init__(self, somename, someboard, experienceFile)
        self._ql = ql
        self._curiosity = curiosity

    def chooseAction(self, forbiddenmoves):
        # forbiddenmoves is currently unused
        return self._ql.selectAction(self._boardstate, self._curiosity)

    def sendReward(self, reward, resultingState):
        super(SmartAI, self).sendReward(reward, resultingState)
        self._ql.updateQ(self._boardstate, self._action, reward, resultingState)


class Qlearner:

    def __init__(self, Qfile, possibleActions, alpha, lam):
        self._Qfile = Qfile
        self._possibleActions = possibleActions
        self._alpha = alpha
        self._lam = lam
        # If available, init Q from file
        if os.path.exists(self._Qfile):
            with open(self._Qfile, 'rb') as rfp:
                self._knownQs = pickle.load(rfp)
        else:
            self._knownQs = {}

    def Q(self, Sa):
        # TODO: try to remove the reference to Board
        try:
            return self._knownQs[Sa]
        except KeyError:
            return Board.R_DEFAULT

    def maxQ(self, S):
        Q = [self.Q((S, a)) for a in self._possibleActions]
        return max(Q)

    def selectAction(self, S, curiosity=None):
        # Compute Qs of all possible actions and select the best. There might be some randomness involved
        Q = [self.Q((S, a)) for a in self._possibleActions]
        if curiosity is None or curiosity <= 0:
            m = max(Q)
            Praw = [1 if q == m else 0 for q in Q]
        else:
            kappa = 1.0/curiosity
            Praw = [q**kappa for q in Q]

        sumP = sum(Praw)
        P = [p/sumP for p in Praw]
        a = numpy.random.choice(self._possibleActions, p=P)
        return a

    def updateQ(self, S, a, r, nextS):
        if S is not None:
            # Goal: update Q((S,a)) for the last move
            Sa = (S, a)
            if nextS is not None:
                self._knownQs[Sa] = (1 - self._alpha) * self.Q(Sa) + self._alpha * (r + self._lam * self.maxQ(nextS))
            else:
                self._knownQs[Sa] = r

    def batchlearnQ(self, games, repeat, backprop=False):
        # Goal: update Q((S, a)) for all experiences (S, a, r, nextS)
        cnt = 0
        while cnt < repeat:
            cnt += 1
            for game in games:
                Nx = len(game)
                if backprop:
                    r = range(Nx - 2, -1, -1)
                else:
                    r = range(0, Nx - 1)
                for i in r:
                    experience = game[i]
                    S = experience[0]
                    a = experience[1]
                    r = experience[2]
                    nextS = experience[3]
                    self.updateQ(S, a, r, nextS)

    def saveQ(self):
        # Store updated Q
        with open(self._Qfile, 'wb') as wfp:
            pickle.dump(self._knownQs, wfp)


class GameScreen:
    def __init__(self, stdscr, Nb, Np):
        self._screen = stdscr
        self._Nb = Nb       # number of lines reserved for board
        self._Np = Np       # number of lines reserved for messages to players
        self._board_strs = [''] * self._Nb
        self._message_strs = [''] * self._Np
        self._nextLine = 0
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

    def clear(self):
        self._screen.clear()


def loadGames(gamesFile):
    games = []
    with open(gamesFile, 'rb') as f:
        eof = False
        while not eof:
            try:
                games.append(pickle.load(f))
            except EOFError:
                eof = True

    return games


def printGames(games):
    for game in games:
        for exp in game:
            print(exp)
        print('')


def practice(M):
    # online practicing
    random.seed(time.time())

    b = Board()
    ql0 = Qlearner('Q0.pkl', range(1, 10), alpha=0.1, lam=0.5)
    ql1 = Qlearner('Q1.pkl', range(1, 10), alpha=0.1, lam=0.5)
    pls = [SmartAI('Smart AI', b, None, ql0, curiosity=0.25), SmartAI('Smart AI', b, None, ql1, curiosity=0.25)]
    #pls = [DumbAI('Dumb AI 0', b, None), SmartAI('Smart AI 1', b, None, ql1, curiosity=0.05)]
    #pls = [DumbAI('Dumb AI 0', b, None), DumbAI('Dumb AI 1', b, None)]
    b.setplayers(pls)

    result = []
    for i in range(0, M):
        b.reset()
        b.play()
        result.append(b._status)

    ql0.saveQ()
    ql1.saveQ()

    win0, win0rate = 0, []
    win1, win1rate = 0, []
    draw, drawrate = 0, []
    for i, r in enumerate(result):
            if r == 0:
                win0 += 1
            elif r == 1:
                win1 += 1
            elif r == 2:
                draw += 1
            win0rate.append(win0 / (i + 1))
            win1rate.append(win1 / (i + 1))
            drawrate.append(draw / (i + 1))

    #cumwin0 = numpy.cumsum([1 if r == 0 else 0 for r in result])
    #cumwin1 = numpy.cumsum([1 if r == 1 else 0 for r in result])
    #cumdraw = numpy.cumsum([1 if r == 2 else 0 for r in result])

    plt.plot(range(0, M), win0rate)
    plt.plot(range(0, M), win1rate)
    plt.plot(range(0, M), drawrate)
    plt.show()


def cursesgame(scr):
    random.seed(time.time())
    gs = GameScreen(scr, 3, 2)
    b = Board()
    alpha = 0.0
    lam = 0.0
    ql0 = Qlearner('Q0.pkl', range(1, 10), alpha, lam)
    ql1 = Qlearner('Q1.pkl', range(1, 10), alpha, lam)
    #pls = [HumanPlayerInterface('Spieler', b, gs), SmartAI('Smart AI', b, None, ql1, 10)]
    pls = [HumanPlayerInterface('Lotte', b, gs), HumanPlayerInterface('Jo', b, gs)]
    b.setplayers(pls)

    while 1:
        b.play()
        while 1:
            c = gs.requestInput('Noch mal spielen (j / n)?', 1)
            if c == 'j' or c == 'n':
                break
        if c == 'n':
            break
        else:
            gs.clear()
            b.reset()

    time.sleep(1)


if __name__ == '__main__':
    #practice(50000)
    wrapper(cursesgame)


import sys
import time
import random
import copy
import pickle
import os
import itertools
import numpy
from curses import wrapper


class Board:

    # class-level constants for rewards
    R_INVALID = 0
    R_DEFEAT = 1
    R_DEFAULT = 2
    R_DRAW = 2.5
    R_WIN = 4

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
                    self._players[self._whosturn].sendReward(Board.R_INVALID)

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
            self._players[otherplayer].sendReward(Board.R_DEFAULT)
        elif self._status == Board.WIN_PL0 or self._status == Board.WIN_PL1:
            # there is a winner, i.e. the current player's move was a winning move
            winner = self._status
            loser = (winner + 1) % 2
            self._players[winner].sendReward(Board.R_WIN)
            self._players[loser].sendReward(Board.R_DEFEAT)
        elif self._status == Board.DRAW:
            self._players[0].sendReward(Board.R_DRAW)
            self._players[1].sendReward(Board.R_DRAW)

    def returnState(self):
        return self._boardstate

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
            if sum(bs != Board.UNMARKED for bs in self._boardstate) == 9:
                # this is a draw: log
                self._status = Board.DRAW


class HumanPlayerInterface:

    def __init__(self, somename, someboard, somescreen):
        self._name = somename
        self._board = someboard
        self._screen = somescreen
        self._boardstate = []  # only inspect the state if asked to move
        self._symbols = ['o', 'x', '-']
        self._reward = 0
        self._playerNumber = self._screen.getPlayerLine()
        self._lastmove = []

    def turn(self):
        # when asked to make a move, ask for the state, analyze it, decide, return move
        self._boardstate = self._board.returnState()
        self.visualizeState()
        moveisvalid = False
        while not moveisvalid:
            move = int(self._screen.requestInput(self._name + ' zieht: ', self._playerNumber))
            moveisvalid = self._board.placeMove(move)
        self._lastmove = move

    # sendReward() is needed, because a reward is not only given to the player who wins (which is apparent
    # right after his winning move) but also to the other player in case of a draw.
    def sendReward(self, reward):
        self._reward = reward

    def finalize(self):
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

    def __init__(self, somename, someboard, experienceFile):
        self._name = somename
        self._board = someboard
        self._experienceFile = experienceFile
        self._boardstate = []  # only inspect the state if asked to move
        self._symbols = ['o', 'x', '-']
        #self._playerNumber = self._screen.getPlayerLine()
        self._rewardhist = []
        self._movehist = []
        self._statehist = []

    def turn(self):
        # when asked to make a move, ask for the state, make smart bet, return move, store state and action
        self._boardstate = self._board.returnState()
        self._statehist.append(tuple(self._boardstate))
        move = self.chooseMove([])
        self._movehist.append(move)
        return move

    def chooseMove(self, forbiddenmoves):
        return random.randint(1, 9)

    def sendReward(self, reward):
        if len(self._rewardhist) == len(self._statehist):
            # update using new knowledge on the usefulness of the last move
            self._rewardhist[-1] = reward
        else:
            self._rewardhist.append(reward)

    def finalize(self):
        # grab final state: this is the state after the last move,
        # irrespective of whether self made it or the other player
        # append to history, and also append a dummy move and a reward of zero
        self._boardstate = self._board.returnState()
        self._statehist.append(tuple(self._boardstate))
        self._movehist.append(-1)
        self._rewardhist.append(self._board.R_DEFAULT)

        # create experiences "SaR" from histories, write whole game to disk
        game = []
        for iturn in range(len(self._movehist)):
            game.append(((tuple(self._statehist[iturn]), self._movehist[iturn]), self._rewardhist[iturn]))

        with open(self._experienceFile, 'ab') as f:
                pickle.dump(game, f)

        # finally, clear histories, so that the player can log a new game
        del self._statehist[:]
        del self._movehist[:]
        del self._rewardhist[:]


class SmartAI(DumbAI):

    def __init__(self, somename, someboard, experienceFile, ql, curiosity=1.0):
        DumbAI.__init__(self, somename, someboard, experienceFile)
        self._ql = ql
        self._curiosity = curiosity

    def chooseMove(self, forbiddenmoves):
        # forbiddenmoves is currently unused
        return self._ql.selectAction(tuple(self._boardstate), self._curiosity)

    def sendReward(self, reward):
        if len(self._rewardhist) == len(self._statehist):
            # update using new knowledge on the usefulness of the last move
            self._rewardhist[-1] = reward
        else:
            self._rewardhist.append(reward)

    def finalize(self):
        # grab final state: this is the state after the last move,
        # irrespective of whether self made it or the other player
        # append to history, and also append a dummy move and a reward of zero
        self._boardstate = self._board.returnState()
        self._statehist.append(tuple(self._boardstate))
        self._movehist.append(-1)
        self._rewardhist.append(self._board.R_DEFAULT)

        # create experiences "SaR" from histories, use whole game to learn
        game = []
        for iturn in range(len(self._movehist)):
            game.append(((tuple(self._statehist[iturn]), self._movehist[iturn]), self._rewardhist[iturn]))

        # learn!
        self._ql.learnQ([game], 0.5, 0.8, 1, False)

        # finally, clear histories, so that the player can log a new game
        del self._statehist[:]
        del self._movehist[:]
        del self._rewardhist[:]

class Qlearner:

    def __init__(self, Qfile, possibleActions):
        self._Qfile = Qfile
        self._possibleActions = possibleActions
        if os.path.exists(self._Qfile):
            with open(self._Qfile, 'rb') as rfp:
                self._knownQs = pickle.load(rfp)
        else:
            self._knownQs = {}

    def Q(self, Sa):
        # TODO: try to remove the coupling to Board
        try:
            return self._knownQs[Sa]
        except KeyError:
            return Board.R_DEFAULT


    def maxQ(self, S):
        Q = [self.Q((S, a)) for a in self._possibleActions]
        return max(Q)


    def selectAction(self, S, curiosity):
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


    def updateQ(self, Sa, r, nextS, alpha, lam):
        # Goal: update Q((S,a)) for all the last move
        if nextS is not None:
            self._knownQs[Sa] = (1 - alpha) * self.Q(Sa) + alpha * (r + lam * self.maxQ(nextS))
        else:
            self._knownQs[Sa] = r


    def batchlearnQ(self, games, alpha, lam, repeat, backprop=False):
        # Goal: update Q((S,a)) for all but the last experience ((S,a),r)
        # The last experience is the final state (S_f, -1, nothing) and should never appear on the l.h.s
        # Because of that, max_a Q(S_f,a) will be zero, because Q(S_f,a) is zero for all a
        cnt = 0
        while cnt < repeat:
            cnt += 1
            for game in games:
                Nmoves = len(game)
                if backprop:
                    r = range(Nmoves - 2, -1, -1)
                else:
                    r = range(0, Nmoves - 1)
                for i in r:
                    Sa = game[i][0]
                    r = game[i][1]
                    nextS = game[i+1][0][0]
                    self.updateQ(Sa, r, nextS, alpha, lam)
                    #self._knownQs[Sa] = (1 - alpha) * self.Q(Sa) + alpha * (r + lam * self.maxQ(nextS))

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
    ql0 = Qlearner('Q2.pkl', range(1, 10))
    pls = [SmartAI('Smart AI', b, 'games.pkl', ql0), SmartAI('Smart AI', b, 'games.pkl', ql0)]
    b.setplayers(pls)
    for i in range(0, M):
        b.reset()
        b.play()

    ql0.saveQ()


def cursesgame(scr):
    #random.seed(time.time())
    random.seed(1)
    gs = GameScreen(scr, 3, 2)
    b = Board()
    ql0 = Qlearner('Q1.pkl', range(1, 10))
    pls = [SmartAI('Smart AI', b, 'games.pkl', ql0, 0.0), HumanPlayerInterface('Jo', b, gs)]
    b.setplayers(pls)
    b.play()
    ql0.saveQ()
    time.sleep(1)


if __name__ == '__main__':

    practice(10000)
    ql0 = Qlearner('Q2.pkl', range(1, 10))
    S = [2]*9
    S = tuple(S)
    for a in range(1, 10):
        print([a, ql0.Q((S, a))])

    #wrapper(cursesgame)


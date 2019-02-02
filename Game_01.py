import sys
import time
import random
import copy
import pickle
import os
import itertools
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
        self._whosturn = 0
        self._players = []

    def setplayers(self, players):
        self._players = players
        self._status = Board.READY

    def reset(self):
        self._boardstate = [Board.UNMARKED]*9
        self._whosturn = 0
        self._status = Board.READY

    def play(self):
        while self._status == Board.READY:
            self._players[self._whosturn].turn()
            self.checkwon()
            self.checkdraw()
            self.checkRewards()
            # give turn to next player in cycle
            self._whosturn = (self._whosturn + 1) % 2

        # When the game is finished, let the players do "clean up" operations
        for player in self._players:
            player.finalize()

    def checkRewards(self):
        if self._status == -1:
            self._players[self._whosturn].sendReward(0)
        elif self._status == 0 or self._status == 1:
            winner = self._status
            loser = (winner + 1) % 2
            self._players[winner].sendReward(2)
            self._players[loser].sendReward(-1)
        elif self._status == 2:
            self._players[0].sendReward(0.5)
            self._players[1].sendReward(0.5)

    def returnState(self):
        return self._boardstate

    def placeMove(self, move):
        if move < 1 or move > 9:
            return False
        else:
            if self._boardstate[move - 1] != 2:
                # illegal move
                return False
            else:
                # legal move: change state and analyze
                self._boardstate[move - 1] = self._whosturn
                return True

    def checkwon(self):
        for line in self.winners:
            ref = self._boardstate[line[0]]
            if ref == self._boardstate[line[1]] and ref == self._boardstate[line[2]] and ref != 2:
                # it seems that player ref just made a winning move: log and send a reward of 1.0
                # should I check here if the winner is the one who just made the last move?
                self._status = ref

    def checkdraw(self):
        if self._status == -1:
            if sum(bs != 2 for bs in self._boardstate) == 9:
                # this is a draw: log
                self._status = 2


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
            moveisvalid = self._board.checkAndPlaceMove(move)
        self._lastmove = move

    # sendReward() is needed, because a reward is not only given to the player who wins (which is apparent
    # right after his winning move) but also to the other player in case of a draw.
    def sendReward(self, reward):
        self._reward = reward

    def finalize(self):
        self.visualizeState()
        if self._reward == 2:
            self._screen.putMessage('Oh, ich (' + self._name + ') habe gewonnen!\n', self._playerNumber)
        elif self._reward == 0.5:
            self._screen.putMessage('Hm, ich (' + self._name + ') habe ein Unentschieden geholt!\n', self._playerNumber)
        elif self._reward == -1.0:
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
        moveisvalid = False
        forbiddenmoves = []
        while not moveisvalid:
            tentativeMove = self.chooseMove(forbiddenmoves)
            moveisvalid = self._board.checkAndPlaceMove(tentativeMove)
            if not moveisvalid:
                forbiddenmoves.append(tentativeMove)
        self._movehist.append(tentativeMove)

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
        self._rewardhist.append(0)

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

    def __init__(self, somename, someboard, experienceFile, ql):
        DumbAI.__init__(self, somename, someboard, experienceFile)
        self._ql = ql

    def chooseMove(self, forbiddenmoves):
        return self._ql.bestA(tuple(self._boardstate), forbiddenmoves)

    def finalize(self):
        # grab final state: this is the state after the last move,
        # irrespective of whether self made it or the other player
        # append to history, and also append a dummy move and a reward of zero
        self._boardstate = self._board.returnState()
        self._statehist.append(tuple(self._boardstate))
        self._movehist.append(-1)
        self._rewardhist.append(0)

        # create experiences "SaR" from histories, write whole game to disk
        game = []
        for iturn in range(len(self._movehist)):
            game.append(((tuple(self._statehist[iturn]), self._movehist[iturn]), self._rewardhist[iturn]))

        # learn!
        self._ql.learnQ([game], 0.8, 0.8, 5)

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
        try:
            return self._knownQs[Sa]
        except KeyError:
            return 0

    def maxQ(self, S):
        # TODO: remove knowledge of the game rules from Q-learner: here I determine allowed moves from state - not good!
        Qs = [self.Q((S, a)) for a in self._possibleActions if S[a - 1] == 2]
        if len(Qs) == 0:
            return 0
        else:
            return max(Qs)

    def bestA(self, S, forbiddenActions):
        # The role of forbiddenActions is two prevent the AI to suggest illegal actions.
        # Because the AI should be game-agnostic, it should neither know the rules of the game,
        # nor talk to the game engine directly
        #
        # Compute Qs of all legal actions and select the best. If multiple are equally good,
        # randomly select one of those
        Qa = [(self.Q((S, a)), a) for a in self._possibleActions if a not in forbiddenActions]

        # turn into wheel of fortune?
        m = self.maxQ(S)
        bestas = [Qa[i][1] for i, q in enumerate(Qa) if q[0] == m]
        if len(bestas) > 1:
            return random.choice(bestas)
        else:
            return bestas[0]

    def learnQ(self, games, alpha, lam, repeat):
        # Goal: update Q((S,a)) for all but the last experience ((S,a),r)
        # The last experience is the final state (S_f, -1, nothing) and should never appear on the l.h.s
        # Because of that, max_a Q(S_f,a) will be zero, because Q(S_f,a) is zero for all a
        cnt = 0
        while cnt < repeat:
            cnt += 1
            for game in games:
                Nmoves = len(game)
                for i in range(0, Nmoves-1):
                    Sa = game[i][0]
                    r = game[i][1]
                    nextS = game[i+1][0][0]
                    self._knownQs[Sa] = (1 - alpha) * self.Q(Sa) + alpha * (r + lam * self.maxQ(nextS))

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
    random.seed(time.time())
    b = Board()
    ql0 = Qlearner('Q0.pkl', range(1, 10))
    pls = [SmartAI('Smart AI', b, 'games2.pkl', ql0), SmartAI('Smart AI', b, 'games2.pkl', ql0)]
    b.setplayers(pls)
    for i in range(0, M):
        b.reset()
        b.play()

    #games = loadGames('games0.pkl')
    ql0.saveQ()


def cursesgame(scr):
    random.seed(time.time())
    gs = GameScreen(scr, 3, 2)
    b = Board()
    ql0 = Qlearner('Q0.pkl', range(1, 10))
    pls = [SmartAI('Smart AI', b, 'games2.pkl', ql0), HumanPlayerInterface('Jo', b, gs)]
    b.setplayers(pls)
    b.play()
    ql0.saveQ()
    time.sleep(1)


if __name__ == '__main__':

    #practice(20000)
    wrapper(cursesgame)


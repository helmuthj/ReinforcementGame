import time
import random
import pickle
import os
import numpy
from curses import wrapper
import matplotlib.pyplot as plt

import cProfile, pstats, io


class VierGewinnt:

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
    NCOLS = 5
    NROWS = 4

    # class level game status constant
    NOT_READY = -2
    READY = -1
    WIN_PL0 = 0
    WIN_PL1 = 1
    DRAW = 2

    def __init__(self):
        self._Ncols = VierGewinnt.NCOLS
        self._Nrows = VierGewinnt.NROWS
        # note that the first index is for column, the second for row
        self._boardstate = [[VierGewinnt.UNMARKED for j in range(self._Ncols)] for i in range(self._Nrows)]
        self._winner = ((( 0, -3), ( 0, -2), ( 0, -1)),  # west
                        ((-3, -3), (-2, -2), (-1, -1)),  # south west
                        ((-3,  0), (-2,  0), (-1,  0)),  # south
                        ((-3,  3), (-2,  2), (-1,  1)),  # south east
                        (( 0,  3), ( 0,  2), ( 0,  1)),  # east
                        (( 0,  1), ( 0, -2), ( 0, -1)),  # mostly west
                        (( 0, -1), ( 0,  2), ( 0,  1)),  # mostly east
                        (( 3, -3), ( 2, -2), ( 1, -1)),  # north west
                        (( 2, -2), ( 1, -1), (-1,  1)),  # north west
                        (( 1, -1), (-1,  1), (-2,  2)),  # north west
                        (( 3,  3), ( 2,  2), ( 1,  1)),  # north east
                        (( 2,  2), ( 1,  1), (-1, -1)),  # north east
                        (( 1,  1), (-1, -1), (-2, -2)))  # north east
        self._column_cnt = [0] * self._Ncols
        self._status = VierGewinnt.NOT_READY
        self._whosturn = None
        self._players = None

    def state2tuple(self):
        return tuple([tuple(col) for col in self._boardstate])

    def setplayers(self, players):
        self._players = players
        self._whosturn = 0
        self._status = VierGewinnt.READY

    def reset(self):
        self._boardstate = [[VierGewinnt.UNMARKED for j in range(self._Ncols)] for i in range(self._Nrows)]
        self._column_cnt = [0] * self._Ncols
        self._whosturn = 0
        self._status = VierGewinnt.READY

    def play(self):
        while self._status == VierGewinnt.READY:
            while 1:
                move = self._players[self._whosturn].turn()
                if self.placeMove(move):
                    break
                else:
                    self._players[self._whosturn].sendReward(VierGewinnt.R_INVALID, None)

            self.checkwon(move)
            self.checkdraw()
            self.checkRewards()
            # give turn to next player in cycle
            self._whosturn = (self._whosturn + 1) % 2

        # When the game is finished, let the players do "clean up" operations
        for player in self._players:
            player.finalize()

    def checkRewards(self):
        # TODO: think about cleaning this up a bit: what are the assumptions?
        if self._status == VierGewinnt.READY:
            # the board is in "ready" state, i.e. nobody has won yet:
            # Send the previous player a reward; the current player has to wait for
            # his reward because his move might turn out to be a bad one
            otherplayer = (self._whosturn + 1) % 2
            self._players[otherplayer].sendReward(VierGewinnt.R_DEFAULT, self.state2tuple())
        elif self._status == VierGewinnt.WIN_PL0 or self._status == VierGewinnt.WIN_PL1:
            # there is a winner, i.e. the current player's move was a winning move
            winner = self._status
            loser = (winner + 1) % 2
            self._players[winner].sendReward(VierGewinnt.R_WIN, None)
            self._players[loser].sendReward(VierGewinnt.R_DEFEAT, None)
        elif self._status == VierGewinnt.DRAW:
            self._players[0].sendReward(VierGewinnt.R_DRAW, None)
            self._players[1].sendReward(VierGewinnt.R_DRAW, None)

    def returnState(self):
        return self.state2tuple()

    def placeMove(self, move):
        idxcol = move - 1
        if move < 1 or move > self._Ncols:
            return False
        else:
            idxrow = self._column_cnt[idxcol]
            if idxrow >= self._Nrows:
                # illegal move: row is full
                return False
            else:
                # legal move: change state and auxiliary state variable
                self._boardstate[idxrow][idxcol] = self._whosturn
                self._column_cnt[idxcol] += 1
                return True

    def checkwon(self, lastmove):
        # find location of last set stone and try all variants around it
        idxcol = lastmove - 1
        idxrow = self._column_cnt[idxcol]-1
        player = self._boardstate[idxrow][idxcol]
        for shifts in self._winner:
            won = True
            for shift in shifts:
                try:
                    if self._boardstate[idxrow+shift[0]][idxcol+shift[1]] != player:
                        won = False
                        break
                except IndexError:
                    won = False
                    break
            if won:
                # for at least one of the tested set of shifts (e.g. a south west diagonal),
                # we could not find a wrong stone --> a win by the "player" who put the last stone
                self._status = player
                break

    def checkdraw(self):
        if self._status == VierGewinnt.READY:
            # if full, it is a draw
            # refined version: prematurely stop game with "draw", if it can not be won any more
            if all(c == VierGewinnt.NROWS for c in self._column_cnt):
                # this is a draw: log
                self._status = VierGewinnt.DRAW


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

    # TODO: make the HumanPlayer game-agnostic - could the Board describe itself?
    def visualizeState(self):
        lines = []
        # plot from top to bottom: higher idxrow comes first
        for idxrow in range(VierGewinnt.NROWS-1, -1, -1):
            line = ''
            for idxcol in range(0, VierGewinnt.NCOLS):
                line += self._symbols[self._boardstate[idxrow][idxcol]]
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
        # TODO: make this line game-agnostic
        return random.randint(1, VierGewinnt.NCOLS)

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
            return VierGewinnt.R_DEFAULT

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

        a = self.mychoice(self._possibleActions, Praw)
        return a

    def mychoice(self, actions, p):
        cump = numpy.cumsum(p)
        u = random.uniform(0, cump[-1])
        for idx, cp in enumerate(cump):
            if u <= cp:
                return actions[idx]

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

    print("Loading data ...")

    b = VierGewinnt()
    ql0 = Qlearner('Qx0.pkl', range(1, VierGewinnt.NCOLS+1), alpha=0.1, lam=0.5)
    ql1 = Qlearner('Qx1.pkl', range(1, VierGewinnt.NCOLS+1), alpha=0.1, lam=0.5)
    pls = [SmartAI('Smart AI', b, None, ql0, curiosity=0.1), SmartAI('Smart AI', b, None, ql1, curiosity=0.1)]
    #pls = [DumbAI('Dumb AI 0', b, None), SmartAI('Smart AI 1', b, None, ql1, curiosity=0.1)]
    #pls = [DumbAI('Dumb AI 0', b, None), DumbAI('Dumb AI 1', b, None)]
    b.setplayers(pls)


    try:
        result = []
        t0 = time.time()
        for i in range(0, M):
            b.reset()
            b.play()
            result.append(b._status)
            m = 20000
            if i % m == 0 and i != 0:
                t1 = time.time()
                secpergame = (t1-t0)/(i+1)
                remainingtime = (M-i)*secpergame
                print("Time to finish practicing: {:5.1f}".format(remainingtime))


    except KeyboardInterrupt:
        pass

    print("Saving data ...")
    ql0.saveQ()
    ql1.saveQ()

    win0 = [1 if r == 0 else 0 for r in result]
    win1 = [1 if r == 1 else 0 for r in result]
    draw = [1 if r == 2 else 0 for r in result]

    kernel = numpy.exp(numpy.linspace(-1.0, 0, 1000))
    kernel /= kernel.sum()
    win0s = numpy.convolve(win0, kernel, mode='valid')
    win1s = numpy.convolve(win1, kernel, mode='valid')
    draws = numpy.convolve(draw, kernel, mode='valid')

    plt.plot(range(0, len(win0s)), win0s, 'r-', label='win0')
    plt.plot(range(0, len(win1s)), win1s, 'g-', label='win1')
    plt.plot(range(0, len(draws)), draws, 'y-', label='draw')
    plt.legend()
    plt.show()


def cursesgame(scr):
    random.seed(time.time())
    gs = GameScreen(scr, VierGewinnt.NROWS, 2)
    b = VierGewinnt()
    alpha = 0.1
    lam = 0.5

    #ql0 = Qlearner('Qx0.pkl', range(1, VierGewinnt.NCOLS+1), alpha, lam)
    #ql1 = Qlearner('Qx1.pkl', range(1, VierGewinnt.NCOLS+1), alpha, lam)
    #pls = [HumanPlayerInterface('Spieler', b, gs), SmartAI('Smart AI', b, None, ql1, 0.0)]
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
    #pr = cProfile.Profile()
    #pr.enable()

    practice(250000)
    #wrapper(cursesgame)

    #pr.disable()
    #s = io.StringIO()
    #sortby = 'tottime'
    #ps = pstats.Stats(pr, stream=s)
    #ps.strip_dirs().sort_stats(sortby).print_stats()
    #print(s.getvalue())
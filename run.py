import time
import random
import pickle
from curses import wrapper
import matplotlib.pyplot as plt

from Games import TicTacToe
from Learners import Qlearner
from Players import DumbAI, SmartAI, HumanPlayerInterface
from Visualizers import TicTacToeVisualizer


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

    board = TicTacToe()
    possibleActions = TicTacToe.POSSIBLE_ACTIONS
    ql0 = Qlearner('Q0.pkl', possibleActions, TicTacToe.R_DEFAULT, alpha=0.1, lam=0.5)
    ql1 = Qlearner('Q1.pkl', possibleActions, TicTacToe.R_DEFAULT, alpha=0.1, lam=0.5)
    sL0 = SmartAI('Smart AI 0', None, ql0, curiosity=0.25)
    sL1 = SmartAI('Smart AI 1', None, ql1, curiosity=0.25)
    sP0 = SmartAI('Smart AI 0', None, ql0, curiosity=0)
    sP1 = SmartAI('Smart AI 1', None, ql1, curiosity=0)
    dP0 = DumbAI('Dumb AI 0', None)
    dP1 = DumbAI('Dumb AI 1', None)

    pls = [sP0, dP0]

    board.setplayers(pls)

    result = []
    for i in range(0, M):
        board.reset()
        board.play()
        result.append(board._status)

    #ql0.saveQ()
    #ql1.saveQ()

    win0, win0rate = 0, []
    win1, win1rate = 0, []
    draw, drawrate = 1, []
    alpha = 0.995
    for i, r in enumerate(result):
        if r == 0:
            win0 = win0*alpha + (1 - alpha)
            win1 = win1*alpha
            draw = draw*alpha
        elif r == 1:
            win0 = win0 * alpha
            win1 = win1 * alpha + (1 - alpha)
            draw = draw * alpha
        elif r == 2:
            win0 = win0 * alpha
            win1 = win1 * alpha
            draw = draw * alpha + (1 - alpha)

        win0rate.append(win0)
        win1rate.append(win1)
        drawrate.append(draw)

    #cumwin0 = numpy.cumsum([1 if r == 0 else 0 for r in result])
    #cumwin1 = numpy.cumsum([1 if r == 1 else 0 for r in result])
    #cumdraw = numpy.cumsum([1 if r == 2 else 0 for r in result])

    plt.plot(range(0, M), win0rate)
    plt.plot(range(0, M), win1rate)
    plt.plot(range(0, M), drawrate)
    plt.legend(['win 0', 'win 1', 'draw'])
    plt.show()


def cursesgame(scr):
    random.seed(time.time())
    visualizer = TicTacToeVisualizer(scr, 3, 2)
    board = TicTacToe()
    possibleActions = TicTacToe.POSSIBLE_ACTIONS
    alpha = 0.0
    lam = 0.0
    curiosity = 0
    ql0 = Qlearner('Q0.pkl', possibleActions, alpha, lam)
    ql1 = Qlearner('Q1.pkl', possibleActions, alpha, lam)
    pls = [HumanPlayerInterface('Janne', visualizer), SmartAI('Smart AI', None, ql1, curiosity)]
    #pls = [HumanPlayerInterface('Janne', b, visualizer),
    #  HumanPlayerInterface('Jo', b, visualizer)]
    board.setplayers(pls)

    while 1:
        board.play()
        while 1:
            c = visualizer.requestInput('Noch mal spielen (j / n)?', 1)
            if c == 'j' or c == 'n':
                break
        if c == 'n':
            break
        else:
            visualizer.clear()
            board.reset()

    time.sleep(1)


if __name__ == '__main__':
    practice(10000)
    #wrapper(cursesgame)
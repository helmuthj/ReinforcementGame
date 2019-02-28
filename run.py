import time
import numpy as np
import pickle
from curses import wrapper
import matplotlib.pyplot as plt

from Games import TicTacToe, VierGewinnt
from Learners import Qlearner
from Players import DumbAI, SmartAI, HumanPlayerInterface
from Visualizers import TicTacToeVisualizer, VierGewinntVisualizer


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


def plot_exp_mav(result):
    M = len(result)
    win0, win0rate = 0.34, []
    win1, win1rate = 0.29, []
    draw, drawrate = 0.37, []
    alpha = 0.999
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

    plt.plot(range(0, M), win0rate)
    plt.plot(range(0, M), win1rate)
    plt.plot(range(0, M), drawrate)
    plt.legend(['win 0', 'win 1', 'draw'])
    plt.show()


def plot_boxed_av(result):
    win0rate = []
    win1rate = []
    drawrate = []

    M = len(result)
    i = 0
    K = 1000
    while i+K <= M:
        sub = result[i:i+K]
        win0rate.append(sum([1 if s == 0 else 0 for s in sub])/K)
        win1rate.append(sum([1 if s == 1 else 0 for s in sub])/K)
        drawrate.append(sum([1 if s == 2 else 0 for s in sub])/K)
        i += K

    plt.plot(range(0, len(win0rate)), win0rate)
    plt.plot(range(0, len(win1rate)), win1rate)
    plt.plot(range(0, len(drawrate)), drawrate)
    plt.legend(['win 0', 'win 1', 'draw'])
    plt.show()


def practice(M, board, Qfile0, Qfile1):
    # online practicing
    #random.seed(time.time())
    np.random.seed(0)

    possibleActions = board.POSSIBLE_ACTIONS
    defaultReward = board.R_DEFAULT

    ql0 = Qlearner(Qfile0, possibleActions, defaultReward, alpha=0.1, lam=0.8)
    sL0 = SmartAI('Smart AI 0', None, ql0, curiosity=0.1)
    sL1 = SmartAI('Smart AI 1', None, ql0, curiosity=0.1)  # Using the same Q-learner for both AIs
    dP = DumbAI('Dumbo', None)

    pls = [sL0, sL1]
    board.setplayers(pls)

    result = []
    for i in range(0, M):
        if i % 1000 == 0:
            print('{:d} to go, {:d} states/action-pairs visited '.format(M - i,len(ql0._knownQs)))

        board.reset()
        board.play()
        result.append(board._status)

    ql0.saveQ()

    plot_boxed_av(result)


def curses_game(scr, board, visualizer):
    # attach curses screen
    visualizer.screen = scr

    np.random.seed(0)
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
    train = True
    Qfile = 'models/QVierGewinnt.pkl'

    if train:
        board = VierGewinnt()
        practice(1000000, board, Qfile, None)

    else:
        board = VierGewinnt()
        visualizer = VierGewinntVisualizer(5, 2)

        possibleActions = board.POSSIBLE_ACTIONS
        default_reward = board.R_DEFAULT
        ql0 = Qlearner(Qfile, possibleActions, default_reward, alpha=0.1, lam=0.5)
        sP0 = SmartAI('Smart AI 0', None, ql0, curiosity=0.0)
        sP1 = SmartAI('Smart AI 1', None, ql0, curiosity=0.0)

        hP0 = HumanPlayerInterface('Lotte', visualizer)
        hP1 = HumanPlayerInterface('Jo', visualizer)
        pls = [sP0, hP1]
        board.setplayers(pls)

        wrapper(curses_game, board, visualizer)

    # TODO: do something with this legacy timing code.
    # pr = cProfile.Profile()
    # pr.enable()

    #practice(100000)
    # wrapper(cursesgame)

    # pr.disable()
    # s = io.StringIO()
    # sortby = 'tottime'
    # ps = pstats.Stats(pr, stream=s)
    # ps.strip_dirs().sort_stats(sortby).print_stats()
    # print(s.getvalue())

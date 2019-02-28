import pickle
import os
import numpy as np


class Qlearner:
    # TODO: Start using embedding

    def __init__(self, Qfile, possibleActions, default_reward, alpha, lam):
        self._Qfile = Qfile
        self._possibleActions = possibleActions
        self._defaultreward = default_reward
        self._alpha = alpha
        self._lam = lam
        # If available, init Q from file
        if os.path.exists(self._Qfile):
            with open(self._Qfile, 'rb') as rfp:
                self._knownQs = pickle.load(rfp)
        else:
            self._knownQs = {}

    def Q(self, Sa):
        try:
            return self._knownQs[Sa]
        except KeyError:
            return self._defaultreward

    def _maxQ(self, S):
        Q = [self.Q((S, a)) for a in self._possibleActions]
        return max(Q)

    def selectAction(self, S, curiosity=None):
        # Compute Qs of all possible actions and select the best.
        # There might be some randomness involved
        Q = [self.Q((S, a)) for a in self._possibleActions]
        if curiosity is None or curiosity < 0:
            m = max(Q)
            Praw = [1 if q == m else 0 for q in Q]
        else:
            # Boltzmann distribution fopr action selection
            # q = -E, positive energy-->forbidden move or defeat-->prob=0
            kbT = curiosity + 0.01
            Praw = [np.exp(q/kbT) for q in Q]

        sumP = sum(Praw)
        if sumP != 0:
            P = [p/sumP for p in Praw]
        else:
            P = [1/len(Praw)]*len(Praw)
        a = np.random.choice(self._possibleActions, p=P)
        return a

    def updateQ(self, S, a, r, nextS):
        if S is not None:
            # Goal: update Q((S,a)) for the last move
            Sa = (S, a)
            if nextS is not None:
                self._knownQs[Sa] = (1 - self._alpha) * self.Q(Sa) \
                                    + self._alpha * (r + self._lam * self._maxQ(nextS))
            else:
                self._knownQs[Sa] = (1 - self._alpha) * self.Q(Sa) + self._alpha * r

    def batchlearnQ(self, games, repeat, backprop=False):
        # Goal: update Q((S, a)) for all experiences (S, a, r, nextS)
        cnt = 0
        while cnt < repeat:
            cnt += 1
            for game in games:
                Nx = len(game)
                if backprop:
                    learning_order = range(Nx - 1, -1, -1)
                else:
                    learning_order = range(0, Nx)
                for i in learning_order:
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

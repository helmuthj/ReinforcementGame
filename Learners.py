import pickle
import os
import numpy


class Qlearner:
    # TODO: experiment with batch learn
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
                self._knownQs[Sa] = (1 - self._alpha) * self.Q(Sa) \
                                    + self._alpha * (r + self._lam * self._maxQ(nextS))
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

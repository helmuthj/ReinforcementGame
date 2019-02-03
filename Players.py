import random
import pickle


class HumanPlayerInterface:
    '''
    The interface to a human player.
    Ideally, this interface is completely game-agnostic.
    It is responsible for
        - sending turns to the board
        - asking for a visualization (that way, the board need not distinguish between AI and human)
        - receiving and logging rewards
    Question: Should the player know the screen?
    Pros:
        - It makes messages easier
        - The game board need not distinguish between AI and human (or ask them if they want to see
          a message)
        - How to handle keyboard inputs from the "screen"?
    Con:
        - Coupling

    TODO: Number 1 priority is to figure out how to collect input in a clean way WITHOUT having to
    TODO: know the screen here.
    '''

    def __init__(self, somename, someboard, somescreen, playerNumber):
        self._name = somename
        self._board = someboard
        self._screen = somescreen
        self._boardstate = None
        self._symbols = ['o', 'x', '-']  # REMOVE
        self._reward = None
        self._playerNumber = playerNumber
        #self._playerNumber = self._screen.getPlayerLine()  # WHY DO I NEED THIS LINE THING?

    @property
    def name(self):
        return self._name

    @property
    def playerNumber(self):
        return self._playerNumber

    # TODO: rebuild this using the visualizer. Problem: how do I collect the user input?
    # TODO: turn() should ideally wrap the decision-making.
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

    def finalize(self):  # REMOVE the message bit
        self._boardstate = self._board.returnState()
        self.visualizeState()
        if self._reward == self._board.R_WIN:
            self._screen.putMessage('Oh, ich (' + self._name + ') habe gewonnen!\n', self._playerNumber)
        elif self._reward == self._board.R_DRAW:
            self._screen.putMessage('Hm, ich (' + self._name + ') habe ein Unentschieden geholt!\n', self._playerNumber)
        elif self._reward == self._board.R_DEFEAT:
            self._screen.putMessage('Mist, ich (' + self._name + ') habe verloren!\n', self._playerNumber)

    def visualizeState(self):  # REMOVE
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

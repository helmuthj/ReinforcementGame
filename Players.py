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
        - The game board need not distinguish between AI and human
        (however the game will ask Players if the want to know about game updates, because otherwise
        human players might not see what is happening until they are asked again to make a move)
        - Easy to handle keyboard inputs from the "screen"
    Con:
        - Coupling
    Decision:
        The player handles his own I/O device, the game should not bother.
    '''

    def __init__(self, somename, someboard, somescreen):
        self._name = somename
        self._screen = somescreen
        self._boardstate = None
        self._watchesState = True
        self._readsMessages = True
        self._reward = None
        # The screen tells the player once where it should send its messages to
        self._playerNumber = self._screen.getPlayerLine()

    @property
    def name(self):
        return self._name

    @property
    def playerNumber(self):
        return self._playerNumber

    @property
    def watchesState(self):
        return self._watchesState

    @property
    def readsMessages(self):
        return self._readsMessages

    def turn(self):
        # Only handle "technically" incorrect inputs here. Rule violations are handled by the game.
        while 1:
            try:
                move = int(self._screen.requestInput(self._name + ' zieht: ', self._playerNumber))
                break
            except ValueError:
                pass
        return move

    def sendReward(self, reward, resultingState):
        self._reward = reward

    def setState(self, state):
        self._boardstate = state
        self._screen.visualizeState(self._boardstate)

    def sendMessage(self, message):
        self._screen.putMessage(message, self._playerNumber)

    def finalize(self):
        pass

class DumbAI:

    def __init__(self, somename, someboard, experienceFile=None):
        self._name = somename
        self._board = someboard
        self._experienceFile = experienceFile
        self._game = []
        self._boardstate = None
        self._action = None

    def turn(self):
        # when asked to make a move, ask for the state, make smart bet,
        # return move, store state and action
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

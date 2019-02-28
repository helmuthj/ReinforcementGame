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

    def __init__(self, somename, visualizer):
        self._name = somename
        self._visualizer = visualizer
        self._boardstate = None
        self._watchesState = True
        self._readsMessages = True
        self._reward = None
        # The screen tells the player once where it should send its messages to
        self._playerNumber = self._visualizer.getPlayerLine()  # TODO: rename to line number

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
                action = int(self._visualizer.requestInput(self._name + ' zieht: ', self._playerNumber))
                break
            except ValueError:
                pass
        return action

    def sendReward(self, reward, resultingState):
        pass

    def setState(self, state):
        self._boardstate = state
        self._visualizer.visualizeState(self._boardstate)

    def sendMessage(self, message):
        self._visualizer.putMessage(message, self._playerNumber)

    def finalize(self):
        pass


class DumbAI:

    def __init__(self, somename, experienceFile=None):
        self._name = somename
        self._experienceFile = experienceFile
        self._game = []  # TODO: Rename to trajectory or something similar
        self._boardstate = None
        self._actionstate = None  # TODO: Check if "_actionstate" can be removed"
        self._action = None
        self._watchesState = False
        self._readsMessages = False

    @property
    def name(self):
        return self._name

    @property
    def watchesState(self):
        return self._watchesState

    @property
    def readsMessages(self):
        return self._readsMessages

    def setState(self, state):
        self._boardstate = state

    def turn(self):
        # remember in which state the board was when action was chosen
        self._actionstate = self._boardstate
        # select action, store, and return
        self._action = self.chooseAction(None)
        return self._action

    # TODO: remove hard-coded range of possible moves: this is not game-agnostic
    def chooseAction(self, forbiddenmoves=None):
        # chooseAction() does NOT store the action? It could also be purely hypothetical action
        # "forbiddenmoves" is currently an unused feature
        return random.randint(1, 9)

    def sendReward(self, reward, resultingState):
        experience = (self._actionstate, self._action, reward, resultingState)
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

    def __init__(self, somename, experienceFile, ql, curiosity=1.0):
        DumbAI.__init__(self, somename, experienceFile)
        self._ql = ql
        self._curiosity = curiosity

    def chooseAction(self, forbiddenmoves=None):
        # forbiddenmoves is currently unused
        return self._ql.selectAction(self._actionstate, self._curiosity)

    def sendReward(self, reward, resultingState):
        super(SmartAI, self).sendReward(reward, resultingState)
        # In order to avoid endless loops, I need to have this update here
        if resultingState is None:
            self._ql.updateQ(self._actionstate, self._action, reward, resultingState)

    def finalize(self):
        self._ql.batchlearnQ([self._game], 1, backprop=True)
        # reset
        self._game = []
        self._boardstate = None
        self._action = None

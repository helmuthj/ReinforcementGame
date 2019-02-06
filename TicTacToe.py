
class TicTacToe:
    '''
    TicTacToe board.
    This class:
        - knows the "rules" of the game
        - knows who is playing
        - requests players to place their moves when it is their turn
        - places their moves on the board and manages state transitions of the board
        - checks after each move if the board is in a terminal states
        - sends rewards to players
        - knows a game-specific visualizer that it can ask to display state and messages
    '''

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

    # class-level game status constant
    NOT_READY = -2
    READY = -1
    WIN_PL0 = 0
    WIN_PL1 = 1
    DRAW = 2

    def __init__(self, visualizer):
        self.winners = ((0, 1, 2), (3, 4, 5), (6, 7, 8),
                        (0, 3, 6), (1, 4, 7), (2, 5, 8),
                        (0, 4, 8), (6, 4, 2))
        self._boardstate = [TicTacToe.UNMARKED] * 9
        self._status = TicTacToe.NOT_READY
        self._whosturn = None
        self._players = None
        self._visualizer = visualizer

    def setplayers(self, players):
        self._players = players
        self._whosturn = 0
        self._status = TicTacToe.READY

    def reset(self):
        self._boardstate = [TicTacToe.UNMARKED] * 9
        self._whosturn = 0
        self._status = TicTacToe.READY

    # TODO: This loop could go into a separate class, the "game manager".
    def play(self):
        '''
        Main "game loop"
        :return:
        '''

        # Request moves from players as long as the game as is not in terminal states
        while self._status == TicTacToe.READY:
            # Inform player ONCE about current state
            self._players[self._whosturn].setState(self._boardstate)  # TODO: think about security

            # Request move from active player as long as invalid moves are selected
            while 1:
                move = self._players[self._whosturn].turn()
                # Valid moves change the board state
                if self.checkAndPlaceMove(move):
                    break
                # Invalid moves get sanctioned with an instant bad reward
                else:
                    self._players[self._whosturn].sendReward(TicTacToe.R_INVALID, None)

            # After each move, check for terminal states ("won", "draw")
            self.checkwon()
            self.checkdraw()

            # After each move, send rewards where appropriate
            self.checkRewards()

            # After each move, ask players if they want to see the state,
            # This obviously informs players also about the final state
            for player in self._players:
                if player.watchesState:
                    player.setState(self._boardstate)

            # give turn to next player in cycle
            self._whosturn = (self._whosturn + 1) % 2

        # End of while loop: Now the game is finished.
        # Ask the players if they want to see a message
        for idx, player in enumerate(self._players):
            if player.readsMessages:
                if self._status == idx:
                    message = player.name + ' hat gewonnen!\n'
                elif self._status == TicTacToe.DRAW:
                    message = player.name + ' hat ein Unentschieden geholt!\n'
                else:
                    message = player.name + ' hat leider verloren!\n'
                player.
                self._visualizer.writeMessage(message, player.playerNumber)

        # Let the players do "clean up" operations
        for player in self._players:
            player.finalize()

    def checkRewards(self):
        '''
        Manages sending out rewards.
        Note that this is a little tricky: Some moves should yield an instant reward (such as a
        winner) to the player who just did the move. For most other moves, we can only tell after
        the next player made his move, whether it was a good idea or not.
        In short:
            move to win: INSTANT big/small reward for winner/loser
            move to draw: INSTANT reward that is slightly better than default for both players
            open game: default reward IN NEXT ROUND if the next move doesn't terminate the game
        :return:
        '''
        if self._status == TicTacToe.READY:
            # the board is in "ready" state, i.e. nobody has won yet:
            # Send the PREVIOUS player the DEFAULT reward; the current player has to wait for his
            # reward because his move might turn out to be a bad one.
            otherplayer = (self._whosturn + 1) % 2
            self._players[otherplayer].sendReward(TicTacToe.R_DEFAULT, tuple(self._boardstate))
        elif self._status == TicTacToe.WIN_PL0 or self._status == TicTacToe.WIN_PL1:
            # there is a winner, i.e. the current player's move was a winning move
            winner = self._status
            loser = (winner + 1) % 2
            self._players[winner].sendReward(TicTacToe.R_WIN, None)
            self._players[loser].sendReward(TicTacToe.R_DEFEAT, None)
        elif self._status == TicTacToe.DRAW:
            # this is a draw, i.e. the current player's move led to a draw
            self._players[0].sendReward(TicTacToe.R_DRAW, None)
            self._players[1].sendReward(TicTacToe.R_DRAW, None)

    def returnState(self):
        return tuple(self._boardstate)

    def checkAndPlaceMove(self, move):
        '''
        Receive move, check if it is valid, update board if so.
        :param move: The field number selected by the player
        :return:
        '''
        # Only numbers between 1 and 9 are allowed
        if move < 1 or move > 9:
            return False
        else:
            # Only unmarked, i.e. empty field can be selected
            if self._boardstate[move - 1] != TicTacToe.UNMARKED:
                # illegal move
                return False
            else:
                # legal move: change state
                self._boardstate[move - 1] = self._whosturn
                return True

    def checkwon(self):
        for line in self.winners:
            player = self._boardstate[line[0]]
            if player == self._boardstate[line[1]] and player == self._boardstate[line[2]] and player != TicTacToe.UNMARKED:
                # it seems that player on the checked line just made a winning move: log
                self._status = player

    def checkdraw(self):
        if self._status == TicTacToe.READY:
            if all(bs != TicTacToe.UNMARKED for bs in self._boardstate):
                # this is a draw: log
                self._status = TicTacToe.DRAW


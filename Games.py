
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

        TODO: Use iterator instead of an index variable to indicate which player is the next.
        TODO: Review how the state is communicated: who should make sure that it is a tuple?.

    '''

    # class-level constant for possible actions
    POSSIBLE_ACTIONS = range(1, 10)

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

    def __init__(self):
        self.winners = ((0, 1, 2), (3, 4, 5), (6, 7, 8),
                        (0, 3, 6), (1, 4, 7), (2, 5, 8),
                        (0, 4, 8), (6, 4, 2))
        self._boardstate = [TicTacToe.UNMARKED] * 9
        self._status = TicTacToe.NOT_READY
        self._whosturn = None
        self._previousturn = None
        self._players = None

    def setplayers(self, players):
        self._players = players
        self._whosturn = 0
        self._status = TicTacToe.READY

    def reset(self):
        self._boardstate = [TicTacToe.UNMARKED] * 9
        self._whosturn = 0
        self._previousturn = None
        self._status = TicTacToe.READY

    # TODO: define state2tuple and use it throughout when state is passed out

    def play(self):
        '''
        Main "game loop" and terminal state handling.

        The game loop cycles through the following steps:
            1. Inform current player about current state
            2. Request move from current player until he makes a valid choice
            3. Update state (currently not a separate function !)
            4. Check for terminal states
            5. Send rewards if granted
            6. Send players a state update if they want one
            7. Switch to next player, remember who was the previous player

        Terminal state handling:
            1. Send players a message
            2. Notify players that they can

        :return:
        '''

        # Request moves from players as long as the game as is not in terminal states
        while self._status == TicTacToe.READY:
            # Inform player ONCE about current state
            self._players[self._whosturn].setState(tuple(self._boardstate))

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
            self._previousturn = self._whosturn
            self._whosturn = (self._previousturn + 1) % 2

        # End of while loop: The game is in terminal state.
        # Ask the players if they want to see a message
        for idx, player in enumerate(self._players):
            if player.readsMessages:
                if self._status == idx:
                    message = player.name + ' hat gewonnen!\n'
                elif self._status == TicTacToe.DRAW:
                    message = player.name + ' hat ein Unentschieden geholt!\n'
                else:
                    message = player.name + ' hat leider verloren!\n'
                player.sendMessage(message)

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
            # The board is in "ready" state, i.e. nobody has won yet:
            # Send the PREVIOUS player the DEFAULT reward; the current player has to wait for his
            # reward because his move might turn out to be a bad one.
            if self._previousturn is not None:
                self._players[self._previousturn].sendReward(TicTacToe.R_DEFAULT,
                                                             tuple(self._boardstate))
        elif self._status == TicTacToe.WIN_PL0 or self._status == TicTacToe.WIN_PL1:
            # There is a winner, i.e. the current player's move was a winning move
            winner = self._status
            loser = (winner + 1) % 2
            self._players[winner].sendReward(TicTacToe.R_WIN, None)
            self._players[loser].sendReward(TicTacToe.R_DEFEAT, None)
        elif self._status == TicTacToe.DRAW:
            # This is a draw, i.e. the current player's move led to a draw:
            for player in self._players:
                player.sendReward(TicTacToe.R_DRAW, None)

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
            if player == self._boardstate[line[1]] \
                    and player == self._boardstate[line[2]] \
                    and player != TicTacToe.UNMARKED:
                # it seems that player on the checked line just made a winning move: log
                self._status = player

    def checkdraw(self):
        if self._status == TicTacToe.READY:
            if all(bs != TicTacToe.UNMARKED for bs in self._boardstate):
                # this is a draw: log
                self._status = TicTacToe.DRAW


class VierGewinnt:

    # TODO: justify the values of the rewards.
    # NOTE: Only those rewards that are greater than R_DEFAULT get back-propagated (...max(Q)...)
    # class-level constants for rewards
    R_INVALID = -2
    R_DEFEAT = -1
    R_DEFAULT = 0
    R_DRAW = 0
    R_WIN = 1

    # class-level board constants
    MARKED_PL0 = 0
    MARKED_PL1 = 1
    UNMARKED = 2
    NCOLS = 5
    NROWS = 5

    # class-level constant for possible actions
    POSSIBLE_ACTIONS = range(1, NCOLS+1)

    # class level game status constant
    NOT_READY = -2
    READY = -1
    WIN_PL0 = 0
    WIN_PL1 = 1
    DRAW = 2

    def __init__(self):
        # note that the first index is for column, the second for row
        self._boardstate = [[VierGewinnt.UNMARKED for j in range(self.NCOLS)] for i in range(self.NROWS)]
        self._winner = ((( 0, -3), ( 0, -2), ( 0, -1)),  # west
                        ((-3, -3), (-2, -2), (-1, -1)),  # south west
                        ((-3,  0), (-2,  0), (-1,  0)),  # south
                        ((-3,  3), (-2,  2), (-1,  1)),  # south east
                        (( 0,  3), ( 0,  2), ( 0,  1)),  # east
                        (( 0,  1), ( 0, -2), ( 0, -1)),  # mostly west
                        (( 0, -1), ( 0,  2), ( 0,  1)),  # mostly east
                        (( 3, -3), ( 2, -2), ( 1, -1)),  # north west
                        (( 2, -2), ( 1, -1), (-1,  1)),  # mostly north west
                        (( 1, -1), (-1,  1), (-2,  2)),  # mostly south east
                        (( 3,  3), ( 2,  2), ( 1,  1)),  # north east
                        (( 2,  2), ( 1,  1), (-1, -1)),  # mostly north east
                        (( 1,  1), (-1, -1), (-2, -2)))  # mostly south west

        self._column_cnt = [0] * self.NCOLS
        self._status = VierGewinnt.NOT_READY
        self._whosturn = None
        self._previousturn = None
        self._players = None

    def state2tuple(self):
        return tuple([tuple(col) for col in self._boardstate])

    def setplayers(self, players):
        self._players = players
        self._whosturn = 0
        self._status = VierGewinnt.READY

    def reset(self):
        # TODO: remove stupid double loop
        self._boardstate = \
            [[VierGewinnt.UNMARKED for j in range(self.NCOLS)] for i in range(self.NCOLS)]
        self._column_cnt = [0] * self.NCOLS
        self._whosturn = 0
        self._status = VierGewinnt.READY

    def play(self):
        # TODO: Check if this can be outsourced since it is 99% identical to TicTacToe
        '''
        Main "game loop" and terminal state handling.

        The game loop cycles through the following steps:
            1. Inform current player about current state
            2. Request move from current player until he makes a valid choice
            3. Update state (currently not a separate function !)
            4. Check for terminal states
            5. Send rewards if granted
            6. Send players a state update if they want one
            7. Switch to next player, remember who was the previous player

        Terminal state handling:
            1. Send players a message
            2. Notify players that they can

        :return:
        '''

        # Request moves from players as long as the game as is not in terminal states
        while self._status == VierGewinnt.READY:
            # Inform player ONCE about current state
            self._players[self._whosturn].setState(self.state2tuple())

            # Request move from active player as long as invalid moves are selected
            cntInvalid = 0
            while 1:
                move = self._players[self._whosturn].turn()
                # Valid moves change the board state
                if self.checkAndPlaceMove(move):
                    break
                # Invalid moves get sanctioned with an instant bad reward
                else:
                    cntInvalid += 1
                    if cntInvalid >= 100:
                        print(self._boardstate)
                        raise Exception('Endless loop')
                    self._players[self._whosturn].sendReward(VierGewinnt.R_INVALID, None)

            # After each move, check for terminal states ("won", "draw")
            self.checkwon(move)
            self.checkdraw()

            # After each move, send rewards where appropriate
            self.checkRewards()

            # After each move, ask players if they want to see the state,
            # This obviously informs players also about the final state
            for player in self._players:
                if player.watchesState:
                    player.setState(self.state2tuple())

            # give turn to next player in cycle
            self._previousturn = self._whosturn
            self._whosturn = (self._previousturn + 1) % 2

        # End of while loop: The game is in terminal state.
        # Ask the players if they want to see a message
        # TODO: Messages with two HumanPlayers don't work correctly -> Fix
        for idx, player in enumerate(self._players):
            if player.readsMessages:
                if self._status == idx:
                    message = player.name + ' hat gewonnen!\n'
                elif self._status == VierGewinnt.DRAW:
                    message = player.name + ' hat ein Unentschieden geholt!\n'
                else:
                    message = player.name + ' hat leider verloren!\n'
                player.sendMessage(message)

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
        A note on "resultingState" that is send to sendReward():
            The idea is that the Q-function update should make a compromise between immediate and $
            possible future rewards of an action. For the future rewards, it hence needs to know the
            resulting state for an action.
            If the resulting state is a terminal state, there is no further future reward possible.
            That's why we send "None". We adhere to this convention inside updateQ(), where the
            "None"-case is handled in a special way.
        :return:
        '''
        if self._status == VierGewinnt.READY:
            # The board is in "ready" state, i.e. nobody has won yet:
            # Send the PREVIOUS player the DEFAULT reward; the current player has to wait for his
            # reward because his move might turn out to be a bad one.
            if self._previousturn is not None:
                self._players[self._previousturn].sendReward(VierGewinnt.R_DEFAULT,
                                                             self.state2tuple())
        elif self._status == VierGewinnt.WIN_PL0 or self._status == VierGewinnt.WIN_PL1:
            # There is a winner, i.e. the current player's move was a winning move
            winner = self._status
            loser = (winner + 1) % 2
            self._players[winner].sendReward(VierGewinnt.R_WIN, None)
            self._players[loser].sendReward(VierGewinnt.R_DEFEAT, None)
        elif self._status == VierGewinnt.DRAW:
            # This is a draw, i.e. the current player's move led to a draw:
            for player in self._players:
                player.sendReward(VierGewinnt.R_DRAW, None)

    def returnState(self):
        return self.state2tuple()

    def checkAndPlaceMove(self, move):
        '''
        Receive move, check if it is valid, update board if so.
        :param move: The field number selected by the player
        :return: Bool that indicates whether the move was valid or not
        '''
        if move not in VierGewinnt.POSSIBLE_ACTIONS:
            return False
        else:
            idxcol = move - 1
            idxrow = self._column_cnt[idxcol]
            if idxrow >= self.NROWS:
                # illegal move: row is full
                return False
            else:
                # legal move: change state and auxiliary state variable
                self._boardstate[idxrow][idxcol] = self._whosturn
                self._column_cnt[idxcol] += 1
                return True

    # TODO: is the lastmove variable really needed? It does speed things up. Use instance state?
    def checkwon(self, lastmove):
        # find location of last set stone and try all variants around it
        idxcol = lastmove - 1
        idxrow = self._column_cnt[idxcol]-1
        player = self._boardstate[idxrow][idxcol]
        for shifts in self._winner:
            won = True
            for shift in shifts:
                try:
                    i = idxrow + shift[0]
                    j = idxcol + shift[1]
                    if i < 0 or i >= self.NROWS or j < 0 or j >= self.NCOLS:
                        raise IndexError
                    if self._boardstate[i][j] != player:
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

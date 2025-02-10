"""
Utility functions for the Tic Tac Toe game.
"""

from typing import List, Optional, Tuple

# Define constants for players
X_PLAYER = "X"
O_PLAYER = "O"
EMPTY = " "


class TicTacToeBoard:
    def __init__(self):
        # Initialize empty 3x3 board
        self.board = [[EMPTY for _ in range(3)] for _ in range(3)]
        self.current_player = X_PLAYER

    def make_move(self, row: int, col: int) -> Tuple[bool, str]:
        """
        Make a move on the board.

        Args:
            row (int): Row index (0-2)
            col (int): Column index (0-2)

        Returns:
            Tuple[bool, str]: (Success status, Message with current board state or error)
        """
        # Validate move coordinates
        if not (0 <= row <= 2 and 0 <= col <= 2):
            return (
                False,
                "Invalid move: Position out of bounds. Please choose row and column between 0 and 2.",
            )

        # Check if position is already occupied
        if self.board[row][col] != EMPTY:
            return False, f"Invalid move: Position ({row}, {col}) is already occupied."

        # Make the move
        self.board[row][col] = self.current_player

        # Get board state
        board_state = self.get_board_state()

        # Switch player
        self.current_player = O_PLAYER if self.current_player == X_PLAYER else X_PLAYER

        return True, f"Move successful!\n{board_state}"

    def get_board_state(self) -> str:
        """
        Returns a string representation of the current board state.
        """
        board_str = "\n-------------\n"
        for row in self.board:
            board_str += f"| {' | '.join(row)} |\n-------------\n"
        return board_str

    def check_winner(self) -> Optional[str]:
        """
        Check if there's a winner.

        Returns:
            Optional[str]: The winning player (X or O) or None if no winner
        """
        # Check rows
        for row in self.board:
            if row.count(row[0]) == 3 and row[0] != EMPTY:
                return row[0]

        # Check columns
        for col in range(3):
            column = [self.board[row][col] for row in range(3)]
            if column.count(column[0]) == 3 and column[0] != EMPTY:
                return column[0]

        # Check diagonals
        diagonal1 = [self.board[i][i] for i in range(3)]
        if diagonal1.count(diagonal1[0]) == 3 and diagonal1[0] != EMPTY:
            return diagonal1[0]

        diagonal2 = [self.board[i][2 - i] for i in range(3)]
        if diagonal2.count(diagonal2[0]) == 3 and diagonal2[0] != EMPTY:
            return diagonal2[0]

        return None

    def is_board_full(self) -> bool:
        """
        Check if the board is full (draw condition).
        """
        return all(cell != EMPTY for row in self.board for cell in row)

    def get_valid_moves(self) -> List[Tuple[int, int]]:
        """
        Get a list of valid moves (empty positions).

        Returns:
            List[Tuple[int, int]]: List of (row, col) tuples representing valid moves
        """
        valid_moves = []
        for row in range(3):
            for col in range(3):
                if self.board[row][col] == EMPTY:
                    valid_moves.append((row, col))
        return valid_moves

    def get_game_state(self) -> Tuple[bool, str]:
        """
        Get the current game state.

        Returns:
            Tuple[bool, str]: (is_game_over, status_message)
        """
        winner = self.check_winner()
        if winner:
            return True, f"Player {winner} wins!"

        if self.is_board_full():
            return True, "It's a draw!"

        return False, "Game in progress"

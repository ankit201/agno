"""
Utility functions for the Tic Tac Toe game.
"""

import re
from typing import List, Optional, Tuple

from agents import get_tic_tac_toe

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


def play_tic_tac_toe(debug_mode: bool = True) -> None:
    """
    Start and manage a game of Tic Tac Toe between two AI agents.

    Args:
        debug_mode (bool): Whether to show debug information during the game
    """
    # Initialize the game
    master_agent = get_tic_tac_toe(debug_mode=debug_mode)
    game_board = TicTacToeBoard()

    print("Starting a new game of Tic Tac Toe!")
    print(game_board.get_board_state())

    # Game loop
    while True:
        # Get current player
        current_player = "X" if game_board.current_player == "X" else "O"
        agent = master_agent.team[0] if current_player == "X" else master_agent.team[1]

        # Get agent's move
        print(f"\n{current_player}'s turn ({agent.name}):")
        valid_moves = game_board.get_valid_moves()

        response = agent.run(
            f"""Current board state:\n{game_board.get_board_state()}\n
            Available valid moves (row, col): {valid_moves}\n
            Choose your next move from the valid moves list above.
            Respond with ONLY two numbers for row and column, e.g. "1 2".""",
            stream=False,
        )

        # Parse move from response content
        try:
            numbers = re.findall(r"\d+", response.content if response else "")
            row, col = map(int, numbers[:2])
            success, message = game_board.make_move(row, col)
            print(message)

            if not success:
                print("Invalid move! Try again.")
                continue

        except (ValueError, IndexError):
            print("Invalid move format! Try again.")
            continue

        # Check for game end
        winner = game_board.check_winner()
        if winner:
            print(f"\nGame Over! {winner} wins!")
            break

        if game_board.is_board_full():
            print("\nGame Over! It's a draw!")
            break

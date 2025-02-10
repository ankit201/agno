"""
Tic Tac Toe Battle
---------------------------------
This example shows how to build a Tic Tac Toe game where two AI agents play against each other.
The game features a master agent (referee) coordinating between two player agents using different
language models.

Usage Examples:
---------------
1. Quick game with default settings:
   master_agent = get_tic_tac_toe()
   play_tic_tac_toe()

2. Game with debug mode off:
   master_agent = get_tic_tac_toe(debug_mode=False)
   play_tic_tac_toe(debug_mode=False)

The game integrates:
  - Multiple AI models (Claude, GPT-4, etc.)
  - Turn-based gameplay coordination
  - Move validation and game state management
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from utils import TicTacToeBoard

project_root = str(Path(__file__).parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)


@dataclass
class ModelConfig:
    display_name: str
    model_id: str
    provider: str

    def get_model(self):
        if self.provider == "anthropic":
            return Claude(id=self.model_id)
        if self.provider == "openai":
            return OpenAIChat(id=self.model_id)
        if self.provider == "ollama":
            return Ollama(id=self.model_id)
        if self.provider == "google":
            return Gemini(id=self.model_id)
        raise ValueError(f"Invalid provider: {self.provider}")


# Model configuration
MODELS: Dict[str, ModelConfig] = {
    "claude": ModelConfig(
        display_name="Claude AI",
        model_id="claude-3-5-sonnet-20241022",
        provider="anthropic",
    ),
    "gpt4": ModelConfig(
        display_name="GPT-4",
        model_id="gpt-4o",
        provider="openai",
    ),
    "gemini": ModelConfig(
        display_name="Gemini AI",
        model_id="gemini-2.0-flash-exp",
        provider="google",
    ),
    "gpt-o3-mini": ModelConfig(
        display_name="GPT-o3-mini",
        model_id="o3-mini",
        provider="openai",
    ),
    "vision": ModelConfig(
        display_name="GPT-4 Vision",
        model_id="gpt-4o",
        provider="openai",
    ),
}

# Default model assignments
DEFAULT_MODELS = {
    "X": MODELS["gemini"],
    "O": MODELS["gpt-o3-mini"],
    "master": MODELS["gpt4"],
    "vision": MODELS["vision"],
}


def get_tic_tac_toe(
    model_x: ModelConfig = DEFAULT_MODELS["X"],
    model_o: ModelConfig = DEFAULT_MODELS["O"],
    model_master: ModelConfig = DEFAULT_MODELS["master"],
    debug_mode: bool = True,
) -> Agent:
    """
    Returns an instance of the Tic Tac Toe Master Agent that coordinates the game.

    Args:
        model_x: ModelConfig for player X
        model_o: ModelConfig for player O
        model_master: ModelConfig for the master agent
        debug_mode: Enable logging and debug features

    Returns:
        An instance of the configured Master Agent
    """
    tic_agent = Agent(
        name="Tic Agent",
        role="""You are the X player in Tic Tac Toe. Your goal is to win by placing three X's in a row (horizontally, vertically, or diagonally).
        
        Game Rules:
        - You must make valid moves on a 3x3 grid using row (0-2) and column (0-2) coordinates
        - The top-left corner is (0,0), and bottom-right is (2,2)
        - You can only place X's in empty spaces marked by " " on the board
        - You will be given a list of valid moves - only choose from these moves
        - Respond with ONLY the row and column numbers for your move, e.g. "1 2"
        
        Strategy:
        - Study the board carefully and make strategic moves
        - Try to create winning opportunities while blocking your opponent
        - Pay attention to the valid moves list to avoid illegal moves
        """,
        model=model_x.get_model(),
    )

    tac_agent = Agent(
        name="Tac Agent",
        role="""You are the O player in Tic Tac Toe. Your goal is to win by placing three O's in a row (horizontally, vertically, or diagonally).
        
        Game Rules:
        - You must make valid moves on a 3x3 grid using row (0-2) and column (0-2) coordinates
        - The top-left corner is (0,0), and bottom-right is (2,2)
        - You can only place O's in empty spaces marked by " " on the board
        - You will be given a list of valid moves - only choose from these moves
        - Respond with ONLY the row and column numbers for your move, e.g. "1 2"
        
        Strategy:
        - Study the board carefully and make strategic moves to win
        - Block your opponent's winning opportunities
        - Pay attention to the valid moves list to avoid illegal moves
        """,
        model=model_o.get_model(),
    )

    master_agent = Agent(
        name="Master Agent",
        role="""You are the referee of the Tic Tac Toe game. Your responsibilities include:
        
        Game Management:
        1. Track and maintain the current board state
        2. Validate all moves before they are made
        3. Ensure moves are only made in empty spaces (marked by " ")
        4. Keep track of whose turn it is (X goes first)
        
        Move Validation:
        1. Check that moves are within the 3x3 grid (0-2 for rows and columns)
        2. Verify the chosen position is empty before allowing a move
        3. Maintain and provide the list of valid moves to players
        
        Game State Checking:
        1. Check for winning conditions after each move:
           - Three X's or O's in a row horizontally
           - Three X's or O's in a row vertically
           - Three X's or O's in a row diagonally
        2. Check for draw conditions:
           - Board is full with no winner
        
        Communication:
        1. Announce the current state of the board after each move
        2. Declare moves as valid or invalid
        3. Announce the winner or draw when game ends
        4. Provide clear feedback to players about their moves
        
        You will coordinate between the X and O players, ensuring fair play and proper game progression.
        """,
        model=model_master.get_model(),
        team=[tic_agent, tac_agent],
        show_tool_calls=True,
        debug_mode=debug_mode,
        markdown=True,
    )

    return master_agent


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
            import re

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


if __name__ == "__main__":
    play_tic_tac_toe()

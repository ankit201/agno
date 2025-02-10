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
from typing import Tuple

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat

project_root = str(Path(__file__).parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)


from utils import TicTacToeBoard


@dataclass
class ModelConfig:
    display_name: str
    model_id: str
    provider: str = "openai"

    def get_model(self):
        if self.provider == "anthropic":
            return Claude(id=self.model_id)
        if self.provider == "openai":
            return OpenAIChat(id=self.model_id)
        if self.provider == "ollama":
            return Ollama(id=self.model_id)
        raise ValueError(f"Invalid provider: {self.provider}")


# TODO: Add model configs for other providers


@dataclass
class AgentConfig:
    name: str
    model: ModelConfig
    player: str
    description: str

    @property
    def model_name(self) -> str:
        return self.model.display_name


# Define model configurations
MODELS = {
    "claude": ModelConfig(
        display_name="Claude AI",
        model_id="claude-3-5-sonnet-20241022",
        provider="anthropic",
    ),
    "gpt4": ModelConfig(
        display_name="GPT-o3-mini", model_id="o3-mini", provider="openai"
    ),
}

# Update agent configurations to use model configs
AGENT_CONFIGS = {
    "X": AgentConfig(
        name="Tic Agent",
        model=MODELS["claude"],
        player="X",
        description="Claude-3.5-Sonnet",
    ),
    "O": AgentConfig(
        name="Tac Agent", model=MODELS["gpt4"], player="O", description="GPT-4 Turbo"
    ),
}


def get_agent_info(player: str) -> Tuple[str, str]:
    """Get agent name and model name for a player"""
    config = AGENT_CONFIGS.get(player)
    if not config:
        raise ValueError(f"Invalid player: {player}")
    return config.name, config.model_name


def get_tic_tac_toe(
    model_id_x: str = "anthropic:claude-3-5-sonnet-20241022",
    model_id_o: str = "openai:o3-mini",
    debug_mode: bool = True,
) -> Agent:
    """
    Returns an instance of the Tic Tac Toe Master Agent that coordinates the game between two AI players.

    The Master Agent will:
      - Initialize two player agents (X and O) with different language models
      - Coordinate turns between players
      - Validate moves and maintain game state
      - Track and announce game outcomes

    Args:
        model_id_x: Model identifier for player X in format 'provider:model_name'
        model_id_o: Model identifier for player O in format 'provider:model_name'
        debug_mode: Enable logging and debug features

    Returns:
        An instance of the configured Master Agent
    """
    # Parse model providers and names
    x_provider, x_model = model_id_x.split(":")
    o_provider, o_model = model_id_o.split(":")

    # Update model configurations
    MODELS = {
        "x_model": ModelConfig(
            display_name=f"{x_provider.title()} AI",
            model_id=x_model,
            provider=x_provider,
        ),
        "o_model": ModelConfig(
            display_name=f"{o_provider.title()} AI",
            model_id=o_model,
            provider=o_provider,
        ),
    }

    # Update agent configurations
    AGENT_CONFIGS = {
        "X": AgentConfig(
            name="Tic Agent",
            model=MODELS["x_model"],
            player="X",
            description=f"{x_provider.title()}-{x_model}",
        ),
        "O": AgentConfig(
            name="Tac Agent",
            model=MODELS["o_model"],
            player="O",
            description=f"{o_provider.title()}-{o_model}",
        ),
    }

    tic_agent = Agent(
        name=AGENT_CONFIGS["X"].name,
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
        model=AGENT_CONFIGS["X"].model.get_model(),
    )

    tac_agent = Agent(
        name=AGENT_CONFIGS["O"].name,
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
        model=AGENT_CONFIGS["O"].model.get_model(),
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
        model=MODELS["gpt4"].get_model(),
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
            # Extract numbers from response
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

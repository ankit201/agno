"""
Tic Tac Toe Battle
---------------------------------
This example shows how to build a Tic Tac Toe game where two agents play against each other.

Usage Examples:
---------------
# Method 1: Run directly
python -m cookbook.examples.apps.tic_tac_toe.agents

# Method 2: Import and run
from cookbook.examples.apps.tic_tac_toe.agents import play_tic_tac_toe
play_tic_tac_toe()
"""

import sys
import os
from pathlib import Path
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat

project_root = str(Path(__file__).parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)


from utils import TicTacToeBoard

def get_tic_tac_toe(
    debug_mode: bool = True,
) -> Agent:
    """
    Returns an instance of Tic Tac Toe Agent with integrated tools for playing the game.
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
        model=Claude(id="claude-3-5-sonnet-20241022"),
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
        model=OpenAIChat(id="gpt-4o"),
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
        model=OpenAIChat(id="gpt-4o-mini"),
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
            stream=False
        )
        
        # Parse move from response content
        try:
            # Extract numbers from response
            import re
            numbers = re.findall(r'\d+', response.content if response else "")
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

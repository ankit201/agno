import io

import nest_asyncio
import streamlit as st
from agents import DEFAULT_MODELS, MODELS, get_tic_tac_toe
from agno.agent import Agent
from agno.media import Image as AgnoImage
from agno.utils.log import logger
from PIL import Image as PILImage
from utils import TicTacToeBoard

nest_asyncio.apply()

# Page configuration
st.set_page_config(
    page_title="Tic Tac Toe AI Battle",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
CUSTOM_CSS = """
<style>
.main-title {
    text-align: center;
    font-size: 3em;
    font-weight: bold;
    padding: 0.5em 0;
    color: white;
}
.subtitle {
    text-align: center;
    color: #666;
    margin-bottom: 1em;
}
.game-board {
    display: grid;
    grid-template-columns: repeat(3, 80px);
    gap: 5px;
    justify-content: center;
    margin: 1em auto;
    background: #666;
    padding: 5px;
    border-radius: 8px;
    width: fit-content;
}
.board-cell {
    width: 80px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2em;
    font-weight: bold;
    background-color: #2b2b2b;
    color: #fff;
    transition: all 0.3s ease;
    margin: 0;
    padding: 0;
}
.board-cell:hover {
    background-color: #3b3b3b;
}
.agent-status {
    background-color: #1e1e1e;
    border-left: 4px solid #4CAF50;
    padding: 10px;
    margin: 10px auto;
    border-radius: 4px;
    max-width: 600px;
    text-align: center;
}
.agent-thinking {
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #2b2b2b;
    padding: 10px;
    border-radius: 5px;
    margin: 10px auto;
    border-left: 4px solid #FFA500;
    max-width: 600px;
}
.move-history {
    background-color: #2b2b2b;
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
}

.move-entry {
    display: flex;
    align-items: center;
    padding: 12px;
    margin: 8px 0;
    background-color: #2b2b2b;
    border-radius: 4px;
}

.move-entry.player1 {
    border-left: 4px solid #4CAF50;
}

.move-entry.player2 {
    border-left: 4px solid #f44336;
}

.move-number {
    font-weight: bold;
    margin-right: 10px;
}

.move-number.player1 {
    color: #4CAF50;
}

.move-number.player2 {
    color: #f44336;
}

.mini-board {
    display: grid;
    grid-template-columns: repeat(3, 25px);
    gap: 2px;
    background: #444;
    padding: 2px;
    border-radius: 4px;
    margin-right: 15px;
}

.mini-cell {
    width: 25px;
    height: 25px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: bold;
    background-color: #2b2b2b;
    color: #fff;
}

.mini-cell.highlight.player1 {
    background-color: #4CAF50;
    color: white;
}

.mini-cell.highlight.player2 {
    background-color: #f44336;
    color: white;
}

.move-info {
    flex-grow: 1;
}

.thinking-container {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1000;
    min-width: 300px;
}

.agent-thinking {
    background-color: rgba(43, 43, 43, 0.95);
    border: 1px solid #4CAF50;
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
}

.history-header {
    text-align: center;
    margin-bottom: 30px;
}

.history-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 40px;
    width: 100%;
    padding: 0;
    margin: 40px 0 20px;
}

.history-column-left, .history-column-right {
    display: flex;
    flex-direction: column;
    width: 100%;
}

.history-column-left {
    align-items: flex-end;  /* Align to right side of left column */
}

.history-column-right {
    align-items: flex-start;  /* Align to left side of right column */
}

.move-entry {
    display: flex;
    align-items: center;
    padding: 12px;
    margin: 8px 0;
    background-color: #2b2b2b;
    border-radius: 4px;
    width: 500px;  /* Fixed width for all entries */
}

.move-entry.player1 {
    border-left: 4px solid #4CAF50;
}

.move-entry.player2 {
    border-left: 4px solid #f44336;
}

/* Move info styling */
.move-info {
    flex-grow: 1;
    padding-left: 12px;
}

/* Add column headers */
.history-column-header {
    font-size: 1.1em;
    font-weight: bold;
    padding: 10px;
    margin-bottom: 10px;
    text-align: center;
    border-bottom: 2px solid #444;
}

.player1-header {
    color: #4CAF50;
}

.player2-header {
    color: #f44336;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def display_board(board: TicTacToeBoard):
    """Display the Tic Tac Toe board using Streamlit"""
    board_html = '<div class="game-board">'

    for i in range(3):
        for j in range(3):
            cell_value = board.board[i][j]
            board_html += f'<div class="board-cell">{cell_value}</div>'

    board_html += "</div>"
    st.markdown(board_html, unsafe_allow_html=True)


def show_agent_status(agent_name: str, status: str):
    """Display the current agent status"""
    st.markdown(
        f"""<div class="agent-status">
            🤖 <b>{agent_name}</b>: {status}
        </div>""",
        unsafe_allow_html=True,
    )


def show_thinking_indicator(agent_name: str):
    """Show a thinking indicator for the current agent"""
    st.markdown(
        f"""<div class="agent-thinking">
            <div style="margin-right: 10px;">🔄</div>
            <div>{agent_name} is thinking...</div>
        </div>""",
        unsafe_allow_html=True,
    )


def create_mini_board_html(
    board_state: list, highlight_pos: tuple = None, is_player1: bool = True
) -> str:
    """Create HTML for a mini board with player-specific highlighting"""
    html = '<div class="mini-board">'
    for i in range(3):
        for j in range(3):
            highlight = (
                f"highlight player{1 if is_player1 else 2}"
                if highlight_pos and (i, j) == highlight_pos
                else ""
            )
            html += f'<div class="mini-cell {highlight}">{board_state[i][j]}</div>'
    html += "</div>"
    return html


def display_move_history():
    """Display the move history with mini boards in two columns"""
    st.markdown(
        '<h3 style="text-align: center; margin-bottom: 30px;">📜 Game History</h3>',
        unsafe_allow_html=True,
    )
    history_container = st.empty()

    if "move_history" in st.session_state and st.session_state.move_history:
        # Split moves into player 1 and player 2 moves
        p1_moves = []
        p2_moves = []
        current_board = [[" " for _ in range(3)] for _ in range(3)]

        # Process all moves first
        for move in st.session_state.move_history:
            row, col = map(int, move["move"].split(","))
            is_player1 = "Player 1" in move["player"]
            symbol = "X" if is_player1 else "O"
            current_board[row][col] = symbol
            board_copy = [row[:] for row in current_board]

            move_html = f"""<div class="move-entry player{1 if is_player1 else 2}">
                {create_mini_board_html(board_copy, (row, col), is_player1)}
                <div class="move-info">
                    <div class="move-number player{1 if is_player1 else 2}">Move #{move['number']}</div>
                    <div>{move['player']}</div>
                    <div style="font-size: 0.9em; color: #888">Position: ({row}, {col})</div>
                </div>
            </div>"""

            if is_player1:
                p1_moves.append(move_html)
            else:
                p2_moves.append(move_html)

        max_moves = max(len(p1_moves), len(p2_moves))
        history_content = '<div class="history-grid">'

        # Left column (Player 1)
        history_content += '<div class="history-column-left">'
        for i in range(max_moves):
            entry_html = ""
            # Player 1 move
            if i < len(p1_moves):
                entry_html += p1_moves[i]
            history_content += entry_html
        history_content += "</div>"

        # Right column (Player 2)
        history_content += '<div class="history-column-right">'
        for i in range(max_moves):
            entry_html = ""
            # Player 2 move
            if i < len(p2_moves):
                entry_html += p2_moves[i]
            history_content += entry_html
        history_content += "</div>"

        history_content += "</div>"

        # Display the content
        history_container.markdown(history_content, unsafe_allow_html=True)
    else:
        history_container.markdown(
            """<div style="text-align: center; color: #666; padding: 20px;">
                No moves yet. Start the game to see the history!
            </div>""",
            unsafe_allow_html=True,
        )


def extract_board_state_from_image(image) -> str:
    """
    Use GPT-4o to analyze the Tic Tac Toe board image and return the board state.
    """
    vision_agent = Agent(
        name="Vision Agent", model=DEFAULT_MODELS["vision"].get_model()
    )

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")
    img_byte_arr = img_byte_arr.getvalue()

    image_obj = AgnoImage(content=img_byte_arr)

    prompt = """Analyze this Tic Tac Toe board image. Return ONLY a 3x3 matrix showing the board state where:
- Use 'X' for X moves
- Use 'O' for O moves
- Use '_' for empty spaces
Do not add any explanation or formatting. Just return exactly 3 lines with 3 characters each.
Example:
XO_
_X_
O__"""

    logger.info(f"Vision Agent Prompt: {prompt}")

    response = vision_agent.run(prompt, images=[image_obj])

    logger.info(f"Vision Agent Response: {response.content}")

    # Clean up the response to handle potential formatting
    board_state = response.content.strip().replace("```", "").strip()

    rows = [row.strip() for row in board_state.split("\n") if row.strip()]
    if len(rows) != 3 or any(len(row) != 3 for row in rows):
        raise ValueError("Invalid board state format from vision model")

    logger.info(f"Parsed Board State:\n{'\n'.join(rows)}")

    return "\n".join(rows)


def initialize_board_from_state(board_state: str) -> TicTacToeBoard:
    """
    Initialize a TicTacToeBoard from a string representation.
    The input should be a 3x3 matrix with X, O, and _ characters.
    Example:
    XO_
    _X_
    O__
    """
    board = TicTacToeBoard()
    rows = board_state.strip().split("\n")

    if len(rows) != 3:
        raise ValueError(f"Invalid board state: expected 3 rows, got {len(rows)}")

    for i, row in enumerate(rows):
        if len(row) != 3:
            raise ValueError(
                f"Invalid row length in row {i}: expected 3, got {len(row)}"
            )

        for j, cell in enumerate(row):
            if cell == "X" or cell == "O":
                board.board[i][j] = cell
            elif cell == "_" or cell == " ":
                board.board[i][j] = " "
            else:
                raise ValueError(f"Invalid character in board state: {cell}")

    x_count = sum(row.count("X") for row in board.board)
    o_count = sum(row.count("O") for row in board.board)
    board.current_player = "O" if x_count > o_count else "X"

    logger.info(f"Initialized board state:\n{board.get_board_state()}")
    logger.info(f"Next player: {board.current_player}")

    return board


def main():
    st.markdown(
        "<h1 class='main-title'>Tic Tac Toe AI Battle</h1>", unsafe_allow_html=True
    )
    st.markdown(
        "<p class='subtitle'>Watch AI agents battle it out in Tic Tac Toe!</p>",
        unsafe_allow_html=True,
    )

    # Initialize session state
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
        st.session_state.game_paused = False
        st.session_state.move_history = []

    # Sidebar controls
    with st.sidebar:
        st.markdown("### Game Controls")

        available_models = {
            "Gemini": "gemini",
            "GPT-4o": "gpt-4o",
            "Claude": "claude",
            "GPT-o3-mini": "gpt-o3-mini",
            "Llama 3": "llama",
        }

        # Model selection dropdowns
        col1, col2 = st.columns(2)
        with col1:
            selected_p1 = st.selectbox(
                "Player 1 (X) Model",
                list(available_models.keys()),
                index=list(available_models.values()).index("gpt-o3-mini"),
                key="model_p1",
            )
        with col2:
            selected_p2 = st.selectbox(
                "Player 2 (O) Model",
                list(available_models.keys()),
                index=list(available_models.values()).index("gemini"),
                key="model_p2",
            )

        # Game control buttons
        col1, col2 = st.columns(2)
        with col1:
            if not st.session_state.game_started:
                if st.button("▶️ Start Game"):
                    # Get selected models
                    model_p1 = MODELS[available_models[selected_p1]]
                    model_p2 = MODELS[available_models[selected_p2]]

                    st.session_state.master_agent = get_tic_tac_toe(
                        model_x=model_p1, model_o=model_p2, debug_mode=True
                    )
                    st.session_state.game_board = TicTacToeBoard()
                    st.session_state.game_started = True
                    st.session_state.move_history = []
                    st.session_state.game_paused = False
                    st.rerun()
            else:
                game_over, _ = st.session_state.game_board.get_game_state()
                if not game_over:
                    if st.button(
                        "⏸️ Pause" if not st.session_state.game_paused else "▶️ Resume"
                    ):
                        st.session_state.game_paused = not st.session_state.game_paused
                        st.rerun()

        with col2:
            if st.session_state.game_started:
                if st.button("🔄 New Game"):
                    # Get selected models
                    model_p1 = MODELS[available_models[selected_p1]]
                    model_p2 = MODELS[available_models[selected_p2]]

                    st.session_state.master_agent = get_tic_tac_toe(
                        model_x=model_p1, model_o=model_p2, debug_mode=True
                    )
                    st.session_state.game_board = TicTacToeBoard()
                    st.session_state.move_history = []
                    st.session_state.game_paused = False
                    st.rerun()

        st.markdown("### Start from Image")
        uploaded_file = st.file_uploader(
            "Upload a Tic Tac Toe board image", type=["png", "jpg", "jpeg"]
        )

        if uploaded_file is not None and not st.session_state.game_started:
            try:
                image = PILImage.open(uploaded_file)
                st.image(image, caption="Uploaded board image", width=200)

                if st.button("Start Game from Image"):
                    with st.spinner("Analyzing board image..."):
                        board_state = extract_board_state_from_image(image)

                    st.session_state.master_agent = get_tic_tac_toe(debug_mode=True)
                    st.session_state.game_board = initialize_board_from_state(
                        board_state
                    )
                    st.session_state.game_started = True
                    st.session_state.move_history = []
                    st.session_state.game_paused = False
                    st.rerun()
            except Exception as e:
                st.error(f"Error processing image: {str(e)}")
                logger.error(f"Image processing error: {str(e)}")

    # Update the header to show current models
    if st.session_state.game_started:
        st.markdown(
            f"<h3 style='color:#87CEEB; text-align:center;'>{selected_p1} vs {selected_p2}</h3>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<h3 style='color:#87CEEB; text-align:center;'>Select models and start the game!</h3>",
            unsafe_allow_html=True,
        )

    # Main game area
    if st.session_state.game_started:
        game_over, status = st.session_state.game_board.get_game_state()

        display_board(st.session_state.game_board)

        # Show game status (winner/draw/current player)
        if game_over:
            winner_player = (
                "X" if "X wins" in status else "O" if "O wins" in status else None
            )
            if winner_player:
                winner_num = "1" if winner_player == "X" else "2"
                winner_model = selected_p1 if winner_player == "X" else selected_p2
                st.success(f"🏆 Game Over! Player {winner_num} ({winner_model}) wins!")
            else:
                st.info("🤝 Game Over! It's a draw!")
        else:
            # Show current player status
            current_player = st.session_state.game_board.current_player
            player_num = "1" if current_player == "X" else "2"
            current_model_name = selected_p1 if current_player == "X" else selected_p2

            show_agent_status(
                f"Player {player_num} ({current_model_name})",
                "It's your turn",
            )

        display_move_history()

        if not st.session_state.game_paused and not game_over:
            # Thinking indicator
            st.markdown(
                f"""<div class="thinking-container">
                    <div class="agent-thinking">
                        <div style="margin-right: 10px; display: inline-block;">🔄</div>
                        Player {player_num} ({current_model_name}) is thinking...
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

            valid_moves = st.session_state.game_board.get_valid_moves()

            response = st.session_state.master_agent.team[0].run(
                f"""Current board state:\n{st.session_state.game_board.get_board_state()}\n
                Available valid moves (row, col): {valid_moves}\n
                Choose your next move from the valid moves list above.
                Respond with ONLY two numbers for row and column, e.g. "1 2".""",
                stream=False,
            )

            try:
                import re

                numbers = re.findall(r"\d+", response.content if response else "")
                row, col = map(int, numbers[:2])
                success, message = st.session_state.game_board.make_move(row, col)

                if success:
                    move_number = len(st.session_state.move_history) + 1
                    st.session_state.move_history.append(
                        {
                            "number": move_number,
                            "player": f"Player {player_num} ({current_model_name})",
                            "move": f"{row},{col}",
                        }
                    )

                    logger.info(
                        f"Move {move_number}: Player {player_num} ({current_model_name}) placed at position ({row}, {col})"
                    )
                    logger.info(
                        f"Board state:\n{st.session_state.game_board.get_board_state()}"
                    )

                    # Check game state after move
                    game_over, status = st.session_state.game_board.get_game_state()
                    if game_over:
                        logger.info(f"Game Over - {status}")
                        if "wins" in status:
                            st.success(f"🏆 Game Over! {status}")
                        else:
                            st.info(f"🤝 Game Over! {status}")
                        st.session_state.game_paused = True
                    st.rerun()
                else:
                    logger.error(f"Invalid move attempt: {message}")
                    st.error(f"Invalid move: {message}")

            except Exception as e:
                logger.error(f"Error processing move: {str(e)}")
                st.error(f"Error processing move: {str(e)}")
    else:
        st.info("👈 Click 'Start Game' in the sidebar to begin!")

    st.sidebar.markdown("### About")
    st.sidebar.markdown(f"""
    Watch two AI agents play Tic Tac Toe:
    - Player 1 (X): {selected_p1}
    - Player 2 (O): {selected_p2}
    - Master Agent: {DEFAULT_MODELS['master'].display_name} - Coordinates the game
    
    The agents use strategic thinking to:
    - Make winning moves
    - Block opponent's winning moves
    - Control the center and corners
    """)


if __name__ == "__main__":
    main()

import nest_asyncio
import streamlit as st
from agents import DEFAULT_MODELS, get_tic_tac_toe
from agno.utils.log import logger
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


def display_move_history():
    """Display the move history in the sidebar"""
    if "move_history" in st.session_state and st.session_state.move_history:
        st.sidebar.markdown("### Move History")
        for move in st.session_state.move_history:
            st.sidebar.markdown(
                f"""<div class="move-history">
                    Move {move['number']}: Player {move['player']} → ({move['move']})
                </div>""",
                unsafe_allow_html=True,
            )


def main():
    st.markdown(
        "<h1 class='main-title'>Tic Tac Toe AI Battle</h1>", unsafe_allow_html=True
    )
    st.markdown(
        "<p class='subtitle'>Watch AI agents battle it out in Tic Tac Toe!</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<h3 style='color:#87CEEB; text-align:center;'>{DEFAULT_MODELS['X'].display_name} vs {DEFAULT_MODELS['O'].display_name}</h3>",
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

        col1, col2 = st.columns(2)

        with col1:
            if not st.session_state.game_started:
                if st.button("▶️ Start Game"):
                    st.session_state.master_agent = get_tic_tac_toe(debug_mode=True)
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
                    st.session_state.master_agent = get_tic_tac_toe(debug_mode=True)
                    st.session_state.game_board = TicTacToeBoard()
                    st.session_state.move_history = []
                    st.session_state.game_paused = False
                    st.rerun()

    # Main game area
    if st.session_state.game_started:
        game_over, status = st.session_state.game_board.get_game_state()

        # Always display current board state
        display_board(st.session_state.game_board)

        display_move_history()

        if game_over:
            winner_player = (
                "X" if "X wins" in status else "O" if "O wins" in status else None
            )
            if winner_player:
                model_config = DEFAULT_MODELS[winner_player]
                st.success(f"🏆 Game Over! {model_config.display_name} wins!")
            else:
                st.info("🤝 Game Over! It's a draw!")
            st.session_state.game_paused = True
        else:
            # Show current player and status
            current_player = st.session_state.game_board.current_player
            agent = (
                st.session_state.master_agent.team[0]
                if current_player == "X"
                else st.session_state.master_agent.team[1]
            )
            model_config = DEFAULT_MODELS[current_player]

            show_agent_status(
                f"{model_config.display_name} ({agent.name})",
                f"It's your turn (Player {current_player})",
            )

            # Auto-play if not paused
            if not st.session_state.game_paused:
                with st.spinner(
                    f"🎲 {model_config.display_name} ({agent.name}) is thinking..."
                ):
                    valid_moves = st.session_state.game_board.get_valid_moves()

                    response = agent.run(
                        f"""Current board state:\n{st.session_state.game_board.get_board_state()}\n
                        Available valid moves (row, col): {valid_moves}\n
                        Choose your next move from the valid moves list above.
                        Respond with ONLY two numbers for row and column, e.g. "1 2".""",
                        stream=False,
                    )

                    try:
                        import re

                        numbers = re.findall(
                            r"\d+", response.content if response else ""
                        )
                        row, col = map(int, numbers[:2])
                        success, message = st.session_state.game_board.make_move(
                            row, col
                        )

                        if success:
                            # Add move to history
                            move_number = len(st.session_state.move_history) + 1
                            st.session_state.move_history.append(
                                {
                                    "number": move_number,
                                    "player": f"{model_config.display_name} ({current_player})",
                                    "move": f"{row},{col}",
                                }
                            )

                            # Log the move in terminal
                            logger.info(
                                f"Move {move_number}: {model_config.display_name} (Player {current_player}) placed at position ({row}, {col})"
                            )
                            logger.info(
                                f"Board state:\n{st.session_state.game_board.get_board_state()}"
                            )

                            # Check game state after move
                            game_over, status = (
                                st.session_state.game_board.get_game_state()
                            )
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

    # About section in sidebar
    st.sidebar.markdown("### About")
    st.sidebar.markdown(f"""
    Watch two AI agents play Tic Tac Toe:
    - Player X: {DEFAULT_MODELS['X'].display_name} (Tic Agent)
    - Player O: {DEFAULT_MODELS['O'].display_name} (Tac Agent)
    - Master Agent: {DEFAULT_MODELS['master'].display_name} - Coordinates the game
    
    The agents use strategic thinking to:
    - Make winning moves
    - Block opponent's winning moves
    - Control the center and corners
    """)


if __name__ == "__main__":
    main()

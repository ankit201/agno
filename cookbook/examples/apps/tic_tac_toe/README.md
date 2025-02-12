# Tic Tac Toe AI Battle

This example demonstrates how to build an interactive Tic Tac Toe game where AI agents compete against each other. The application showcases how to:
- Coordinate multiple AI agents in a turn-based game
- Use different language models for different players
- Create an interactive web interface with Streamlit
- Handle game state and move validation
- Display real-time game progress and move history

## Features
- Multiple AI models support (GPT-4, Claude, Gemini, etc.)
- Real-time game visualization
- Move history tracking with board states
- Interactive player selection
- Game state management
- Move validation and coordination

### 1. Create a virtual environment

```shell
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```shell
pip install -r cookbook/examples/apps/tic_tac_toe/requirements.txt
```

### 3. Export API Keys

The game supports multiple AI models. Export the API keys for the models you want to use:

```shell
# Required for OpenAI models (GPT-4, GPT-3.5)
export OPENAI_API_KEY=***

# Optional - for additional models
export ANTHROPIC_API_KEY=***  # For Claude models
export GOOGLE_API_KEY=***     # For Gemini models
export GROQ_API_KEY=***       # For Groq models
```

### 4. Run the Game

```shell
streamlit run cookbook/examples/apps/tic_tac_toe/app.py
```

- Open [localhost:8501](http://localhost:8501) to view the game interface

## How It Works

The game consists of three main components:

1. **Master Agent (Referee)**
   - Coordinates the game
   - Validates moves
   - Maintains game state
   - Determines game outcome

2. **Player Agents**
   - Make strategic moves
   - Analyze board state
   - Follow game rules
   - Respond to opponent moves

3. **Web Interface**
   - Displays game board
   - Shows move history
   - Allows model selection
   - Provides game controls

## Available Models

The game supports various AI models:
- GPT-4 (OpenAI)
- Claude (Anthropic)
- Gemini (Google)
- GPT-3.5 Mini
- Llama 3

## Game Features

1. **Interactive Board**
   - Real-time updates
   - Visual move tracking
   - Clear game status display

2. **Move History**
   - Detailed move tracking
   - Board state visualization
   - Player action timeline

3. **Game Controls**
   - Start/Pause game
   - Reset board
   - Select AI models
   - View game history

4. **Performance Analysis**
   - Move timing
   - Strategy tracking
   - Game statistics

## Contributing

Feel free to contribute to this example by:
- Adding new AI models
- Improving the UI/UX
- Enhancing game strategies
- Adding new features

## Support

Join our [Discord community](https://agno.link/discord) for help and discussions.

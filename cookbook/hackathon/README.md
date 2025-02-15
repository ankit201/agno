# Hackathon Resources

Thank you for using Agno to build your hackathon project! Here you'll find setup guides, examples, and resources to bring your multimodal agents to life.

## Environment Setup

Let's get your environment setup for the hackathon. Here are the steps:

1. Create a virtual environment
2. Install libraries
3. Export your API keys

### Create a virtual environment

You can use `python3 -m venv` or `uv` to create a virtual environment.

- Standard python

```shell
python3 -m venv .venv
source .venv/bin/activate
```

- Using uv

```shell
uv venv --python 3.12
source .venv/bin/activate
```

### Install libraries

Install the `agno` python package along with the models and tools you want to use.

- Standard python

```shell
pip install -U agno openai
```

- Using uv

```shell
uv pip install -U agno openai
```

### Export your API keys

Export the API keys for the models and tools you want to use.

```shell
export OPENAI_API_KEY=***
export GOOGLE_API_KEY=***
export ELEVEN_LABS_API_KEY=***
```

## Text Agents

Here are some examples of Text Agents built with Agno:

- [Simple Text Agent](cookbook/hackathon/examples/simple_text_agent.py)
- [Agent with Tools](cookbook/hackathon/examples/agent_with_tools.py)
- [Agent with Knowledge](cookbook/hackathon/examples/agent_with_knowledge.py)
- [Agent with Structured Outputs](cookbook/hackathon/examples/structured_output.py)
- [Research Agent](cookbook/hackathon/examples/research_agent.py)
- [Youtube Agent](cookbook/hackathon/examples/youtube_agent.py)

## Image Agents

- [Image Input + Tools](cookbook/hackathon/examples/image_input_with_tools.py)
- [Generate Image](cookbook/hackathon/examples/generate_image.py)
- [Image to Structured Output](cookbook/hackathon/examples/image_to_structured_output.py)

## Audio Agents

- [Audio Input](cookbook/hackathon/examples/audio_input.py)

## Video Agents

- [Video Input](cookbook/hackathon/examples/video_input.py)

### Use Agent UI to give an interface to your agent

Run:

```shell
agno setup
```

```
python cookbook/playground/demo.py
```

Then head to: [app.agno.com/playground](https://app.agno.com/playground) to see your agent in action!

## Model usage:

```cookbook/hackathon/models```

##  Examples:

```cookbook/hackathon/examples```

## Multimodal Examples:

```cookbook/hackathon/multimodal_examples```

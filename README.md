# Telephone Game LLM

A fun experiment that plays [telephone](https://en.wikipedia.org/wiki/Telephone_game) with language models. Pass a message through a chain of LLMs and watch how it transforms.

Beyond being a bit of fun, this is a research tool for exploring how different models interpret and rephrase content - increasingly relevant as we enter an era of agentic AI where models frequently chain together.

## Installation

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/ohnotnow/telephone_game_llm.git
cd telephone_game_llm
uv sync
```

Set your API keys as environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENROUTER_API_KEY="sk-or-..."  # optional, for additional models
```

## Usage

### Basic usage

```bash
uv run python main.py "The quick brown fox jumps over the lazy dog"
```

### Specify models

```bash
uv run python main.py "Hello world" -m gpt-4o claude-3-5-sonnet-latest gemini/gemini-pro
```

### Multiple iterations

Loop through the model chain multiple times:

```bash
uv run python main.py "A fact about history" -m gpt-4o-mini claude-3-5-haiku-latest -i 3
```

### Using a config file

```bash
uv run python main.py -c examples/basic.yml
```

Override config values with CLI args:

```bash
uv run python main.py -c examples/basic.yml -i 5 -m gpt-4o claude-3-5-sonnet-latest
```

### All options

```
usage: main.py [-h] [-c CONFIG] [-m MODELS [MODELS ...]] [-s SYSTEM]
               [--no-system] [-i ITERATIONS] [-o OUTPUT_DIR] [--no-save]
               [message]

Options:
  message               The initial message to pass through the chain
  -c, --config          Path to YAML config file
  -m, --models          List of models to use in the chain
  -s, --system          System prompt to use for all models
  --no-system           Don't use any system prompt
  -i, --iterations      Number of times to loop through the chain (default: 1)
  -o, --output-dir      Directory to save results (default: results)
  --no-save             Don't save results to file
```

## Config file format

```yaml
message: "Your starting message"

models:
  - gpt-4o-mini
  - claude-3-5-haiku-latest
  - gpt-4o-mini

system_prompt: >
  You are playing a game of telephone.
  Repeat the message you receive, trying to preserve its meaning.
  Be concise.

iterations: 1
output_dir: results
```

See the `examples/` directory for more config examples.

## Model naming

This project uses [litellm](https://docs.litellm.ai/) which provides a unified interface to many LLM providers:

| Provider | Format | Examples |
|----------|--------|----------|
| OpenAI | `model-name` | `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo` |
| Anthropic | `model-name` | `claude-3-5-sonnet-latest`, `claude-3-5-haiku-latest` |
| Google | `gemini/model-name` | `gemini/gemini-pro`, `gemini/gemini-1.5-flash` |
| OpenRouter | `openrouter/provider/model` | `openrouter/meta-llama/llama-3-70b-instruct` |

## Output

Results are saved as JSON in the `results/` directory:

```json
{
  "initial_message": "The quick brown fox jumps over the lazy dog",
  "models": ["gpt-4o-mini", "claude-3-5-haiku-latest"],
  "system_prompt": "...",
  "iterations": 1,
  "timestamp": "2026-01-03T19:06:32.856042",
  "steps": [
    {
      "step": 1,
      "iteration": 1,
      "model": "gpt-4o-mini",
      "input": "The quick brown fox jumps over the lazy dog",
      "output": "A fast brown fox leaps over a sleepy dog."
    },
    ...
  ],
  "final_message": "A fast brown fox leaps over a sleepy dog."
}
```

## Research ideas

- Compare orderings: Does A -> B -> C produce different results than C -> B -> A?
- Measure drift: How many iterations before a factual statement becomes unrecognizable?
- Model families: Do models from the same provider preserve each other's outputs better?
- System prompt effects: How does guidance (or lack thereof) affect transformation?

## License

MIT License - see [LICENSE](LICENSE) for details.

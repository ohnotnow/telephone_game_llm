"""
Telephone Game with LLMs

Pass a message through a chain of language models and see how it transforms.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import yaml
from litellm import completion


def run_chain(initial_message: str, models: list[str], system_prompt: str | None = None, iterations: int = 1) -> dict:
    """
    Run a message through a chain of models, telephone-game style.

    Args:
        initial_message: The starting message
        models: List of model names to use
        system_prompt: Optional system prompt for all models
        iterations: Number of times to loop through the full chain

    Returns a dict with the full chain results.
    """
    results = {
        "initial_message": initial_message,
        "models": models,
        "system_prompt": system_prompt,
        "iterations": iterations,
        "timestamp": datetime.now().isoformat(),
        "steps": [],
    }

    current_message = initial_message
    step_number = 0
    total_steps = len(models) * iterations

    for iteration in range(iterations):
        if iterations > 1:
            print(f"\n--- Iteration {iteration + 1}/{iterations} ---")

        for model in models:
            step_number += 1
            print(f"\n[Step {step_number}/{total_steps}] Sending to {model}...")

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": current_message})

            try:
                response = completion(model=model, messages=messages)
                output = response.choices[0].message.content

                step = {
                    "step": step_number,
                    "iteration": iteration + 1,
                    "model": model,
                    "input": current_message,
                    "output": output,
                }
                results["steps"].append(step)

                print(f"    Response: {output[:100]}{'...' if len(output) > 100 else ''}")

                current_message = output

            except Exception as e:
                print(f"    Error: {e}")
                step = {
                    "step": step_number,
                    "iteration": iteration + 1,
                    "model": model,
                    "input": current_message,
                    "error": str(e),
                }
                results["steps"].append(step)
                results["final_message"] = current_message
                return results

    results["final_message"] = current_message
    return results


def save_results(results: dict, output_dir: Path) -> Path:
    """Save results to a JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"run_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    return filename


def print_summary(results: dict) -> None:
    """Print a nice summary of the telephone game results."""
    print("\n" + "=" * 60)
    print("TELEPHONE GAME RESULTS")
    print("=" * 60)

    chain_desc = " -> ".join(results["models"])
    if results["iterations"] > 1:
        chain_desc = f"({chain_desc}) x {results['iterations']}"
    print(f"\nChain: {chain_desc}")

    print(f"\n{'ORIGINAL MESSAGE':^60}")
    print("-" * 60)
    print(results["initial_message"])

    print(f"\n{'FINAL MESSAGE':^60}")
    print("-" * 60)
    print(results["final_message"])

    if len(results["steps"]) > 1:
        print(f"\n{'INTERMEDIATE STEPS':^60}")
        print("-" * 60)
        for step in results["steps"]:
            iter_info = f" (iter {step['iteration']})" if results["iterations"] > 1 else ""
            print(f"\n[{step['step']}] {step['model']}{iter_info}:")
            if "error" in step:
                print(f"    ERROR: {step['error']}")
            else:
                output = step["output"]
                if len(output) > 200:
                    print(f"    {output[:200]}...")
                else:
                    print(f"    {output}")


def load_config(config_path: Path) -> dict:
    """Load configuration from a YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Play telephone with LLMs - pass a message through a chain of models"
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="The initial message to pass through the chain"
    )
    parser.add_argument(
        "-c", "--config",
        type=Path,
        help="Path to YAML config file"
    )
    parser.add_argument(
        "-m", "--models",
        nargs="+",
        help="List of models to use in the chain"
    )
    parser.add_argument(
        "-s", "--system",
        help="System prompt to use for all models"
    )
    parser.add_argument(
        "--no-system",
        action="store_true",
        help="Don't use any system prompt"
    )
    parser.add_argument(
        "-i", "--iterations",
        type=int,
        help="Number of times to loop through the model chain (default: 1)"
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        help="Directory to save results (default: results)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to file"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate an HTML visualization after the run"
    )
    parser.add_argument(
        "--strict-punctuation",
        action="store_true",
        help="Treat trailing periods as changes in visualization diffs"
    )

    args = parser.parse_args()

    # Start with defaults
    config = {
        "models": ["gpt-4o-mini", "claude-3-5-haiku-latest", "gpt-4o-mini"],
        "system_prompt": "You are playing a game of telephone. Repeat the message you receive, trying to preserve its meaning. Be concise.",
        "iterations": 1,
        "output_dir": "results",
    }

    # Load config file if provided
    if args.config:
        file_config = load_config(args.config)
        config.update(file_config)

    # CLI args override config file
    if args.message:
        config["message"] = args.message
    if args.models:
        config["models"] = args.models
    if args.system:
        config["system_prompt"] = args.system
    if args.no_system:
        config["system_prompt"] = None
    if args.iterations:
        config["iterations"] = args.iterations
    if args.output_dir:
        config["output_dir"] = str(args.output_dir)
    if args.no_save:
        config["no_save"] = True

    # Validate we have a message
    if "message" not in config or not config["message"]:
        parser.error("A message is required (via argument or config file)")

    system_prompt = config.get("system_prompt")
    iterations = config.get("iterations", 1)
    output_dir = Path(config.get("output_dir", "results"))
    no_save = config.get("no_save", False)
    visualize = args.visualize
    strict_punctuation = args.strict_punctuation

    chain_desc = " -> ".join(config["models"])
    if iterations > 1:
        chain_desc = f"({chain_desc}) x {iterations}"

    print("Starting telephone game...")
    print(f"Chain: {chain_desc}")
    print(f"Initial message: {config['message']}")

    results = run_chain(config["message"], config["models"], system_prompt, iterations)

    print_summary(results)

    if not no_save:
        filepath = save_results(results, output_dir)
        print(f"\nResults saved to: {filepath}")

    if visualize:
        from visualize import generate_html

        output_dir.mkdir(parents=True, exist_ok=True)
        if not no_save:
            html_path = filepath.with_suffix('.html')
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_path = output_dir / f"run_{timestamp}.html"

        html = generate_html(results, strict_punctuation=strict_punctuation)
        with open(html_path, "w") as f:
            f.write(html)

        print(f"Visualization saved to: {html_path}")


if __name__ == "__main__":
    main()

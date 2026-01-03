"""
Telephone Game with LLMs

Pass a message through a chain of language models and see how it transforms.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from litellm import completion


def run_chain(initial_message: str, models: list[str], system_prompt: str | None = None) -> dict:
    """
    Run a message through a chain of models, telephone-game style.

    Returns a dict with the full chain results.
    """
    results = {
        "initial_message": initial_message,
        "models": models,
        "system_prompt": system_prompt,
        "timestamp": datetime.now().isoformat(),
        "steps": [],
    }

    current_message = initial_message

    for i, model in enumerate(models):
        print(f"\n[Step {i + 1}/{len(models)}] Sending to {model}...")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": current_message})

        try:
            response = completion(model=model, messages=messages)
            output = response.choices[0].message.content

            step = {
                "step": i + 1,
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
                "step": i + 1,
                "model": model,
                "input": current_message,
                "error": str(e),
            }
            results["steps"].append(step)
            break

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

    print(f"\nChain: {' -> '.join(results['models'])}")

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
            print(f"\n[{step['step']}] {step['model']}:")
            if "error" in step:
                print(f"    ERROR: {step['error']}")
            else:
                output = step["output"]
                if len(output) > 200:
                    print(f"    {output[:200]}...")
                else:
                    print(f"    {output}")


def main():
    parser = argparse.ArgumentParser(
        description="Play telephone with LLMs - pass a message through a chain of models"
    )
    parser.add_argument(
        "message",
        help="The initial message to pass through the chain"
    )
    parser.add_argument(
        "-m", "--models",
        nargs="+",
        default=["gpt-4o-mini", "claude-3-5-haiku-latest", "gpt-4o-mini"],
        help="List of models to use in the chain (default: gpt-4o-mini claude-3-5-haiku-latest gpt-4o-mini)"
    )
    parser.add_argument(
        "-s", "--system",
        default="You are playing a game of telephone. Repeat the message you receive, trying to preserve its meaning. Be concise.",
        help="System prompt to use for all models"
    )
    parser.add_argument(
        "--no-system",
        action="store_true",
        help="Don't use any system prompt"
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("results"),
        help="Directory to save results (default: results)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to file"
    )

    args = parser.parse_args()

    system_prompt = None if args.no_system else args.system

    print("Starting telephone game...")
    print(f"Chain: {' -> '.join(args.models)}")
    print(f"Initial message: {args.message}")

    results = run_chain(args.message, args.models, system_prompt)

    print_summary(results)

    if not args.no_save:
        filepath = save_results(results, args.output_dir)
        print(f"\nResults saved to: {filepath}")


if __name__ == "__main__":
    main()

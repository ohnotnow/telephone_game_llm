"""
Visualize Telephone Game Results

Generates a film noir newspaper-style HTML visualization of the telephone game results.
Changed words appear as cut-out "blackmail note" letters - inverted text on dark backgrounds.
"""

import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path


def tokenize(text: str) -> list[str]:
    """Split text into words while preserving whitespace and punctuation."""
    return re.findall(r'\S+|\s+', text)


def _last_non_space_index(tokens: list[str]) -> int | None:
    for i in range(len(tokens) - 1, -1, -1):
        if not tokens[i].isspace():
            return i
    return None


def _apply_trailing_period_tolerance(
    original_tokens: list[str],
    modified_tokens: list[str],
    strict_punctuation: bool,
) -> tuple[list[str], list[str]]:
    if strict_punctuation:
        return original_tokens, modified_tokens

    orig_keys = original_tokens[:]
    mod_keys = modified_tokens[:]

    orig_last = _last_non_space_index(original_tokens)
    mod_last = _last_non_space_index(modified_tokens)
    if orig_last is None or mod_last is None:
        return orig_keys, mod_keys

    orig_token = original_tokens[orig_last]
    mod_token = modified_tokens[mod_last]
    if mod_token.endswith('.') and not orig_token.endswith('.'):
        if mod_token[:-1] == orig_token:
            mod_keys[mod_last] = mod_token[:-1]

    return orig_keys, mod_keys


def get_word_diffs(
    original: str,
    modified: str,
    strict_punctuation: bool = False,
) -> list[tuple[str, bool]]:
    """
    Compare two strings and return a list of (word, is_changed) tuples.

    Returns the modified text with each token marked as changed or unchanged.
    """
    orig_tokens = tokenize(original)
    mod_tokens = tokenize(modified)

    orig_keys, mod_keys = _apply_trailing_period_tolerance(
        orig_tokens,
        mod_tokens,
        strict_punctuation,
    )

    matcher = SequenceMatcher(None, orig_keys, mod_keys)
    result = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for token in mod_tokens[j1:j2]:
                result.append((token, False))
        elif tag == 'replace':
            for token in mod_tokens[j1:j2]:
                result.append((token, True))
        elif tag == 'insert':
            for token in mod_tokens[j1:j2]:
                result.append((token, True))
        # 'delete' - we don't show deleted words, only what's in the modified text

    return result


def render_diff_html(tokens: list[tuple[str, bool]]) -> str:
    """Render tokens as HTML with changed words styled as blackmail letters."""
    html_parts = []

    for token, is_changed in tokens:
        if token.isspace():
            html_parts.append(token)
        elif is_changed:
            # Blackmail note style - inverted, slightly rotated, cut-out look
            html_parts.append(f'<span class="changed">{token}</span>')
        else:
            html_parts.append(f'<span class="unchanged">{token}</span>')

    return ''.join(html_parts)


def generate_html(results: dict, strict_punctuation: bool = False) -> str:
    """Generate the full HTML visualization."""

    steps_html = []
    previous_output = results["initial_message"]

    for step in results["steps"]:
        if "error" in step:
            diff_html = f'<span class="error">ERROR: {step["error"]}</span>'
        else:
            diff_tokens = get_word_diffs(
                previous_output,
                step["output"],
                strict_punctuation=strict_punctuation,
            )
            diff_html = render_diff_html(diff_tokens)
            previous_output = step["output"]

        iteration_badge = ""
        if results.get("iterations", 1) > 1:
            iteration_badge = f'<span class="iteration-badge">Round {step["iteration"]}</span>'

        steps_html.append(f'''
        <div class="step">
            <div class="step-header">
                <span class="step-number">#{step["step"]}</span>
                <span class="model-name">{step["model"]}</span>
                {iteration_badge}
            </div>
            <div class="step-content">{diff_html}</div>
        </div>
        ''')

    chain_display = " → ".join(results["models"])
    if results.get("iterations", 1) > 1:
        chain_display = f'({chain_display}) × {results["iterations"]}'

    timestamp = results.get("timestamp", "Unknown")

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>THE TELEPHONE CHRONICLE</title>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Special+Elite&family=UnifrakturMaguntia&family=IM+Fell+English:ital@0;1&display=swap" rel="stylesheet">

    <style>
        :root {{
            --paper-cream: #f4e4c1;
            --paper-dark: #e8d4a8;
            --ink-black: #1a1612;
            --ink-brown: #2d2319;
            --sepia-dark: #3d2e1f;
            --sepia-mid: #6b5344;
            --sepia-light: #8b7355;
            --accent-red: #8b2500;
            --cutout-bg: #1a1612;
            --cutout-text: #f4e4c1;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background: var(--paper-cream);
            min-height: 100vh;
            font-family: 'IM Fell English', Georgia, serif;
            color: var(--ink-black);
            position: relative;
            overflow-x: hidden;
        }}

        /* Aged paper texture overlay */
        body::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image:
                url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
            opacity: 0.08;
            pointer-events: none;
            z-index: 1000;
        }}

        /* Coffee stain effect */
        body::after {{
            content: '';
            position: fixed;
            top: 15%;
            right: 5%;
            width: 180px;
            height: 180px;
            background: radial-gradient(ellipse at center,
                transparent 30%,
                rgba(139, 115, 85, 0.08) 50%,
                rgba(139, 115, 85, 0.12) 60%,
                transparent 70%);
            border-radius: 50%;
            transform: rotate(-15deg);
            pointer-events: none;
            z-index: 999;
        }}

        .newspaper {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
            position: relative;
        }}

        /* Masthead */
        .masthead {{
            text-align: center;
            border-bottom: 3px double var(--ink-black);
            padding-bottom: 1rem;
            margin-bottom: 0.5rem;
        }}

        .masthead-title {{
            font-family: 'UnifrakturMaguntia', 'Playfair Display', serif;
            font-size: clamp(2.5rem, 8vw, 4.5rem);
            letter-spacing: 0.05em;
            color: var(--ink-black);
            text-shadow: 2px 2px 0 var(--paper-dark);
            margin-bottom: 0.25rem;
        }}

        .masthead-subtitle {{
            font-family: 'Special Elite', monospace;
            font-size: 0.7rem;
            letter-spacing: 0.3em;
            text-transform: uppercase;
            color: var(--sepia-mid);
        }}

        .dateline {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.75rem;
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--sepia-light);
            margin-bottom: 1.5rem;
            font-family: 'Special Elite', monospace;
            color: var(--sepia-mid);
        }}

        .edition {{
            font-style: italic;
        }}

        /* Main Headline */
        .headline-container {{
            text-align: center;
            margin: 2rem 0;
            padding: 1.5rem;
            background: linear-gradient(180deg, var(--paper-dark) 0%, var(--paper-cream) 100%);
            border-top: 4px solid var(--ink-black);
            border-bottom: 4px solid var(--ink-black);
            position: relative;
        }}

        .headline-label {{
            font-family: 'Special Elite', monospace;
            font-size: 0.65rem;
            letter-spacing: 0.4em;
            text-transform: uppercase;
            color: var(--accent-red);
            margin-bottom: 0.75rem;
            display: block;
        }}

        .headline {{
            font-family: 'Playfair Display', Georgia, serif;
            font-weight: 900;
            font-size: clamp(1.5rem, 5vw, 2.8rem);
            line-height: 1.1;
            color: var(--ink-black);
            text-transform: uppercase;
            letter-spacing: 0.02em;
            hyphens: auto;
        }}

        /* Chain info styled as byline */
        .byline {{
            text-align: center;
            margin: 1.5rem 0;
            padding: 1rem;
            font-family: 'IM Fell English', serif;
            font-style: italic;
            color: var(--sepia-mid);
            border-left: 3px solid var(--sepia-light);
            border-right: 3px solid var(--sepia-light);
        }}

        .byline strong {{
            font-family: 'Special Elite', monospace;
            font-style: normal;
            color: var(--ink-black);
        }}

        /* Section header */
        .section-header {{
            font-family: 'Playfair Display', serif;
            font-weight: 700;
            font-size: 1.1rem;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            color: var(--ink-black);
            border-bottom: 2px solid var(--ink-black);
            padding-bottom: 0.3rem;
            margin: 2rem 0 1.5rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .section-header::before,
        .section-header::after {{
            content: '◆';
            font-size: 0.6rem;
        }}

        /* Steps styling */
        .steps {{
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}

        .step {{
            background: linear-gradient(135deg, var(--paper-cream) 0%, var(--paper-dark) 100%);
            border: 1px solid var(--sepia-light);
            padding: 1.25rem;
            position: relative;
            box-shadow:
                3px 3px 0 rgba(0,0,0,0.1),
                inset 0 0 30px rgba(139, 115, 85, 0.05);
        }}

        .step::before {{
            content: '';
            position: absolute;
            top: -2px;
            left: 10%;
            right: 10%;
            height: 2px;
            background: repeating-linear-gradient(
                90deg,
                var(--ink-black) 0px,
                var(--ink-black) 4px,
                transparent 4px,
                transparent 8px
            );
        }}

        .step-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px dashed var(--sepia-light);
        }}

        .step-number {{
            font-family: 'Playfair Display', serif;
            font-weight: 900;
            font-size: 1.5rem;
            color: var(--accent-red);
            min-width: 2.5rem;
        }}

        .model-name {{
            font-family: 'Special Elite', monospace;
            font-size: 0.85rem;
            background: var(--ink-black);
            color: var(--paper-cream);
            padding: 0.25rem 0.75rem;
            letter-spacing: 0.05em;
        }}

        .iteration-badge {{
            font-family: 'IM Fell English', serif;
            font-size: 0.75rem;
            font-style: italic;
            color: var(--sepia-mid);
            margin-left: auto;
        }}

        .step-content {{
            font-family: 'IM Fell English', Georgia, serif;
            font-size: 1.15rem;
            line-height: 1.8;
            color: var(--ink-brown);
        }}

        /* The blackmail note effect for changed words */
        .changed {{
            display: inline-block;
            background: var(--cutout-bg);
            color: var(--cutout-text);
            padding: 0.1em 0.35em;
            margin: 0.1em 0.05em;
            font-family: 'Special Elite', monospace;
            font-size: 0.95em;
            transform: rotate(var(--rotation, 0deg));
            box-shadow:
                2px 2px 0 rgba(0,0,0,0.3),
                inset 0 0 0 1px rgba(255,255,255,0.1);
            position: relative;
            border: 1px solid var(--sepia-dark);
        }}

        /* Slight random rotations for cut-out effect */
        .changed:nth-child(3n) {{ --rotation: -1.5deg; }}
        .changed:nth-child(3n+1) {{ --rotation: 1deg; }}
        .changed:nth-child(3n+2) {{ --rotation: -0.5deg; }}
        .changed:nth-child(5n) {{ --rotation: 2deg; }}
        .changed:nth-child(7n) {{ --rotation: -2deg; }}

        /* Some variation in the cutout backgrounds */
        .changed:nth-child(4n) {{
            background: var(--sepia-dark);
        }}

        .changed:nth-child(6n) {{
            background: #2a1f14;
            border-color: var(--ink-black);
        }}

        .unchanged {{
            display: inline;
        }}

        .error {{
            color: var(--accent-red);
            font-family: 'Special Elite', monospace;
            font-style: italic;
        }}

        /* Final message footer */
        .finale {{
            margin-top: 3rem;
            padding: 2rem;
            background: var(--ink-black);
            color: var(--paper-cream);
            text-align: center;
            position: relative;
        }}

        .finale::before {{
            content: '— FINAL TRANSMISSION —';
            display: block;
            font-family: 'Special Elite', monospace;
            font-size: 0.7rem;
            letter-spacing: 0.3em;
            margin-bottom: 1rem;
            color: var(--sepia-light);
        }}

        .finale-text {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.4rem;
            font-weight: 400;
            font-style: italic;
            line-height: 1.6;
        }}

        /* Footer */
        .footer {{
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid var(--sepia-light);
            text-align: center;
            font-family: 'Special Elite', monospace;
            font-size: 0.65rem;
            color: var(--sepia-mid);
            letter-spacing: 0.1em;
        }}

        /* Print styles */
        @media print {{
            body::before,
            body::after {{
                display: none;
            }}

            .newspaper {{
                max-width: none;
                padding: 1rem;
            }}
        }}

        /* Responsive adjustments */
        @media (max-width: 600px) {{
            .newspaper {{
                padding: 1rem;
            }}

            .dateline {{
                flex-direction: column;
                gap: 0.25rem;
                text-align: center;
            }}

            .step-header {{
                flex-wrap: wrap;
            }}

            .iteration-badge {{
                width: 100%;
                margin-left: 0;
                margin-top: 0.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="newspaper">
        <header class="masthead">
            <h1 class="masthead-title">The Telephone Chronicle</h1>
            <p class="masthead-subtitle">All the News That's Fit to Mutate</p>
        </header>

        <div class="dateline">
            <span class="date">{timestamp[:10] if len(timestamp) >= 10 else timestamp}</span>
            <span class="edition">LLM Evening Edition</span>
            <span class="price">Price: One API Call</span>
        </div>

        <div class="headline-container">
            <span class="headline-label">◆ Original Transmission ◆</span>
            <h2 class="headline">{results["initial_message"]}</h2>
        </div>

        <div class="byline">
            Passed through the wire via <strong>{chain_display}</strong>
        </div>

        <div class="section-header">The Metamorphosis</div>

        <div class="steps">
            {''.join(steps_html)}
        </div>

        <div class="finale">
            <p class="finale-text">"{results["final_message"]}"</p>
        </div>

        <footer class="footer">
            Generated by Telephone Game LLM • Words that changed are shown in blackmail style
        </footer>
    </div>
</body>
</html>'''

    return html


def main():
    parser = argparse.ArgumentParser(
        description="Generate a film noir newspaper visualization of telephone game results"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the JSON results file"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output HTML file path (default: same name as input with .html extension)"
    )
    parser.add_argument(
        "--strict-punctuation",
        action="store_true",
        help="Treat trailing periods as changes in the diff output"
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1

    with open(args.input) as f:
        results = json.load(f)

    html = generate_html(results, strict_punctuation=args.strict_punctuation)

    if args.output:
        output_path = args.output
    else:
        output_path = args.input.with_suffix('.html')

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"Visualization saved to: {output_path}")
    return 0


if __name__ == "__main__":
    exit(main())

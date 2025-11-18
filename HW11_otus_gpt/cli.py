"""
CLI Interface for OTUS Joke Generator
Simple command-line interface for generating jokes
"""

import argparse
from joke_generator import JokeGenerator


def main():
    """Command-line interface for joke generation"""
    parser = argparse.ArgumentParser(
        description='OTUS Joke Generator - Generate jokes using GPT-2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --category programming
  python cli.py --category dad_jokes --num 3
  python cli.py --custom "Write a joke about Python programming:"
  python cli.py --category general --temperature 1.2
        """
    )

    parser.add_argument(
        '--category',
        '-c',
        type=str,
        default='general',
        choices=['programming', 'dad_jokes', 'puns', 'general'],
        help='Joke category (default: general)'
    )

    parser.add_argument(
        '--num',
        '-n',
        type=int,
        default=1,
        help='Number of jokes to generate (default: 1)'
    )

    parser.add_argument(
        '--temperature',
        '-t',
        type=float,
        default=0.8,
        help='Generation temperature 0.1-2.0 (default: 0.8, higher = more creative)'
    )

    parser.add_argument(
        '--max-length',
        '-l',
        type=int,
        default=100,
        help='Maximum length in tokens (default: 100)'
    )

    parser.add_argument(
        '--custom',
        type=str,
        default=None,
        help='Custom prompt instead of category'
    )

    parser.add_argument(
        '--model',
        '-m',
        type=str,
        default='distilgpt2',
        help='Model name from HuggingFace (default: distilgpt2)'
    )

    args = parser.parse_args()

    # Print header
    print("=" * 70)
    print("OTUS JOKE GENERATOR")
    print("=" * 70)
    print()

    # Initialize generator
    generator = JokeGenerator(model_name=args.model)

    # Generate jokes
    if args.num == 1:
        print(f"Generating a {args.category} joke...\n")
        joke = generator.generate_joke(
            category=args.category,
            temperature=args.temperature,
            max_length=args.max_length,
            custom_prompt=args.custom
        )
        print(joke)
    else:
        print(f"Generating {args.num} {args.category} jokes...\n")
        jokes = generator.batch_generate(
            category=args.category,
            num_jokes=args.num,
            temperature=args.temperature,
            max_length=args.max_length
        )
        for i, joke in enumerate(jokes, 1):
            print(f"--- Joke {i} ---")
            print(joke)
            print()

    print()
    print("=" * 70)


if __name__ == '__main__':
    main()

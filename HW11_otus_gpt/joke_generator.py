"""
OTUS Joke Generator - GPT-based joke generation bot
Supports multiple joke categories and generation parameters
"""

import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from typing import Optional, Dict, List
import warnings

warnings.filterwarnings('ignore')


class JokeGenerator:
    """
    A GPT-2 based joke generator supporting multiple categories
    """

    # Joke category prompts
    JOKE_PROMPTS: Dict[str, List[str]] = {
        'programming': [
            "Here's a programming joke:\nQ: Why do programmers prefer dark mode?\nA:",
            "Here's a funny coding joke:\nQ: How many programmers does it take to change a light bulb?\nA:",
            "Programming humor:\nQ: Why do Java developers wear glasses?\nA:",
        ],
        'dad_jokes': [
            "Here's a dad joke:\nQ: What do you call a fake noodle?\nA:",
            "Dad joke time:\nQ: Why don't eggs tell jokes?\nA:",
            "Classic dad joke:\nQ: What do you call a bear with no teeth?\nA:",
        ],
        'puns': [
            "Here's a funny pun:\nQ: What do you call a fish wearing a bowtie?\nA:",
            "Pun of the day:\nQ: Why did the scarecrow win an award?\nA:",
            "Clever pun:\nQ: What do you call a sleeping bull?\nA:",
        ],
        'general': [
            "Here's a funny joke:\nQ:",
            "Joke of the day:\n",
            "Let me tell you a joke:\n",
        ]
    }

    def __init__(self, model_name: str = 'distilgpt2', device: Optional[str] = None):
        """
        Initialize the joke generator

        Args:
            model_name: HuggingFace model name (default: distilgpt2)
            device: Device to run on ('cuda', 'cpu', or None for auto)
        """
        print(f"Loading model: {model_name}...")

        # Set device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device

        print(f"Using device: {self.device}")

        # Load model and tokenizer
        self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        self.model = GPT2LMHeadModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

        # Set pad token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        print("Model loaded successfully!")

    def generate_joke(
        self,
        category: str = 'general',
        temperature: float = 0.8,
        max_length: int = 100,
        top_p: float = 0.9,
        custom_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a joke

        Args:
            category: Joke category ('programming', 'dad_jokes', 'puns', 'general')
            temperature: Randomness (0.1-2.0, higher = more creative)
            max_length: Maximum token length
            top_p: Nucleus sampling parameter
            custom_prompt: Custom prompt instead of category

        Returns:
            Generated joke text
        """
        # Get prompt
        if custom_prompt:
            prompt = custom_prompt
        else:
            import random
            prompts = self.JOKE_PROMPTS.get(category, self.JOKE_PROMPTS['general'])
            prompt = random.choice(prompts)

        # Encode prompt
        inputs = self.tokenizer.encode(prompt, return_tensors='pt').to(self.device)

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=max_length,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                num_return_sequences=1,
                pad_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.2,
                no_repeat_ngram_size=3
            )

        # Decode
        joke = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Clean up
        joke = self._clean_joke(joke)

        return joke

    def _clean_joke(self, text: str) -> str:
        """Clean up generated joke text"""
        # Stop at double newline
        if '\n\n' in text:
            text = text.split('\n\n')[0]

        # Limit lines
        lines = text.split('\n')
        if len(lines) > 5:
            text = '\n'.join(lines[:5])

        return text.strip()

    def get_categories(self) -> List[str]:
        """Get list of available joke categories"""
        return list(self.JOKE_PROMPTS.keys())

    def batch_generate(
        self,
        category: str = 'general',
        num_jokes: int = 3,
        **kwargs
    ) -> List[str]:
        """
        Generate multiple jokes

        Args:
            category: Joke category
            num_jokes: Number of jokes to generate
            **kwargs: Additional generation parameters

        Returns:
            List of generated jokes
        """
        jokes = []
        for _ in range(num_jokes):
            joke = self.generate_joke(category=category, **kwargs)
            jokes.append(joke)
        return jokes


def main():
    """Demo of the joke generator"""
    print("=" * 60)
    print("OTUS JOKE GENERATOR - Demo")
    print("=" * 60)

    # Initialize generator
    generator = JokeGenerator()

    # Generate jokes from different categories
    categories = generator.get_categories()

    for category in categories:
        print(f"\n--- {category.upper()} ---")
        joke = generator.generate_joke(category=category, temperature=0.7)
        print(joke)
        print()


if __name__ == '__main__':
    main()

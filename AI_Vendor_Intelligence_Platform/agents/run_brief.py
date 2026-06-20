"""Clean CLI entry point for generating vendor intelligence briefs."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.supervisor import generate_brief


def main():
    """Main entry point for CLI usage."""
    if len(sys.argv) < 2:
        print("Usage: python agents/run_brief.py <company_name>")
        print("Example: python agents/run_brief.py Cohere")
        print("")
        print("Available companies:")
        print("  Anthropic, OpenAI, Cohere, Mistral, Scale AI,")
        print("  Hugging Face, Perplexity, LangChain, Pinecone,")
        print("  Weaviate, Nvidia, Snowflake, and 40 more...")
        sys.exit(1)

    company_name = " ".join(sys.argv[1:])
    print(f"Generating intelligence brief for: {company_name}")
    print("=" * 60)
    brief = generate_brief(company_name)


if __name__ == "__main__":
    main()

# main.py
"""
Entry point for the Second Brain CLI.
Run with: python main.py
"""
import asyncio
from src.cli.app import SecondBrainCLI


def main():
    cli = SecondBrainCLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
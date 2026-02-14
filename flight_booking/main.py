"""Entry point for the Voyager travel agent.

Run with:
    python -m flight_booking          # starts FastAPI server
    python -m flight_booking --cli    # interactive CLI mode
"""

from __future__ import annotations

import argparse
import os
import sys


def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start the FastAPI server."""
    import uvicorn
    uvicorn.run("flight_booking.api:app", host=host, port=port, reload=True)


def run_cli() -> None:
    """Run the agent in interactive CLI mode (no web UI)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "ERROR: ANTHROPIC_API_KEY not set.\n\n"
            "  export ANTHROPIC_API_KEY='sk-...'\n"
        )
        sys.exit(1)

    amadeus_id = os.environ.get("AMADEUS_CLIENT_ID")
    amadeus_secret = os.environ.get("AMADEUS_CLIENT_SECRET")
    if not amadeus_id or not amadeus_secret:
        print(
            "WARNING: Amadeus API credentials not found.\n"
            "  export AMADEUS_CLIENT_ID='your_key'\n"
            "  export AMADEUS_CLIENT_SECRET='your_secret'\n"
            "  Get free keys at: https://developers.amadeus.com\n"
            "  The agent will start but travel searches will fail.\n"
        )

    from .agent import TravelAgent

    agent = TravelAgent()
    print("\n✈  Welcome to Voyager Travel!")
    print("   Your AI travel agent — flights, hotels, experiences.\n")
    print("   Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nBon voyage!")
            sys.exit(0)

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "bye"):
            print("\nBon voyage!")
            break

        print("\nVoyager: ", end="", flush=True)
        response = agent.chat_sync(user_input)
        print(response)
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Voyager Travel Agent")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (no web UI)")
    parser.add_argument("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    args = parser.parse_args()

    if args.cli:
        run_cli()
    else:
        run_server(args.host, args.port)


if __name__ == "__main__":
    main()

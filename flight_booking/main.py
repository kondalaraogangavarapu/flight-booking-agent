"""CLI entry point for the flight booking agent."""

from __future__ import annotations

import os
import sys

from .agent import AgentState, FlightBookingAgent
from .amadeus_client import AmadeusFlightClient


def main() -> None:
    """Run the interactive flight booking agent."""
    client_id = os.environ.get("AMADEUS_CLIENT_ID")
    client_secret = os.environ.get("AMADEUS_CLIENT_SECRET")

    if not client_id or not client_secret:
        print(
            "ERROR: Amadeus API credentials not found.\n\n"
            "Please set the following environment variables:\n"
            "  export AMADEUS_CLIENT_ID='your_api_key'\n"
            "  export AMADEUS_CLIENT_SECRET='your_api_secret'\n\n"
            "Get free API keys at: https://developers.amadeus.com\n"
        )
        sys.exit(1)

    client = AmadeusFlightClient(client_id, client_secret)
    agent = FlightBookingAgent(client)
    print(agent.greet())

    while agent.state != AgentState.COMPLETED:
        try:
            user_input = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            sys.exit(0)

        response = agent.process_input(user_input)
        print(f"\n{response}")


if __name__ == "__main__":
    main()

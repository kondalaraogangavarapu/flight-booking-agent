"""Tests for the conversational flight booking agent (with mocked API)."""

from flight_booking.agent import AgentState, FlightBookingAgent


class TestAgentGreeting:
    def test_greet_sets_state(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        assert agent.state == AgentState.COLLECTING_ORIGIN

    def test_greet_returns_message(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        msg = agent.greet()
        assert "welcome" in msg.lower()
        assert "where" in msg.lower()


class TestAgentOrigin:
    def test_valid_origin_by_code(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        response = agent.process_input("JFK")
        assert agent.state == AgentState.COLLECTING_DESTINATION
        assert "JFK" in response

    def test_valid_origin_by_city_single_match(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        response = agent.process_input("New York")
        # Single match -> goes straight to destination
        assert agent.state == AgentState.COLLECTING_DESTINATION

    def test_origin_multi_match_disambiguation(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        response = agent.process_input("London")
        # Multiple matches -> disambiguation
        assert agent.state == AgentState.DISAMBIGUATING_ORIGIN
        assert "LHR" in response
        assert "LGW" in response

    def test_disambiguate_origin(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        agent.process_input("London")
        response = agent.process_input("1")  # pick LHR
        assert agent.state == AgentState.COLLECTING_DESTINATION
        assert agent.criteria.origin == "LHR"

    def test_invalid_origin(self, mock_client):
        mock_client.search_locations.side_effect = lambda kw: []
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        response = agent.process_input("Atlantis")
        assert agent.state == AgentState.COLLECTING_ORIGIN
        assert "couldn't find" in response.lower()


class TestAgentDestination:
    def test_valid_destination(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        agent.process_input("JFK")
        response = agent.process_input("LAX")
        assert agent.state == AgentState.COLLECTING_DATES

    def test_same_as_origin(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        agent.process_input("JFK")
        response = agent.process_input("JFK")
        assert agent.state == AgentState.COLLECTING_DESTINATION
        assert "same" in response.lower()


class TestAgentDates:
    def _setup_to_dates(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        agent.process_input("JFK")
        agent.process_input("LAX")
        return agent

    def test_valid_departure_date(self, mock_client):
        agent = self._setup_to_dates(mock_client)
        response = agent.process_input("2026-06-15")
        assert agent.state == AgentState.COLLECTING_RETURN_DATE

    def test_invalid_date(self, mock_client):
        agent = self._setup_to_dates(mock_client)
        response = agent.process_input("not a date")
        assert agent.state == AgentState.COLLECTING_DATES

    def test_one_way(self, mock_client):
        agent = self._setup_to_dates(mock_client)
        agent.process_input("2026-06-15")
        response = agent.process_input("one way")
        assert agent.state == AgentState.COLLECTING_PASSENGERS

    def test_return_date(self, mock_client):
        agent = self._setup_to_dates(mock_client)
        agent.process_input("2026-06-15")
        response = agent.process_input("2026-06-22")
        assert agent.state == AgentState.COLLECTING_PASSENGERS


class TestAgentPassengersAndCabin:
    def _setup_to_passengers(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        agent.process_input("JFK")
        agent.process_input("LAX")
        agent.process_input("2026-06-15")
        agent.process_input("one way")
        return agent

    def test_valid_passengers(self, mock_client):
        agent = self._setup_to_passengers(mock_client)
        agent.process_input("2")
        assert agent.state == AgentState.COLLECTING_CABIN_CLASS
        assert agent.criteria.passengers == 2

    def test_invalid_passengers(self, mock_client):
        agent = self._setup_to_passengers(mock_client)
        agent.process_input("0")
        assert agent.state == AgentState.COLLECTING_PASSENGERS

    def test_cabin_class_economy(self, mock_client):
        agent = self._setup_to_passengers(mock_client)
        agent.process_input("1")
        agent.process_input("1")
        assert agent.state == AgentState.COLLECTING_PREFERENCES

    def test_cabin_class_business(self, mock_client):
        agent = self._setup_to_passengers(mock_client)
        agent.process_input("1")
        agent.process_input("business")
        assert agent.state == AgentState.COLLECTING_PREFERENCES


class TestAgentPreferences:
    def _setup_to_prefs(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        agent.process_input("JFK")
        agent.process_input("LAX")
        agent.process_input("2026-06-15")
        agent.process_input("one way")
        agent.process_input("1")
        agent.process_input("1")
        return agent

    def test_no_preferences_triggers_search(self, mock_client):
        agent = self._setup_to_prefs(mock_client)
        response = agent.process_input("no")
        assert agent.state == AgentState.SELECTING_OUTBOUND
        assert "found" in response.lower()

    def test_preferences_parsed(self, mock_client):
        agent = self._setup_to_prefs(mock_client)
        agent.process_input("$400 non-stop morning delta")
        assert agent.criteria.max_price == 400
        assert agent.criteria.max_stops == 0
        assert agent.criteria.preferred_time == "morning"
        assert agent.criteria.preferred_airline == "Delta Air Lines"


class TestAgentGlobalCommands:
    def test_quit(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        agent.process_input("quit")
        assert agent.state == AgentState.COMPLETED

    def test_restart(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        agent.process_input("JFK")
        response = agent.process_input("restart")
        assert agent.state == AgentState.COLLECTING_ORIGIN
        assert "welcome" in response.lower()

    def test_help(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        response = agent.process_input("help")
        assert "help" in response.lower()
        assert "amadeus" in response.lower()

    def test_empty_input(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        response = agent.process_input("")
        assert "didn't catch" in response.lower()


class TestAgentFullBookingFlow:
    def test_one_way_booking(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        agent.process_input("JFK")
        agent.process_input("LAX")
        agent.process_input("2026-06-15")
        agent.process_input("one way")
        agent.process_input("1")
        agent.process_input("economy")
        response = agent.process_input("no")

        assert agent.state == AgentState.SELECTING_OUTBOUND
        assert len(agent.outbound_flights) == 3

        # Select first flight
        agent.process_input("1")
        assert agent.state == AgentState.COLLECTING_PASSENGER_INFO

        agent.process_input("John Doe")
        assert agent.state == AgentState.COLLECTING_EMAIL

        agent.process_input("john@example.com")
        assert agent.state == AgentState.CONFIRMING_BOOKING

        response = agent.process_input("yes")
        assert agent.state == AgentState.COMPLETED
        assert agent.booking.confirmed is True
        assert "booking" in response.lower()

    def test_sort_commands(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        agent.process_input("JFK")
        agent.process_input("LAX")
        agent.process_input("2026-06-15")
        agent.process_input("one way")
        agent.process_input("1")
        agent.process_input("economy")
        agent.process_input("no")

        response = agent.process_input("sort price")
        assert "sorted" in response.lower()

        response = agent.process_input("sort duration")
        assert "sorted" in response.lower()

    def test_round_trip_booking(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        agent.process_input("JFK")
        agent.process_input("LAX")
        agent.process_input("2026-06-15")
        agent.process_input("2026-06-22")
        agent.process_input("1")
        agent.process_input("economy")
        response = agent.process_input("no")

        assert agent.state == AgentState.SELECTING_OUTBOUND

        # Select first flight -- round trip goes straight to passenger info
        response = agent.process_input("1")
        assert agent.state == AgentState.COLLECTING_PASSENGER_INFO
        assert "round-trip" in response.lower()

    def test_cancel_booking(self, mock_client):
        agent = FlightBookingAgent(mock_client)
        agent.greet()
        agent.process_input("JFK")
        agent.process_input("LAX")
        agent.process_input("2026-06-15")
        agent.process_input("one way")
        agent.process_input("1")
        agent.process_input("economy")
        agent.process_input("no")
        agent.process_input("1")
        agent.process_input("Jane Doe")
        agent.process_input("jane@example.com")
        response = agent.process_input("no")
        assert agent.state == AgentState.COMPLETED
        assert "cancelled" in response.lower()

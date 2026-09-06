"""
ORCA Coordinator Agent.

The Coordinator is responsible for:
- Receiving user queries
- Determining which specialized agents are needed
- Sending requests to those agents
- Collecting and validating agent responses
- Preparing information for final reasoning
"""

from typing import Any, Dict, List, Optional

from schemas import AgentRequest, AgentResponse, Location


class Coordinator:
    """
    Central orchestration component of ORCA.

    The Coordinator does not directly perform weather, ocean,
    or marine analysis. It delegates those responsibilities
    to specialized agents.
    """

    def __init__(self) -> None:
        """Initialize the Coordinator."""

        self.available_agents = {
            "weather_agent",
            "ocean_agent",
            "marine_agent",
        }

    def determine_required_agents(self, query: str) -> List[str]:
        """
        Determine which specialized agents are required
        for a user query.

        This is an initial rule-based implementation.
        It can later be replaced or enhanced with an
        LLM-based intent router.
        """

        query_lower = query.lower()

        required_agents = set()

        weather_keywords = [
            "weather",
            "rain",
            "wind",
            "storm",
            "cyclone",
            "temperature",
            "forecast",
            "warning",
        ]

        ocean_keywords = [
            "wave",
            "waves",
            "current",
            "sea",
            "ocean",
            "swell",
            "tide",
        ]

        marine_keywords = [
            "chlorophyll",
            "fishing",
            "fish",
            "marine",
            "ecosystem",
            "plankton",
            "pfz",
            "fishing zone",
        ]

        if any(keyword in query_lower for keyword in weather_keywords):
            required_agents.add("weather_agent")

        if any(keyword in query_lower for keyword in ocean_keywords):
            required_agents.add("ocean_agent")

        if any(keyword in query_lower for keyword in marine_keywords):
            required_agents.add("marine_agent")

        # For general marine safety/fishing questions,
        # multiple agents may be useful.
        if "safe" in query_lower or "safety" in query_lower:
            required_agents.update(
                {
                    "weather_agent",
                    "ocean_agent",
                    "marine_agent",
                }
            )

        return sorted(required_agents)

    def create_request(
        self,
        query: str,
        location: Optional[Location] = None,
        parameters: Optional[List[str]] = None,
    ) -> AgentRequest:
        """
        Create a standard request that can be sent
        to a specialized agent.
        """

        location = location or Location()

        request = AgentRequest(
            query=query,
            location_name=location.name,
            latitude=location.latitude,
            longitude=location.longitude,
            parameters=parameters or [],
        )

        error = request.validate()

        if error:
            raise ValueError(error)

        return request

    def validate_response(
        self,
        response: AgentResponse,
    ) -> bool:
        """
        Validate a response received from a specialized agent.
        """

        error = response.validate()

        if error:
            return False

        return True

    def collect_responses(
        self,
        responses: List[AgentResponse],
    ) -> Dict[str, AgentResponse]:
        """
        Validate and organize responses received from
        specialized agents.
        """

        valid_responses: Dict[str, AgentResponse] = {}

        for response in responses:
            if self.validate_response(response):
                valid_responses[response.agent] = response

        return valid_responses

    def get_status(self) -> Dict[str, Any]:
        """Return basic Coordinator status information."""

        return {
            "component": "coordinator",
            "status": "ready",
            "available_agents": sorted(self.available_agents),
        }


if __name__ == "__main__":
    coordinator = Coordinator()

    query = "Is it safe to fish tomorrow near Mangalore?"

    agents = coordinator.determine_required_agents(query)

    print("Query:", query)
    print("Required agents:", agents)
    print("Status:", coordinator.get_status())

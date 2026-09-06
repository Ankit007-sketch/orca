"""
ORCA Coordinator Router.

The router analyzes a user query and determines which
specialized agents should be involved.
"""

from typing import List


class AgentRouter:
    """Routes user queries to the appropriate ORCA agents."""

    WEATHER_KEYWORDS = [
        "weather",
        "rain",
        "wind",
        "storm",
        "cyclone",
        "temperature",
        "forecast",
        "warning",
    ]

    OCEAN_KEYWORDS = [
        "wave",
        "waves",
        "current",
        "sea",
        "ocean",
        "swell",
        "tide",
    ]

    MARINE_KEYWORDS = [
        "chlorophyll",
        "fishing",
        "fish",
        "marine",
        "ecosystem",
        "plankton",
        "pfz",
        "fishing zone",
    ]

    SAFETY_KEYWORDS = [
        "safe",
        "safety",
        "danger",
        "risk",
        "dangerous",
    ]

    def route(self, query: str) -> List[str]:
        """
        Determine which specialized agents are required
        for the given user query.
        """

        if not query or not query.strip():
            return []

        query_lower = query.lower()

        required_agents = set()

        # Weather-related queries
        if any(
            keyword in query_lower
            for keyword in self.WEATHER_KEYWORDS
        ):
            required_agents.add("weather_agent")

        # Ocean-related queries
        if any(
            keyword in query_lower
            for keyword in self.OCEAN_KEYWORDS
        ):
            required_agents.add("ocean_agent")

        # Marine/ecosystem-related queries
        if any(
            keyword in query_lower
            for keyword in self.MARINE_KEYWORDS
        ):
            required_agents.add("marine_agent")

        # Safety questions require information from
        # all relevant environmental agents.
        if any(
            keyword in query_lower
            for keyword in self.SAFETY_KEYWORDS
        ):
            required_agents.update(
                {
                    "weather_agent",
                    "ocean_agent",
                    "marine_agent",
                }
            )

        return sorted(required_agents)


if __name__ == "__main__":
    router = AgentRouter()

    test_queries = [
        "What is the weather tomorrow?",
        "What are the wave conditions?",
        "What is the chlorophyll level?",
        "Is it safe to fish tomorrow?",
    ]

    for query in test_queries:
        agents = router.route(query)

        print(f"\nQuery: {query}")
        print(f"Agents: {agents}")

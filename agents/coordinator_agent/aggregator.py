"""
ORCA Response Aggregator.

The Aggregator collects validated responses from specialized
agents and combines their information into a single structure
for the reasoning layer.
"""

from typing import Any, Dict, List

from schemas import AgentResponse


class ResponseAggregator:
    """Combines responses from ORCA specialized agents."""

    def aggregate(
        self,
        responses: List[AgentResponse],
    ) -> Dict[str, Any]:
        """
        Combine agent responses into a unified structure.

        Invalid responses are skipped so that one failed agent
        does not prevent the other agents from contributing.
        """

        aggregated: Dict[str, Any] = {
            "agents": {},
            "combined_data": {},
            "assessments": {},
            "sources": [],
            "errors": [],
        }

        for response in responses:
            # Skip invalid responses
            validation_error = response.validate()

            if validation_error:
                aggregated["errors"].append(
                    {
                        "agent": response.agent,
                        "error": validation_error,
                    }
                )
                continue

            # Store the complete response
            aggregated["agents"][response.agent] = (
                response.to_dict()
            )

            # Store agent-specific data
            aggregated["combined_data"][response.agent] = (
                response.data
            )

            # Store assessment separately
            aggregated["assessments"][response.agent] = (
                {
                    "risk_level": response.assessment.risk_level,
                    "summary": response.assessment.summary,
                }
            )

            # Collect unique sources
            for source in response.sources:
                if source not in aggregated["sources"]:
                    aggregated["sources"].append(source)

            # Collect agent errors
            for error in response.errors:
                aggregated["errors"].append(
                    {
                        "agent": response.agent,
                        "error": error,
                    }
                )

        return aggregated


if __name__ == "__main__":
    print("ORCA Response Aggregator")
    print("Status: Ready")

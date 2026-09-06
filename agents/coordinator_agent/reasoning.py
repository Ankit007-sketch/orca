"""
ORCA Cross-Agent Reasoning.

The reasoning layer analyzes validated information from
multiple specialized agents and produces an overall
risk assessment and recommendation.
"""

from typing import Any, Dict, List


class ORCAReasoner:
    """Performs cross-agent reasoning for ORCA."""

    RISK_PRIORITY = {
        "unknown": 0,
        "low": 1,
        "moderate": 2,
        "high": 3,
    }

    def assess_overall_risk(
        self,
        assessments: Dict[str, Dict[str, Any]],
    ) -> str:
        """
        Determine the overall risk level from agent assessments.

        The highest valid risk level is used as the initial
        conservative assessment.
        """

        if not assessments:
            return "unknown"

        highest_risk = "unknown"

        for assessment in assessments.values():
            risk_level = str(
                assessment.get("risk_level", "unknown")
            ).lower()

            if risk_level not in self.RISK_PRIORITY:
                continue

            if (
                self.RISK_PRIORITY[risk_level]
                > self.RISK_PRIORITY[highest_risk]
            ):
                highest_risk = risk_level

        return highest_risk

    def generate_recommendation(
        self,
        risk_level: str,
    ) -> str:
        """Generate a user-facing recommendation."""

        recommendations = {
            "low": (
                "Conditions appear generally favorable. "
                "Normal precautions are recommended."
            ),
            "moderate": (
                "Conditions require caution. "
                "Review the available environmental information "
                "before proceeding."
            ),
            "high": (
                "Conditions indicate elevated risk. "
                "Avoid or postpone the activity until conditions "
                "improve."
            ),
            "unknown": (
                "There is not enough reliable information to "
                "make a confident recommendation."
            ),
        }

        return recommendations.get(
            risk_level,
            recommendations["unknown"],
        )

    def create_reasoning_summary(
        self,
        assessments: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        """
        Extract important reasoning points from each agent.
        """

        reasoning_points = []

        for agent, assessment in assessments.items():
            summary = assessment.get("summary", "")

            if summary:
                reasoning_points.append(
                    f"{agent}: {summary}"
                )

        return reasoning_points

    def reason(
        self,
        aggregated_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Perform cross-agent reasoning using aggregated data.
        """

        assessments = aggregated_data.get(
            "assessments",
            {},
        )

        overall_risk = self.assess_overall_risk(
            assessments
        )

        recommendation = self.generate_recommendation(
            overall_risk
        )

        reasoning_points = self.create_reasoning_summary(
            assessments
        )

        return {
            "overall_risk": overall_risk,
            "recommendation": recommendation,
            "reasoning": reasoning_points,
            "agents_considered": list(assessments.keys()),
            "sources": aggregated_data.get("sources", []),
            "errors": aggregated_data.get("errors", []),
        }


if __name__ == "__main__":
    reasoner = ORCAReasoner()

    sample_data = {
        "assessments": {
            "weather_agent": {
                "risk_level": "moderate",
                "summary": "Moderate wind conditions.",
            },
            "ocean_agent": {
                "risk_level": "low",
                "summary": "Wave conditions are generally favorable.",
            },
            "marine_agent": {
                "risk_level": "low",
                "summary": "Marine indicators are favorable.",
            },
        },
        "sources": [
            "IMD",
            "INCOIS",
        ],
        "errors": [],
    }

    result = reasoner.reason(sample_data)

    print("Overall risk:", result["overall_risk"])
    print("Recommendation:", result["recommendation"])

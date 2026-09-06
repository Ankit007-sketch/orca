"""
Marine Agent for ORCA
======================

Responsible for gathering and interpreting marine/ocean-ecosystem data
(sea surface temperature, waves, salinity, chlorophyll, weather) for a
given location, and returning a structured payload the Coordinator
Agent can consume.

Public entrypoint:
    from agents.marine_agent import MarineAgent, MarineAgentInput

    agent = MarineAgent()
    result = agent.analyze(MarineAgentInput(lat=13.08, lon=80.27, location_name="Chennai coast"))
    payload = result.to_dict()   # hand this to the Coordinator Agent
"""

from .agent import MarineAgent
from .schemas import MarineAgentInput, MarineAgentOutput, ParameterReading

__all__ = ["MarineAgent", "MarineAgentInput", "MarineAgentOutput", "ParameterReading"]

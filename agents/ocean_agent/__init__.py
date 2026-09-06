"""
Ocean/Chlorophyll Agent for ORCA
================================

Responsible for retrieving and interpreting chlorophyll observations from
IRS-P4 OCM (Ocean Colour Monitor) data for a requested location and time,
and returning a structured payload the Coordinator Agent can consume.

Public entrypoint:
    from agents.ocean_agent import OceanAgent, OceanAgentInput

    agent = OceanAgent()
    result = agent.analyze(OceanAgentInput(lat=13.08, lon=80.27))
    payload = result.to_dict()
"""

from .agent import OceanAgent
from .schemas import OceanAgentInput, OceanAgentOutput, ChlorophyllReading

__all__ = ["OceanAgent", "OceanAgentInput", "OceanAgentOutput", "ChlorophyllReading"]

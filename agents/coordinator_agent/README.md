# Coordinator Agent

The Coordinator Agent is the central orchestration component of ORCA.

## Responsibilities

- Receive the user's query.
- Understand the user's intent, location, and time requirements.
- Decide which specialized agents are required.
- Send requests to the relevant agents.
- Collect responses from the agents.
- Validate and combine the responses.
- Perform cross-agent reasoning.
- Generate the final structured response.

## Connected Agents

- Marine Agent
- Ocean Agent
- Weather Agent

## Workflow

User Query
↓
Coordinator Agent
↓
Select Required Agents
↓
Request Data
↓
Marine / Ocean / Weather Agents
↓
Collect Responses
↓
Validate & Combine
↓
Cross-Agent Reasoning
↓
Final Recommendation

## Common Agent Response

All specialized agents should return their results using the common ORCA response structure.

## Development Status

Initial coordinator structure created.

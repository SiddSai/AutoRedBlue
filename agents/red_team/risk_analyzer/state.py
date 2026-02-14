from ast import List
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    attack_spec: str
    attack_scopes: list(str)


# receives an attack spec input from the user, converts it into a test scope
# to be fed into the SeedPromptGeneratorAgent
# e.g. 
#
# User input:
# “Test the model for self-harm content generation.”
#
# Risk Analyzer outputs:
#
# Category: self-harm
# Harm type: instructional
# Constraints: realistic, actionable



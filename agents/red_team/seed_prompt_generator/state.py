from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    attack_scopes: list(str)
    seed_prompts: list(str)


# receives tests scopes from the RiskAnalyzerAgent, from which it generates
# a desired output from the attack (a success criteria if you will)
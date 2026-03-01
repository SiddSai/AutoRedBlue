from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    risks: dict # Contains 'summary': str, 'analysis': str, 'test_case_scope': list[str]
    seed_prompts: list(dict)


# receives tests scopes from the RiskAnalyzerAgent, from which it generates
# an input and desired output from the attack (a success criteria if you will)
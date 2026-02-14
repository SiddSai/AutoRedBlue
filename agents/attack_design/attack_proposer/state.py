from ast import List
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    attack_proposals: List(str)


# attack_proposals is a list of strings specifiyng single attacks mechanisms broadly, including references when necessary
# e.g. Cultural: Harmful cultural references



from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    seed_prompt: list(str)
    conversation: list(dict)
    evaluation: list(bool)

# receives attack prompts and responses from the interaction with the subject
# model, evaluates if the attack was succesfull taking into account the seed prompt 
# as the objective
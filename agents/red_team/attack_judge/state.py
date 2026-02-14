from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    seed_prompts: list(str)
    attack_prompts: list(str)
    attack_responses: list(str)
    attack_succes: list(bool)

# receives attack prompts and responses from the interaction with the subject
# model, evaluates if the attack was succesfull taking into account the seed prompt 
# as the objective
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    seed_prompts: list(str)
    attack_prompts: list(str)

# receives seedprompts as objectives to pursue in the generation of concrete attacks
# from the attack library csv
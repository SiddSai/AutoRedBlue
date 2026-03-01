from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    seed_prompt: dict
    conversarion: list(dict)
    attack: dict

# receives seedprompts as objectives to pursue in the generation of concrete attacks
# from the attack library csv

# formatted_attack = {
#     "attack_library_id": "",
#     "justification": "",
#     "concrete_attack": ""
# }
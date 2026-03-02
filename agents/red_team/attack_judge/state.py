from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    seed_prompt: list   # The seed prompt used for the attack
    conversation: list  # List of conversation exchanges between attacker and target
    evaluation: dict    # Evaluation results including safety assessment and score


# Evaluation: 
# {
#     "safety_assessment": "",
#     "strengths": "",
#     "weaknesses": "",
#     "attack_score": "true/false",
# }
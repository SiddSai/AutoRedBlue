from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# receives tests scopes from the RiskAnalyzerAgent, from which it generates
# an input and desired output from the attack (a success criteria if you will)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    risks: dict # Contains 'summary': str, 'analysis': str, 'test_case_scope': list[str]
    num_test_cases: int # amount of requestes seed_prompts
    seed_prompts: list

# Seed_prompt
# {
#     "id": TC001",
#     "description": "", 
#     "expected_outcome": "",
#     "input_data": "",
# }
from mimetypes import init
from typing import Annotated, Optional, ParamSpecArgs, Sequence, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END 
from langgraph.prebuilt import ToolNode
from pprint import pprint

# AGENTS

from agents.base_agent import BasicAgent

from agents.gt_eval.eval_agent import AttackJudgeAgent
from agents.gt_eval.eval_agent import AgentState as AttackJudgeState

attack_judge_agent = AttackJudgeAgent()
attack_judge_agent.compile_app()

class RouterState(TypedDict):
    user_input:     str         # user request for the attack scope/objective
    conversation:   list        # conversation history between target/attacker
    score:          dict        # attack success score per conversation
    messages: Annotated[        # messages tracked for the internal (subject) model
        Sequence[BaseMessage],
        add_messages
    ]

class RedTeam(BasicAgent):
    def __init__(self, target_model=None): 
        super().__init__(model=target_model, state=RouterState)
        
        def run_test_case(state): 

            # attack the model
            attack_message = HumanMessage(content=state["user_input"])
            state["conversation"].append({
                "attacker": attack_message.content,
            })

            response = self.model.invoke([self.system_prompt] + [attack_message])         # single shot
            #                              ^^^ system prompt of the base agent

            # store response
            state["conversation"].append({"target_response": response.content})

            return state

        def run_evaluation(state):

            init_evaluator_state = {
                "messages": [],
                "conversation": state["conversation"]
            }

            evaluator_output = attack_judge_agent.invoke(init_evaluator_state)
            evaluation = evaluator_output["evaluation"]
            state["score"] = evaluation # ovewrites the previous, no problem

            return state

        self.graph.add_node("run_test_case", run_test_case)
        self.graph.add_node("run_evaluation", run_evaluation)
                
        self.graph.add_edge(START, "run_test_case")
        self.graph.add_edge("run_test_case", "run_evaluation")
        self.graph.add_edge("run_evaluation", END)


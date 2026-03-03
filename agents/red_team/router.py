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
import json
import os
import time

# TOOLKITS 
from services.attack_registry.attack_registry_toolkit import REGISTRY_PATH
import services.attack_library.attack_library_toolkit as attack_library

# AGENTS
from agents.base_agent import BasicAgent

from agents.red_team.risk_analyzer.agent import RiskAnalysisAgent

from agents.red_team.seed_prompt_generator.agent import SeedPromptGeneratorAgent

from agents.red_team.strategy_designer.agent import StrategyDesignerAgent
from agents.red_team.strategy_designer.state import AgentState as StrategyDesignerState

from agents.red_team.attack_judge.agent import AttackJudgeAgent
from agents.red_team.attack_judge.state import AgentState as AttackJudgeState

attack_judge_agent = AttackJudgeAgent()
attack_judge_agent.compile_app()

risk_analyzer_agent = RiskAnalysisAgent()
risk_analyzer_agent.compile_app()

seed_prompt_generator_agent = SeedPromptGeneratorAgent()
seed_prompt_generator_agent.compile_app()

strategy_designer_agent = StrategyDesignerAgent()
strategy_designer_agent.compile_app()

class RouterState(TypedDict):
    user_input: str             # user request for the attack scope/objective
    risks: dict                 # concrete attack scope/themes/categories/constraints
    seed_prompts: list          # concrete attack objectives: input - expected output (success condition)
    conversations: list         # tracks the ongoing back and forth between redteam and subject model 
    scores: list                # attack success scores per conversation
    messages: Annotated[        # messages tracked for the internal (subject) model
        Sequence[BaseMessage],
        add_messages
    ]
    current_iter: int           # current attempt of a given test_case
    max_iter: int               # maximum amount of attempts (conversation length)
    num_test_cases: int         # specified amount of test cases
    current_test_case: int      # test_case counter
    registry: list              # last entried appended to JSON registry 

def run_risk_analyzer_agent(state: RouterState):
    init_state = {
        "messages": [("user", state["user_input"])]
    }
    result = risk_analyzer_agent.invoke(init_state)
    print("risk_analyzer_output: ", result)
    return {"risks": result["risks"]}

def run_seed_prompt_generator_agent(state: RouterState):
    init_state = {
        "messages": [],
        "risks": state["risks"],
        "num_test_cases": state["num_test_cases"]
    }
    result = seed_prompt_generator_agent.invoke(init_state)
    print("seed_prompts agent output: ")
    pprint(result["seed_prompts"])
    return {
        "seed_prompts": result["seed_prompts"],
        "conversations": [[] for _ in range(len(result["seed_prompts"]))],
        "scores": [None for _ in range(len(result["seed_prompts"]))],
    }

class RedTeam(BasicAgent):
    def __init__(self, target_model=None): 
        super().__init__(model=target_model, state=RouterState)
        
        def run_test_case(state): 
            if int(state["current_iter"]) >= int(state["max_iter"]):
                return state

            current_test_case = state["current_test_case"]
            current_conversation = state["conversations"][current_test_case]
            current_seed_prompt = state["seed_prompts"][current_test_case]

            init_designer_state = {
                "messages": [],
                "conversation": current_conversation, 
                "seed_prompt": current_seed_prompt
            }
            
            designer_output = strategy_designer_agent.invoke(init_designer_state)
            attack_choice = designer_output["attack"]

            # attack the model
            attack_message = HumanMessage(content=attack_choice["concrete_attack"])
            state["conversations"][current_test_case].append({
                "attack_library_id": attack_choice["attack_library_id"],
                "attacker": attack_choice["concrete_attack"],
                "justification": attack_choice["justification"]
            })

            # state["messages"].append(attack_message)                                  # multi turn
            # response = self.model.invoke([self.system_prompt] + state["messages"])    
            response = self.model.invoke([self.system_prompt] + [attack_message])         # single shot

            # store response
            # state["messages"].append(response)
            state["conversations"][current_test_case].append({"target_response": response.content})

            # incremente iter_count
            state["current_iter"] += 1

            return state

        def run_evaluation(state):
    
            current_test_case = int(state["current_test_case"])
            current_conversation = state["conversations"][current_test_case]
            current_seed_prompt = state["seed_prompts"][current_test_case]

            init_evaluator_state = {
                "messages": [],
                "conversation": current_conversation, 
                "seed_prompt": current_seed_prompt
            }

            evaluator_output = attack_judge_agent.invoke(init_evaluator_state)
            evaluation = evaluator_output["evaluation"]
            state["scores"][current_test_case] = evaluation # ovewrites the previous, no problem

            # ... and update success_rate on the attack
            attack_id = current_conversation[-2]["attack_library_id"]
            attack_library.update_success_rate(attack_id, evaluation["attack_score"])

            return state

        def advance_state(state):
            current_test_case = int(state["current_test_case"])
            current_iter = int(state["current_iter"])
            max_iter = int(state["max_iter"])

            current_score_obj = state["scores"][current_test_case]
            current_test_case_success = current_score_obj.get("attack_score", False)

            if current_test_case_success or current_iter >= max_iter:
                state["current_test_case"] = current_test_case + 1
                state["messages"] = []
                state["current_iter"] = 0

            return state

        def switch(state) -> str:
            # determine wether to continue current test_case, move to next test_case, 
            # or finish execution
            print("switch - current_test_case: ", state["current_test_case"], " seed_prompts: ", len(state["seed_prompts"]))
            if state["current_test_case"] >= len(state["seed_prompts"]):
                return "end_batch"
            return "continue"
        
        def get_data(state):

            # Extract sample data
            # input:
            # prompt + context

            # output:
            # (1) Correctness: 0 (unsuccesful) or 1 (successful) under query cost constraints
            # (2) Costs: completion tokens over all iterations and number of queries
            # (3) Conversation: Final prompt, expected output, response

            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                registry = json.load(f)

            for i in range(len(state["seed_prompts"])):
                evaluation = state["scores"][i]
                conversation = state["conversations"][i]
                seed_prompt = state["seed_prompts"][i]

                entry = {
                    "correctness": 1 if evaluation["attack_score"] else 0,
                    "cost": int(len(conversation) / 2),
                    "conversation": {
                        "final_prompt": conversation[-2]["attacker"],
                        "expected_output": seed_prompt["expected_outcome"],
                        "response": conversation[-1]["target_response"],
                    },
                }

                registry.append(entry)

            with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
                json.dump(registry, f, ensure_ascii=False, indent=2)

            # also save it to our state registry
            state_registry = state["registry"]
            state_registry.append(entry)

            return state

        self.graph.add_node("risk_analyzer_agent", run_risk_analyzer_agent)
        self.graph.add_node("seed_prompt_generator_agent", run_seed_prompt_generator_agent)
        self.graph.add_node("run_test_case", run_test_case)
        self.graph.add_node("run_evaluation", run_evaluation)
        self.graph.add_node("advance_state", advance_state)
        self.graph.add_node("get_data", get_data)
                
        self.graph.add_edge(START, "risk_analyzer_agent")
        self.graph.add_edge("risk_analyzer_agent", "seed_prompt_generator_agent")
        self.graph.add_edge("seed_prompt_generator_agent", "run_test_case")
        self.graph.add_edge("run_test_case", "run_evaluation")
        self.graph.add_edge("run_evaluation", "advance_state")

        self.graph.add_conditional_edges(
            "advance_state",
            switch,
            {
                "continue": "run_test_case",
                "end_batch": "get_data"
            }
        )

        self.graph.add_edge("get_data", END)


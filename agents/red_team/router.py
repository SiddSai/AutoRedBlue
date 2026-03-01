from mimetypes import init
from typing import TypedDict
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END 
from langgraph.prebuilt import ToolNode
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
    seed_prompts: list(dict)    # concrete attack objectives: input - expected output (success condition)
    conversations: list(dict)   # tracks the ongoing back and forth between redteam and subject model 
    scores: list(dict)          # attack success scores per conversation
    messages: list(dict)        # messages tracked for the internal (subject) model
    current_iter: int           # current attempt of a given test_case
    max_iter: int               # maximum amount of attempts (conversation length)
    current_test_case: int      # test_case counter

def run_risk_analyzer_agent(state: RouterState):
    init_state = {
        "messages": [("user", state["user_input"])]
    }
    result = risk_analyzer_agent.invoke(init_state)
    return {"risks": result["risks"]}

def run_seed_prompt_generator_agent(state: RouterState):
    init_state = {
        "messages": [],
        "risks": state["risks"]
    }
    result = seed_prompt_generator_agent.invoke(init_state)
    return {"seed_prompts": result["seed_prompts"]}

class RedTeam(BasicAgent):
    # Note: probably don't need to inherit from the base agent or add some 
    # functionality to ignore the creation of the "agent" node
    def __init__(self, target_model=None): 
        super().__init__(self, model=target_model, state=RouterState)
        
        def run_test_case(state): 

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
            state["messages"].append(attack_message)
            state["conversation"].append({
                "attacker": attack_choice["concrete_attack"],
                "justification": attack_choice["justification"]
            })
            response = self.model.invoke([self.system_prompt] + state["messages"])

            # store response
            state["messages"].append(response)
            state["conversation"].append({"target_response": response.content})

            # incremente iter_count
            state["current_iter"] += 1

            return state
        
        def run_evaluation(state):
    
            current_test_case = state["current_test_case"]
            current_conversation = state["conversations"][current_test_case]
            current_seed_prompt = state["seed_prompts"][current_test_case]

            init_evaluator_state = {
                "messages": [],
                "conversation": current_conversation, 
                "seed_prompt": current_seed_prompt
            }

            evaluator_output = attack_judge_agent.invoke(init_evaluator_state)
            state["scores"][current_test_case] = evaluator_output["evaluation"] # ovewrites the previous, no problem

            return state

        def switch(state) -> str:
            # determine wether to continue current test_case, move to next test_case, 
            # or finish execution

            current_test_case = state["current_test_case"]
            current_iter = state["current_iter"]
            max_iter = state["max_iter"]
            current_test_case_success = state["scores"].get(current_test_case, {}).get("attack_score", False)

            if current_test_case_success: # success!
                state["current_test_case"] += 1
                state["messages"] = [] # clear model
                state["current_iter"] = 0

            if current_iter > max_iter: # failed for good
                state["current_test_case"] += 1
                state["messages"] = []
                state["current_iter"] = 0

            if state["current_test_case"] >= len(state["seed_prompts"]):
                return "end_batch"
            return "continue"
        
        def get_data(state):
            # TODO: 
            # Extract sample data and feed library
            return state

        self.graph.add_node("risk_analyzer_agent", run_risk_analyzer_agent)
        self.graph.add_node("seed_prompt_generator_agent", run_seed_prompt_generator_agent)
        self.graph.add_node("run_test_case", run_test_case)
        self.graph.add_node("run_evaluation", run_evaluation)
        self.grapg.add_node("get_data", get_data)
                
        self.graph.add_edge(START, "risk_analyzer_agent")
        self.graph.add_edge("risk_analyzer_agent", "seed_prompt_generator_agent")
        self.graph.add_edge("seed_prompt_generator_agent", "run_test_case")
        self.graph.add_edge("run_test_case", "run_evaluation")

        self.graph.add_conditional_edges(
            "run_evaluation",
            switch,
            {
                "continue": "run_test_case",
                "end_batch": "get_data"
            }
        )

        self.graph.add_edge("get_data", END)
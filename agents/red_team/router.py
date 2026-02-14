from typing import Annotated, ParamSpecArgs, Sequence, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END 
from langgraph.prebuilt import ToolNode

from agents.red_team.attack_judge.agent import AttackJudgeAgent
from agents.red_team.risk_analyzer.agent import RiskAnalysisAgent
from agents.red_team.seed_prompt_generator.agent import SeedPromptGeneratorAgent
from agents.red_team.strategy_designer.agent import StrategyDesignerAgent

attack_judge_agent = AttackJudgeAgent().compile_app()
risk_analyzer_agent = RiskAnalysisAgent().compile_app()
seed_prompt_generator_agent = SeedPromptGeneratorAgent().compile_app()
strategy_designer_agent = StrategyDesignerAgent().compile_app()

class RouterState(TypedDict):
    pass

def run_risk_analyzer_agent(state: RouterState):
    init_state = {
        "messages": []
    }
    result = risk_analyzer_agent.invoke(init_state)
    return result

def run_judge_agent(state: RouterState):
    init_state = {
        "messages": []
    }
    result = attack_judge_agent.invoke(init_state)
    return result

def run_seed_prompt_generator_agent(state: RouterState):
    init_state = {
        "messages": []
    }
    result = seed_prompt_generator_agent.invoke(init_state)
    return result

def run_strategy_designer_agent(state: RouterState):
    init_state = {
        "messages": []
    }
    result = strategy_designer_agent.invoke(init_state)
    return result

router = StateGraph(RouterState)
router.add_node("judge_agent", run_judge_agent)
router.add_node("risk_analyzer_agent", run_risk_analyzer_agent)
router.add_node("seed_prompt_generator_agent", run_seed_prompt_generator_agent)
router.add_node("strategy_designer_agent", run_strategy_designer_agent)

router.add_edge(START, "risk_analyzer_agent")
router.add_edge("risk_analyzer_agent", "seed_prompt_generator_agent")
router.add_edge("seed_prompt_generator_agent", "strategy_designer_agent")
router.add_edge("strategy_designer_agent", "judge_agent")
router.add_edge("judge_agent", END)

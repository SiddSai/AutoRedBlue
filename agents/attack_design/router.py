from tokenize import ENDMARKER
from typing import Annotated, ParamSpecArgs, Sequence, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END 
from langgraph.prebuilt import ToolNode

from agents.attack_design.attack_designer.agent import AttackDesignerAgent
from agents.attack_design.attack_proposer.agent import AttackProposerAgent

attack_designer_agent = AttackDesignerAgent()
attack_designer_agent.compile_app()

attack_proposer_agent = AttackProposerAgent()
attack_proposer_agent.compile_app()

class RouterState(TypedDict):
    attack_proposals: list(str)
    done: bool

def run_proposer_agent(state:RouterState):
    init_state = {
        "messages": [],
        "attack_proposals": []
    } # init state from the proposer agent
    out_state = attack_proposer_agent.invoke(init_state)
    return {
        "attack_proposals": out_state["attack_proposals"] # pass proposals to the router
    }

def run_designer_agent(state:RouterState):
    init_state = {
        "messages": [],
        "attack_proposals": state["attack_proposals"]
    } # init state from the designer agent
    attack_designer_agent.invoke(init_state)
    return {
        "done": True
    }

router = StateGraph(RouterState)
router.add_node("proposer_agent", run_proposer_agent)
router.add_node("designer_agent", run_designer_agent)

router.add_edge(START, "proposer_agent")
router.add_edge("proposer_agent", "designer_agent")
router.add_edge("designer_agent", END)

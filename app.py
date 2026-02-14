"""
Main application that encapsulates the core functionalities and classes for AutoRedTeamer
"""
from typing import Annotated, ParamSpecArgs, Sequence, TypedDict
from dotenv import load_dotenv
from langchain_core import messages
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END 
from langgraph.prebuilt import ToolNode

from agents.attack_design.router import ad_router
from agents.red_team.router import rt_router

class RouterState(TypedDict): 
    messages: list(str)
    pass

red_team_router = ad_router.compile()
attack_design_router = rt_router.compile()

def red_team(state:RouterState):
    init_state = {
        "messages": []
    }
    red_team_router.invoke(init_state)

def attack_design(state:RouterState):
    init_state = {
        "messages": []
    }

class App():
    def __init__(self):
        pass



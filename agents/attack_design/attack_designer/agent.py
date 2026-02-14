from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END 
from langgraph.prebuilt import ToolNode

from agents.base_agent import BasicAgent

"""
receives a list of attack proposals in text format, its objective 
is to look through the current attack library and decide which attacks to implement
them by formating them into the csv library structure.

can also be prompted to refine an attack implementation
"""

class AttackDesignerAgent(BasicAgent):
    def __init__(self, tools: list = None):
        super().__init__(tools=tools)


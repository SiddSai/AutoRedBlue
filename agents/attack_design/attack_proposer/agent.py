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
Checks the attack library csv, navigates github API as well as Semantic
Scholar API to come up with attack proposals in broad text format (attack proposals)
to be fed into the attack designer agent 
"""
class AttackProposerAgent(BasicAgent):
    def __init__(self, tools: list = None):
        super().__init__(tools=tools)
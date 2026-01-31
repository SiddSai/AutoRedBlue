"""
Main application that encapsulates the core functionalities and classes for AutoRedTeamer
"""

from typing import Annotated, ParamSpecArgs, Sequence, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END 
from langgraph.prebuilt import ToolNode


class App():
    def __init__(self):
        """Define the core graph for the agent flow"""
        pass



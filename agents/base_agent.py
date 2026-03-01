# Base agent class (common-shared functionalities)

from typing import Annotated, Optional, ParamSpecArgs, Sequence, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END 
from langgraph.prebuilt import ToolNode
from IPython.display import Image, display

load_dotenv()

basic_system_prompt = "You are an AI assistant, answer the user query to your best abillity"

class AgentState(TypedDict): 
    messages : Annotated[Sequence[BaseMessage], add_messages]

class BasicAgent():
    def __init__(self, tools: list = None, state:TypedDict = AgentState(), system_prompt=basic_system_prompt, model=ChatOpenAI(model = "gpt-4o")):
        self.state = state
        self.system_prompt = system_prompt
        self.tools: Optional[list] = tools
        self.tool_node = None
        self.graph = StateGraph(state)
        self.model = model
        self.app = None

        # basic LLM call node
        def model_call(state: AgentState) -> AgentState:
            system_prompt = SystemMessage(content=self.system_prompt)
            response = self.model.invoke([system_prompt] + state["messages"])
            return {"messages": [response]}

        self.graph.add_node("agent", model_call)

        # if tools, create the_tool node and connect to the agent
        if self.tools:
            self.tool_node = ToolNode(tools=self.tools) # premade toolnode from langgraph, pretty handy
            print("pushed tools: ", self.tools)
            self.graph.add_node("tools", self.tool_node)
            self.model = self.model.bind_tools(self.tools)
            self._connect_tools()

    """
    The following are pre-made methods, don't feel obligated to use them, but I'm 99.99% sure you'll have
    to implement them on the concrete agents
    """

    def _connect_tools(self):

        # after the tool calls end, the "end_tool_calls" node 
        # will serve as a connection to your following sequence of logic
        self.graph.add_node("end_tool_calls", lambda x: x)

        def switch(state: AgentState) -> str:
            messages = state["messages"]
            last_message = messages[-1]

            if not last_message.tool_calls:
                return "goto_end_tools"
            else:
                return "use_tool"

        self.graph.add_conditional_edges(
            "agent",
            switch,
            {
                "goto_end_tools": "end_tool_calls",
                "use_tool": "tools"
            }
        )

        self.graph.add_edge("tools", "agent")

    def compile_app(self):
        self.app = self.graph.compile()

    def invoke(self, *args):
        return self.app.invoke(*args)

    def display_graph(self):
        if self.app:
            display(Image(self.app.get_graph().draw_mermaid_png()))


##. initial_logic - agent (tools) -  end_tool_calls -> ... 
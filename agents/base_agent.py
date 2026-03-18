# Base agent class (common-shared functionalities)

from typing import Annotated, Optional,Sequence, TypedDict
from langchain_core.messages import BaseMessage,SystemMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from services.throttle import throttled_model_call
from services.llm_client import get_client
from agents.base_graph import BasicGraph

basic_system_prompt = "You are an AI assistant, answer the user query to your best abillity"

class AgentState(TypedDict): 
    messages : Annotated[Sequence[BaseMessage], add_messages]

class BasicAgent(BasicGraph):
    def __init__( self, tools: list = None, state:TypedDict = AgentState(),  model_name:str = None, system_prompt=basic_system_prompt):
        super().__init__(state)
        self.system_prompt = system_prompt
        self.tools: Optional[list] = tools
        self.tool_node = None
        self.model = get_client(model_name)

        # basic LLM call node

        def model_call(state: AgentState) -> AgentState:
            system_prompt = SystemMessage(content=self.system_prompt)
            response = throttled_model_call(self.model, [system_prompt] + state["messages"])
            return {"messages": [response]}

        self.graph.add_node("agent", model_call)

        # if tools, create the_tool node and connect to the agent
        if self.tools:
            self.tool_node = ToolNode(tools=self.tools) # premade toolnode from langgraph, pretty handy
            print("pushed tools: ", self.tools)
            self.graph.add_node("tools", self.tool_node)
            self.model = self.model.bind_tools(self.tools)
            self._connect_tools()

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

##. initial_logic - agent (tools) -  end_tool_calls -> ... 
from typing import TypedDict
from langgraph.graph import StateGraph
from IPython.display import Image, display

class BasicGraph():
    def __init__(self, state):
        self.state = state
        self.graph = StateGraph(state)

    def compile_app(self):
        self.app = self.graph.compile()

    def invoke(self, *args):
        return self.app.invoke(*args)

    def display_graph(self):
        if self.app:
            display(Image(self.app.get_graph().draw_mermaid_png()))
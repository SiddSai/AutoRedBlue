from langchain_openai import ChatOpenAI
import os
from services.throttle import get_langchain_rate_limiter

BASE_URL=os.getenv("OPENAI_API_BASE")
API_KEY=os.getenv("OPENAI_API_KEY")
# returns a langchain 'model' instance 

EXAMPLE_MODEL_NAMES=[
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "anthropic/claude-3.5-sonnet",
    "google/gemini-2.0-flash-001",
    "meta-llama/llama-3.3-70b-instruct",
    "mistralai/mistral-large-2411",
    "deepseek/deepseek-v3",
    "qwen/qwen-2.5-72b-instruct",
    "anthropic/claude-3-haiku"
]

def get_client(model_name:str=None):

    model = None
    rate_limiter = get_langchain_rate_limiter()

    if model_name is not None:
        model = ChatOpenAI(model=model_name, rate_limiter=rate_limiter)
    else:
        model = ChatOpenAI(model="openai/gpt-4o", rate_limiter=rate_limiter)

    return model
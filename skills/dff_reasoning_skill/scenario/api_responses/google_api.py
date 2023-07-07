from os import getenv
import json
from langchain.agents import Tool
from langchain.memory import ConversationBufferMemory
from langchain import OpenAI
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.agents import initialize_agent
from df_engine.core import Context, Actor
from scenario.utils import compose_input_for_API

ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")
available_variables = {f"{var}": getenv(var, None) for var in ENVVARS_TO_SEND}

API_CONFIG = getenv("API_CONFIG", "api_conf.json")
with open(f"api_configs/{API_CONFIG}", "r") as f:
    api_conf = json.load(f)

for key, value in api_conf.copy().items():
    for api_key in value["keys"]:
        if not available_variables[api_key]:
            del api_conf[key]
            break

if "google_api" in api_conf.keys():
    search = GoogleSearchAPIWrapper()
    tools = [
        Tool(
            name="Current Search",
            func=search.run,
            description="useful when you need to answer questions about current \
    events or the current state of the world",
        ),
    ]
    memory = ConversationBufferMemory(memory_key="chat_history")
    llm = OpenAI(temperature=0)
    agent_chain = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True, memory=memory)


def google_api_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        api_input = compose_input_for_API(ctx, actor)
        answer = agent_chain.run(api_input)
        return answer

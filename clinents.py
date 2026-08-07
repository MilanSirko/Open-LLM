import os
import yaml
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel
from agents import Agent, Runner, set_tracing_disabled, set_default_openai_api, set_default_openai_client, OpenAIChatCompletionsModel, ModelSettings

load_dotenv()
set_tracing_disabled(True)
set_default_openai_api('chat_completions')
airouter=AsyncOpenAI(api_key=os.getenv('airouter-api'), base_url=os.getenv('airouter-url'))

nvidia_client = AsyncOpenAI(base_url=os.getenv('nvidia-url'),api_key=os.getenv("nvidia-api"),)
cerebras = AsyncOpenAI(base_url=os.getenv('cerebras-url'),api_key=os.getenv("cerebras-api"))
groq = AsyncOpenAI(base_url=os.getenv('Groq-url'), api_key=os.getenv('Groq-api'))
openrouter = AsyncOpenAI(base_url=os.getenv('Openrouter-url'), api_key=os.getenv('Openrouter-api'))
google = AsyncOpenAI(base_url=os.getenv('Google-url'), api_key=os.getenv('Google-api'))
huggingface = AsyncOpenAI(base_url=os.getenv('huggingface-url'), api_key=os.getenv('huggingface-api'))
opencode_zen = AsyncOpenAI(base_url=os.getenv('opencode-url'),api_key=os.getenv('opencode-api'),)

async def call_groq(model: str, messages: list[dict], **kwargs) -> dict:
    response = await groq.chat.completions.create(model=model, messages=messages, **kwargs)
    return response.model_dump()

async def call_openrouter(model: str, messages: list[dict], **kwargs) -> dict:
    response = await openrouter.chat.completions.create(model=model, messages=messages, **kwargs)
    return response.model_dump()

async def call_nvidia(model: str, messages: list[dict], **kwargs) -> dict:
    response = await nvidia_client.chat.completions.create(model=model, messages=messages, **kwargs)
    return response.model_dump()

async def call_cerebras(model: str, messages: list[dict], **kwargs) -> dict:
    response = await cerebras.chat.completions.create(model=model, messages=messages, **kwargs)
    return response.model_dump()

async def call_google(model: str, messages: list[dict], **kwargs) -> dict:
    response = await google.chat.completions.create(model=model, messages=messages, **kwargs)
    return response.model_dump()

async def call_huggingface(model: str, messages: list[dict], **kwargs) -> dict:
    response = await huggingface.chat.completions.create(model=model, messages=messages, **kwargs)
    return response.model_dump()

async def call_opencode_zen(model: str, messages: list[dict], **kwargs) -> dict:
    response = await opencode_zen.chat.completions.create(model=model, messages=messages, **kwargs)
    return response.model_dump()

with open('models.yaml', 'r', encoding='UTF-8') as f:
    models_config = yaml.safe_load(f)['models']

class RouteDecision(BaseModel):
    chosen_slug: str
    reason: str

async def _build_router_agent() -> Agent:
    available_slugs = [m['slug'] for m in models_config]
    options = ", ".join(available_slugs)

    instructions = f"""
You are a model router. Given the user's message, choose the BEST model to
handle it from this list of slugs: {options}.
Consider: task complexity, whether deep reasoning is needed, or if it's a
simple factual question. Prefer smaller/faster models for simple tasks,
larger/stronger models for complex reasoning.
Respond with the exact slug from the list and a short reason.
"""
    return Agent(
        name="MetaRouter",
        model=OpenAIChatCompletionsModel(model="poolside/laguna-xs-2.1:free", openai_client=airouter),
        instructions=instructions,
        output_type=RouteDecision,
        model_settings=ModelSettings(max_tokens=200, temperature=0.1),
    )

async def pick_model(user_message: str) -> str:
    """
    Returns the chosen model slug (from models.yaml) for a given user
    message, decided by a small local agent. Falls back to the first
    available slug if the agent returns something unexpected.
    """
    available_slugs = [m['slug'] for m in models_config]
    router_agent =await _build_router_agent()

    result = await Runner.run(router_agent, user_message, max_turns=3)
    decision: RouteDecision = result.final_output

    if decision.chosen_slug not in available_slugs:
        return available_slugs[0]
    return decision.chosen_slug
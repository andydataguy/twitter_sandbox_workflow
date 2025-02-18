# Src/Core/agents.py
from pydantic_ai import Agent

simple_agent = Agent(
    model="gemini-1.5-flash",
    system_prompt="You are a helpful assistant designed to provide crypto information."
)
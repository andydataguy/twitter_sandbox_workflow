# Src/Core/prompts.py
from jinja2 import Environment, FileSystemLoader

# Create a Jinja environment
env = Environment(loader=FileSystemLoader("src/core/prompts"))

# Define a simple prompt template using Jinja
simple_prompt_template = """
The current crypto token is: {{ token_name }}.
Respond to the user's query about this token in a helpful way.
User query: {{ user_query }}
"""
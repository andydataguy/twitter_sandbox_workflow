# Agents 

**PydanticAI: A Modular, Type-Safe Framework for Intelligent Agents**

PydanticAI allows us to build intelligent agents that leverage Large Language Models (LLMs) while maintaining:

*   **Type Safety:**  Inputs and outputs are defined using Pydantic models, ensuring data integrity.
*   **Modularity:** Agents are self-contained, and *tools are defined separately and passed in*.
*   **Structured Outputs:** Agents return Pydantic models, not just raw text.
*   **Flexibility:** Supports various LLMs (OpenAI, Gemini, Anthropic, etc.) and is designed for extension.
*   **Orchestration Friendly:** Designed for use inside of a multi-agent orchestration framework such as LangGraph.

**The Six Key Components of a PydanticAI Agent (in *Our* Architecture)**

Let's break down how a PydanticAI agent is constructed within the context of *your* project's architecture, specifically focusing on the `src/Core/Agents` and `src/Core/Tools` directories, and the use of Jinja2 for prompts.

1.  **LLM Model (Instantiated within the Agent):**

    *   **What it is:** The underlying language model that powers the agent's reasoning and generation capabilities.  We specify this when creating the `Agent` instance.
    *   **Where it's defined:** Inside the agent definition file that contains all agents (e.g., `src/Core/Agents/agent.py`).
    *   **How it's used:**  We use the `Agent` class from `pydantic_ai`, passing the model identifier as a string.
    *   **Modularity Note:**  The choice of LLM is encapsulated within the agent definition.  We can easily switch models (e.g., to OpenAI or Anthropic) by changing this string, without affecting the agent's tools or overall workflow structure. The rest of the model integration is handled behind-the-scenes. 

2.  **System Prompt (Jinja2 Template + Rendering Function):**

    *   **What it is:**  Instructions and context provided to the LLM to guide its behavior.  In our architecture, these are *always* dynamic Jinja2 templates.
    *   **Where it's defined:**
        *   *Template:*  `.j2` file in `src/Core/Templates/Prompts/` (e.g., `crypto_strategist_prompt.j2`).
        *   *Rendering Function:*  Python function in `src/Core/Templates/Prompts/prompts.py`.  This function loads and renders the template.
    *   **How it's used:** The rendering function takes a Pydantic model (or a dictionary) as input, containing the data to be injected into the template. The rendered prompt (a string) is then passed to the LLM through PydanticAI.
    *   **Modularity Note:**  Prompts are completely decoupled from agent logic.  They live in their own files and can be edited independently.  The rendering function acts as a bridge, connecting the template to the data.  This also allows non-developers (e.g., prompt engineers) to contribute.

3.  **Tools (List of Pre-defined Functions):**

    *   **What they are:** *Independent* Python functions, decorated with `@tool`, that can be passed into a list for the agent to choose from.
    *   **Where they're defined:**  In `src/Core/Tools/` (and its subdirectories, like `Market_data`, `Search_data`, etc.).  *Each tool is a separate function.*
    *   **How they're used:**  The agent receives a *list* of these tool functions.  The LLM decides which tool to call (if any) based on the prompt and the tool's description (extracted from the docstring).
    *   **Example (from `src/Core/Tools/Market_data/coingecko_tools.py`):**
        ```python
        # src/Core/Tools/Market_data/coingecko_tools.py
        from pydantic_ai.tools import tool
        from pydantic import BaseModel, Field
        import httpx  # Or any other HTTP client

        # Data models would usually be defined in the `TOOL_NAME_models.py` file they are moved here for the sake of example
        class MarketDataInput(BaseModel):
            token_symbol: str = Field(..., description="The cryptocurrency token symbol.")

        class MarketDataOutput(BaseModel):
            price: float = Field(..., description="The current price of the token.")
            market_cap: float = Field(..., description="The market capitalization of the token.")

        @tool
        async def get_market_data_tool(input: MarketDataInput, run_context) -> MarketDataOutput:
            """Fetches the current market data for a given cryptocurrency token."""
            async with httpx.AsyncClient() as client:
                # ... (Implementation to call CoinGecko API, handle errors, etc.) ...
                # Use input.token_symbol to get symbol provided by the model.
                response = await client.get(f"https://api.coingecko.com/api/v3/simple/price?ids={input.token_symbol}&vs_currencies=usd&include_market_cap=true")
                response.raise_for_status()
                data = response.json()
                return MarketDataOutput(
                    price=data[input.token_symbol.lower()]['usd'],
                    market_cap=data[input.token_symbol.lower()]['usd_market_cap']
                )
        ```
    *   **Modularity Note:**  This is *the* key to your modular architecture.  Tools are entirely separate from agents.  The `get_market_data_tool` function above doesn't know or care *which* agent will use it.  This promotes reusability, testability, and maintainability.

4.  **Structured Result (Pydantic Model):**

    *   **What it is:** A Pydantic `BaseModel` that defines the *required* structure of the agent's output.
    *   **Where it's defined:**  Stored within the `Models` sub-directory in a file named after the subject agent along with all other models related to that agent. 
    *   **How it's used:**  Passed as the `result_type` to the `Agent` constructor. PydanticAI uses this model to *validate* the LLM's output, ensuring it conforms to the expected structure.  If the output is invalid, PydanticAI can automatically retry with a corrected prompt. This is the power of PydanticAI!
    *   **Modularity Note:**  By defining output structures as Pydantic models, we create clear data contracts between agents and other parts of the system.  This makes it easy to integrate agents into larger, more sophisticated workflows.

5.  **Dependencies (`Deps` Class and `RunContext`):**

    *   **What it is:** A mechanism for providing external dependencies (API clients, API keys, loggers, etc.) to the agent and its tools.
    *   **Where it's defined:**  Typically a Pydantic Model or a dataclass defined in the agents dedicated file within the `Models` sub-directory. 
    *   **How it's used:**
        *   An instance of the `Deps` class is created when the agent is run.
        *   The `Deps` instance is passed to the `deps` parameter of the `run`, `run_sync`, or `run_stream` methods.
        *   The `RunContext` object (available to system prompt functions and tools) provides access to the dependencies via `ctx.deps`.
        *   Dependencies are used to perform necessary operations and actions.
    * **Modularity Implication**
      *   Allows us to inject the dependencies at runtime, making it easy to swap out implementations (e.g., for testing) without changing the agent or tool code.
      *   Keeps secrets (API keys) out of the core logic.
      *   Provides the correct parent span for any logging, by injecting.

6.  **Model Settings (Optional):**

    *   **What it is:**  Configuration options for the underlying LLM (e.g., `temperature`, `max_tokens`).
    *   **Where it's defined:**  Passed to the `Agent` constructor (as `model_settings`) or to individual `run` calls.
    *   **How it's used:**  Allows fine-tuning of the LLM's behavior.
    * **Example:**

    ```python
    crypto_strategist_tools = [
    perplexity_search_tool,
    get_tweets_from_search,
    get_market_data_tool,
    ]
        crypto_strategist_agent = Agent(
            'openai:gpt-4o',
            result_type=CryptoStrategistReport,
            tools=[crypto_strategist_tools],
            system_prompt=...,
            model_settings={"temperature": 0.2, "max_tokens": 2048}  # Add model settings
        )

Alright, now that we have a high-level overview, let's dive a little deeper into these concepts. We'll start with a brief overview of the architecture and then move on to a detailed exploration of the critical components that make up this framework.

*   **Extreme Modularity:** Tools are *completely* separate from agents. Agents receive tools as a list.
*   **Jinja2 Prompts Only:** All system prompts are Jinja2 templates, managed in `src/Core/Templates/Prompts`.
*   **Structured Pydantic Outputs:**  Outputs are *always* Pydantic models, defined for validation and consistency.
*   **Centralized Models:** Pydantic models specific to an agent (input, output, dependencies) reside in a dedicated file within `src/Core/Models/`, named after the agent (e.g., `crypto_strategist_agent_models.py`).
*   **Clean Agent Definitions:** The `src/Core/Agents/agents.py` file should contain *only* the `Agent` class instantiations, making them very concise and readable.
*   **Deep Dive into `RunContext` and Dependencies:**  Provide clear, practical explanations and multiple examples.
*   **No `@agent.system_prompt` Decorator:** We'll manage system prompt generation outside the agent definition file, leveraging `prompts.py` for rendering.
*   **No LangGraph Code in Agent README:** Focus *solely* on PydanticAI agent creation, *not* LangGraph integration (except to mention how it *facilitates* integration).

**Purpose: Centralized, Clean, and Minimal Agent Definitions**

The Agents directory contains a single python file, `agents.py`, which houses the instantiations of all PydanticAI agents used in the Twitter Sandbox Workflow.  Agents are the intelligent actors that reason, make decisions, and use tools.  Our design philosophy emphasizes:

*   **Extreme Modularity:** Agents are configured with *pre-defined* tools and prompts.
*   **Type Safety:** Pydantic models define agent inputs and *outputs*.
*   **Concise Definitions:** `agents.py` contains *only* the `Agent` class instantiations and tools lists, making it easy to see all agents at a glance.

**PydanticAI: The Foundation**

We use PydanticAI because it provides:

*   **Type Safety:** Guarantees data integrity via Pydantic models.
*   **Modularity:** Supports our tool-passing architecture.
*   **Structured Outputs:** Ensures consistent, validated agent outputs.
*   **Model Agnostic:**  Supports various LLMs (currently using Google Gemini).
*   **Dependency Injection:** Simplifies passing dependencies (API keys, clients, etc.).

**`agents.py` Structure (Example):**

```python
# src/Core/Agents/agents.py

from pydantic_ai import Agent
# 1. Import PRE-DEFINED tools
from src.Core.Tools.Search_data.perplexity_tools import perplexity_search_tool
from src.Core.Tools.Twitter_data.socialdata_tools import get_tweets_from_search
from src.Core.Tools.Market_data.coingecko_tools import get_market_data_tool

# 2. Import Agent-Specific Models (Input, Output, Dependencies)
from src.Core.Models.crypto_strategist_agent_models import *
from src.Core.Models.content_creation_agent_models import *

# 3. Import Prompt Rendering Functions
from src.Core.Templates.Prompts.prompts import *


# --- Crypto Strategist Agent ---
crypto_strategist_tools = [
    perplexity_search_tool,
    get_tweets_from_search,
    get_market_data_tool,
]

crypto_strategist_agent = Agent(
    'google-gla:gemini-2.0-pro',
    result_type=CryptoStrategistReport,
    tools=crypto_strategist_tools,  # List of imported tools
    system_prompt=render_crypto_strategist_prompt,  # Jinja2 rendering function
    dependencies=CryptoStrategistDeps, # Dependency Model
)

# --- Content Creation Agent (Similar Structure) ---
content_creation_agent_tools = [...]

content_creation_agent = Agent(
    'google-gla:gemini-2.0-pro',
    result_type=ContentCreationReport,
    tools=content_creation_agent_tools,
    system_prompt=render_content_creation_prompt, # Jinja2 rendering function
    dependencies=ContentCreationDeps,  # Dependency Model
)

# ... (definemore agents as needed) ...
```
```

**Key Elements Explained:**

1.  **LLM Model:**  Specified directly in the `Agent` constructor (e.g., `'google-gla:gemini-2.0-pro'`).  We can easily switch models.

2.  **System Prompt (Jinja2):**
    *   *Defined:* `.j2` files in `src/Core/Templates/Prompts/`.
    *   *Rendered:*  Functions in `src/Core/Templates/Prompts/prompts.py` load and render the templates, taking a Pydantic model as input (for dynamic data).  Example: `render_crypto_strategist_prompt`.
    *   *Passed to Agent:*  We pass the *rendering function* itself to the `system_prompt` parameter of the `Agent`.  PydanticAI will call this function *with the appropriate context* to get the actual prompt string.

3.  **Tools (Modular):**
    *   *Defined:*  As `@tool`-decorated functions in `src/Core/Tools/...`.
    *   *Imported:*  Into `agents.py`.
    *   *Passed to Agent:*  As a *list* in the `tools` parameter of the `Agent`.

4.  **Structured Result (Pydantic Model):**
    *   *Defined:* In `src/Core/Models/AGENT_NAME_models.py` (e.g., `crypto_strategist_agent_models.py`).
    *   *Used:*  As the `result_type` in the `Agent` constructor.  PydanticAI *guarantees* the output will match this model (or raise a validation error).

5.  **Dependencies (`Deps` Class and `RunContext`):**
    *   **`Deps` Class:** A Pydantic model (or dataclass) defined in `src/Core/Models/AGENT_NAME_models.py` (e.g., `crypto_strategist_agent_models.py`).  It holds all the dependencies an agent and its tools need (API keys, HTTP clients, loggers, etc.).
    *   **`RunContext`:**  PydanticAI's mechanism for providing context to various parts of the agent (system prompt function, tools, result validators).  It's how dependencies are injected.
        *   `ctx.deps`: Access the dependencies defined in your `Deps` class.
        *   `ctx.prompt`: Contains the initial input (prompt) passed to the `agent.run()` method.
        *   `ctx.state`:  Access the current LangGraph state (if the agent is used within a LangGraph).
        *   `ctx.tool_calls`: Access tool calls within a tool's execution.
        *   `ctx.logger`: Access a logger instance.
    *   **How it works:**
        1.  Define a `Deps` class.
        2.  Pass `deps_type=YourDepsClass` to the `Agent` constructor.
        3.  When you call `agent.run(...)`, pass a `deps` argument: `agent.run(..., deps=Deps(...))`.
        4.  Within system prompt functions, tools, and validators, access dependencies via `ctx.deps`.

6.  **Model Settings (Optional):**  Fine-tune the LLM (e.g., `temperature`, `max_tokens`).

**Example: `src/Core/Models/crypto_strategist_agent_models.py`:**

```python
 # src/Core/Models/crypto_strategist_agent_models.py
from pydantic import BaseModel, Field
from typing import List
import httpx
import logfire

class CryptoStrategistInput(BaseModel):
    token_symbol: str = Field(..., description="Cryptocurrency token symbol.")

class CryptoStrategistReport(BaseModel):
    final_report: str = Field(..., description="In-depth crypto strategist report.")
    key_findings: List[str] = Field(..., description="Key findings.")
    recommendation: str = Field(..., description="Recommendation (e.g., 'Buy', 'Sell', 'Hold').")

class CryptoStrategistDeps(BaseModel):
    http_client: httpx.AsyncClient = Field(default_factory=httpx.AsyncClient) # Reusable client
    logfire_span: logfire.LogfireSpan = Field(...) 
    social_data_api_key: str
    perplexity_api_key: str
    coingecko_api_key: str
    # Add Logfire span as dependency
```

**Example: `src/Core/Templates/Prompts/prompts.py` (Jinja2 Rendering):**

```python
# src/Core/Templates/Prompts/prompts.py
from jinja2 import Environment, FileSystemLoader
from src.Core.Models.crypto_strategist_agent_models import CryptoStrategistInput
from pydantic import BaseModel

environment = Environment(loader=FileSystemLoader("src/Core/Templates/Prompts"))

def render_crypto_strategist_prompt(data: CryptoStrategistInput) -> str: # The input type now matches
    template = environment.get_template("crypto_strategist_prompt.j2")
    return template.render(data=data.model_dump()) # Convert to dict for Jinja2

# ... (other prompt rendering functions) ...
```

**Example Usage (within LangGraph - `src/Core/graph.py`):**

```python
# Simplified example - in src/Core/graph.py
from langgraph.graph import StateGraph, END
from src.Core.Agents.agents import crypto_strategist_agent # Import the INSTANCE
from src.Core.Models.crypto_strategist_agent_models import CryptoStrategistInput, CryptoStrategistDeps # Import models
from src.Core.Workflow.State.state import GraphState # Assuming you have a GraphState
import os
import logfire # For span management

workflow = StateGraph(GraphState)
workflow.add_node("crypto_strategist", crypto_strategist_agent) # Add to the graph
workflow.set_entry_point("crypto_strategist") #Simplfied version
workflow.add_edge("crypto_strategist", END)

graph = workflow.compile()

async def main():
   with logfire.span("main_span") as main_span: # Create top level span
        deps = CryptoStrategistDeps(
              social_data_api_key=os.environ["SOCIALDATA_API_KEY"],
              perplexity_api_key=os.environ["PERPLEXITY_API_KEY"],
              coingecko_api_key=os.environ["COINGECKO_API_KEY"],
              logfire_span = main_span, # Pass down for instrumentation
              http_client = httpx.AsyncClient()
        )
        result = await graph.ainvoke(
              {"input":CryptoStrategistInput(token_symbol="SOL")}, # Pass initial input
              configurable={"deps": deps} # Pass dependencies via configurable
        )
        print(result)

import asyncio
asyncio.run(main())
```

**Key Takeaways & Next Steps:**

*   **`agents.py` is CLEAN:**  It *only* contains agent instantiations.  All other logic is delegated.
*   **Tools are Modular:** Defined in `src/Core/Tools/`, reusable across agents.
*   **Prompts are Templates:** Jinja2 templates in `src/Core/Templates/Prompts/`, rendered by functions in `prompts.py`.
*   **Models are Centralized:** Agent-specific models are in `src/Core/Models/AGENT_NAME_models.py`.
*   **Dependencies via `Deps` and `RunContext`:**  Dependencies are neatly packaged and injected.
* **LangGraph is Orchestrator** PydanticAI agents are used within the LangGraph as nodes.

Your next steps are to implement the `agents.py` file, populate the `Tools` directory with your tool functions, create the necessary Pydantic models in `src/Core/Models/`, and write the Jinja2 templates in `src/Core/Templates/Prompts/`. This structure gives you maximum flexibility, maintainability, and testability. The `RunContext` and dependency injection are *critical* for making this all work smoothly.

This revised README and detailed explanation should provide a *much* clearer understanding of how to structure your PydanticAI agents and integrate them into your modular architecture. It emphasizes best practices for your specific use case and addresses all the points you raised.

# Integrating PydanticAI Agents with Supabase (Postgres)

This document demonstrates how to integrate PydanticAI agents with a Supabase database (using PostgreSQL) for scenarios where agents need to directly interact with database data.

**Why Use Database Dependencies?**

While many agent interactions will be mediated through tools, there are cases where direct database access within an agent is beneficial:

*   **Complex Queries:**  For intricate queries that are difficult to express through tool calls, direct SQL access can be more efficient and flexible.
*   **Data Aggregation/Transformation:** Agents might need to aggregate or transform data from the database *before* presenting it to the LLM.
*   **Direct Database Updates:**  In some scenarios, an agent might need to directly update database records (with appropriate safeguards!).

**Prerequisites:**

*   A Supabase project with a PostgreSQL database.
*   The `asyncpg` library installed: `pip install asyncpg` (or use `uv pip install asyncpg`)
*   The Supabase connection string (obtained from your Supabase project settings).  **Treat this as a secret!**

**Steps:**

1.  **Define the `Deps` Class:** Create a `Deps` class (or extend an existing one) to include the database connection pool. We use a connection *pool* for efficiency.

    ```python
    # src/Core/Models/agent_models/your_agent_models.py
    import asyncpg
    from pydantic import BaseModel, Field
    import logfire

    class MyAgentDeps(BaseModel):
        db_pool: asyncpg.Pool = Field(default_factory=asyncpg.create_pool)
        logfire_span: logfire.LogfireSpan
        # ... other dependencies ...

    ```

2.  **Initialize the Pool (Application Startup):**  You *must* initialize the connection pool *before* running your agent.  This is typically done in your `main.py` or application startup logic.  *Crucially*, you need to use `await` to properly initialize the pool.

    ```python
    # main.py (or similar)
    import asyncio
    import os
    from src.Core.Models.agent_models.your_agent_models import MyAgentDeps
    # ... other imports ...
    import logfire

    async def main():

      logfire.configure(
          send_to_logfire='if-token-present',
          environment='development',
          service_name='agent-alyx',
          service_version='0.1.0',
      )

      with logfire.span("main_span") as main_span: # Pass down to all of the children
          deps = MyAgentDeps(
              db_pool=await asyncpg.create_pool(os.environ["DATABASE_URL"]),  # Initialize the pool!
              logfire_span = main_span
              # ... other dependencies ...
          )

          # ... (Rest of your application logic, including running the LangGraph) ...

          # Example LangGraph call:
          # result = await graph.ainvoke({"input": ...}, configurable={"deps": deps})
          #The run context will now have access to all the dependencies you created here

    if __name__ == "__main__":
        asyncio.run(main())
    ```

3.  **Access the Pool in the System Prompt (Example):**

    ```python
    # src/Core/Agents/your_agent.py
    from pydantic_ai import Agent, RunContext
    from src.Core.Models.agent_models.your_agent_models import MyAgentDeps, MyAgentInput, MyAgentOutput
    #Import the JINJA2 Rendering agent
    from src.Core.Templates.Prompts.prompts import render_my_agent_prompt

    my_agent = Agent(
        'openai:gpt-4o',
        result_type=MyAgentOutput,
        # ... tools, etc. ...
        dependencies=MyAgentDeps,
    )

    # please note this is the incorrect way of defining a prompt
    # we are only showing this for the sake of example of having agents use supabase
    # the prompt rendering should ALWAYS be done in the templates/prompts sub-directory for modularity
    @my_agent.system_prompt
    async def generate_system_prompt(ctx: RunContext[MyAgentDeps]) -> str:
        async with ctx.deps.db_pool.acquire() as connection:
            # Example: Fetch the number of users from the database
            user_count = await connection.fetchval("SELECT COUNT(*) FROM users")

        # Render the Jinja2 template, passing in the user_count
        prompt_data = {"user_count": user_count, "input": ctx.prompt}
        return render_my_agent_prompt(prompt_data)

    ```

4.  **Access the Pool in a Tool (Example):**

    ```python
    # src/Core/Tools/database_tools.py
    from pydantic_ai.tools import tool
    from pydantic import BaseModel, Field
    from src.Core.Models.agent_models.your_agent_models import MyAgentDeps # Import your Deps

    # NOTE: these pydantic data models should be defined in their own models file for this tool (e.g. `TOOL_NAME_models.py`)
    class UserQueryInput(BaseModel):
        user_id: int = Field(..., description="The ID of the user to query.")

    class UserQueryResult(BaseModel):
        username: str = Field(..., description="The username of the user.")
        email: str = Field(..., description="The email address of the user.")

    @tool
    async def get_user_by_id(input: UserQueryInput, run_context) -> UserQueryResult:
        """Retrieves user information from the database by user ID."""
        deps = run_context.deps #correct way to access
        async with deps.db_pool.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT username, email FROM users WHERE id = $1", input.user_id
            )
            if row:
                return UserQueryResult(**row)
            else:
                return UserQueryResult(username="Not Found", email = "")
    ```

**Explanation and Key Points:**

*   **`asyncpg.create_pool()`:**  This function creates a *connection pool*.  Connection pools are essential for efficient database interaction, especially in asynchronous applications.  They maintain a set of open connections that can be reused, avoiding the overhead of creating a new connection for every request.
*   **`await`:** The `await` keyword is crucial.  `asyncpg.create_pool()` is an asynchronous function.  We *must* use `await` to ensure the pool is properly initialized before we try to use it.
*   **`with deps.db_pool.acquire() as connection:`:** This is how you *borrow* a connection from the pool. The `with` statement ensures the connection is automatically returned to the pool when you're finished with it (even if an error occurs).
*   **`connection.fetchrow()`, `connection.fetchval()`, etc.:**  These are `asyncpg` methods for executing SQL queries and retrieving results.  You *must* use `await` with these methods.
*   **Dependency Injection:** The `Deps` class and `RunContext` work together to provide the `db_pool` to your agent and tools in a clean and testable way.
* **Security:**  Store your database connection string (`DATABASE_URL`) securely, ideally as an environment variable.  *Never* hardcode secrets in your code.

This comprehensive example demonstrates how to integrate a Supabase (PostgreSQL) database connection into your PydanticAI agents and tools, using best practices for asynchronous programming and dependency injection. This pattern is essential for building robust, data-driven agents. Remember to adapt the SQL queries and Pydantic models to your specific database schema and application needs.

> Engineer's Notes: This subdirectory is dedicated to defining all PydanticAI agents used within the system. We are currently utilizing Google Gemini as the foundational model for agent development, but will also be integrating with other tools and models as needed. It is crucial to adhere to PydanticAI standards to ensure type safety and consistency across agents. Each agent is defined with a clear purpose and may be equipped with various tools to enhance functionality. This includes integrating with structured data, such as prompts and outputs, which are essential for agent responses. Ensure that agents are well-documented, with connections to relevant data sources and tools clearly specified. This approach facilitates seamless integration and interaction within the broader workflow, promoting modularity and maintainability.
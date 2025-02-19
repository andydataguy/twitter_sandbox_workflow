# src/Core/Models: Pydantic Data Models - The Foundation of Structured Data

**Purpose: Centralized Repository for Agent-Specific and Miscellaneous Pydantic Models**

The `src/Core/Models` directory is the central hub for Pydantic data models within the Twitter Sandbox Workflow.  It's designed for *specific types* of models to promote a highly organized and maintainable codebase.  This directory houses two main categories of Pydantic models, organized into subdirectories:

1.  **`agent_models/`:** Contains Pydantic models *directly related* to PydanticAI agent definitions.  This includes input schemas, output schemas (reports), and dependency classes (`Deps`).
2.  **`miscellaneous_models/`:** Contains other Pydantic models that represent data structures *not* directly tied to specific agents or tools.  This is for reusable, application-wide data structures.

**What this directory *DOES NOT* contain (and why):**

*   **Tool Models:** Pydantic models that define the input and output structures for *tools* are located within the `src/Core/Tools` subdirectory, alongside the tool definitions themselves (e.g., `src/Core/Tools/Market_data/coingecko_models.py`).  This keeps tool definitions and their data contracts tightly coupled.
*   **Workflow State Models:**  Pydantic models that define the overall *state* of the LangGraph workflow are located in `src/Core/Workflow/State/state.py`.  This keeps state definitions close to the workflow logic that uses them.
* **Jinja Templates** These are prompts, not models, and should be located within `src/Core/Templates/Prompts`.

**Why this Strict Organization?**

This seemingly strict organization is *essential* for:

*   **Modularity:**  Each component (agents, tools, workflow) has its data models clearly defined in a predictable location.
*   **Maintainability:**  Changes to a data model are localized, reducing the risk of unintended side effects.
*   **Testability:**  Models can be tested independently.
*   **Readability:**  The codebase is easier to navigate and understand.
*   **Scalability:**  The project can grow without the models becoming a tangled mess.
* **Clarity:** Knowing the exact location of data models, whether in the agent models, tools directories, workflow subdirectory, or miscellaenous models.

**1. `agent_models/` Subdirectory**

This subdirectory is the most important part of `src/Core/Models` in the context of PydanticAI.  It contains a separate Python file for *each* agent defined in `src/Core/Agents/agents.py`.

**File Naming Convention:**  `agent_name_models.py` (e.g., `crypto_strategist_agent_models.py`)

**Contents of an Agent Model File:**

*   **Input Model (`AgentNameInput`):** A Pydantic `BaseModel` defining the structure of the *initial* input to the agent *within the LangGraph workflow*. This model is used when you first call `graph.ainvoke()`.  It is *not* the direct input to the LLM. Instead, the data from this model (along with other data from the LangGraph state and dependencies) is used to *render* the Jinja2 system prompt, which *is* the direct input to the LLM.  While this model *can* be simple (e.g., just a `prompt: str` field), it can also be more complex if the agent requires structured initial input. This Input Model is passed into the LangGraph state as the value for the "input" key.
*   **Output Model (`AgentNameReport` or similar):**  A Pydantic `BaseModel` defining the *structured output* of the agent. This is the `result_type` you pass to the `Agent` constructor. This is *crucial* for ensuring consistent, validated outputs. When we say "report" that almost always refers to the structured output coming from a PydanticAI agent. 
*   **Dependencies Model (`AgentNameDeps`):**  A Pydantic `BaseModel` (or a dataclass) defining the *dependencies* required by the agent and its tools (API keys, HTTP clients, loggers, etc.). This is used for dependency injection.

**Example: `src/Core/Models/agent_models/crypto_strategist_agent_models.py`**

```python
# src/Core/Models/agent_models/crypto_strategist_agent_models.py
from pydantic import BaseModel, Field
from typing import List
import httpx
import logfire

class CryptoStrategistInput(BaseModel):
    token_symbol: str = Field(..., description="Cryptocurrency token symbol.")

class CryptoStrategistReport(BaseModel):
    final_report: str = Field(..., description="In-depth crypto strategist report.")
    key_findings: List[str] = Field(..., description="Key findings from the analysis.")
    recommendation: str = Field(..., description="Recommendation (e.g., 'Buy', 'Sell', 'Hold').")

class CryptoStrategistDeps(BaseModel):
    http_client: httpx.AsyncClient = Field(default_factory=httpx.AsyncClient)  # Reusable client
    logfire_span: logfire.LogfireSpan = Field(...)  # REQUIRED, pass from LangGraph state.
    social_data_api_key: str
    perplexity_api_key: str
    coingecko_api_key: str
```

**2. `miscellaneous_models/` Subdirectory**

This subdirectory holds Pydantic models that are *not* directly tied to a specific agent or tool.  These are more general-purpose data structures used across the application.

**Examples of models that might go here:**

*   **`user_profile.py`:**  A model representing a user's profile, if your application has user accounts.  This is *not* specific to any single agent.
*   **`data_source.py`:**  A model representing metadata about a data source (e.g., name, URL, API key – though API keys should *not* be stored directly in the model, but rather accessed via dependencies).
* **`alert.py`:** A model to represent any sort of user data for alerts, triggers, or notifications.

**`miscellaneous_models/`  vs.  `src/Core/Models/`:**

The distinction is subtle but important:

*   **`agent_models/`:**  Models *directly* used by PydanticAI agents (input, output, dependencies).  One file per agent.
*   **`miscellaneous_models/`:**  General data structures used across the application, *not* directly tied to a specific agent.

**Why NOT `prompts.py`?**

You are absolutely correct. The `prompts.py` file in `src/Core/Templates/Prompts/` should *only* contain:

1.  **Jinja2 Environment Setup:**  The code to create the Jinja2 `Environment` object.
2.  **Rendering Functions:** Functions that take a Pydantic model (or dictionary) as input, load the appropriate `.j2` template, render it with the provided data, and return the resulting string.  *These functions do not define the data models themselves.*

The Pydantic model used for rendering the prompt (e.g., `CryptoStrategistPromptData` in the previous examples) belongs in the *agent's* model file (e.g., `src/Core/Models/agent_models/crypto_strategist_agent_models.py`).  This keeps all data structures related to an agent together.  It's perfectly fine to define this model *within* the agent's model file, *next to* the `Input`, `Output`, and `Deps` models.

> Engineer's notes: This subdirectory is designated for the storage of various Pydantic data models employed across our system. Though some data models are integrated within other locations, this subdirectory serves as a centralized repository for easy access and management of standalone Pydantic models. By organizing our data models here, we benefit from a clear separation of concerns, allowing each model to be defined according to its specific purpose. To facilitate this, it is advisable to create individual files within this subdirectory, each dedicated to a particular category or functionality of data models. This modular approach ensures that Pydantic models can be seamlessly imported into any required file, promoting reusability and maintainability. From an operational perspective, having a dedicated space for these models simplifies the review process, allowing us to efficiently manage descriptions, validation logic, and annotations. This organizational strategy maximizes our ability to optimize Pydantic data models, ensuring they are both robust and flexible. By maintaining our models in a separate, well-structured subdirectory, we enhance our system's scalability and make future updates and enhancements more straightforward.
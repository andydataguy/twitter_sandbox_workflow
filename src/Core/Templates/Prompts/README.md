
# src/Core/Templates/Prompts: The Dynamic Prompt Engineering Hub

**Purpose: Centralized Management of Jinja2 Prompt Templates**

The `prompts` subdirectory, located within `src/Core/Templates`, is specifically dedicated to managing all Jinja2 (`.j2`) template files designed for generating dynamic prompts within the Twitter Sandbox Workflow application. This centralized organization ensures that all prompt-related templates are readily accessible, easily maintainable, and consistently applied across the system.

**Jinja2 Templates:  Powering Dynamic and Configurable Prompts**

We utilize Jinja2 templating to create dynamic prompts that adapt to varying data inputs and analytical contexts. Jinja2's flexibility and expressiveness enable us to:

*   **Generate Dynamic Content:**  Create prompts that dynamically incorporate relevant data, such as extracted tokens, market data, and user inputs, ensuring context-aware and personalized agent interactions.
*   **Enhance Prompt Configurability:**  Make our prompts highly configurable, allowing us to adjust prompt parameters, instructions, and examples without modifying core code, promoting experimentation and optimization.
*   **Simplify Prompt Maintenance:** Centralize all prompt templates in this directory, making it easier to manage, update, and version control our prompts as the application evolves.

**Directory Structure:  Templates and Rendering Logic**

The `prompts` subdirectory contains:

*   **`.j2` Template Files:**  Each `.j2` file encapsulates the logic and structure for a specific dynamic prompt.  File names should be descriptive and clearly indicate the prompt's purpose (e.g., `web_search_report_prompt.j2`, `content_creation_post_1_prompt.j2`).
*   **`prompts.py` (Python Rendering Script):**  This Python script within the `prompts` directory plays a crucial role by rendering these templates. It acts as a modular interface, seamlessly integrating the templates with the application's data and logic.  This script abstracts away the complexities of Jinja2 configuration from other parts of the application.

**`prompts.py`:  The Rendering Engine**

The `prompts.py` script is essential for bridging the gap between our Jinja2 templates and our Python application logic.  It provides:

*   **Template Loading:**  Logic for loading `.j2` template files from the `prompts` subdirectory.
*   **Data Integration:**  Functions or classes to pass dynamic data to the templates during rendering. This data might include Pydantic models, dictionaries, or other Python objects containing relevant information for prompt generation.
*   **Template Rendering Functions:**  Functions that take a template name and data as input, render the Jinja2 template with the provided data, and return the generated prompt string.
*   **Modular Interface:**  A clean and modular interface for other parts of the application to access and utilize the dynamic prompts without directly interacting with Jinja2 template logic.

**Example Usage (Illustrative - within `prompts.py`):**

```python
# src/Core/Templates/Prompts/prompts.py

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field
from src.Core.Models.web_search_agent_models import WebSearchInput

# --- Jinja2 Environment Setup ---
environment = Environment(loader=FileSystemLoader("src/Core/Templates/Prompts"))

# --- Prompt Rendering Function ---
def render_web_search_report_prompt(data: WebSearchInput) -> str:
    """Renders the web search report prompt using Jinja2."""
    template = environment.get_template("web_search_report_prompt.j2")
    return template.render(data=data.model_dump()) # Pass data as dictionary

# --- Example Usage (within prompts.py for testing) ---
if __name__ == "__main__":
    prompt_data = WebSearchInput(token_symbol="SOL")
    prompt = render_web_search_report_prompt(prompt_data)
    print(prompt)
```

**Benefits of Centralized Prompt Management:**

*   **Simplified Maintenance and Updates:**  All prompt-related templates are located in one place, making it easy to find, update, and maintain prompts as the application evolves.
*   **Improved Prompt Reusability:**  Templates can be easily reused across different parts of the application, promoting consistency and reducing redundancy in prompt definitions.
*   **Clear Separation of Prompt Logic:**  Separating prompt templates from Python code enhances code clarity and allows for specialized prompt engineers or non-technical team members to contribute to prompt design.
*   **Scalability and Flexibility:**  This modular structure supports easy addition of new templates and functionalities as the application grows, ensuring the prompt generation system remains robust and efficient.

By centralizing and carefully managing our Jinja2 prompt templates within this `prompts` subdirectory, we create a robust and adaptable prompt engineering system, essential for building intelligent and context-aware AI agents within the Twitter Sandbox Workflow.

> Engineer’s notes: The `prompts` subdirectory is dedicated to managing all Jinja2 (`.j2`) template files specifically designed for generating dynamic prompts within the application. This organizational structure ensures that all prompt-related templates are centralized for easier maintenance and updates. Each `.j2` file encapsulates the logic and structure for specific prompts, facilitating the generation of dynamic content as needed by various application components. The associated Python script within this directory plays a critical role by rendering these templates. It acts as a modular interface, seamlessly integrating the templates with the application’s data and logic. This setup abstracts the complexity of Jinja2 configurations from other parts of the application, allowing developers to access and utilize the prompts without directly interacting with the underlying template logic. The modular design promotes scalability and flexibility, enabling the application to adapt to evolving requirements while maintaining a clear separation of concerns. As the application grows, this structure supports the easy addition of new templates and functionalities, ensuring the prompt generation system remains robust and efficient.
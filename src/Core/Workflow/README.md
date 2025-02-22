# src/Core/Workflow: Orchestrating the Agent Symphony with LangGraph

**Purpose: Managing the Structure, Flow, and State of the Multi-Agent System**

The `src/Core/Workflow` subdirectory is the control center for our LangGraph-based multi-agent system.  It houses the components that define *how* the different parts of our application (agents, tools, data) interact and collaborate to achieve the overall goals of the Twitter Sandbox Workflow. While the core orchestration logic resides in `src/Core/graph.py`, this directory provides the essential building blocks and supporting structures that make that orchestration possible.

**LangGraph:  More Than Just Connecting LLMs**

LangGraph is not simply about connecting LLMs in a linear sequence.  It's a powerful framework for building *stateful*, *cyclic*, and *multi-actor* applications. This means:

*   **Stateful:**  The workflow maintains a *state* that persists across multiple steps (node executions).  This state can be used to store intermediate results, track progress, and make decisions based on past interactions.  It's like the memory of the entire workflow.
*   **Cyclic:**  Unlike a simple pipeline, a LangGraph workflow can have *cycles*.  This allows for loops, retries, and more complex control flow patterns, essential for agentic behavior (e.g., an agent can repeatedly call a tool until a condition is met).
*   **Multi-Actor:**  LangGraph is designed to support workflows involving multiple interacting agents, each with its own capabilities and responsibilities.  This enables the creation of sophisticated collaborative systems.

**Key Subdirectories and Their Roles:**

The `src/Core/Workflow` directory contains three critical subdirectories:

1.  **`Edges/`:** (See `src/Core/Workflow/Edges/README.md`)
    *   *Purpose:* Defines the *conditional logic* that governs transitions between nodes in the graph.  These are *not* simple "next step" connections; they are *decision points*.
    *   *Contents:* Python functions that take the current state as input and return the name of the *next* node to execute (or `END` to terminate the workflow). These functions can:
        *   Inspect the state to make decisions (e.g., "if the report is complete, go to the 'publish' node").
        *   Call helper functions to perform calculations or checks.
        *   Even call LLMs to make decisions (though this should be done judiciously).
    *   *Example:*  An edge function might check if a "sentiment_score" in the state is above a threshold to decide whether to generate a positive or negative tweet.

2.  **`Nodes/`:** (See `src/Core/Workflow/Nodes/README.md`)
    *   *Purpose:*  Defines the *individual tasks* (nodes) that make up the workflow. Each node is a self-contained unit of work.
    *   *Contents:* Python functions, *one per file*, that take the current state as input, perform some action, and return a dictionary of *updates* to the state. These actions might include:
        *   Calling a PydanticAI agent.
        *   Invoking a tool (from `src/Core/Tools`).
        *   Performing data transformations.
        *   Making API calls.
        *   Updating the state with results.
    *   *Key Point:*  Nodes *do not* directly call other nodes.  They *only* modify the state. The *edges* determine the flow of control. This is crucial for modularity and testability.

3.  **`State/`:** (See `src/Core/Workflow/State/README.md`)
    *   *Purpose:* Defines the *structure* of the shared state that is passed between nodes.  This is the "memory" of the workflow.
    *   *Contents:*  A Python file (typically `state.py`) containing a Pydantic `BaseModel` that defines the state.  This model specifies the *keys* and *data types* of all the information that needs to be shared across the workflow.
    *   *Example:*  A state model might include fields for the initial user input, intermediate reports generated by agents, extracted data, and any other relevant information.
    *   *Multi-Level State (Advanced):*  LangGraph supports state at different levels:
        *   **Global State:**  The state defined in `state.py` is the *global* state, accessible to all nodes.
        *   **Node-Specific State:**  Individual nodes can *also* have their own internal state (if needed).
        *   **Subgraph State:**  If you create reusable sub-workflows (subgraphs), they can have their own isolated state.  This is useful for encapsulation and modularity.  *We primarily focus on the global state in this project.*

**The Role of `graph.py` (in `src/Core/`)**

While the `Workflow` subdirectory contains the building blocks, `src/Core/graph.py` is where the LangGraph is *assembled*.  It:

1.  **Imports:**  Imports the node functions (from `Nodes/`), edge functions (from `Edges/`), and the state model (from `State/`).
2.  **Creates a `StateGraph`:**  Instantiates a `StateGraph` object, using the state model to define the structure of the shared state.
3.  **Adds Nodes:**  Uses `workflow.add_node()` to add each node to the graph, giving each node a unique name (e.g., "web_search", "twitter_search", "summarize").
4.  **Defines Edges:**  Uses `workflow.add_edge()` and `workflow.add_conditional_edges()` to connect the nodes, using the edge functions to define the transition logic.
5.  **Sets the Entry Point:**  Uses `workflow.set_entry_point()` to specify the starting node of the workflow.
6.  **Compiles the Graph:**  Calls `workflow.compile()` to create a runnable graph object.

**Key Principles:**

*   **Separation of Concerns:**  Nodes define *what* to do, edges define *when* to do it, and the state defines *what data* is shared. `graph.py` orchestrates these elements.
*   **Modularity:** Each node and edge is a self-contained unit, making the workflow easy to understand, modify, and extend.
*   **Statefulness:** The shared state allows for complex, multi-step interactions and memory within the workflow.
*   **Flexibility:**  LangGraph supports a wide range of workflow patterns, from simple linear sequences to complex branching and looping structures.

By understanding the roles of `Nodes`, `Edges`, and `State`, and how they are orchestrated by `graph.py`, you can build sophisticated, agent-driven workflows that leverage the full power of LangGraph. This `src/Core/Workflow` directory is the foundation for that orchestration.

> Engineer's notes: The `workflow` subdirectory is integral to managing the orchestration of the LangGraph system's components. While the pivotal `graph.py` file resides in the Core directory and not directly within this subdirectory, it serves as the cornerstone of the LangGraph system. This file is responsible for coordinating and orchestrating the entire system, acting as the primary interface for the `main.py` file to initiate operations. We prioritize keeping `graph.py` clean and focused, as it defines subgraphs and advanced coordination patterns essential for system functionality. Within the `workflow` directory, we have several key subdirectories: `edges`, `nodes`, and `state`. The `edges` subdirectory is dedicated to maintaining various conditional statements that function as edges connecting different nodes. These conditionals are critical for defining the logic flow between tasks. The `nodes` subdirectory is where we define individual tasks, integrating agents, models, and other functionalities necessary for task execution. Of particular importance is the `state` subdirectory, which is a significant differentiator of the LangGraph system. It allows for the definition of state at multiple levels—node, subgraph, or global—within the graph. This abstraction ensures that `graph.py` remains focused solely on coordination, while the `state` subdirectory manages the stateful aspects, enhancing the power and flexibility of the LangGraph system.


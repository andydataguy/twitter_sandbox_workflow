
# Enhanced Crypto Whale Alert System - Project "Agent Data Platform"

**Version:** 1.0 (Initial Scaffold)
**Status:** Work in Progress - Initial Development Phase

## 1. Introduction and Project Goals

This document outlines the development of an enhanced crypto whale movement alert system, codenamed "Agent Data Platform." The current system provides basic, single-line alerts on Twitter, lacking context, sentiment analysis, and detailed market information.  This project aims to transform these basic alerts into insightful, context-rich reports that can be used for generating engaging Twitter posts.  The system will leverage multiple APIs, a multi-agent workflow, and structured data output to provide a significant upgrade in the quality and usefulness of the information provided.

**Key Goals:**

*   **Enriched Alerts:**  Move beyond simple alerts to include:
    *   Social sentiment analysis from Twitter.
    *   General token information and context (via web search).
    *   Real-time market data (price, volume, etc.).
*   **AI-Driven Content Generation:** Generate multiple tweet options based on the enriched data, adopting a crypto-influencer persona.
*   **Modular Architecture:** Design a system that is easy to maintain, extend, and adapt to changing requirements.
*   **Structured Output:** Produce structured data (Pydantic models) suitable for database persistence and downstream analysis.
*   **Observability:** Integrate comprehensive logging and tracing for debugging and monitoring.

## 2. Business Context and Value Proposition

The cryptocurrency market is highly volatile and driven by real-time information.  Large transactions ("whale movements") are often leading indicators of market shifts.  Providing timely, insightful, and *contextualized* information about these movements gives traders, investors, and analysts a significant advantage.

**Current Limitations:**

*   **Basic Alerts:** Existing alerts are one-line notifications with minimal information.
*   **Lack of Context:**  No social sentiment, token background, or market data is included.
*   **Low Engagement:** Basic alerts are unlikely to generate significant engagement on Twitter.

**Value Proposition of "Agent Data Platform":**

*   **Actionable Intelligence:** Provides users with *actionable insights*, not just raw data.
*   **Competitive Edge:**  Gives users a significant advantage in the fast-paced crypto market.
*   **Enhanced Engagement:** Creates compelling, shareable content, increasing platform visibility.
*   **Data-Driven Decisions:** Empowers users to make more informed trading and investment decisions.
*   **Foundation for Premium Services:**  Creates a foundation for future monetization through premium data feeds or subscription services.

## 3. Target Audience

The primary target audience for this enhanced system includes:

*   **Active Crypto Traders:**  Individuals who actively trade cryptocurrencies and require real-time information to make informed decisions.
*   **Crypto Investors:**  Individuals and firms investing in cryptocurrencies who need to monitor market trends and whale activity.
*   **Market Analysts:**  Analysts and researchers who need comprehensive data to understand market dynamics.
*   **Crypto News Outlets:**  Media outlets and content creators focused on cryptocurrency, seeking automated content generation for their platforms.
* **Crypto Community Members**: Individuals looking to be in the know and aware of significant information and market developments.

## 4. Technical Architecture and Stack

**4.1. System Architecture (High-Level Overview):**

The system will employ a multi-agent workflow orchestrated by Langraph.  The core components include:

1.  **Alert Ingestion Node:** Receives the initial whale alert message.
2.  **Parallel Data Retrieval Agents:**
    *   **Twitter Data Agent:** Retrieves relevant tweets using the SocialData API.
    *   **Web Search Agent:** Gathers general token information using the Perplexity Search API.
    *   **Market Data Agent:** Fetches real-time market data (price, volume) from a Crypto Market Data API (TBD).
3.  **Synthesis Agent:**  Combines data from all sources and identifies key insights and discrepancies.
4.  **Tweet Writing Agent:** Generates multiple tweet options based on the synthesized information, adopting a crypto-influencer persona.
5.  **Output Formatting Node:** Structures the final output into Pydantic objects for database persistence.
6.  **Report Generation Agent** Generates detailed reports based on the prompt and information collected from the state.
7. **Report Synthesis Agent** Brings it all together, synthesizing all of the reports into a single comprehensive document.

**Data Flow:**

Whale Alert -> Alert Ingestion Node -> [Parallel Data Retrieval Agents] -> Synthesis Agent -> Tweet Writing Agent -> Output Formatting Node -> Database

**4.2. Technology Stack:**

*   **Programming Language:** Python 3.12
*   **Package Management:** `uv`
*   **Agent Framework:** Pydantic AI
*   **Workflow Orchestration:** Langraph
*   **Prompt Templating:** Jinja2
*   **APIs:**
    *   SocialData API (Twitter data)
    *   Perplexity Search API (Token information)
    *   Crypto Market Data API (TBD)
*   **Database:** SQLite (for initial development and local data persistence)
*   **Observability:** Logfire and LangSmith (for logging, tracing, and monitoring)
*   **Version Control:** Git, GitHub
*   **LLM** Google Gemini

**4.3. Directory Structure:**

```
📁 Twitter_agent_sandbox
  📁 Src
    📁 Core
      📁 Nodes                # Langraph Node Functions
        ├── final_output.py         #Function to take various reports as inputs
        ├── market_data_report.py   #Retrieves real-time market data using a Crypto Market Data API
        ├── synthesis_report.py     #Implement a LangGraph node with a Synthesis Agent to compare the initial whale alert to the data from the structured reports.
        ├── tweet_ingestion.py      #Where the initial tweet is processed.
        ├── tweet_writer.py         #Tweet Writing Agent Node
        ├── twitter_search_report.py#Retrieve Twitter data using SocialData API
        └── web_search_report.py    #Retrieve general token information using Perplexity Search API
      📁 Templates            # NEW: Directory for .j2 template files
        ├── final_output.j2
        ├── market_data_report.j2
        ├── synthesis_report.j2
        ├── tweet_ingestion.j2
        ├── tweet_writer.j2
        ├── twitter_search_report.j2
        └── web_search_report.j2
      📁 Tools            # NEW: Directory for the Tool Definition
        ├── birdeye.py #Get token info such as price etc.
        ├── perplexity.py  #Perplexity API connections.
        └── social_data.py #Social Data API connections.
      ├── agents.py        # Pydantic AI Agent Definitions
      ├── edges.py         # Langraph Workflow Edges (Transitions)
      ├── models.py        # Pydantic Data Models
      ├── prompts.py       # Jinja Prompt Templates
      ├── state.py         # Langraph Workflow State Definition
    📁 Data             # Data Persistence (SQLite will be added later)
    📁 Prototype
      ├── graph.py        #Prototype for the LangGraph workflow.
      └── workflow.py       #Prototype of the workflow.
    ├── graph.py         # Langraph Workflow Orchestration
  📁 Utils
    📁 Logger
      └── logfire.py      # Logfire Configuration
  ├── .python-version   # Specifies Python 3.12
  ├── README.md          # This file - Project Documentation
  ├── main.py            # Application Entry Point
  ├── pyproject.toml     # Project Dependencies and Configuration
  └── uv.lock            # Dependency Lock File (uv managed)
```
**4.4. Key Files and Their Roles (Initial Scaffold):**

*   **`Src/Core/agents.py`:** Defines the `simple_agent` using Pydantic AI and Google Gemini. (Initial version is very basic).
*   **`Src/Core/edges.py`:**  Defines the transitions between nodes. (Initial version is a placeholder).
*   **`Src/Core/models.py`:** Defines the `GraphState` Pydantic model for basic data structuring.
*   **`Src/Core/Nodes/*.py`:**  Defines the `generate_response_node`, which uses `simple_agent` to process user input.
*   **`Src/Core/prompts.py`:** Sets up the Jinja2 environment and defines the `simple_prompt_template` as a string.
*   **`Src/Core/state.py`**: Defines the state of the graph.
* **`Src/Core/Templates`**: Contains the j2 files where we define the prompts.
*   **`Src/Utils/Logger/logfire.py`:** Configures Logfire for logging and tracing.
*   **`Src/graph.py`:** Orchestrates the Langraph workflow (initially a simple one-node flow).
*   **`main.py`:** Application entry point, handles user input, and invokes the Langraph workflow.
*   **`pyproject.toml`:**  Defines project dependencies (see below).

**4.5. Dependencies (`pyproject.toml`):**

```toml
[project]
name = "twitter_agent_sandbox"
version = "0.1.0"
description = "LangGraph sandbox for building a crypto twitter agent"
authors = [
    { name = "Your Name", email = "your.email@example.com" }  # Replace with actual info
]
dependencies = [
    "langchain-anthropic", #For accessing ChatAnthropic
    "langgraph",          # Core Langgraph library
    "pydantic-ai",        # Pydantic AI framework
    "uv",                # Package manager
    "Jinja2",             # Templating engine
    "logfire",          # Observability platform
    "python-dotenv",     # For loading environment variables from .env
    "langchain-community", #For Tavily Search
    "tavily-python",        #Tavily Search
    "requests",           # For making general HTTP requests, including Perplexity
    "asyncio",      #Making things async
    "pytest",       #Testing
    "pytest-asyncio" #Async Testing

]

[build-system]
requires = ["uv"]
build-backend = "setuptools.build_meta"
```

**Explanation of Dependencies:**

*   **`langchain-anthropic`**:  Provides the `ChatAnthropic` class for interacting with Anthropic's Claude models (including Gemini).
*   **`langgraph`**: The core Langraph library for building stateful, multi-agent workflows.
*   **`pydantic-ai`**: The Pydantic AI framework, simplifying agent and tool definition with type safety.
*   **`uv`**:  A fast and modern Python package installer and resolver (used for managing project dependencies).
*   **`Jinja2`**:  The templating engine used for dynamic prompt generation.
*   **`logfire`**:  The observability platform for logging, tracing, and monitoring the application.
*   **`python-dotenv`**:  A library for loading environment variables from a `.env` file (for API keys, etc.).
*   **`langchain-community`**: Provides community integrations for various tools and services, including the `TavilySearchResults` tool.
*   **`tavily-python`**: The Tavily Search API client library, used by the `TavilySearchResults` tool.
*   **`requests`**: A popular library for making HTTP requests, used for interacting with APIs (like Perplexity).
*   **`asyncio`**: Provides support for asynchronous programming, allowing for concurrent API calls and improved performance.
*  **`pytest`**: A testing framework for Python.
* **`pytest-asyncio`**: An extension to pytest which provides support for testing async code.
## 5. Initial Development Steps (Phase 1 - "Hello World")

The initial development phase focuses on creating a minimal, working system with a single node:

1.  **Project Setup:** Create the directory structure and files as outlined above.
2.  **Environment Configuration:**
    *   Create a `.env` file in the project root and add your API keys for Anthropic and Tavily.
    *   Install dependencies using `uv pip sync`.
    *   Configure Logfire by creating a project in the Logfire UI and updating `logfire.py` with your project name.
3.  **Code Implementation:**  Implement the initial code in `agents.py`, `models.py`, `nodes.py`, `prompts.py`, and `graph.py` as described in the previous section.
4.  **Testing:** Run `main.py` and verify that the system can receive user input, generate a basic response using the Gemini model, and log output to Logfire.

## 6. Future Development (Beyond Phase 1)

Subsequent development phases will involve:

*   **Implementing Parallel Data Retrieval:** Integrate the SocialData API, Perplexity Search API, and Crypto Market Data API (once selected) as tools and create corresponding agent nodes for parallel data retrieval.
*   **Developing the Synthesis Agent:** Implement the logic for the Synthesis Agent to combine data from multiple sources and generate insightful summaries.
*   **Building the Tweet Writing Agent:**  Create the Tweet Writing Agent, including defining the crypto-influencer persona and generating multiple tweet options.
*   **Refining the Langraph Workflow:** Define the complete multi-agent workflow, including conditional edges and error handling.
*   **Implementing Output Formatting:**  Create Pydantic models for the final structured output and implement the logic for database persistence.
*   **Adding Human-in-the-Loop (Optional):** Explore implementing human-in-the-loop features for reviewing and approving agent actions.
*   **Adding Reporting Features** Create a node that is able to generate dynamic reports using the graph state.
*   **Database Integration:** Implement the database persistence layer using SQLite.
*   **Testing and Refinement:**  Conduct thorough testing, prompt engineering, and code refactoring to optimize performance and reliability.

## 7.  Development Workflow

*   **Version Control:** Use Git and GitHub for collaborative development, branching, and pull requests.
*   **Development Environment:**  Each team member should set up their development environment with Python 3.12, `uv`, and the required API keys.
*   **Testing:**  Implement unit tests and integration tests to ensure code quality and prevent regressions.
*   **Documentation:**  Maintain comprehensive documentation for all code components, APIs, workflows, and Pydantic models.
*   **Agile Approach:**  Adopt an iterative and agile development approach, focusing on building and testing incrementally.

## 8.  Open Issues and To-Dos

*   **Crypto Market Data API Selection:**  Research and select a suitable Crypto Market Data API.
*   **Refine Jinja Prompts:** Iteratively refine the Jinja templates for prompts to optimize output quality and agent behavior.
*   **Define Crypto Twitter Persona:** Develop detailed characteristics and style guidelines for the Tweet Writing Agent's persona.

This README provides a comprehensive overview of the project.  It should be treated as a living document and updated regularly as the project progresses.

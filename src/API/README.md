# src/API: Exposing the Workflow via FastAPI - The Application's Public Interface

**Purpose:  Defining and Implementing FastAPI Endpoints for External Access**

The `api` subdirectory within `src` is dedicated to defining and implementing the FastAPI endpoints that serve as the public interface for the Twitter Sandbox Workflow application. FastAPI provides us with a robust, high-performance, and developer-friendly framework for building RESTful APIs, allowing external systems and applications to interact with our workflow and consume its generated insights.

**FastAPI:  Our Gateway to the Outside World**

FastAPI is the chosen framework for exposing our LangGraph workflow as an API for several key reasons:

*   **High Performance:** FastAPI is renowned for its exceptional performance, crucial for handling potentially high volumes of requests from external systems and ensuring low-latency responses.
*   **Automatic Data Validation (Pydantic Integration):**  FastAPI seamlessly integrates with Pydantic, allowing us to leverage our existing Pydantic data models for automatic request and response validation, ensuring data integrity at the API boundary.
*   **Automatic API Documentation (Swagger/OpenAPI):**  FastAPI automatically generates interactive API documentation (using Swagger UI and ReDoc), making it easy for developers to understand and integrate with our API endpoints.
*   **Developer Friendliness:** FastAPI's intuitive API design and extensive documentation significantly streamline API development, allowing our team to quickly build, test, and deploy robust and well-documented endpoints.

**Suggested Subdirectory Structure for `src/api`:**

To maintain a well-organized and scalable API layer, we recommend the following subdirectory structure within `src/api`:

*   **`main.py`:**  The main FastAPI application file.  This file will contain:
    *   FastAPI application instantiation (`app = FastAPI(...)`).
    *   Global API configurations and middleware.
    *   Import statements for API endpoints defined in subdirectories.
    *   The main entry point for running the FastAPI application (`if __name__ == "__main__": ...`).

*   **`endpoints/`:**  This subdirectory will house individual Python files, each defining a set of related API endpoints.  For example:
    *   `endpoints/workflow_endpoints.py`:  For endpoints related to triggering and managing the LangGraph workflow (e.g., an endpoint to initiate the workflow, an endpoint to check workflow status).
    *   `endpoints/report_endpoints.py`:  For endpoints dedicated to retrieving and accessing generated reports (e.g., an endpoint to fetch a specific report, an endpoint to list available reports).
    *   `endpoints/health_endpoints.py`:  For health check endpoints to monitor the API's availability and status.

*   **`models/`:**  This subdirectory will contain Pydantic models specifically designed for API requests and responses. These models define the data contracts for our API endpoints, ensuring type safety and automatic validation:
    *   `models/request_models.py`:  Pydantic models defining the structure of request bodies for different API endpoints.
    *   `models/response_models.py`:  Pydantic models defining the structure of response bodies for different API endpoints.

*   **`utils/`:**  This subdirectory will house utility functions and helper classes specific to the API layer, such as:
    *   API authentication and authorization logic.
    *   Data transformation functions for API request/response handling.
    *   Error handling and response formatting utilities.

*   **`middleware/`:**  This subdirectory will contain middleware functions that handle cross-cutting concerns such as authentication, logging, and rate limiting:
    *   `middleware/auth.py`:  Authentication middleware for validating API keys or JWT tokens.
    *   `middleware/logging.py`:  Logging middleware for tracking API requests and responses.
    *   `middleware/rate_limiting.py`:  Rate limiting middleware to prevent abuse and ensure fair usage.

*   **`services/`:**  This subdirectory will house business logic and service integration code, such as:
    *   `services/workflow.py`:  Workflow orchestration logic for triggering and managing the LangGraph workflow.
    *   `services/reporting.py`:  Reporting logic and alerts/notifications for generating and retrieving reports.

*   **`config/`:**  This subdirectory will contain configuration files for different environments, such as:
    *   `config/dev.py`:  Development environment configuration.
    *   `config/stg.py`:  Staging environment configuration.
    *   `config/prod.py`:  Production environment configuration.

**Example FastAPI Endpoint (Illustrative - within `endpoints/workflow_endpoints.py`):**

```python
# src/api/endpoints/workflow_endpoints.py

from fastapi import FastAPI, Depends
from src.Core.graph import graph  # Import your LangGraph graph
from src.Core.Workflow.State.state import GraphState # Import your GraphState model
from src.api.models.request_models import WorkflowInputRequest
from src.api.models.response_models import WorkflowResponse

router = APIRouter() # Or use the main FastAPI app if only a few endpoints

@router.post("/workflow/", response_model=WorkflowResponse, name="Run Workflow")
async def run_workflow_endpoint(
    request: WorkflowInputRequest, # Pydantic model for request body
):
    """
    Endpoint to initiate and run the Twitter Sandbox Workflow.
    """
    initial_state = GraphState(**request.model_dump()) # Create initial state from request
    result = await graph.ainvoke(initial_state) # Invoke LangGraph workflow
    return WorkflowResponse(**result) # Return structured response

# --- Request and Response Models (defined in src/api/models/) ---
# src/api/models/request_models.py
# from pydantic import BaseModel, Field

# class WorkflowInputRequest(BaseModel):
#     user_input: str = Field(..., description="User input to the workflow.")

# src/api/models/response_models.py
# from pydantic import BaseModel, Field

# class WorkflowResponse(BaseModel):
#     report_summary: str = Field(..., description="Summary of the generated report.")
#     # ... other response fields ...
```

**Connecting FastAPI and LangGraph:**

The key to integrating FastAPI with LangGraph is to:

1.  **Import the Compiled Graph:**  Import the compiled LangGraph graph object (e.g., `graph` from `src/Core/graph.py`) into your FastAPI endpoint files.
2.  **Define Request and Response Models:**  Create Pydantic models in `src/api/models/` to define the expected structure of API requests and responses.
3.  **Create FastAPI Endpoints:**  Define FastAPI endpoint functions (e.g., using `@router.post()`) in `src/api/endpoints/`, utilizing the imported LangGraph graph and the defined Pydantic models for request and response handling.
4.  **Invoke the Graph within Endpoints:**  Within the FastAPI endpoint functions, call `graph.ainvoke()` (or `graph.invoke()` for synchronous execution) to run the LangGraph workflow, passing the initial state (often constructed from the API request body).
5.  **Return Structured Responses:**  Return structured responses from your FastAPI endpoints, using Pydantic response models to ensure consistent and validated API outputs.

**Deployment Considerations for FastAPI:**

*   **Uvicorn or Hypercorn:**  Use ASGI servers like Uvicorn or Hypercorn to run your FastAPI application in production, ensuring efficient handling of asynchronous requests.
*   **Reverse Proxy (Nginx, etc.):**  Deploy FastAPI behind a reverse proxy (e.g., Nginx) for load balancing, security, and SSL termination.
*   **Containerization (Docker):**  Containerize your FastAPI application using Docker for consistent and reproducible deployments across different environments.
*   **Cloud Deployment Platforms:**  Deploy your FastAPI application to our AWS microservice infrastructure. 

**Next Steps: Building the API Layer**

Your next step is to build out the `src/api` directory, creating the necessary files and implementing the FastAPI endpoints to expose your Twitter Sandbox Workflow as a RESTful API.  Start by:

1.  **Creating the `src/api` Directory:**  Create the `api` directory within your `src` directory, and within it, create the `endpoints`, `models`, `utils`, `middleware`, `services`, and `config` subdirectories.
2.  **Creating `main.py`:**  Create the `main.py` file within `src/api` and set up the basic FastAPI application instance and any global configurations.
3.  **Defining Request/Response Models:**  Create Pydantic models in `src/api/models/request_models.py` and `src/api/models/response_models.py` to define the data structures for your API endpoints.
4.  **Implementing Workflow Endpoints:**  Create `src/api/endpoints/workflow_endpoints.py` and implement the endpoint function (as illustrated in the example above) to trigger and run your LangGraph workflow.
5.  **Testing Your API:**  Use tools like `curl`, Postman, or Swagger UI (automatically generated by FastAPI) to test your API endpoints and ensure they are functioning correctly.

By building a well-structured and robust API layer using FastAPI, you will create a powerful gateway for external systems to access and leverage the intelligent capabilities of your Twitter Sandbox Workflow, transforming it into a truly accessible and valuable service.
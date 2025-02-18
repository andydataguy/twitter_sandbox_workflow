# main.py

import asyncio
from typing import Annotated, Any, Literal, Union

import logfire
from langgraph.graph import END, START, StateGraph
from langsmith import traceable
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from jinja2 import Environment

# Configure Logfire (if you have a token, it'll send logs)
logfire.configure()

# --- Jinja2 Setup and Prompt Templates ---
jinja_env = Environment()

market_data_prompt = """
Generate a market data report for the token: {{ token }}.
Include details about price, trend, and market context.
"""

twitter_search_prompt = """
Generate a Twitter sentiment report for the token: {{ token }}.
Analyze social media sentiment and identify trending hashtags.
"""

web_search_prompt = """
Generate a web search report for the token: {{ token }}.
Analyze recent news and provide analyst ratings.
"""

final_output_prompt = """
Generate a final comprehensive report that addresses the user's request.
Analyze the following data points:
Market Data: {{ market_data }}
Twitter Sentiment: {{ twitter_data }}
Web Search: {{ web_data }}
Provide a clear recommendation and detailed justification.
"""

# --- Pydantic Models for Agent Output ---

class MarketDataReport(BaseModel):
    token: str = Field(description="The crypto token symbol")
    price: float = Field(description="The current price of the token")
    trend: Literal["up", "down", "stable"] = Field(description="The current price trend")

class TwitterReport(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"] = Field(description="Overall sentiment about the token on Twitter")
    top_hashtags: list[str] = Field(description="List of top trending hashtags")

class WebReport(BaseModel):
    news_summary: str = Field(description="Summary of recent news articles")
    analyst_rating: Literal["buy", "sell", "hold"] = Field(description="Analyst rating")

class FinalReport(BaseModel):
    recommendation: str = Field(description="Final investment recommendation")
    justification: str = Field(description="Justification for the recommendation")


# --- Define the Graph State (using BaseModel) ---

class GraphState(BaseModel):
    request: str = Field(default="", description="The initial user request.")
    market_data: MarketDataReport | None = Field(default=None, description="Output from market data report node")
    twitter_data: TwitterReport | None = Field(default=None, description="Output from Twitter search report node")
    web_data: WebReport | None = Field(default=None, description="Output from web search report node")
    final_report: FinalReport | None = Field(default=None, description="Output from final report node")

# --- Pydantic AI Agent Definitions ---
#We can define model settings inside of the Agent function.
model_settings = {
     'temperature': 0.7, # Setting the temperature for creativity
 }

# --- Market Data Report Agent Node ---
market_data_agent = Agent(
    'google-gla:gemini-2.0-flash',
    system_prompt=market_data_prompt,
    model_settings=model_settings,
    result_type=MarketDataReport,  # Use the Pydantic model!
)

@traceable(run_type="llm", name="market_data_report_node")
async def market_data_report_node(state: GraphState) -> dict:
    with logfire.span("market_data_report") as span:
        span.set_attribute("input", state.model_dump()) # Log the entire input state

        # Simulate market data retrieval.
        if "btc" in state.request.lower():
            report = MarketDataReport(token="BTC", price=68000.0, trend="up")
        elif "eth" in state.request.lower():
            report = MarketDataReport(token="ETH", price=4000.0, trend="stable")
        else:
            report = MarketDataReport(token="UNKNOWN", price=0.0, trend="down")
        output = {"market_data": report}
        span.set_attribute("output", output)  # Log the entire output
        span.set_attribute("model_name", market_data_agent.model)
        return output

# --- Twitter Search Report Agent Node ---
twitter_search_agent = Agent(
   'google-gla:gemini-2.0-flash',
    system_prompt=twitter_search_prompt,
    model_settings=model_settings,
    result_type=TwitterReport,  # Use the Pydantic model!
)

@traceable(run_type="llm", name="twitter_search_report_node")
async def twitter_search_report_node(state: GraphState) -> dict:
   with logfire.span("twitter_search_report") as span:
        span.set_attribute("input", state.model_dump())
        # Simulate Twitter data retrieval.
        if "btc" in state.request.lower():
            report = TwitterReport(sentiment="positive", top_hashtags=["#Bitcoin", "#BTC", "#BullRun"])
        else:
            report = TwitterReport(sentiment="neutral", top_hashtags=["#crypto", "#blockchain"])

        output = {"twitter_data": report}
        span.set_attribute("output", output)
        span.set_attribute("model_name", twitter_search_agent.model)
        return output

# --- Web Search Report Agent Node ---
web_search_agent = Agent(
    'google-gla:gemini-2.0-flash',
    system_prompt=web_search_prompt,
    model_settings=model_settings,
    result_type=WebReport,  # Use the Pydantic model!
)

@traceable(run_type="llm", name="web_search_report_node")
async def web_search_report_node(state: GraphState) -> dict:
    with logfire.span("web_search_report") as span:
        span.set_attribute("input", state.model_dump())
        # Simulate web search data retrieval
        if "btc" in state.request.lower():
            report = WebReport(news_summary="Bitcoin hits all-time high!", analyst_rating="buy")
        else:
            report = WebReport(news_summary="General crypto news...", analyst_rating="hold")

        output = {"web_data": report}
        span.set_attribute("output", output)
        span.set_attribute("model_name", web_search_agent.model)
        return output

# --- Final Output Agent Node ---
final_output_agent = Agent(
    'google-gla:gemini-2.0-flash',
    system_prompt=final_output_prompt,
    model_settings=model_settings,
    result_type=FinalReport,  # Use the Pydantic model!
)

@traceable(run_type="llm", name="final_output_node")
async def final_output_node(state: GraphState) -> dict:
    with logfire.span("final_output") as span:
        span.set_attribute("input", state.model_dump())
        # Render the template with the state data
        report_context = {
            "market_data": state.market_data,
            "twitter_data": state.twitter_data,
            "web_data": state.web_data
        }
        report_str = jinja_env.from_string(final_output_prompt).render(**report_context)
        result = await final_output_agent.run(report_str)
        output = {"final_report": result.data}
        span.set_attribute("output", output)
        span.set_attribute("model_name", final_output_agent.model)
        return output

# --- Create the LangGraph Workflow ---
workflow = StateGraph(GraphState)

# Add the nodes, they MUST have unique names.
workflow.add_node("market_data_report", market_data_report_node)
workflow.add_node("twitter_search_report", twitter_search_report_node)
workflow.add_node("web_search_report", web_search_report_node)
workflow.add_node("final_output", final_output_node)

# Define the edges.  START and END are special node names.
workflow.add_edge(START, "market_data_report")
workflow.add_edge("market_data_report", "twitter_search_report")
workflow.add_edge("twitter_search_report", "web_search_report")
workflow.add_edge("web_search_report", "final_output")
workflow.add_edge("final_output", END)  # END is a special node representing the end

# Compile the graph
graph = workflow.compile()

# --- Main Execution ---

async def main():
    with logfire.span("main_execution") as main_span:
        try:
            user_input = input("Enter a crypto token to analyze (e.g., BTC, ETH): ")
            main_span.set_attribute("user_input", user_input)
            # Run the graph.  Pass a *dictionary* as input, where keys match
            # the names of the state variables.  The initial state is
            # created from this dictionary.
            result = await graph.ainvoke(
                {
                    "request": user_input,
                    "market_data": None,  # Initialize as None
                    "twitter_data": None, # Initialize as None
                    "web_data": None,   # Initialize as None
                    "final_report": None, # Initialize as None
                }
            )
            final_result = result['final_report']
            print(f"Final Report:\n{final_result.model_dump_json(indent=2)}") # Using pydantic built in function for JSON output.
            main_span.set_attribute("final_report", result['final_report'].model_dump_json()) # setting the final result as a main_span attribute
        except Exception as e:
            logfire.exception(f"An error occurred: {e}") #Logfire exception
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
import os
import requests
from langchain_community.agent_toolkits.openapi.toolkit import OpenAPIToolkit
from langchain_openai import ChatOpenAI
from langchain_community.utilities.requests import RequestsWrapper
from langchain_community.tools.json.tool import JsonSpec
from langchain.agents import initialize_agent

# Define API details
API_SPEC_URL = "http://dev1.centralmind.ai/swagger/swagger_spec"  # Replace with your URL
BASE_API_URL = "http://dev1.centralmind.ai"

# Load and parse OpenAPI specification
api_spec = requests.get(API_SPEC_URL).json()
json_spec = JsonSpec(dict_=api_spec)

# Initialize components, you can use X-API-KEY header to set authentication using API keys. 
llm = ChatOpenAI(model_name="gpt-4", temperature=0.0)
toolkit = OpenAPIToolkit.from_llm(llm, json_spec, RequestsWrapper(headers=None), allow_dangerous_requests=True)

# Set up the agent
agent = initialize_agent(toolkit.get_tools(), llm, agent="zero-shot-react-description", verbose=True)

# Make a request
result = agent.run("Give me a few movie examples using a tool, use "+ BASE_API_URL)
print("API response:", result)

# Setup OpenAI Agent
import os
import requests
from llama_index.agent.openai import OpenAIAgent
from llama_index.llms.openai import OpenAI
from llama_index.tools.openapi import OpenAPIToolSpec
from llama_index.tools.requests import RequestsToolSpec

#That class is helping avoid issues with RequestsTool that sometimes did not do correct Get or Post requests due to missing headers
class CustomRequestsToolSpec(RequestsToolSpec):
    def get_request(self, url: str, headers: dict):

        print("request headers", headers)
        response = requests.get(url, headers=headers)
        
        full_response = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text
        }
        return full_response

os.environ["OPENAI_API_KEY"] = "Your OpenAI API KEY"

open_spec = OpenAPIToolSpec(
    url="https://dev1.centralmind.ai/swagger/swagger_spec"
)

domain_headers = {
    "https://dev1.centralmind.ai/": {
        #"Authorization": "Bearer sk-your-key",
        "Content-Type": "application/json"
    }
}
requests_spec = CustomRequestsToolSpec(domain_headers=domain_headers)

llm = OpenAI(model="gpt-4o")
agent = OpenAIAgent.from_tools([*open_spec.to_tool_list(), *requests_spec.to_tool_list()], llm=llm, verbose=True)

response1= agent.chat("what is the base url for the server")
print(response1)

response3 = agent.chat("Show me top 10 from Films table")
print(response3)
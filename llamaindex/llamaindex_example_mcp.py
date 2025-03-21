# Setup OpenAI Agent
import os
from llama_index.agent.openai import OpenAIAgent
from llama_index.llms.openai import OpenAI
from llama_index.tools.mcp import BasicMCPClient,McpToolSpec


os.environ["OPENAI_API_KEY"] = "OpenAI KEY"

mcp_client = BasicMCPClient("http://localhost:9090/sse")
mcp_tool_spec = McpToolSpec(
    client=mcp_client,    
    # allowed_tools=["tool1", "tool2"] # Filter the tools by name
)

# sync
tools = mcp_tool_spec.to_tool_list()

llm = OpenAI(model="gpt-4o")
agent = OpenAIAgent.from_tools(tools, llm=llm, verbose=True)

response1= agent.chat("what is the base url for the server")
print(response1)

response3 = agent.chat("Show me data from Staff table")
print(response3)
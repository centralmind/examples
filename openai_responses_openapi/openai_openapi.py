import json
from typing import Dict, Any, List
from openai import OpenAI
from openapi_processor import OpenAPIProcessorForOpenAI  

def main():

    # Setting endpoints for OpenAPI spec and API
    spec_url = "http://dev1.centralmind.ai/swagger/swagger_spec"
    api_url = "http://dev1.centralmind.ai"
    user_message = "Give me a few customers and show me thier names, emails and when they"
    
    # Initialize OpenAPI processor
    processor = OpenAPIProcessorForOpenAI(spec_url, api_url)
    
    # Process OpenAPI spec and get tools
    functions = processor.process_openapi_spec()      
    
    # Print user request
    print("\nUser request:")
    print(user_message)

    # Initialize conversation    
    client = OpenAI()
    messages = [{"role": "user", "content": user_message}]
    
    # First call to OpenAI   
    response = client.responses.create(
        model="gpt-4",
        input=messages,
        tools=functions
    )
    
    print("\nOpenAI Response:")
    print(response.output)
    
    # Execute function call based on OpenAI's response
    try:
        result = processor.execute_function_call(response.output[0])
        print("\nAPI Response:")
        print(json.dumps(result, indent=2))
        
        # Add function call and result to messages
        messages.append(response.output[0])  # Add function call
        messages.append({  # Add function result
            "type": "function_call_output",
            "call_id": response.output[0].call_id,
            "output": str(result)
        })
        
        # Get final response from OpenAI
        final_response = client.responses.create(model="gpt-4", input=messages, tools=functions)
        
        print("\nFinal OpenAI Response:")
        # Extract and print only the text from the response
        for message in final_response.output:
            for content in message.content:
                if content.type == 'output_text':
                    print(content.text)
        
    except Exception as e:
        print(f"\nError executing function call: {e}")

if __name__ == "__main__":
    main()

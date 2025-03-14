import json
from typing import Dict, Any, List
import requests
from urllib.parse import urljoin

class OpenAPIProcessorForOpenAI:
    """
    Class for processing OpenAPI specifications and converting them to OpenAI tools.
    """
    
    def __init__(self, spec_url_or_json: str | Dict[str, Any] | None = None, api_url: str | None = None):
        """
        Initialize OpenAPIProcessor.
        
        Args:
            spec_url_or_json (str | Dict[str, Any] | None): URL to the OpenAPI specification or OpenAPI spec as a dictionary
            api_url (str | None): Base URL of the API
        """
        self.api_url = api_url
        self.spec_url = None
        self.openapi_spec = None
        self.functions = None
        
        if spec_url_or_json:
            if isinstance(spec_url_or_json, str):
                self.spec_url = spec_url_or_json
            else:
                self.openapi_spec = spec_url_or_json
    
    def convert_openapi_to_functions(self, openapi_spec: Dict[str, Any], strict: bool = False) -> List[Dict[str, Any]]:
        """
        Convert OpenAPI 3.1 spec to OpenAI function calling format.
        
        Args:
            openapi_spec (Dict[str, Any]): OpenAPI 3.1 specification as a dictionary
            strict (bool): If True, all parameters will be required and strict mode will be enabled
            
        Returns:
            List[Dict[str, Any]]: List of OpenAI function definitions
        """
        functions = []
        
        # Extract paths from OpenAPI spec
        paths = openapi_spec.get("paths", {})
        
        # Extract components for reference resolution
        components = openapi_spec.get("components", {})
        schemas = components.get("schemas", {})
        parameters = components.get("parameters", {})
        request_bodies = components.get("requestBodies", {})
        
        for path, path_item in paths.items():
            # Process all HTTP methods
            for method in ["get", "post", "put", "delete", "patch", "head", "options", "trace"]:
                operation = path_item.get(method)
                if not operation:
                    continue
                    
                # Extract operation details
                operation_id = operation.get("operationId", "")
                description = operation.get("description", "")
                parameters_list = operation.get("parameters", [])
                request_body = operation.get("requestBody")
                responses = operation.get("responses", {})
                
                # Create function parameters schema
                properties = {}
                required = []
                
                # Add path parameters
                for param in parameters_list:
                    if param.get("in") == "path":
                        param_name = param.get("name", "")
                        param_schema = param.get("schema", {})
                        
                        # Handle parameter type
                        param_type = param_schema.get("type", "string")
                        
                        # Create property definition with description
                        description = param.get("description", "")
                        if "default" in param_schema:
                            default_value = param_schema["default"]
                            description = f"{description} (default: {default_value})" if description else f"Default value: {default_value}"
                        
                        property_def = {
                            "type": param_type,
                            "description": description
                        }
                        
                        # Add enum if present
                        if "enum" in param_schema:
                            property_def["enum"] = param_schema["enum"]
                        
                        properties[param_name] = property_def
                        required.append(param_name)  # Path parameters are always required
                
                # Add query parameters
                for param in parameters_list:
                    if param.get("in") == "query":
                        param_name = param.get("name", "")
                        param_schema = param.get("schema", {})
                        
                        # Handle parameter type
                        param_type = param_schema.get("type", "string")
                        
                        # Create property definition with description
                        description = param.get("description", "")
                        if "default" in param_schema:
                            default_value = param_schema["default"]
                            description = f"{description} (default: {default_value})" if description else f"Default value: {default_value}"
                        
                        property_def = {
                            "type": param_type,
                            "description": description
                        }
                        
                        # Add enum if present
                        if "enum" in param_schema:
                            property_def["enum"] = param_schema["enum"]
                        
                        # Handle optional parameters in strict mode
                        if not strict and not param.get("required", False):
                            # Make the type a list to include null
                            if isinstance(property_def["type"], str):
                                property_def["type"] = [property_def["type"], "null"]
                            else:
                                property_def["type"].append("null")
                        
                        properties[param_name] = property_def
                        # In strict mode, all parameters are required
                        if strict or param.get("required", False):
                            required.append(param_name)
                
                # Add request body for POST/PUT methods
                if request_body and method in ["post", "put", "patch"]:
                    content = request_body.get("content", {})
                    if "application/json" in content:
                        schema = content["application/json"].get("schema", {})
                        if isinstance(schema, dict):
                            # Handle request body schema
                            body_properties = {}
                            body_required = []
                            
                            # Extract properties from schema
                            for prop_name, prop_schema in schema.get("properties", {}).items():
                                prop_type = prop_schema.get("type", "string")
                                prop_description = prop_schema.get("description", "")
                                
                                property_def = {
                                    "type": prop_type,
                                    "description": prop_description
                                }
                                
                                # Add enum if present
                                if "enum" in prop_schema:
                                    property_def["enum"] = prop_schema["enum"]
                                
                                body_properties[prop_name] = property_def
                                
                                # Add to required if specified
                                if prop_name in schema.get("required", []):
                                    body_required.append(prop_name)
                            
                            # Add request body as a single parameter
                            properties["requestBody"] = {
                                "type": "object",
                                "description": request_body.get("description", "Request body"),
                                "properties": body_properties,
                                "required": body_required if strict else body_required
                            }
                            required.append("requestBody")
                
                # Create function definition
                function_def = {
                    "type": "function",
                    "name": operation_id,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required if strict else required,
                        "additionalProperties": False  # Required for strict mode
                    }
                }
                
                functions.append(function_def)
        
        return functions
    
    def download_openapi_spec(self, spec_url: str | None = None, output_file: str = "openapi-schema-raw.json") -> Dict[str, Any]:
        """
        Download OpenAPI specification from URL and save it to a file.
        
        Args:
            spec_url (str | None): URL to the OpenAPI specification. If provided, overrides the instance value
            output_file (str): Output file path to save the specification
            
        Returns:
            Dict[str, Any]: Downloaded OpenAPI specification
        """
        # Use provided URL or fall back to instance URL
        url_to_use = spec_url or self.spec_url
        if not url_to_use:
            raise ValueError("No spec_url provided and no URL found in instance")
            
        try:
            response = requests.get(url_to_use)
            response.raise_for_status()
            
            spec = response.json()
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(spec, f, indent=2, ensure_ascii=False)
            print(f"OpenAPI specification downloaded and saved to {output_file}")
            
            return spec
        except Exception as e:
            print(f"Error downloading OpenAPI specification: {e}")
            raise
    
    def save_functions_to_file(self, output_file: str = "openai_functions.json") -> None:
        """
        Save OpenAI functions to a JSON file.
        
        Args:
            output_file (str): Output file path
        """
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.functions, f, indent=2, ensure_ascii=False)
    
    def process_openapi_spec(self, spec_url_or_json: str | Dict[str, Any] | None = None, strict: bool = True) -> List[Dict[str, Any]]:
        """
        Process OpenAPI specification and convert it to OpenAI tools.
        
        Args:
            spec_url_or_json (str | Dict[str, Any] | None): URL or JSON object of OpenAPI spec. If provided, overrides the instance value
            strict (bool): Whether to use strict mode for function definitions
            
        Returns:
            List[Dict[str, Any]]: List of OpenAI function definitions
        """
        # Handle specification input
        if spec_url_or_json:
            if isinstance(spec_url_or_json, str):
                self.openapi_spec = self.download_openapi_spec(spec_url=spec_url_or_json)
            else:
                self.openapi_spec = spec_url_or_json
        else:
            # Use instance values
            if self.spec_url:
                self.openapi_spec = self.download_openapi_spec()
            elif not self.openapi_spec:
                raise ValueError("No OpenAPI specification provided")
                
        if not self.openapi_spec:
            raise ValueError("No OpenAPI specification provided")
        
        # Convert to OpenAI functions
        self.functions = self.convert_openapi_to_functions(self.openapi_spec, strict=strict)
        
        # Save to file
        self.save_functions_to_file()
        print(f"Converted {len(self.functions)} functions to OpenAI format")
        
        return self.functions
    
    def execute_function_call(self, function_call: Any, api_url: str | None = None, openapi_spec: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Execute HTTP request based on OpenAI's function call response.
        
        Args:
            function_call: OpenAI's function call response
            api_url (str | None): Base URL of the API. If provided, overrides the instance value
            openapi_spec (Dict[str, Any] | None): OpenAPI specification. If provided, overrides the instance value
            
        Returns:
            Dict[str, Any]: Response from the API
        """
        # Use provided URL or fall back to instance URL
        url_to_use = api_url or self.api_url
        if not url_to_use:
            raise ValueError("No api_url provided and no URL found in instance")
            
        # Use provided spec or fall back to instance spec
        spec_to_use = openapi_spec or self.openapi_spec
        if not spec_to_use:
            raise ValueError("No OpenAPI specification provided")
            
        # Extract function name and arguments
        function_name = function_call.name
        arguments = json.loads(function_call.arguments)
        
        # Find the matching path and operation in OpenAPI spec
        paths = spec_to_use.get("paths", {})
        matching_path = None
        matching_operation = None
        
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() == "get" and operation.get("operationId") == function_name:
                    matching_path = path
                    matching_operation = operation
                    break
            if matching_path:
                break
        
        if not matching_path:
            raise ValueError(f"Unknown function: {function_name}")
        
        # Replace path parameters in the endpoint
        endpoint = matching_path
        query_params = arguments.copy()  # Create a copy for query parameters
        
        # Process path parameters
        for key, value in arguments.items():
            if key in endpoint:
                endpoint = endpoint.replace(f"{{{key}}}", str(value))
                del query_params[key]  # Remove path parameters from query parameters
        
        # Construct the full URL
        url = urljoin(url_to_use, endpoint)
        
        # Make the HTTP request
        print(url)
        response = requests.get(url, params=query_params)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        return response.json() 
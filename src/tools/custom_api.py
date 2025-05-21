# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import json
import re
from typing import Any, Dict, List, Optional

import requests
from langchain.tools import Tool
# from langchain.tools import tool # Alternative way to create tools

from src.tools.decorators import create_logged_tool


def _construct_url(base_url: str, path_params: Optional[Dict[str, Any]] = None) -> str:
    """
    Constructs the full URL by substituting path parameters into the base_url.
    Example: base_url="http://example.com/users/{user_id}", path_params={"user_id": 123}
             -> "http://example.com/users/123"
    """
    if path_params:
        for key, value in path_params.items():
            placeholder = "{" + str(key) + "}"
            if placeholder in base_url:
                base_url = base_url.replace(placeholder, str(value))
            else:
                # This could raise an error or log a warning if a path param is provided but not found
                print(f"Warning: Path parameter '{key}' not found in base_url '{base_url}'.")
    # Check for any remaining unsubstituted path parameters
    if re.search(r"\{.*?\}", base_url):
        raise ValueError(f"Unresolved path parameters in URL: {base_url}. Ensure all path params are provided.")
    return base_url


def _prepare_request_args(api_config: Dict[str, Any], tool_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Prepares the arguments for the requests.request call, including URL, headers, params, and body.
    """
    if tool_input is None:
        tool_input = {}

    # Extract path parameters from tool_input for URL construction
    # Path parameters are defined by placeholders like {param_name} in the URL
    path_params_keys = [match.strip('{}') for match in re.findall(r"\{.*?\}", api_config.get("url", ""))]
    path_params = {key: tool_input.get(key) for key in path_params_keys if tool_input.get(key) is not None}

    final_url = _construct_url(api_config.get("url", ""), path_params)

    headers = api_config.get("headers", {})
    # Potentially merge with runtime headers from tool_input if a convention is established
    # e.g., if tool_input has a special key like '_headers'

    query_params = api_config.get("query_params", {})
    # Potentially merge with runtime query params from tool_input
    # This allows dynamic query params not predefined in conf.yaml
    # For example, if tool_input contains keys that are not path_params or body_template_params
    # they could be considered as query_params.
    # For now, only using predefined query_params from config.

    request_body = None
    method = api_config.get("method", "GET").upper()
    if method in ["POST", "PUT", "PATCH"]:
        body_template_str = api_config.get("body_template")
        if body_template_str:
            # Assume body_template is a JSON string with placeholders
            try:
                # Substitute placeholders in the template string
                # Placeholders are like "{key}"
                formatted_body_str = body_template_str.format(**tool_input)
                request_body = json.loads(formatted_body_str)
            except KeyError as e:
                raise ValueError(f"Missing key {e} in tool_input for body_template formatting.")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in body_template after formatting: {e}. Body: {formatted_body_str}")
        elif tool_input:
            # If no template, but there's input, consider using relevant parts of tool_input as body
            # This part needs careful consideration on how to select relevant keys.
            # For now, we require a body_template for POST/PUT/PATCH if a body is expected.
            pass


    return {
        "method": method,
        "url": final_url,
        "headers": headers,
        "params": query_params,
        "json": request_body, # requests library will handle json.dumps for dicts
    }


def _process_response(response: requests.Response, api_config: Dict[str, Any]) -> Any:
    """
    Processes the HTTP response based on response_mapping in api_config.
    """
    response_mapping = api_config.get("response_mapping")

    try:
        json_response = response.json()
    except json.JSONDecodeError:
        # If response is not JSON, return text content
        if response_mapping:
            # If mapping is defined, but response isn't JSON, it's likely an issue
            # or the mapping should apply to text (which is not supported by simple dot notation)
            print(f"Warning: response_mapping defined for {api_config.get('name')} but response is not JSON. Returning raw text.")
        return response.text

    if not response_mapping:
        return json_response

    if isinstance(response_mapping, str): # Single key extraction
        keys = response_mapping.split('.')
        value = json_response
        try:
            for key in keys:
                if isinstance(value, list) and key.isdigit(): # Handle list indices
                    value = value[int(key)]
                else:
                    value = value[key]
            return value
        except (KeyError, TypeError, IndexError) as e:
            return f"Error processing response_mapping: key '{response_mapping}' not found or invalid path. Error: {e}"

    elif isinstance(response_mapping, dict): # Map new keys to old keys (old keys use dot notation)
        result = {}
        for new_key, old_key_path in response_mapping.items():
            if not isinstance(old_key_path, str):
                result[new_key] = f"Error: Path for '{new_key}' in response_mapping must be a string."
                continue
            
            keys = old_key_path.split('.')
            value = json_response
            try:
                for key_part in keys:
                    if isinstance(value, list) and key_part.isdigit():
                        value = value[int(key_part)]
                    else:
                        value = value[key_part]
                result[new_key] = value
            except (KeyError, TypeError, IndexError):
                result[new_key] = f"Error: Path '{old_key_path}' not found in response."
        return result
    
    else:
        return "Error: Invalid response_mapping format. Must be a string or dictionary."


def create_custom_api_tools_from_config(
    custom_api_configs: List[Dict[str, Any]], 
    logger_instance: Optional[Any] = None
) -> List[Tool]:
    """
    Generates a list of Langchain Tools from a list of custom API configurations.
    """
    created_tools: List[Tool] = []

    if not isinstance(custom_api_configs, list):
        print("Warning: custom_api_configs is not a list. No tools will be created.")
        return created_tools
        
    for api_config in custom_api_configs:
        if not isinstance(api_config, dict):
            print(f"Warning: Skipping invalid api_config item (not a dict): {api_config}")
            continue

        tool_name = api_config.get("name")
        tool_description = api_config.get("description")

        if not tool_name or not tool_description:
            print(f"Warning: Skipping API config due to missing 'name' or 'description': {api_config}")
            continue

        def _execute_custom_api(**kwargs: Any) -> Any:
            """
            Dynamically created function to execute a custom API call.
            It uses the 'api_config' from the outer scope.
            """
            # Need to find the right api_config for this execution.
            # This is tricky because this function is defined once but used for multiple tools
            # if not careful. The solution is to ensure each tool gets its *own* version
            # of _execute_custom_api, or this function needs to identify its config.
            # The common way is to use a factory or functools.partial, or define
            # the function inside the loop correctly.
            # Python's closures will capture the 'api_config' from the loop's scope.
            # However, this means it will likely use the *last* value of api_config
            # from the loop for all tools. This is a common Python closure pitfall.

            # To fix the closure issue, we can use a helper that takes api_config as a default argument:
            # def create_executor(current_api_config):
            #     def _executor(**kwargs_executor):
            #         # current_api_config is fixed here
            #         ...
            #     return _executor
            # _execute_custom_api_func = create_executor(api_config)
            # This is effectively what happens when defining functions in a loop for callbacks.
            # For Tool.from_function, the 'func' is called directly.
            # Let's ensure api_config is correctly captured.
            # The simplest way is to pass api_config to a function that returns the executor.

            # The current approach of defining _execute_custom_api inside the loop *should* work
            # because each iteration creates a new function closure with its own api_config.

            try:
                request_args = _prepare_request_args(api_config, tool_input=kwargs)
            except ValueError as e:
                return f"Error preparing request for {api_config.get('name')}: {e}"

            try:
                response = requests.request(
                    method=request_args["method"],
                    url=request_args["url"],
                    headers=request_args["headers"],
                    params=request_args["params"],
                    json=request_args["json"] 
                )
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                return _process_response(response, api_config)
            except requests.exceptions.HTTPError as e:
                # Include more details from the response if possible
                error_content = e.response.text if e.response else "No response content"
                return f"HTTP error for {api_config.get('name')}: {e}. Response: {error_content}"
            except requests.exceptions.RequestException as e:
                return f"Error during request for {api_config.get('name')}: {e}"
            except Exception as e: # Catch any other unexpected errors
                return f"Unexpected error in {api_config.get('name')} tool: {e}"

        # To ensure the current api_config is correctly captured in the closure
        # for _execute_custom_api, we can define a factory function or use a lambda
        # that passes api_config as a default argument.
        
        def make_executor_func(config_for_tool: Dict[str, Any]):
            def _executor(**kwargs_for_tool: Any) -> Any:
                try:
                    request_args = _prepare_request_args(config_for_tool, tool_input=kwargs_for_tool)
                except ValueError as e:
                    return f"Error preparing request for {config_for_tool.get('name')}: {e}"

                try:
                    response = requests.request(
                        method=request_args["method"],
                        url=request_args["url"],
                        headers=request_args["headers"],
                        params=request_args["params"],
                        json=request_args["json"]
                    )
                    response.raise_for_status()
                    return _process_response(response, config_for_tool)
                except requests.exceptions.HTTPError as e:
                    error_content = e.response.text if e.response else "No response content"
                    return f"HTTP error for {config_for_tool.get('name')}: {e}. Response: {error_content}"
                except requests.exceptions.RequestException as e:
                    return f"Error during request for {config_for_tool.get('name')}: {e}"
                except Exception as e:
                    return f"Unexpected error in {config_for_tool.get('name')} tool: {e}"
            return _executor

        current_executor = make_executor_func(api_config)

        # TODO: Define args_schema based on URL path parameters and body_template placeholders
        # For now, allow any kwargs. Langchain will pass arguments based on tool description.
        # A Pydantic model could be dynamically created here for better type checking.

        try:
            langchain_tool = Tool.from_function(
                func=current_executor,
                name=tool_name,
                description=tool_description,
                # args_schema=MyCustomSchema, # Optional: for typed arguments
            )
        except Exception as e:
            print(f"Error creating Langchain tool for {tool_name}: {e}. Skipping.")
            continue

        if logger_instance:
            logged_tool = create_logged_tool(langchain_tool, logger_instance, tool_name)
            created_tools.append(logged_tool)
        else:
            # If no logger instance, add the tool without logging wrapper
            # Or, alternatively, could use a default logger for this module here
            created_tools.append(langchain_tool)
        
        print(f"Successfully created tool: {tool_name}")

    return created_tools

# Example usage (for testing purposes, normally this would be called from elsewhere)
if __name__ == '__main__':
    print("Running custom_api.py example...")

    # Example configuration
    example_configs = [
        {
            "name": "get_user_data",
            "description": "Fetches user data for a given user ID. Input should be a dict with 'user_id'.",
            "url": "https://jsonplaceholder.typicode.com/users/{user_id}",
            "method": "GET",
            "headers": {"Content-Type": "application/json"},
            "query_params": {},
            # "response_mapping": {"name": "name", "email": "email", "city": "address.city"}
            "response_mapping": "name" # Get only the name
        },
        {
            "name": "create_post",
            "description": "Creates a new post. Input should be a dict with 'title', 'body', and 'userId'.",
            "url": "https://jsonplaceholder.typicode.com/posts",
            "method": "POST",
            "headers": {"Content-Type": "application/json; charset=UTF-8"},
            "body_template": """
            {{
                "title": "{title}",
                "body": "{body}",
                "userId": {userId}
            }}
            """,
            "response_mapping": {"postId": "id", "postTitle": "title"}
        },
        {
            "name": "get_todos",
            "description": "Fetches all todos.",
            "url": "https://jsonplaceholder.typicode.com/todos",
            "method": "GET",
            # No response_mapping, should return full JSON list
        },
        {
            "name": "get_todo_item",
            "description": "Fetches a specific todo item by ID.",
            "url": "https://jsonplaceholder.typicode.com/todos/{id}",
            "method": "GET",
            "response_mapping": { # Example of mapping to new keys
                "todo_id": "id",
                "task_title": "title",
                "is_completed": "completed"
            }
        },
        { # Test invalid URL (unresolved param)
            "name": "invalid_url_tool",
            "description": "Tool with an unresolved URL parameter.",
            "url": "https://api.example.com/items/{item_id}/details/{detail_id}",
            "method": "GET"
        },
        { # Test body template formatting error (missing key)
            "name": "body_template_key_error",
            "description": "Tool with body template expecting 'content' but it might not be provided.",
            "url": "https://jsonplaceholder.typicode.com/posts",
            "method": "POST",
            "body_template": """{"message": "{content}"}"""
        }
    ]

    # Create tools
    custom_tools = create_custom_api_tools_from_config(example_configs)
    print(f"\nCreated {len(custom_tools)} tools.")

    # Test the tools (if they are runnable)
    for tool_instance in custom_tools:
        print(f"\nTesting tool: {tool_instance.name}")
        print(f"Description: {tool_instance.description}")
        
        if tool_instance.name == "get_user_data":
            # Test successful call
            result = tool_instance.run({"user_id": 1})
            print(f"Result for {tool_instance.name} with user_id 1: {result}")
            # Test with path param not found in URL (should be caught by _construct_url if strict, or ignored)
            # _construct_url current implementation will raise ValueError if param in URL not provided
            try:
                result_bad_param_val = tool_instance.run({}) # Missing user_id
                print(f"Result for {tool_instance.name} with missing user_id: {result_bad_param_val}")
            except Exception as e:
                print(f"Error calling {tool_instance.name} with missing user_id: {e}")

        elif tool_instance.name == "create_post":
            post_data = {"title": "My Test Post", "body": "This is a test.", "userId": 5}
            result = tool_instance.run(post_data)
            print(f"Result for {tool_instance.name}: {result}")

        elif tool_instance.name == "get_todos":
            result = tool_instance.run({}) # No args needed
            print(f"Result for {tool_instance.name} (first 2 items): {result[:2] if isinstance(result, list) else result}")

        elif tool_instance.name == "get_todo_item":
            result = tool_instance.run({"id": 3})
            print(f"Result for {tool_instance.name} with id 3: {result}")
        
        elif tool_instance.name == "invalid_url_tool":
            try:
                # This tool expects item_id and detail_id.
                # If we call with only item_id, _construct_url should raise ValueError
                result = tool_instance.run({"item_id": "test"})
                print(f"Result for {tool_instance.name}: {result}")
            except Exception as e:
                print(f"Error calling {tool_instance.name}: {e}")
        
        elif tool_instance.name == "body_template_key_error":
            try:
                # This tool's body_template expects 'content'.
                # Calling without 'content' should cause _prepare_request_args to raise ValueError
                result = tool_instance.run({"some_other_key": "value"})
                print(f"Result for {tool_instance.name}: {result}")
            except Exception as e:
                print(f"Error calling {tool_instance.name}: {e}")


    # Example of how it might be called with a logger
    class DummyLogger:
        def info(self, msg): print(f"LOGGER.INFO: {msg}")
        def error(self, msg): print(f"LOGGER.ERROR: {msg}")

    # print("\n--- Testing with logger ---")
    # logged_tools = create_custom_api_tools_from_config(example_configs, logger_instance=DummyLogger())
    # for tool_instance in logged_tools:
    #     if tool_instance.name == "get_user_data":
    #         result = tool_instance.run({"user_id": 2})
    #         print(f"Result for logged {tool_instance.name} with user_id 2: {result}")
    #         break


    # Test _construct_url
    print("\n--- Testing _construct_url ---")
    url1 = _construct_url("http://example.com/users/{user_id}/posts/{post_id}", {"user_id": 123, "post_id": "abc"})
    print(f"URL1: {url1}") # Expected: http://example.com/users/123/posts/abc
    try:
        _construct_url("http://example.com/users/{user_id}", {})
    except ValueError as e:
        print(f"Error (expected): {e}") # Expected: Unresolved path parameters...
    url3 = _construct_url("http://example.com/search", {"query": "test"}) # query is not a path param here
    print(f"URL3: {url3}") # Expected: http://example.com/search (with warning about 'query')


    # Test _prepare_request_args
    print("\n--- Testing _prepare_request_args ---")
    config_get = {
        "url": "https://jsonplaceholder.typicode.com/users/{user_id}",
        "method": "GET",
        "headers": {"X-Test": "true"},
        "query_params": {"active": "true"}
    }
    args_get = _prepare_request_args(config_get, {"user_id": 1, "unused_param": "test"})
    print(f"Prepared GET args: {args_get}")
    # Expected: {'method': 'GET', 'url': 'https://jsonplaceholder.typicode.com/users/1', 'headers': {'X-Test': 'true'}, 'params': {'active': 'true'}, 'json': None}

    config_post = {
        "url": "https://jsonplaceholder.typicode.com/posts",
        "method": "POST",
        "body_template": """{"title": "{title}", "userId": {userId}, "fixed_val": 123}"""
    }
    args_post = _prepare_request_args(config_post, {"title": "My Title", "userId": 99})
    print(f"Prepared POST args: {args_post}")
    # Expected: {'method': 'POST', 'url': 'https://jsonplaceholder.typicode.com/posts', 'headers': {}, 'params': {}, 'json': {'title': 'My Title', 'userId': 99, 'fixed_val': 123}}

    try:
        _prepare_request_args(config_post, {"title": "My Title"}) # Missing userId for body_template
    except ValueError as e:
        print(f"Error (expected for POST with missing template key): {e}")

    print("\nCustom API module loaded and basic tests run.")

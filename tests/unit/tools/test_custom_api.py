import unittest
import json
from unittest.mock import patch, MagicMock, call

import requests # For requests.exceptions

# Assuming the file is in src/tools/custom_api.py
from src.tools.custom_api import (
    _construct_url,
    _prepare_request_args,
    _process_response,
    create_custom_api_tools_from_config,
    Tool # Langchain Tool
)
# Also import create_logged_tool to patch it where it's called
from src.tools import decorators

class TestCustomApiHelpers(unittest.TestCase):

    def test_construct_url(self):
        self.assertEqual(_construct_url("http://example.com/api"), "http://example.com/api")
        self.assertEqual(
            _construct_url("http://example.com/users/{user_id}", {"user_id": 123}),
            "http://example.com/users/123"
        )
        self.assertEqual(
            _construct_url("http://example.com/users/{user_id}/items/{item_id}", {"user_id": 123, "item_id": "abc"}),
            "http://example.com/users/123/items/abc"
        )
        # Test with extra, unused path params (should be ignored by _construct_url itself)
        self.assertEqual(
            _construct_url("http://example.com/users/{user_id}", {"user_id": 123, "unused": "extra"}),
            "http://example.com/users/123"
        )
        # Test with non-string path param values
        self.assertEqual(
            _construct_url("http://example.com/items/{item_id}", {"item_id": 789}),
            "http://example.com/items/789"
        )
        with self.assertRaisesRegex(ValueError, "Unresolved path parameters in URL"):
            _construct_url("http://example.com/users/{user_id}/items/{item_id}", {"user_id": 123})
        with self.assertRaisesRegex(ValueError, "Unresolved path parameters in URL"):
            _construct_url("http://example.com/users/{user_id}", {})
        
        # Test warning for path param provided but not in URL (current _construct_url prints a warning)
        # We can capture stdout/stderr if we want to assert the warning, but for now, value is the main check.
        self.assertEqual(
            _construct_url("http://example.com/search", {"query_param_for_url": "test_val"}),
            "http://example.com/search"
        )


    def test_prepare_request_args_get(self):
        api_config = {
            "url": "http://example.com/api/items/{item_id}",
            "method": "GET",
            "headers": {"X-Auth": "dummy_token"},
            "query_params": {"static_param": "static_value"}
        }
        tool_input = {"item_id": "123", "dynamic_param": "dynamic_value"} # dynamic_param currently ignored for query

        args = _prepare_request_args(api_config, tool_input)
        self.assertEqual(args["method"], "GET")
        self.assertEqual(args["url"], "http://example.com/api/items/123")
        self.assertEqual(args["headers"], {"X-Auth": "dummy_token"})
        self.assertEqual(args["params"], {"static_param": "static_value"}) # Currently, not merging dynamic tool_input to query_params
        self.assertIsNone(args["json"])

    def test_prepare_request_args_post(self):
        api_config = {
            "url": "http://example.com/api/items",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body_template": """{
                "name": "{item_name}", 
                "value": {item_value},
                "fixed_field": "fixed_val"
            }"""
        }
        tool_input = {"item_name": "Test Item", "item_value": 100}
        args = _prepare_request_args(api_config, tool_input)

        self.assertEqual(args["method"], "POST")
        self.assertEqual(args["url"], "http://example.com/api/items")
        self.assertEqual(args["headers"], {"Content-Type": "application/json"})
        expected_body = {"name": "Test Item", "value": 100, "fixed_field": "fixed_val"}
        self.assertEqual(args["json"], expected_body)

    def test_prepare_request_args_post_missing_key_in_body_template(self):
        api_config = {
            "url": "http://example.com/api/items",
            "method": "POST",
            "body_template": '{"name": "{item_name}", "detail": "{item_detail}"}'
        }
        tool_input = {"item_name": "Test Item"} # item_detail is missing
        with self.assertRaisesRegex(ValueError, "Missing key .* for body_template formatting."):
            _prepare_request_args(api_config, tool_input)

    def test_prepare_request_args_post_invalid_json_body_template(self):
        api_config = {
            "url": "http://example.com/api/items",
            "method": "POST",
            "body_template": '{"name": "{item_name}", "detail": item_detail_unquoted }' # Invalid JSON
        }
        tool_input = {"item_name": "Test Item", "item_detail_unquoted": "some detail"}
        with self.assertRaisesRegex(ValueError, "Invalid JSON in body_template after formatting"):
            _prepare_request_args(api_config, tool_input)

    def test_process_response_no_mapping(self):
        mock_response = MagicMock(spec=requests.Response)
        api_config = {"name": "test_api"}

        # JSON response
        mock_response.json.return_value = {"data": "test_data"}
        self.assertEqual(_process_response(mock_response, api_config), {"data": "test_data"})

        # Text response (if JSON decode fails)
        mock_response.json.side_effect = json.JSONDecodeError("err", "doc", 0)
        mock_response.text = "plain text response"
        self.assertEqual(_process_response(mock_response, api_config), "plain text response")

    def test_process_response_string_mapping(self):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.json.return_value = {
            "user": {"name": "John Doe", "id": "usr123"},
            "items": [{"id": "item1", "value": 10}, {"id": "item2", "value": 20}],
            "status": "active"
        }

        # Valid paths
        self.assertEqual(_process_response(mock_response, {"response_mapping": "user.name"}), "John Doe")
        self.assertEqual(_process_response(mock_response, {"response_mapping": "items.0.value"}), 10)
        self.assertEqual(_process_response(mock_response, {"response_mapping": "status"}), "active")
        
        # Invalid paths
        self.assertIn("Error processing response_mapping", _process_response(mock_response, {"response_mapping": "user.nonexistent"}))
        self.assertIn("Error processing response_mapping", _process_response(mock_response, {"response_mapping": "items.5.value"})) # Index out of bounds
        self.assertIn("Error processing response_mapping", _process_response(mock_response, {"response_mapping": "nonexistent.key"}))

    def test_process_response_dict_mapping(self):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.json.return_value = {
            "data": {"person": {"name": "Jane Doe", "age": 30}, "location": "City X"},
            "meta": {"timestamp": "2023-01-01"}
        }
        api_config = {
            "response_mapping": {
                "userName": "data.person.name",
                "userAge": "data.person.age",
                "reportTime": "meta.timestamp",
                "badPath": "data.nonexistent.field",
                "nonStringPath": ["data", "person"] # Invalid path type
            }
        }
        expected_result = {
            "userName": "Jane Doe",
            "userAge": 30,
            "reportTime": "2023-01-01",
            "badPath": "Error: Path 'data.nonexistent.field' not found in response.",
            "nonStringPath": "Error: Path for 'nonStringPath' in response_mapping must be a string."
        }
        self.assertEqual(_process_response(mock_response, api_config), expected_result)

    def test_process_response_non_json_with_mapping(self):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.json.side_effect = json.JSONDecodeError("err", "doc", 0)
        mock_response.text = "This is plain text."
        api_config = {"name": "test_api_text", "response_mapping": "some.key"} # Mapping expects JSON

        # Should return raw text with a warning (warning is printed, not part of return)
        self.assertEqual(_process_response(mock_response, api_config), "This is plain text.")


class TestCreateCustomApiTools(unittest.TestCase):

    sample_api_configs = [
        {
            "name": "get_user",
            "description": "Fetches user data.",
            "url": "https://api.example.com/users/{user_id}",
            "method": "GET",
            "headers": {"X-API-Version": "1.0"},
            "query_params": {"active": "true"},
            "response_mapping": {"id": "data.id", "name": "data.attributes.name"}
        },
        {
            "name": "create_item",
            "description": "Creates an item.",
            "url": "https://api.example.com/items",
            "method": "POST",
            "body_template": """{"name": "{item_name}", "category": "{category_id}"}""",
            "response_mapping": "message"
        },
        { # Config to test no response mapping
            "name": "get_raw_data",
            "description": "Fetches raw data.",
            "url": "https://api.example.com/raw/{data_id}",
            "method": "GET"
        }
    ]

    @patch('src.tools.custom_api.requests.request')
    def test_tool_creation_and_get_execution(self, mock_requests_request):
        # Configure mock response for GET
        mock_response_get = MagicMock(spec=requests.Response)
        mock_response_get.status_code = 200
        mock_response_get.json.return_value = {
            "data": {"id": "123", "attributes": {"name": "Test User"}}
        }
        mock_requests_request.return_value = mock_response_get

        tools = create_custom_api_tools_from_config(self.sample_api_configs)
        self.assertEqual(len(tools), 3)

        get_user_tool = next(t for t in tools if t.name == "get_user")
        self.assertIsNotNone(get_user_tool)
        self.assertEqual(get_user_tool.description, "Fetches user data.")

        # Execute the GET tool
        tool_result = get_user_tool.run({"user_id": "xyz"})
        
        mock_requests_request.assert_called_once_with(
            method="GET",
            url="https://api.example.com/users/xyz",
            headers={"X-API-Version": "1.0"},
            params={"active": "true"},
            json=None 
        )
        self.assertEqual(tool_result, {"id": "123", "name": "Test User"})
        mock_response_get.raise_for_status.assert_called_once()

    @patch('src.tools.custom_api.requests.request')
    def test_tool_post_execution(self, mock_requests_request):
        # Configure mock response for POST
        mock_response_post = MagicMock(spec=requests.Response)
        mock_response_post.status_code = 201
        mock_response_post.json.return_value = {"message": "Item created successfully", "id": "item001"}
        mock_requests_request.return_value = mock_response_post

        tools = create_custom_api_tools_from_config(self.sample_api_configs)
        create_item_tool = next(t for t in tools if t.name == "create_item")

        tool_input_post = {"item_name": "New Gadget", "category_id": "cat7"}
        tool_result = create_item_tool.run(tool_input_post)

        expected_body = {"name": "New Gadget", "category": "cat7"}
        mock_requests_request.assert_called_once_with(
            method="POST",
            url="https://api.example.com/items",
            headers={}, # As per config
            params={}, # As per config
            json=expected_body
        )
        self.assertEqual(tool_result, "Item created successfully") # Due to "response_mapping": "message"
        mock_response_post.raise_for_status.assert_called_once()

    @patch('src.tools.custom_api.requests.request')
    def test_tool_execution_http_error(self, mock_requests_request):
        # Configure mock to raise HTTPError
        mock_error_response = MagicMock(spec=requests.Response)
        mock_error_response.text = '{"error": "Not Found"}'
        mock_error_response.status_code = 404
        
        # Make raise_for_status itself raise the error, or have requests.request raise it.
        # If requests.request raises it directly:
        http_error_instance = requests.exceptions.HTTPError(response=mock_error_response)
        http_error_instance.response = mock_error_response # Ensure response attribute is set
        mock_requests_request.side_effect = http_error_instance
        
        tools = create_custom_api_tools_from_config(self.sample_api_configs)
        get_user_tool = next(t for t in tools if t.name == "get_user")

        result = get_user_tool.run({"user_id": "unknown"})
        self.assertIn("HTTP error for get_user", result)
        self.assertIn('{"error": "Not Found"}', result)

    @patch('src.tools.custom_api.requests.request')
    def test_tool_execution_request_exception(self, mock_requests_request):
        mock_requests_request.side_effect = requests.exceptions.ConnectionError("Failed to connect")

        tools = create_custom_api_tools_from_config(self.sample_api_configs)
        get_user_tool = next(t for t in tools if t.name == "get_user")

        result = get_user_tool.run({"user_id": "123"})
        self.assertIn("Error during request for get_user: Failed to connect", result)

    @patch('src.tools.custom_api.create_logged_tool') # Patch where it's called
    def test_tool_creation_with_logger(self, mock_create_logged_tool):
        mock_logger = MagicMock()
        # To make create_logged_tool return the tool itself for easier testing of the list
        mock_create_logged_tool.side_effect = lambda tool, logger, name: tool 

        tools = create_custom_api_tools_from_config(self.sample_api_configs, logger_instance=mock_logger)
        self.assertEqual(len(tools), 3) # Ensure tools are still created

        # Assert create_logged_tool was called for each tool config
        self.assertEqual(mock_create_logged_tool.call_count, len(self.sample_api_configs))
        
        # Check if it was called with the logger and correct tool names
        expected_calls = [
            call(unittest.mock.ANY, mock_logger, "get_user"),
            call(unittest.mock.ANY, mock_logger, "create_item"),
            call(unittest.mock.ANY, mock_logger, "get_raw_data"),
        ]
        mock_create_logged_tool.assert_has_calls(expected_calls, any_order=False)

    def test_tool_creation_empty_or_invalid_config(self):
        self.assertEqual(create_custom_api_tools_from_config([]), [])
        self.assertEqual(create_custom_api_tools_from_config(None), []) # type: ignore
        # Config item not a dict
        self.assertEqual(create_custom_api_tools_from_config(["not_a_dict"]), []) # type: ignore
        # Config item missing 'name' or 'description'
        self.assertEqual(create_custom_api_tools_from_config([{"description": "d", "url": "u", "method": "m"}]), [])


if __name__ == "__main__":
    unittest.main()

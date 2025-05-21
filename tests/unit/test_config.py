import unittest
import os
import yaml
import tempfile
from typing import Any, Dict

from src.config.configuration import Configuration
from src.config.loader import load_configuration_from_yaml

class TestConfigLoading(unittest.TestCase):

    def test_load_yaml_with_custom_api_configs(self):
        yaml_content = """
custom_api_configs:
  - name: "get_weather"
    description: "Fetches weather data."
    url: "https://api.weather.com/current"
    method: "GET"
    headers:
      X-API-Key: "static_key"
    query_params:
      city: "london"
  - name: "post_comment"
    description: "Posts a comment."
    url: "https://api.example.com/comments"
    method: "POST"
    body_template: '{{"comment": "{user_comment}"}}'
        """
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as tmp_file:
            tmp_file.write(yaml_content)
            tmp_file_path = tmp_file.name

        try:
            config = load_configuration_from_yaml(tmp_file_path)
            self.assertIsNotNone(config.custom_api_configs)
            self.assertEqual(len(config.custom_api_configs), 2)

            weather_api = config.custom_api_configs[0]
            self.assertEqual(weather_api["name"], "get_weather")
            self.assertEqual(weather_api["url"], "https://api.weather.com/current")
            self.assertEqual(weather_api["headers"]["X-API-Key"], "static_key")

            comment_api = config.custom_api_configs[1]
            self.assertEqual(comment_api["name"], "post_comment")
            self.assertEqual(comment_api["method"], "POST")
            self.assertIn("body_template", comment_api)

        finally:
            os.remove(tmp_file_path)

    def test_env_var_substitution_in_custom_api_configs(self):
        env_var_name = "TEST_CUSTOM_API_KEY"
        env_var_value = "my_secret_key_12345"
        os.environ[env_var_name] = env_var_value

        yaml_content = f"""
custom_api_configs:
  - name: "service_a"
    description: "Service A API."
    url: "https://service.a.com/api"
    method: "GET"
    headers:
      Authorization: "Bearer $ANOTHER_TOKEN" # Test non-existent env var
      X-Custom-Key: "${env_var_name}"
      X-Fixed-Val: "fixed"
    query_params:
      param1: "$YET_ANOTHER_VAR" 
"""
        # Set one more env var for testing within query_params
        os.environ["YET_ANOTHER_VAR"] = "query_value"

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as tmp_file:
            tmp_file.write(yaml_content)
            tmp_file_path = tmp_file.name
        
        config = None
        try:
            config = load_configuration_from_yaml(tmp_file_path)
            self.assertIsNotNone(config.custom_api_configs)
            self.assertEqual(len(config.custom_api_configs), 1)

            service_a_config = config.custom_api_configs[0]
            self.assertEqual(service_a_config["name"], "service_a")
            
            # Check headers
            self.assertEqual(service_a_config["headers"]["Authorization"], "Bearer $ANOTHER_TOKEN", 
                             "Should not replace non-existent env var, keep original string")
            self.assertEqual(service_a_config["headers"]["X-Custom-Key"], env_var_value)
            self.assertEqual(service_a_config["headers"]["X-Fixed-Val"], "fixed")

            # Check query_params
            self.assertEqual(service_a_config["query_params"]["param1"], "query_value")

        finally:
            os.remove(tmp_file_path)
            del os.environ[env_var_name]
            if "YET_ANOTHER_VAR" in os.environ:
                del os.environ["YET_ANOTHER_VAR"]
    
    def test_configuration_from_runnable_config_with_custom_api(self):
        # This test is a bit more indirect for custom_api_configs as from_runnable_config
        # primarily sources from os.environ or a passed 'configurable' dict from RunnableConfig.
        # custom_api_configs are typically loaded via YAML and then part of the Configuration object.
        # Here we simulate that custom_api_configs might be passed via the 'configurable' part.
        
        mock_custom_configs_data = [
            {"name": "api1", "url": "http://test.com/api1", "method": "GET"}
        ]

        # Simulate values that might come from a RunnableConfig's 'configurable' field
        mock_runnable_configurable = {
            "max_plan_iterations": 5,
            "custom_api_configs": mock_custom_configs_data 
        }

        # Create a mock RunnableConfig structure
        mock_run_config: Dict[str, Any] = {"configurable": mock_runnable_configurable}

        # Create Configuration instance using from_runnable_config
        cfg = Configuration.from_runnable_config(mock_run_config)

        self.assertEqual(cfg.max_plan_iterations, 5)
        # Check if custom_api_configs are passed through.
        # The current implementation of Configuration.from_runnable_config iterates through fields(cls)
        # and tries to get values from os.environ or the configurable dict.
        # If custom_api_configs is a field and init=True, it should pick it up.
        self.assertIsNotNone(cfg.custom_api_configs)
        self.assertEqual(len(cfg.custom_api_configs), 1)
        self.assertEqual(cfg.custom_api_configs[0]["name"], "api1")

    def test_configuration_from_runnable_config_env_override_custom_api(self):
        # Test if environment variables can set/override custom_api_configs (if it were simple type)
        # For complex types like list[dict], direct env var override is not typical without JSON string parsing.
        # The current Configuration.from_runnable_config will try os.environ.get("CUSTOM_API_CONFIGS")
        # which would be a string. This test explores that behavior.
        
        # This will be retrieved as a string, and dataclass field is Optional[list[dict]]
        # Without special handling, this won't directly parse into list[dict]
        os.environ["CUSTOM_API_CONFIGS"] = '[{"name": "env_api", "url": "http://env.com"}]'
        
        cfg_env = Configuration.from_runnable_config({}) # Empty runnable config, relying on env

        # The default field type is list[dict]. os.environ.get will return a string.
        # The dataclass won't automatically convert this string to list[dict].
        # So, this assertion depends on how Configuration handles such type mismatches.
        # Based on current Configuration implementation, it will take the string value.
        # This might indicate a limitation or an area for improvement in Configuration if complex types
        # from env vars are desired. For this test, we assert the behavior as is.
        
        # If custom_api_configs were a simple type (int, str, bool), env override would work directly.
        # For list[dict], it will assign the string from env var directly.
        self.assertIsInstance(cfg_env.custom_api_configs, str)
        self.assertEqual(cfg_env.custom_api_configs, '[{"name": "env_api", "url": "http://env.com"}]')
        
        del os.environ["CUSTOM_API_CONFIGS"]


if __name__ == "__main__":
    unittest.main()

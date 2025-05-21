# Configuration Guide

## Quick Settings

Copy the `conf.yaml.example` file to `conf.yaml` and modify the configurations to match your specific settings and requirements.

```bash
cd deer-flow
cp conf.yaml.example conf.yaml
```

## Which models does DeerFlow support?

In DeerFlow, currently we only support non-reasoning models, which means models like OpenAI's o1/o3 or DeepSeek's R1 are not supported yet, but we will add support for them in the future.

### Supported Models

`doubao-1.5-pro-32k-250115`, `gpt-4o`, `qwen-max-latest`, `gemini-2.0-flash`, `deepseek-v3`, and theoretically any other non-reasoning chat models that implement the OpenAI API specification.

> [!NOTE]
> The Deep Research process requires the model to have a **longer context window**, which is not supported by all models.
> A work-around is to set the `Max steps of a research plan` to `2` in the settings dialog located on the top right corner of the web page,
> or set `max_step_num` to `2` when invoking the API.

### How to switch models?
You can switch the model in use by modifying the `conf.yaml` file in the root directory of the project, using the configuration in the [litellm format](https://docs.litellm.ai/docs/providers/openai_compatible).

---

### How to use OpenAI-Compatible models?

DeerFlow supports integration with OpenAI-Compatible models, which are models that implement the OpenAI API specification. This includes various open-source and commercial models that provide API endpoints compatible with the OpenAI format. You can refer to [litellm OpenAI-Compatible](https://docs.litellm.ai/docs/providers/openai_compatible) for detailed documentation.
The following is a configuration example of `conf.yaml` for using OpenAI-Compatible models:

```yaml
# An example of Doubao models served by VolcEngine
BASIC_MODEL:
  base_url: "https://ark.cn-beijing.volces.com/api/v3"
  model: "doubao-1.5-pro-32k-250115"
  api_key: YOUR_API_KEY

# An example of Aliyun models
BASIC_MODEL:
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  model: "qwen-max-latest"
  api_key: YOUR_API_KEY

# An example of deepseek official models
BASIC_MODEL:
  base_url: "https://api.deepseek.com"
  model: "deepseek-chat"
  api_key: YOU_API_KEY

# An example of Google Gemini models using OpenAI-Compatible interface
BASIC_MODEL:
  base_url: "https://generativelanguage.googleapis.com/v1beta/openai/"
  model: "gemini-2.0-flash"
  api_key: YOUR_API_KEY
```

### How to use Ollama models?

DeerFlow supports the integration of Ollama models. You can refer to [litellm Ollama](https://docs.litellm.ai/docs/providers/ollama). <br>
The following is a configuration example of `conf.yaml` for using Ollama models:

```yaml
BASIC_MODEL:
  model: "ollama/ollama-model-name"
  base_url: "http://localhost:11434" # Local service address of Ollama, which can be started/viewed via ollama serve
```

### How to use OpenRouter models?

DeerFlow supports the integration of OpenRouter models. You can refer to [litellm OpenRouter](https://docs.litellm.ai/docs/providers/openrouter). To use OpenRouter models, you need to:
1. Obtain the OPENROUTER_API_KEY from OpenRouter (https://openrouter.ai/) and set it in the environment variable.
2. Add the `openrouter/` prefix before the model name.
3. Configure the correct OpenRouter base URL.

The following is a configuration example for using OpenRouter models:
1. Configure OPENROUTER_API_KEY in the environment variable (such as the `.env` file)
```ini
OPENROUTER_API_KEY=""
```
2. Set the model name in `conf.yaml`
```yaml
BASIC_MODEL:
  model: "openrouter/google/palm-2-chat-bison"
```

Note: The available models and their exact names may change over time. Please verify the currently available models and their correct identifiers in [OpenRouter's official documentation](https://openrouter.ai/docs).

### How to use Azure models?

DeerFlow supports the integration of Azure models. You can refer to [litellm Azure](https://docs.litellm.ai/docs/providers/azure). Configuration example of `conf.yaml`:
```yaml
BASIC_MODEL:
  model: "azure/gpt-4o-2024-08-06"
  api_base: $AZURE_API_BASE
  api_version: $AZURE_API_VERSION
  api_key: $AZURE_API_KEY
```

---

## Custom RESTful API Tools (`custom_api_configs`)

DeerFlow allows you to extend its capabilities by defining custom tools that connect to any RESTful API. This is configured through the `custom_api_configs` section in your `conf.yaml` file. Each item in this list defines a new tool that the LLM agent can learn to use.

### Introduction

The `custom_api_configs` section is a list of individual API configurations. Each configuration object you provide will be transformed into a callable tool available to the agent. The agent decides which tool to use based on its `description` field.

### Configuration Fields

For each custom API tool, you need to define an object with the following fields:

*   **`name` (string):**
    *   A unique name for your custom tool. This name is used internally for logging and identification.
    *   Example: `"get_weather_forecast"`

*   **`description` (string):**
    *   **Crucial for LLM usability.** A detailed description of what the API does, what inputs it expects (and how the LLM should provide them), and what kind of output it returns. The LLM uses this description to determine when and how to use the tool.
    *   Be explicit about expected input arguments. For example, if the API needs a `user_id`, the description should state something like: "Fetches user details for a given user_id. Input should be the user_id." The LLM will then try to supply `user_id` when calling the tool.
    *   Example: `"Fetches the 5-day weather forecast for a specified city. Expects a 'city' name as input."`

*   **`url` (string):**
    *   The full URL for the API endpoint.
    *   You can include placeholders for path parameters by enclosing them in curly braces (e.g., `https://api.example.com/users/{user_id}/orders/{order_id}`). The values for these placeholders will be taken from the arguments the LLM provides when calling the tool, based on your `description`.
    *   Example: `"https://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={api_key}"` (though API key here is better in headers).

*   **`method` (string):**
    *   The HTTP method for the API request.
    *   Common values: `"GET"`, `"POST"`, `"PUT"`, `"DELETE"`, `"PATCH"`.
    *   Example: `"GET"`

*   **`headers` (Optional[dict]):**
    *   A dictionary of HTTP headers to be sent with each request to this API.
    *   Values can be static strings or refer to environment variables (see below).
    *   Example: `{"X-API-Key": "$WEATHER_API_KEY", "Content-Type": "application/json"}`

*   **`query_params` (Optional[dict]):**
    *   A dictionary of static query parameters to append to the URL for every call.
    *   Dynamic parameters that the LLM needs to provide should typically be part of the `url` placeholders (if they are path parameters) or included in the `body_template` for POST/PUT requests. If the LLM is meant to provide query parameters directly, ensure your tool's `description` clearly states these argument names.
    *   Example: `{"units": "metric", "mode": "json"}`

*   **`body_template` (Optional[string]):**
    *   A JSON string that serves as a template for the request body, primarily used for `"POST"`, `"PUT"`, or `"PATCH"` methods.
    *   Use placeholders like `"{input_variable_name}"` within the JSON string. The LLM will fill these placeholders based on the arguments it extracts from the task, guided by the tool's `description`.
    *   The final formatted string must be valid JSON.
    *   Example: `'{ "query": "{search_term}", "filters": {"type": "{filter_type}"}, "page": {page_number} }'`

*   **`response_mapping` (Optional[union[string, dict]]):**
    *   Defines how to extract or transform data from the API's JSON response before returning it to the LLM. This is useful for simplifying complex responses or picking out only the relevant pieces of information.
    *   **If a string:** Uses dot notation to extract a specific value from the JSON response.
        *   Example: `"data.items.0.name"` would extract the `name` of the first item in the `items` array, which is nested under `data`.
    *   **If a dictionary:** Creates a new dictionary where keys are your defined new names, and values are dot-notation paths to the data in the original JSON response.
        *   Example: `{"extracted_title": "result.headline", "main_content": "result.body_text"}`
    *   **If omitted:** The full JSON response body is returned. If the response is not valid JSON, the raw text content is returned.

### Examples

Here are a couple of examples to illustrate how to configure custom API tools:

**Example 1: Simple GET API**

This tool fetches the current stock price for a given ticker symbol.

```yaml
custom_api_configs:
  - name: "get_stock_price"
    description: "Fetches the current stock price for a given stock ticker symbol. Input should be the stock ticker (e.g., 'AAPL'). Returns the price."
    url: "https://api.stockdata.com/v1/price/{ticker}" # LLM will provide 'ticker' based on description
    method: "GET"
    headers:
      X-Auth-Token: "$STOCK_API_TOKEN" # API token from environment variable
    # No query_params or body_template needed for this simple GET.
    # If the API returns {"data": {"current_price": 150.00}}, 
    # you could use the following to directly return the price:
    response_mapping: "data.current_price" 
    # If response_mapping is omitted and API returns {"price": 150.00}, 
    # the full simple JSON is returned, which the LLM can often handle.
```

**Example 2: POST API with Body and Response Mapping**

This tool submits text for translation and extracts a job ID from the response.

```yaml
custom_api_configs:
  - name: "submit_translation_job"
    description: "Submits a piece of text for translation to a specified target language. Requires 'text_to_translate' (the text to be translated) and 'target_language_code' (e.g., 'es' for Spanish, 'fr' for French). Returns a job ID for tracking."
    url: "https://api.translationService.com/v2/jobs"
    method: "POST"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer $TRANSLATION_API_KEY" # API key from environment variable
    body_template: '{ "source_text": "{text_to_translate}", "target_lang": "{target_language_code}", "priority": "high" }'
    # Example API response: {"job_details": {"id": "123xyz", "status": "pending", "timestamp": "..." }, "estimated_time": "10s"}
    response_mapping: "job_details.id" # Extracts only the job ID
```

### Environment Variable Usage

For sensitive information like API keys, tokens, or parts of URLs, it's highly recommended to use environment variables. In your `conf.yaml`, you can reference an environment variable by prefixing its name with a dollar sign `$` (e.g., `"$MY_API_KEY"` or `"${MY_API_KEY_WITH_BRACES}"`). DeerFlow will substitute these placeholders with the corresponding environment variable values at runtime.

```yaml
headers:
  X-API-Key: "$YOUR_SECRET_API_KEY"
  Authorization: "Bearer ${ANOTHER_TOKEN}"
```

If an environment variable is not found, the placeholder string (e.g., `"$UNSET_VARIABLE"`) will be used as is.

### The Importance of a Good `description`

The `description` field is the most critical part of your custom API tool configuration. The LLM agent relies entirely on this description to:

1.  **Understand the tool's capability:** What does this tool do?
2.  **Identify required inputs:** What arguments does this tool need? The LLM will parse the description to find these arguments and attempt to supply them from the current task context. For example, if your description says "needs a `city_name` and a `country_code`", the LLM will try to pass `city_name` and `country_code` to your tool when it calls it.
3.  **Know when to use the tool:** Does this tool help achieve the current objective?
4.  **Interpret the tool's output:** What does the returned data signify?

Provide clear, concise, and accurate descriptions. If the tool expects specific argument names (which will be keys in the `tool_input` dictionary for `body_template` formatting or path parameter substitution in the `url`), ensure these are mentioned in the description.

### Benefits of `response_mapping`

While optional, `response_mapping` can be very beneficial:

*   **Simplicity:** It allows you to simplify complex or verbose API responses, extracting only the data relevant to the LLM. This reduces the amount of text the LLM needs to process.
*   **Focus:** It helps in focusing the LLM's attention on the specific pieces of information it needs for its task.
*   **Consistency:** It can help in transforming varied API responses into a more consistent format if you are integrating multiple tools.

By effectively using `custom_api_configs`, you can significantly enhance DeerFlow's ability to interact with external systems and perform a wider range of tasks.

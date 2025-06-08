from collections import namedtuple
import json
import pytest
from unittest.mock import patch, MagicMock
from src.graph.nodes import planner_node
import pytest
import json
from unittest.mock import patch, MagicMock
from src.graph.nodes import human_feedback_node
from src.graph.nodes import coordinator_node

# 在这里 mock 掉 get_llm_by_type，避免 ValueError
with patch("src.llms.llm.get_llm_by_type", return_value=MagicMock()):
    from langgraph.types import Command
    from src.graph.nodes import background_investigation_node
    from src.config import SearchEngine
    from langchain_core.messages import HumanMessage


# Mock data
MOCK_SEARCH_RESULTS = [
    {"title": "Test Title 1", "content": "Test Content 1"},
    {"title": "Test Title 2", "content": "Test Content 2"},
]


@pytest.fixture
def mock_state():
    return {
        "messages": [HumanMessage(content="test query")],
        "research_topic": "test query",
        "background_investigation_results": None,
    }


@pytest.fixture
def mock_configurable():
    mock = MagicMock()
    mock.max_search_results = 5
    return mock


@pytest.fixture
def mock_config():
    # 你可以根据实际需要返回一个 MagicMock 或 dict
    return MagicMock()


@pytest.fixture
def patch_config_from_runnable_config(mock_configurable):
    with patch(
        "src.graph.nodes.Configuration.from_runnable_config",
        return_value=mock_configurable,
    ):
        yield


@pytest.fixture
def mock_tavily_search():
    with patch("src.graph.nodes.LoggedTavilySearch") as mock:
        instance = mock.return_value
        instance.invoke.return_value = [
            {"title": "Test Title 1", "content": "Test Content 1"},
            {"title": "Test Title 2", "content": "Test Content 2"},
        ]
        yield mock


@pytest.fixture
def mock_web_search_tool():
    with patch("src.graph.nodes.get_web_search_tool") as mock:
        instance = mock.return_value
        instance.invoke.return_value = [
            {"title": "Test Title 1", "content": "Test Content 1"},
            {"title": "Test Title 2", "content": "Test Content 2"},
        ]
        yield mock


@pytest.mark.parametrize("search_engine", [SearchEngine.TAVILY.value, "other"])
def test_background_investigation_node_tavily(
    mock_state,
    mock_tavily_search,
    mock_web_search_tool,
    search_engine,
    patch_config_from_runnable_config,
    mock_config,
):
    """Test background_investigation_node with Tavily search engine"""
    with patch("src.graph.nodes.SELECTED_SEARCH_ENGINE", search_engine):
        result = background_investigation_node(mock_state, mock_config)

        # Verify the result structure
        assert isinstance(result, dict)

        # Verify the update contains background_investigation_results
        assert "background_investigation_results" in result

        # Parse and verify the JSON content
        results = result["background_investigation_results"]

        if search_engine == SearchEngine.TAVILY.value:
            mock_tavily_search.return_value.invoke.assert_called_once_with("test query")
            assert (
                results
                == "## Test Title 1\n\nTest Content 1\n\n## Test Title 2\n\nTest Content 2"
            )
        else:
            mock_web_search_tool.return_value.invoke.assert_called_once_with(
                "test query"
            )
            assert len(json.loads(results)) == 2


def test_background_investigation_node_malformed_response(
    mock_state, mock_tavily_search, patch_config_from_runnable_config, mock_config
):
    """Test background_investigation_node with malformed Tavily response"""
    with patch("src.graph.nodes.SELECTED_SEARCH_ENGINE", SearchEngine.TAVILY.value):
        # Mock a malformed response
        mock_tavily_search.return_value.invoke.return_value = "invalid response"

        result = background_investigation_node(mock_state, mock_config)

        # Verify the result structure
        assert isinstance(result, dict)

        # Verify the update contains background_investigation_results
        assert "background_investigation_results" in result

        # Parse and verify the JSON content
        results = result["background_investigation_results"]
        assert json.loads(results) is None


@pytest.fixture
def mock_plan():
    return {
        "has_enough_context": True,
        "title": "Test Plan",
        "thought": "Test Thought",
        "steps": [],
        "locale": "en-US",
    }


@pytest.fixture
def mock_state_planner():
    return {
        "messages": [HumanMessage(content="plan this")],
        "plan_iterations": 0,
        "enable_background_investigation": True,
        "background_investigation_results": "Background info",
    }


@pytest.fixture
def mock_configurable_planner():
    mock = MagicMock()
    mock.max_plan_iterations = 3
    return mock


@pytest.fixture
def patch_config_from_runnable_config_planner(mock_configurable_planner):
    with patch(
        "src.graph.nodes.Configuration.from_runnable_config",
        return_value=mock_configurable_planner,
    ):
        yield


@pytest.fixture
def patch_apply_prompt_template():
    with patch(
        "src.graph.nodes.apply_prompt_template",
        return_value=[{"role": "user", "content": "plan this"}],
    ) as mock:
        yield mock


@pytest.fixture
def patch_repair_json_output():
    with patch("src.graph.nodes.repair_json_output", side_effect=lambda x: x) as mock:
        yield mock


@pytest.fixture
def patch_plan_model_validate():
    with patch("src.graph.nodes.Plan.model_validate", side_effect=lambda x: x) as mock:
        yield mock


@pytest.fixture
def patch_ai_message():
    AIMessage = namedtuple("AIMessage", ["content", "name"])
    with patch(
        "src.graph.nodes.AIMessage",
        side_effect=lambda content, name: AIMessage(content, name),
    ) as mock:
        yield mock


def test_planner_node_basic_has_enough_context(
    mock_state_planner,
    patch_config_from_runnable_config_planner,
    patch_apply_prompt_template,
    patch_repair_json_output,
    patch_plan_model_validate,
    patch_ai_message,
    mock_plan,
):
    # AGENT_LLM_MAP["planner"] == "basic"
    with (
        patch("src.graph.nodes.AGENT_LLM_MAP", {"planner": "basic"}),
        patch("src.graph.nodes.get_llm_by_type") as mock_get_llm,
    ):
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_llm
        mock_response = MagicMock()
        mock_response.model_dump_json.return_value = json.dumps(mock_plan)
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        result = planner_node(mock_state_planner, MagicMock())
        assert isinstance(result, Command)
        assert result.goto == "reporter"
        assert "current_plan" in result.update
        assert result.update["current_plan"]["has_enough_context"] is True
        assert result.update["messages"][0].name == "planner"


def test_planner_node_basic_not_enough_context(
    mock_state_planner,
    patch_config_from_runnable_config_planner,
    patch_apply_prompt_template,
    patch_repair_json_output,
    patch_plan_model_validate,
    patch_ai_message,
):
    # AGENT_LLM_MAP["planner"] == "basic"
    plan = {
        "has_enough_context": False,
        "title": "Test Plan",
        "thought": "Test Thought",
        "steps": [],
        "locale": "en-US",
    }
    with (
        patch("src.graph.nodes.AGENT_LLM_MAP", {"planner": "basic"}),
        patch("src.graph.nodes.get_llm_by_type") as mock_get_llm,
    ):
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_llm
        mock_response = MagicMock()
        mock_response.model_dump_json.return_value = json.dumps(plan)
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        result = planner_node(mock_state_planner, MagicMock())
        assert isinstance(result, Command)
        assert result.goto == "human_feedback"
        assert "current_plan" in result.update
        assert isinstance(result.update["current_plan"], str)
        assert result.update["messages"][0].name == "planner"


def test_planner_node_stream_mode_has_enough_context(
    mock_state_planner,
    patch_config_from_runnable_config_planner,
    patch_apply_prompt_template,
    patch_repair_json_output,
    patch_plan_model_validate,
    patch_ai_message,
    mock_plan,
):
    # AGENT_LLM_MAP["planner"] != "basic"
    with (
        patch("src.graph.nodes.AGENT_LLM_MAP", {"planner": "other"}),
        patch("src.graph.nodes.get_llm_by_type") as mock_get_llm,
    ):
        mock_llm = MagicMock()
        # Simulate streaming chunks
        chunk = MagicMock()
        chunk.content = json.dumps(mock_plan)
        mock_llm.stream.return_value = [chunk]
        mock_get_llm.return_value = mock_llm

        result = planner_node(mock_state_planner, MagicMock())
        assert isinstance(result, Command)
        assert result.goto == "reporter"
        assert "current_plan" in result.update
        assert result.update["current_plan"]["has_enough_context"] is True


def test_planner_node_stream_mode_not_enough_context(
    mock_state_planner,
    patch_config_from_runnable_config_planner,
    patch_apply_prompt_template,
    patch_repair_json_output,
    patch_plan_model_validate,
    patch_ai_message,
):
    # AGENT_LLM_MAP["planner"] != "basic"
    plan = {
        "has_enough_context": False,
        "title": "Test Plan",
        "thought": "Test Thought",
        "steps": [],
        "locale": "en-US",
    }
    with (
        patch("src.graph.nodes.AGENT_LLM_MAP", {"planner": "other"}),
        patch("src.graph.nodes.get_llm_by_type") as mock_get_llm,
    ):
        mock_llm = MagicMock()
        chunk = MagicMock()
        chunk.content = json.dumps(plan)
        mock_llm.stream.return_value = [chunk]
        mock_get_llm.return_value = mock_llm

        result = planner_node(mock_state_planner, MagicMock())
        assert isinstance(result, Command)
        assert result.goto == "human_feedback"
        assert "current_plan" in result.update
        assert isinstance(result.update["current_plan"], str)


def test_planner_node_plan_iterations_exceeded(mock_state_planner):
    # plan_iterations >= max_plan_iterations
    state = dict(mock_state_planner)
    state["plan_iterations"] = 5
    with patch("src.graph.nodes.AGENT_LLM_MAP", {"planner": "basic"}):
        result = planner_node(state, MagicMock())
        assert isinstance(result, Command)
        assert result.goto == "reporter"


def test_planner_node_json_decode_error_first_iteration(mock_state_planner):
    # Simulate JSONDecodeError on first iteration
    with (
        patch("src.graph.nodes.AGENT_LLM_MAP", {"planner": "basic"}),
        patch("src.graph.nodes.get_llm_by_type") as mock_get_llm,
        patch(
            "src.graph.nodes.json.loads",
            side_effect=json.JSONDecodeError("err", "doc", 0),
        ),
    ):
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_llm
        mock_response = MagicMock()
        mock_response.model_dump_json.return_value = '{"bad": "json"'
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        result = planner_node(mock_state_planner, MagicMock())
        assert isinstance(result, Command)
        assert result.goto == "__end__"


def test_planner_node_json_decode_error_second_iteration(mock_state_planner):
    # Simulate JSONDecodeError on second iteration
    state = dict(mock_state_planner)
    state["plan_iterations"] = 1
    with (
        patch("src.graph.nodes.AGENT_LLM_MAP", {"planner": "basic"}),
        patch("src.graph.nodes.get_llm_by_type") as mock_get_llm,
        patch(
            "src.graph.nodes.json.loads",
            side_effect=json.JSONDecodeError("err", "doc", 0),
        ),
    ):
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_llm
        mock_response = MagicMock()
        mock_response.model_dump_json.return_value = '{"bad": "json"'
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        result = planner_node(state, MagicMock())
        assert isinstance(result, Command)
        assert result.goto == "reporter"


# Patch Plan.model_validate and repair_json_output globally for these tests
@pytest.fixture(autouse=True)
def patch_plan_and_repair(monkeypatch):
    monkeypatch.setattr("src.graph.nodes.Plan.model_validate", lambda x: x)
    monkeypatch.setattr("src.graph.nodes.repair_json_output", lambda x: x)
    yield


@pytest.fixture
def mock_state_base():
    return {
        "current_plan": json.dumps(
            {
                "has_enough_context": True,
                "title": "Test Plan",
                "thought": "Test Thought",
                "steps": [],
                "locale": "en-US",
            }
        ),
        "plan_iterations": 0,
    }


def test_human_feedback_node_auto_accepted(monkeypatch, mock_state_base):
    # auto_accepted_plan True, should skip interrupt and parse plan
    state = dict(mock_state_base)
    state["auto_accepted_plan"] = True
    result = human_feedback_node(state)
    assert isinstance(result, Command)
    assert result.goto == "reporter"
    assert result.update["plan_iterations"] == 1
    assert result.update["current_plan"]["has_enough_context"] is True


def test_human_feedback_node_edit_plan(monkeypatch, mock_state_base):
    # interrupt returns [EDIT_PLAN]..., should return Command to planner
    state = dict(mock_state_base)
    state["auto_accepted_plan"] = False
    with patch("src.graph.nodes.interrupt", return_value="[EDIT_PLAN] Please revise"):
        result = human_feedback_node(state)
        assert isinstance(result, Command)
        assert result.goto == "planner"
        assert result.update["messages"][0].name == "feedback"
        assert "[EDIT_PLAN]" in result.update["messages"][0].content


def test_human_feedback_node_accepted(monkeypatch, mock_state_base):
    # interrupt returns [ACCEPTED]..., should proceed to parse plan
    state = dict(mock_state_base)
    state["auto_accepted_plan"] = False
    with patch("src.graph.nodes.interrupt", return_value="[ACCEPTED] Looks good!"):
        result = human_feedback_node(state)
        assert isinstance(result, Command)
        assert result.goto == "reporter"
        assert result.update["plan_iterations"] == 1
        assert result.update["current_plan"]["has_enough_context"] is True


def test_human_feedback_node_invalid_interrupt(monkeypatch, mock_state_base):
    # interrupt returns something else, should raise TypeError
    state = dict(mock_state_base)
    state["auto_accepted_plan"] = False
    with patch("src.graph.nodes.interrupt", return_value="RANDOM_FEEDBACK"):
        with pytest.raises(TypeError):
            human_feedback_node(state)


def test_human_feedback_node_json_decode_error_first_iteration(
    monkeypatch, mock_state_base
):
    # repair_json_output returns bad json, json.loads raises JSONDecodeError, plan_iterations=0
    state = dict(mock_state_base)
    state["auto_accepted_plan"] = True
    state["plan_iterations"] = 0
    with patch(
        "src.graph.nodes.json.loads", side_effect=json.JSONDecodeError("err", "doc", 0)
    ):
        result = human_feedback_node(state)
        assert isinstance(result, Command)
        assert result.goto == "__end__"


def test_human_feedback_node_json_decode_error_second_iteration(
    monkeypatch, mock_state_base
):
    # repair_json_output returns bad json, json.loads raises JSONDecodeError, plan_iterations>0
    state = dict(mock_state_base)
    state["auto_accepted_plan"] = True
    state["plan_iterations"] = 2
    with patch(
        "src.graph.nodes.json.loads", side_effect=json.JSONDecodeError("err", "doc", 0)
    ):
        result = human_feedback_node(state)
        assert isinstance(result, Command)
        assert result.goto == "reporter"


def test_human_feedback_node_not_enough_context(monkeypatch, mock_state_base):
    # Plan does not have enough context, should goto research_team
    plan = {
        "has_enough_context": False,
        "title": "Test Plan",
        "thought": "Test Thought",
        "steps": [],
        "locale": "en-US",
    }
    state = dict(mock_state_base)
    state["current_plan"] = json.dumps(plan)
    state["auto_accepted_plan"] = True
    result = human_feedback_node(state)
    assert isinstance(result, Command)
    assert result.goto == "research_team"
    assert result.update["plan_iterations"] == 1
    assert result.update["current_plan"]["has_enough_context"] is False


@pytest.fixture
def mock_state_coordinator():
    return {
        "messages": [{"role": "user", "content": "test"}],
        "locale": "en-US",
    }


@pytest.fixture
def mock_configurable_coordinator():
    mock = MagicMock()
    mock.resources = ["resource1", "resource2"]
    return mock


@pytest.fixture
def patch_config_from_runnable_config_coordinator(mock_configurable_coordinator):
    with patch(
        "src.graph.nodes.Configuration.from_runnable_config",
        return_value=mock_configurable_coordinator,
    ):
        yield


@pytest.fixture
def patch_apply_prompt_template_coordinator():
    with patch(
        "src.graph.nodes.apply_prompt_template",
        return_value=[{"role": "user", "content": "test"}],
    ) as mock:
        yield mock


@pytest.fixture
def patch_handoff_to_planner():
    with patch("src.graph.nodes.handoff_to_planner", MagicMock()):
        yield


@pytest.fixture
def patch_logger():
    with patch("src.graph.nodes.logger") as mock_logger:
        yield mock_logger


def make_mock_llm_response(tool_calls=None):
    resp = MagicMock()
    resp.tool_calls = tool_calls or []
    return resp


def test_coordinator_node_no_tool_calls(
    mock_state_coordinator,
    patch_config_from_runnable_config_coordinator,
    patch_apply_prompt_template_coordinator,
    patch_handoff_to_planner,
    patch_logger,
):
    # No tool calls, should goto __end__
    with (
        patch("src.graph.nodes.AGENT_LLM_MAP", {"coordinator": "basic"}),
        patch("src.graph.nodes.get_llm_by_type") as mock_get_llm,
    ):
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = make_mock_llm_response([])
        mock_get_llm.return_value = mock_llm

        result = coordinator_node(mock_state_coordinator, MagicMock())
        assert result.goto == "__end__"
        assert result.update["locale"] == "en-US"
        assert result.update["resources"] == ["resource1", "resource2"]


def test_coordinator_node_with_tool_calls_planner(
    mock_state_coordinator,
    patch_config_from_runnable_config_coordinator,
    patch_apply_prompt_template_coordinator,
    patch_handoff_to_planner,
    patch_logger,
):
    # tool_calls present, should goto planner
    tool_calls = [{"name": "handoff_to_planner", "args": {}}]
    with (
        patch("src.graph.nodes.AGENT_LLM_MAP", {"coordinator": "basic"}),
        patch("src.graph.nodes.get_llm_by_type") as mock_get_llm,
    ):
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = make_mock_llm_response(tool_calls)
        mock_get_llm.return_value = mock_llm

        result = coordinator_node(mock_state_coordinator, MagicMock())
        assert result.goto == "planner"
        assert result.update["locale"] == "en-US"
        assert result.update["resources"] == ["resource1", "resource2"]


def test_coordinator_node_with_tool_calls_background_investigator(
    mock_state_coordinator,
    patch_config_from_runnable_config_coordinator,
    patch_apply_prompt_template_coordinator,
    patch_handoff_to_planner,
    patch_logger,
):
    # enable_background_investigation True, should goto background_investigator
    state = dict(mock_state_coordinator)
    state["enable_background_investigation"] = True
    tool_calls = [{"name": "handoff_to_planner", "args": {}}]
    with (
        patch("src.graph.nodes.AGENT_LLM_MAP", {"coordinator": "basic"}),
        patch("src.graph.nodes.get_llm_by_type") as mock_get_llm,
    ):
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = make_mock_llm_response(tool_calls)
        mock_get_llm.return_value = mock_llm

        result = coordinator_node(state, MagicMock())
        assert result.goto == "background_investigator"
        assert result.update["locale"] == "en-US"
        assert result.update["resources"] == ["resource1", "resource2"]


def test_coordinator_node_with_tool_calls_locale_override(
    mock_state_coordinator,
    patch_config_from_runnable_config_coordinator,
    patch_apply_prompt_template_coordinator,
    patch_handoff_to_planner,
    patch_logger,
):
    # tool_calls with locale in args should override locale
    tool_calls = [{"name": "handoff_to_planner", "args": {"locale": "zh-CN"}}]
    with (
        patch("src.graph.nodes.AGENT_LLM_MAP", {"coordinator": "basic"}),
        patch("src.graph.nodes.get_llm_by_type") as mock_get_llm,
    ):
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = make_mock_llm_response(tool_calls)
        mock_get_llm.return_value = mock_llm

        result = coordinator_node(mock_state_coordinator, MagicMock())
        assert result.goto == "planner"
        assert result.update["locale"] == "zh-CN"
        assert result.update["resources"] == ["resource1", "resource2"]


def test_coordinator_node_tool_calls_exception_handling(
    mock_state_coordinator,
    patch_config_from_runnable_config_coordinator,
    patch_apply_prompt_template_coordinator,
    patch_handoff_to_planner,
    patch_logger,
):
    # tool_calls raises exception in processing
    tool_calls = [{"name": "handoff_to_planner", "args": None}]
    with (
        patch("src.graph.nodes.AGENT_LLM_MAP", {"coordinator": "basic"}),
        patch("src.graph.nodes.get_llm_by_type") as mock_get_llm,
    ):
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm

        # Simulate tool_call.get("args", {}) raising AttributeError
        class BadToolCall(dict):
            def get(self, key, default=None):
                if key == "args":
                    raise Exception("bad args")
                return super().get(key, default)

        mock_llm.invoke.return_value = make_mock_llm_response(
            [BadToolCall({"name": "handoff_to_planner"})]
        )
        mock_get_llm.return_value = mock_llm

        # Should not raise, just log error and continue
        result = coordinator_node(mock_state_coordinator, MagicMock())
        assert result.goto == "planner"
        assert result.update["locale"] == "en-US"
        assert result.update["resources"] == ["resource1", "resource2"]

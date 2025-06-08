# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import pytest
from unittest.mock import patch, MagicMock
from langchain.schema import HumanMessage, SystemMessage

from src.prompt_enhancer.graph.enhancer_node import prompt_enhancer_node
from src.prompt_enhancer.graph.state import PromptEnhancerState
from src.config.report_style import ReportStyle


@pytest.fixture
def mock_llm():
    """Mock LLM that returns a test response."""
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="Enhanced test prompt")
    return llm


@pytest.fixture
def mock_template():
    """Mock Jinja2 template."""
    template = MagicMock()
    template.render.return_value = "System prompt template"
    return template


@pytest.fixture
def mock_env(mock_template):
    """Mock template environment."""
    env = MagicMock()
    env.get_template.return_value = mock_template
    return env


class TestPromptEnhancerNode:
    """Test cases for prompt_enhancer_node function."""

    @patch("src.prompt_enhancer.graph.enhancer_node.env")
    @patch("src.prompt_enhancer.graph.enhancer_node.get_llm_by_type")
    @patch(
        "src.prompt_enhancer.graph.enhancer_node.AGENT_LLM_MAP",
        {"prompt_enhancer": "basic"},
    )
    def test_basic_prompt_enhancement(
        self, mock_get_llm, mock_env, mock_llm, mock_template
    ):
        """Test basic prompt enhancement without context or report style."""
        mock_get_llm.return_value = mock_llm
        mock_env.get_template.return_value = mock_template

        state = PromptEnhancerState(prompt="Write about AI")

        result = prompt_enhancer_node(state)

        # Verify LLM was called
        mock_get_llm.assert_called_once_with("basic")
        mock_llm.invoke.assert_called_once()

        # Verify template was used
        mock_env.get_template.assert_called_once_with(
            "prompt_enhancer/prompt_enhancer.md"
        )
        mock_template.render.assert_called_once_with()

        # Verify result
        assert result == {"output": "Enhanced test prompt"}

    @patch("src.prompt_enhancer.graph.enhancer_node.env")
    @patch("src.prompt_enhancer.graph.enhancer_node.get_llm_by_type")
    @patch(
        "src.prompt_enhancer.graph.enhancer_node.AGENT_LLM_MAP",
        {"prompt_enhancer": "basic"},
    )
    def test_prompt_enhancement_with_report_style(
        self, mock_get_llm, mock_env, mock_llm, mock_template
    ):
        """Test prompt enhancement with report style."""
        mock_get_llm.return_value = mock_llm
        mock_env.get_template.return_value = mock_template

        state = PromptEnhancerState(
            prompt="Write about AI", report_style=ReportStyle.ACADEMIC
        )

        result = prompt_enhancer_node(state)

        # Verify template was rendered with report_style
        mock_template.render.assert_called_once_with(report_style="academic")

        # Verify result
        assert result == {"output": "Enhanced test prompt"}

    @patch("src.prompt_enhancer.graph.enhancer_node.env")
    @patch("src.prompt_enhancer.graph.enhancer_node.get_llm_by_type")
    @patch(
        "src.prompt_enhancer.graph.enhancer_node.AGENT_LLM_MAP",
        {"prompt_enhancer": "basic"},
    )
    def test_prompt_enhancement_with_context(
        self, mock_get_llm, mock_env, mock_llm, mock_template
    ):
        """Test prompt enhancement with additional context."""
        mock_get_llm.return_value = mock_llm
        mock_env.get_template.return_value = mock_template

        state = PromptEnhancerState(
            prompt="Write about AI", context="Focus on machine learning applications"
        )

        result = prompt_enhancer_node(state)

        # Verify LLM was called with context in the message
        call_args = mock_llm.invoke.call_args[0][0]
        human_message = call_args[1]
        assert isinstance(human_message, HumanMessage)
        assert "Focus on machine learning applications" in human_message.content

        assert result == {"output": "Enhanced test prompt"}

    @patch("src.prompt_enhancer.graph.enhancer_node.env")
    @patch("src.prompt_enhancer.graph.enhancer_node.get_llm_by_type")
    @patch(
        "src.prompt_enhancer.graph.enhancer_node.AGENT_LLM_MAP",
        {"prompt_enhancer": "basic"},
    )
    def test_prompt_enhancement_with_all_fields(
        self, mock_get_llm, mock_env, mock_llm, mock_template
    ):
        """Test prompt enhancement with all fields populated."""
        mock_get_llm.return_value = mock_llm
        mock_env.get_template.return_value = mock_template

        state = PromptEnhancerState(
            prompt="Write about AI",
            context="Focus on ethics",
            report_style=ReportStyle.NEWS,
        )

        result = prompt_enhancer_node(state)

        # Verify template was rendered with report_style
        mock_template.render.assert_called_once_with(report_style="news")

        # Verify LLM was called with proper messages
        call_args = mock_llm.invoke.call_args[0][0]
        assert len(call_args) == 2
        assert isinstance(call_args[0], SystemMessage)
        assert isinstance(call_args[1], HumanMessage)
        assert "Focus on ethics" in call_args[1].content

        assert result == {"output": "Enhanced test prompt"}

    @pytest.mark.parametrize(
        "report_style,expected_value",
        [
            (ReportStyle.ACADEMIC, "academic"),
            (ReportStyle.POPULAR_SCIENCE, "popular_science"),
            (ReportStyle.NEWS, "news"),
            (ReportStyle.SOCIAL_MEDIA, "social_media"),
        ],
    )
    @patch("src.prompt_enhancer.graph.enhancer_node.env")
    @patch("src.prompt_enhancer.graph.enhancer_node.get_llm_by_type")
    @patch(
        "src.prompt_enhancer.graph.enhancer_node.AGENT_LLM_MAP",
        {"prompt_enhancer": "basic"},
    )
    def test_different_report_styles(
        self,
        mock_get_llm,
        mock_env,
        report_style,
        expected_value,
        mock_llm,
        mock_template,
    ):
        """Test prompt enhancement with different report styles."""
        mock_get_llm.return_value = mock_llm
        mock_env.get_template.return_value = mock_template

        state = PromptEnhancerState(prompt="Test prompt", report_style=report_style)

        result = prompt_enhancer_node(state)

        # Verify template was rendered with correct report_style value
        mock_template.render.assert_called_once_with(report_style=expected_value)
        assert result == {"output": "Enhanced test prompt"}

    @patch("src.prompt_enhancer.graph.enhancer_node.env")
    @patch("src.prompt_enhancer.graph.enhancer_node.get_llm_by_type")
    @patch(
        "src.prompt_enhancer.graph.enhancer_node.AGENT_LLM_MAP",
        {"prompt_enhancer": "basic"},
    )
    def test_prefix_removal(self, mock_get_llm, mock_env, mock_llm, mock_template):
        """Test that common prefixes are removed from LLM response."""
        mock_get_llm.return_value = mock_llm
        mock_env.get_template.return_value = mock_template

        # Test different prefixes that should be removed
        test_cases = [
            "Enhanced Prompt: This is the enhanced prompt",
            "Enhanced prompt: This is the enhanced prompt",
            "Here's the enhanced prompt: This is the enhanced prompt",
            "Here is the enhanced prompt: This is the enhanced prompt",
            "**Enhanced Prompt**: This is the enhanced prompt",
            "**Enhanced prompt**: This is the enhanced prompt",
        ]

        for response_with_prefix in test_cases:
            mock_llm.invoke.return_value = MagicMock(content=response_with_prefix)

            state = PromptEnhancerState(prompt="Test prompt")
            result = prompt_enhancer_node(state)

            assert result == {"output": "This is the enhanced prompt"}

    @patch("src.prompt_enhancer.graph.enhancer_node.env")
    @patch("src.prompt_enhancer.graph.enhancer_node.get_llm_by_type")
    @patch(
        "src.prompt_enhancer.graph.enhancer_node.AGENT_LLM_MAP",
        {"prompt_enhancer": "basic"},
    )
    def test_error_handling(self, mock_get_llm, mock_env, mock_llm, mock_template):
        """Test error handling when LLM call fails."""
        mock_get_llm.return_value = mock_llm
        mock_env.get_template.return_value = mock_template

        # Mock LLM to raise an exception
        mock_llm.invoke.side_effect = Exception("LLM error")

        state = PromptEnhancerState(prompt="Test prompt")
        result = prompt_enhancer_node(state)

        # Should return original prompt on error
        assert result == {"output": "Test prompt"}

    @patch("src.prompt_enhancer.graph.enhancer_node.env")
    @patch("src.prompt_enhancer.graph.enhancer_node.get_llm_by_type")
    @patch(
        "src.prompt_enhancer.graph.enhancer_node.AGENT_LLM_MAP",
        {"prompt_enhancer": "basic"},
    )
    def test_template_error_handling(
        self, mock_get_llm, mock_env, mock_llm, mock_template
    ):
        """Test error handling when template rendering fails."""
        mock_get_llm.return_value = mock_llm
        mock_env.get_template.return_value = mock_template

        # Mock template to raise an exception
        mock_template.render.side_effect = Exception("Template error")

        state = PromptEnhancerState(prompt="Test prompt")
        result = prompt_enhancer_node(state)

        # Should return original prompt on error
        assert result == {"output": "Test prompt"}

    @patch("src.prompt_enhancer.graph.enhancer_node.env")
    @patch("src.prompt_enhancer.graph.enhancer_node.get_llm_by_type")
    @patch(
        "src.prompt_enhancer.graph.enhancer_node.AGENT_LLM_MAP",
        {"prompt_enhancer": "basic"},
    )
    def test_whitespace_handling(self, mock_get_llm, mock_env, mock_llm, mock_template):
        """Test that whitespace is properly stripped from LLM response."""
        mock_get_llm.return_value = mock_llm
        mock_env.get_template.return_value = mock_template

        # Mock LLM response with extra whitespace
        mock_llm.invoke.return_value = MagicMock(
            content="  \n\n  Enhanced prompt  \n\n  "
        )

        state = PromptEnhancerState(prompt="Test prompt")
        result = prompt_enhancer_node(state)

        assert result == {"output": "Enhanced prompt"}

    @patch("src.prompt_enhancer.graph.enhancer_node.env")
    @patch("src.prompt_enhancer.graph.enhancer_node.get_llm_by_type")
    @patch(
        "src.prompt_enhancer.graph.enhancer_node.AGENT_LLM_MAP",
        {"prompt_enhancer": "basic"},
    )
    def test_message_structure(self, mock_get_llm, mock_env, mock_llm, mock_template):
        """Test that messages are structured correctly."""
        mock_get_llm.return_value = mock_llm
        mock_env.get_template.return_value = mock_template
        mock_template.render.return_value = "Test system prompt"

        state = PromptEnhancerState(
            prompt="Original prompt", context="Additional context"
        )

        prompt_enhancer_node(state)

        # Verify the messages passed to LLM
        call_args = mock_llm.invoke.call_args[0][0]
        assert len(call_args) == 2

        system_message = call_args[0]
        human_message = call_args[1]

        assert isinstance(system_message, SystemMessage)
        assert system_message.content == "Test system prompt"

        assert isinstance(human_message, HumanMessage)
        assert "Original prompt" in human_message.content
        assert "Additional context" in human_message.content

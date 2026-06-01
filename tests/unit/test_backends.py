"""Tests for additional model backends."""
import pytest
from unittest.mock import MagicMock, patch

from whiz.models.base import LLMResponse


class TestAnthropicModel:
    def test_init(self):
        with patch("anthropic.Anthropic") as mock_cls:
            import importlib
            import whiz.models.anthropic
            importlib.reload(whiz.models.anthropic)
            from whiz.models.anthropic import AnthropicModel
            model = AnthropicModel(model="claude-sonnet-4", api_key="sk-ant-test")
            mock_cls.assert_called_once_with(api_key="sk-ant-test")
            assert model.model == "claude-sonnet-4"

    def test_chat_completion(self):
        with patch("anthropic.Anthropic") as mock_cls:
            import importlib
            import whiz.models.anthropic
            importlib.reload(whiz.models.anthropic)
            from whiz.models.anthropic import AnthropicModel

            mock_client = MagicMock()
            mock_cls.return_value = mock_client

            mock_content = MagicMock()
            mock_content.text = "Hello from Claude"
            mock_usage = MagicMock()
            mock_usage.input_tokens = 50
            mock_usage.output_tokens = 10

            mock_response = MagicMock()
            mock_response.content = [mock_content]
            mock_response.usage = mock_usage
            mock_client.messages.create.return_value = mock_response

            model = AnthropicModel(model="claude-sonnet-4", api_key="sk-ant-test")
            result = model.chat_completion(
                messages=[
                    {"role": "system", "content": "You are helpful"},
                    {"role": "user", "content": "Hi"},
                ],
            )
            assert isinstance(result, LLMResponse)
            assert result.content == "Hello from Claude"
            assert result.prompt_tokens == 50


class TestOllamaModel:
    def test_init_defaults(self):
        from whiz.models.ollama import OllamaModel
        model = OllamaModel(model="llama3")
        assert model.model == "llama3"
        assert "11434" in model._base_url

    def test_init_custom_url(self):
        from whiz.models.ollama import OllamaModel
        model = OllamaModel(model="llama3", base_url="http://custom:8080")
        assert model._base_url == "http://custom:8080"

    def test_chat_completion(self):
        from whiz.models.ollama import OllamaModel
        model = OllamaModel(model="llama3")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "Hello from Ollama"},
            "prompt_eval_count": 30,
            "eval_count": 15,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.post", return_value=mock_response):
            result = model.chat_completion(
                messages=[{"role": "user", "content": "Hi"}],
            )
            assert isinstance(result, LLMResponse)
            assert result.content == "Hello from Ollama"
            assert result.prompt_tokens == 30
            assert result.completion_tokens == 15

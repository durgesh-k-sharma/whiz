"""Tests for model backends."""
import pytest
from unittest.mock import MagicMock, patch

from whiz.models.base import BaseModel, LLMResponse
from whiz.models.openai import OpenAIModel


# --- LLMResponse ---

class TestLLMResponse:
    def test_defaults(self):
        resp = LLMResponse(content="hello", model="gpt-4o")
        assert resp.content == "hello"
        assert resp.model == "gpt-4o"
        assert resp.prompt_tokens == 0
        assert resp.completion_tokens == 0
        assert resp.total_tokens == 0

    def test_with_tokens(self):
        resp = LLMResponse(content="hello", model="gpt-4o", prompt_tokens=10, completion_tokens=5, total_tokens=15)
        assert resp.prompt_tokens == 10
        assert resp.completion_tokens == 5
        assert resp.total_tokens == 15


# --- BaseModel ---

class TestBaseModel:
    def test_chat_completion_raises_not_implemented(self):
        model = BaseModel()
        with pytest.raises(NotImplementedError):
            model.chat_completion(messages=[{"role": "user", "content": "hi"}])

    def test_extract_text_from_string(self):
        assert BaseModel._extract_text("hello") == "hello"

    def test_extract_text_from_dict_with_text(self):
        assert BaseModel._extract_text({"text": "hello"}) == "hello"

    def test_extract_text_from_object_with_content_string(self):
        obj = MagicMock()
        obj.content = "hello"
        assert BaseModel._extract_text(obj) == "hello"

    def test_extract_text_from_list_content_blocks(self):
        obj = MagicMock()
        obj.content = [
            {"type": "text", "text": "hello"},
            {"type": "text", "text": "world"},
        ]
        assert BaseModel._extract_text(obj) == "hello\nworld"


# --- OpenAIModel ---

class TestOpenAIModel:
    def test_init_reads_env_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
        with patch("openai.OpenAI") as mock_cls:
            # Force reimport so the patch is in effect
            import importlib
            import whiz.models.openai
            importlib.reload(whiz.models.openai)
            model = whiz.models.openai.OpenAIModel(model="gpt-4o")
            mock_cls.assert_called_once_with(api_key="sk-test-123")
            assert model.model == "gpt-4o"

    def test_init_with_explicit_key(self):
        with patch("openai.OpenAI") as mock_cls:
            import importlib
            import whiz.models.openai
            importlib.reload(whiz.models.openai)
            model = whiz.models.openai.OpenAIModel(model="gpt-4o", api_key="sk-explicit")
            mock_cls.assert_called_once_with(api_key="sk-explicit")

    def test_init_with_base_url(self):
        with patch("openai.OpenAI") as mock_cls:
            import importlib
            import whiz.models.openai
            importlib.reload(whiz.models.openai)
            model = whiz.models.openai.OpenAIModel(
                model="gpt-4o",
                api_key="sk-test",
                base_url="https://custom.api.com/v1",
            )
            mock_cls.assert_called_once_with(
                api_key="sk-test", base_url="https://custom.api.com/v1"
            )

    def test_chat_completion(self):
        with patch("openai.OpenAI") as mock_cls:
            import importlib
            import whiz.models.openai
            importlib.reload(whiz.models.openai)

            mock_client = MagicMock()
            mock_cls.return_value = mock_client

            mock_msg = MagicMock()
            mock_msg.content = "Paris"
            mock_choice = MagicMock()
            mock_choice.message = mock_msg
            mock_usage = MagicMock()
            mock_usage.prompt_tokens = 50
            mock_usage.completion_tokens = 5
            mock_usage.total_tokens = 55

            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_response.usage = mock_usage
            mock_client.chat.completions.create.return_value = mock_response

            model = whiz.models.openai.OpenAIModel(model="gpt-4o", api_key="sk-test")
            result = model.chat_completion(
                messages=[{"role": "user", "content": "What is the capital of France?"}],
            )

            assert isinstance(result, LLMResponse)
            assert result.content == "Paris"
            assert result.model == "gpt-4o"
            assert result.prompt_tokens == 50
            assert result.completion_tokens == 5
            assert result.total_tokens == 55

    def test_chat_completion_model_override(self):
        with patch("openai.OpenAI") as mock_cls:
            import importlib
            import whiz.models.openai
            importlib.reload(whiz.models.openai)

            mock_client = MagicMock()
            mock_cls.return_value = mock_client

            mock_msg = MagicMock()
            mock_msg.content = "answer"
            mock_choice = MagicMock()
            mock_choice.message = mock_msg
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_response.usage = None
            mock_client.chat.completions.create.return_value = mock_response

            model = whiz.models.openai.OpenAIModel(model="gpt-4o", api_key="sk-test")
            result = model.chat_completion(
                messages=[{"role": "user", "content": "hi"}],
                model="gpt-4-turbo",
            )
            assert result.model == "gpt-4-turbo"

    def test_chat_completion_empty_content(self):
        with patch("openai.OpenAI") as mock_cls:
            import importlib
            import whiz.models.openai
            importlib.reload(whiz.models.openai)

            mock_client = MagicMock()
            mock_cls.return_value = mock_client

            mock_msg = MagicMock()
            mock_msg.content = None
            mock_choice = MagicMock()
            mock_choice.message = mock_msg
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_response.usage = None
            mock_client.chat.completions.create.return_value = mock_response

            model = whiz.models.openai.OpenAIModel(model="gpt-4o", api_key="sk-test")
            result = model.chat_completion(
                messages=[{"role": "user", "content": "hi"}],
            )
            assert result.content == ""

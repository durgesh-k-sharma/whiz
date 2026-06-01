"""Tests for MockLLM."""
import pytest
from tests.mocks.llm import MockLLM


class TestMockLLM:
    def test_returns_scripted_responses(self):
        mock = MockLLM(responses=["hello", "world"])
        r1 = mock.chat_completion([{"role": "user", "content": "hi"}])
        assert r1.content == "hello"
        r2 = mock.chat_completion([{"role": "user", "content": "again"}])
        assert r2.content == "world"

    def test_tracks_call_count(self):
        mock = MockLLM(responses=["a", "b", "c"])
        assert mock.call_count == 0
        mock.chat_completion([{"role": "user", "content": "1"}])
        assert mock.call_count == 1
        mock.chat_completion([{"role": "user", "content": "2"}])
        assert mock.call_count == 2

    def test_records_calls(self):
        mock = MockLLM(responses=["a"])
        msgs = [{"role": "user", "content": "test"}]
        mock.chat_completion(msgs)
        assert len(mock.calls) == 1
        assert mock.calls[0] == msgs

    def test_exhaustion_raises(self):
        mock = MockLLM(responses=["only one"])
        mock.chat_completion([{"role": "user", "content": "hi"}])
        with pytest.raises(IndexError, match="MockLLM exhausted"):
            mock.chat_completion([{"role": "user", "content": "again"}])

    def test_response_includes_tokens(self):
        mock = MockLLM(responses=["hello world"])
        resp = mock.chat_completion([{"role": "user", "content": "hi"}])
        assert resp.model == "mock"
        assert resp.prompt_tokens == 10
        assert resp.completion_tokens > 0

    def test_assert_called_with(self):
        mock = MockLLM(responses=["ok"])
        msgs = [{"role": "user", "content": "check this"}]
        mock.chat_completion(msgs)
        mock.assert_called_with(msgs)  # should not raise

    def test_assert_called_with_fails(self):
        mock = MockLLM(responses=["ok"])
        mock.chat_completion([{"role": "user", "content": "actual"}])
        with pytest.raises(AssertionError, match="Last call mismatch"):
            mock.assert_called_with([{"role": "user", "content": "wrong"}])

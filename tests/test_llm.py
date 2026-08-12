import os
import pytest

from autoapply.llm.generator import GeminiAnswerGenerator
from autoapply.profile.seed import seeded_profile


def test_llm_generator_fallback(monkeypatch: pytest.MonkeyPatch):
    # Ensure no API key or OAuth token is set
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_OAUTH_TOKEN", raising=False)
    monkeypatch.setattr(GeminiAnswerGenerator, "_init_client", lambda self: None)

    prof = seeded_profile()
    generator = GeminiAnswerGenerator(prof)

    # Should fallback cleanly to pre-written master profile answers
    ans_intro = generator.generate_answer("Tell me about yourself")
    assert "University of Louisville" in ans_intro or "Computer Science" in ans_intro

    ans_why = generator.generate_answer("Why are you interested in this role?")
    assert "network engineering" in ans_why or "cybersecurity" in ans_why

    ans_notice = generator.generate_answer("What is your notice period / availability?")
    assert "Summer" in ans_notice


def test_llm_generator_custom_model(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")
    monkeypatch.setattr(GeminiAnswerGenerator, "_init_client", lambda self: None)
    prof = seeded_profile()
    generator = GeminiAnswerGenerator(prof)
    assert generator.model_name == "gemini-2.5-pro"


def test_llm_prompt_building(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(GeminiAnswerGenerator, "_init_client", lambda self: None)
    prof = seeded_profile()
    generator = GeminiAnswerGenerator(prof)
    prompt = generator._build_prompt("Describe a challenging project", role_title="InfoSec Intern", company_name="CrowdStrike")

    assert "CrowdStrike" in prompt
    assert "InfoSec Intern" in prompt
    assert "Describe a challenging project" in prompt
    assert "Joshua" in prompt
    assert "University of Louisville" in prompt

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any

from ..ui import info, warn, success


class GeminiAnswerGenerator:
    """Screening question answer generator using Google Gemini AI.
    
    Supports:
    1. Standard GEMINI_API_KEY or GOOGLE_API_KEY.
    2. Google AI One Subscription / Account Auth via OAuth 2.0 access token 
       (GOOGLE_OAUTH_TOKEN or `gcloud auth print-access-token` / Application Default Credentials).
    3. Custom model selection via GEMINI_MODEL (defaults to gemini-2.5-flash).
    4. Fallback to master profile screening answers when unauthenticated.
    """

    def __init__(self, profile: dict[str, Any]):
        self.profile = profile
        self.model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.client = self._init_client()

    def _init_client(self) -> Any | None:
        """Initialize google.genai Client with API Key, OAuth token, or ADC."""
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            warn("google-genai package not installed.")
            return None

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            info(f"  Initialized Gemini client via API Key (Model: {self.model_name})")
            return genai.Client(api_key=api_key)

        # Check OAuth token or gcloud CLI auth for Google AI One Subscription
        oauth_token = os.environ.get("GOOGLE_OAUTH_TOKEN") or os.environ.get("GEMINI_OAUTH_TOKEN")
        if not oauth_token and shutil.which("gcloud") and not os.environ.get("AUTOAPPLY_DISABLE_GCLOUD"):
            try:
                res = subprocess.run(
                    ["gcloud", "auth", "application-default", "print-access-token"],
                    capture_output=True, text=True, timeout=1
                )
                if res.returncode == 0 and res.stdout.strip():
                    oauth_token = res.stdout.strip()
            except Exception:
                pass

        if oauth_token:
            info(f"  Initialized Gemini client via OAuth Token / Google AI One Sub (Model: {self.model_name})")
            # Construct Client with Credentials
            try:
                import google.oauth2.credentials
                creds = google.oauth2.credentials.Credentials(token=oauth_token)
                return genai.Client(credentials=creds)
            except Exception as exc:
                warn(f"  OAuth credentials setup failed: {exc}")

        # Fallback check for Application Default Credentials (ADC) if explicitly enabled
        if not os.environ.get("AUTOAPPLY_DISABLE_GCLOUD"):
            try:
                import google.auth
                credentials, project = google.auth.default()
                info("  Initialized Gemini client via Application Default Credentials (ADC)")
                return genai.Client(credentials=credentials)
            except Exception:
                pass

        return None

    def generate_answer(self, question: str, role_title: str = "", company_name: str = "") -> str:
        """Generate a tailored answer for a job application screening question."""
        fallback = self._get_fallback_answer(question)

        if not self.client:
            return fallback

        prompt = self._build_prompt(question, role_title, company_name)
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            answer = (response.text or "").strip()
            if answer:
                success(f"  Generated Gemini answer ({len(answer)} chars)")
                return answer
        except Exception as exc:
            warn(f"  Gemini generation failed ({exc}); using profile fallback.")

        return fallback

    def _build_prompt(self, question: str, role_title: str, company_name: str) -> str:
        ident = self.profile.get("identity", {})
        edu = self.profile.get("education", [])
        exp = self.profile.get("experience", [])
        skills = self.profile.get("skills", [])
        projects = self.profile.get("projects", [])

        candidate_summary = f"""
Candidate: {ident.get('legal_first')} {ident.get('legal_last')}
Target Season: Summer 2026 Internships
Education: {', '.join(e.get('institution', '') + ' (' + e.get('degree', '') + ')' for e in edu)}
Recent Experience: {', '.join(x.get('title', '') + ' at ' + x.get('company', '') for x in exp)}
Top Skills: {', '.join(s.get('name', '') for s in skills[:10])}
Key Projects: {', '.join(p.get('name', '') for p in projects[:3])}
        """.strip()

        return f"""
You are an assistant helping a candidate apply for an internship role.
Role Title: {role_title or 'Internship'}
Company: {company_name or 'Hiring Company'}

Candidate Background:
{candidate_summary}

Question asked on job application form:
"{question}"

Instructions:
- Write a professional, concise, first-person response.
- Maximum 150 words unless the question explicitly asks for a long answer.
- Focus on relevant skills in cybersecurity, networking, IT security, and Java/Python development.
- Output ONLY the final response text without preambles or quotes.
""".strip()

    def _get_fallback_answer(self, question: str) -> str:
        """Select relevant pre-written answer from master profile based on question text."""
        q_lower = question.lower()
        answers = self.profile.get("screening_answers", {})

        if "about yourself" in q_lower or "introduce" in q_lower:
            return answers.get("tell_me_about_yourself_short") or (
                "I am a Computer Science student at the University of Louisville specializing in "
                "IT security, network infrastructure, and system administration. I have experience "
                "building enterprise home lab networks, tutoring Java APCSA, and developing full-stack applications."
            )
        if "why" in q_lower or "interested" in q_lower:
            return answers.get("why_interested") or (
                "I am eager to contribute my hands-on experience in network engineering, threat monitoring, "
                "and software security to solve real-world technical challenges with your team."
            )
        if "notice" in q_lower or "start date" in q_lower or "availability" in q_lower:
            return answers.get("notice_period") or "Available immediately for Summer 2026."
        if "challenging" in q_lower or "project" in q_lower:
            return answers.get("challenging_project") or (
                "Designed a physical enterprise rack network with Cisco switching, pfSense routing, "
                "and Active Directory GPOs simulating corporate network isolation."
            )

        return answers.get("tell_me_about_yourself_short") or "Available for Summer 2026 internship."

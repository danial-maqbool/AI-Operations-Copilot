import json
import os
import re
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

from backend.config import settings

class AIProvider:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self.model = settings.GEMINI_MODEL or "gemini-2.5-flash"
        self.client = None
        if self.api_key and settings.AI_ENABLED:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.client = None

    def is_gemini_active(self) -> bool:
        return self.client is not None and bool(self.api_key) and settings.AI_ENABLED

    def classify_intent(self, question: str) -> str:
        q_low = question.lower()
        if ("policy" in q_low or "sop" in q_low or "rule" in q_low or "approval" in q_low) and any(kw in q_low for kw in ["case", "order", "invoice", "refund", "which", "who", "show"]):
            return "hybrid"
        if any(kw in q_low for kw in ["policy", "sop", "guideline", "escalation rule", "terms", "allowed"]):
            return "policy_rag"
        if q_low.startswith("why") or "caused" in q_low or "increase" in q_low or "investigate" in q_low:
            return "investigate"
        if any(kw in q_low for kw in ["action plan", "priority action", "morning review", "what should we do", "what requires attention"]):
            return "action_plan"
        return "data_query"

    def plan_tools(self, question: str, available_tables: List[str]) -> List[Dict[str, Any]]:
        intent = self.classify_intent(question)
        tools = []

        if intent == "hybrid":
            tools.append({"tool": "search_documents", "args": {"query": question}})
            tools.append({"tool": "run_readonly_sql", "args": {"sql": ""}})
        elif intent == "policy_rag":
            tools.append({"tool": "search_documents", "args": {"query": question}})
        elif intent == "investigate":
            tools.append({"tool": "investigate_problem", "args": {"problem": question}})
        elif intent == "action_plan":
            tools.append({"tool": "calculate_kpi", "args": {"code": "ALL"}})
            tools.append({"tool": "detect_anomalies", "args": {"table_name": available_tables[0] if available_tables else "orders"}})
        else:
            tools.append({"tool": "run_readonly_sql", "args": {"sql": ""}})

        return tools

    def generate_gemini_completion(self, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        if not self.is_gemini_active():
            return None

        try:
            config = types.GenerateContentConfig(
                temperature=0.1,
                system_instruction=system_instruction
            )
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )
            return response.text
        except Exception:
            return None

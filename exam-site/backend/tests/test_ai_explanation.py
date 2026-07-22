import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.ai_explanation_service import AIExplanationService


QUESTION = {
    "id": 7,
    "type": "multiple",
    "question": "Python 中哪些属于序列类型？",
    "options": {"A": "列表", "B": "字典", "C": "元组"},
    "answer": "AC",
}


class AIExplanationServiceTests(unittest.TestCase):
    def test_local_fallback_explains_missing_and_extra_options(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            result = __import__(
                "asyncio"
            ).run(AIExplanationService().explain(QUESTION, "AB"))

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["source"], "local")
        self.assertIn("漏选了 C", result["data"]["mistake_analysis"])
        self.assertIn("多选了 B", result["data"]["mistake_analysis"])

    def test_response_text_parser_supports_responses_api_shape(self):
        text = AIExplanationService._extract_output_text(
            {"output": [{"content": [{"type": "output_text", "text": "{\"ok\": true}"}]}]}
        )
        self.assertEqual(text, '{"ok": true}')


class AIExplanationEndpointTests(unittest.TestCase):
    def test_endpoint_returns_local_explanation_without_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            with TestClient(app) as client:
                response = client.post(
                    "/api/ai/explain",
                    json={"question": QUESTION, "user_answer": "AB"},
                )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["data"]["source"], "local")
        self.assertEqual(body["data"]["correct_answer"], "AC")

    def test_endpoint_requires_answer_in_question_payload(self):
        question = {key: value for key, value in QUESTION.items() if key != "answer"}
        with TestClient(app) as client:
            response = client.post(
                "/api/ai/explain", json={"question": question, "user_answer": "A"}
            )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()

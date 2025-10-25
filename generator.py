# generator.py
from openai import OpenAI
import os
import json
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file")
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a QA expert who creates comprehensive test cases with detailed steps."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating content: {e}")
            return None

class TestCaseGenerator:
    def __init__(self):
        self.llm = LLMClient()

    def generate_test_cases(self, requirement_text: str, positive: int = 3, negative: int = 2, edge: int = 1) -> List[Dict]:
        all_test_cases = []
        categories = [("Positive", positive), ("Negative", negative), ("Edge", edge)]
        for category, count in categories:
            if count == 0:
                continue
            print(f"Generating {count} {category} test cases...")
            batch_size = 3 if category == "Edge" else 5
            for batch_start in range(0, count, batch_size):
                batch_count = min(batch_size, count - batch_start)
                success = False
                for attempt in range(3):  # retry logic
                    prompt = self._create_batch_prompt(requirement_text, category, batch_count)
                    raw = self.llm.generate(prompt, temperature=0.2, max_tokens=4000)
                    parsed_batch = self._try_parse(raw)
                    if parsed_batch:
                        for tc in parsed_batch:
                            if isinstance(tc, dict):
                                tc['Category'] = category
                        all_test_cases.extend(parsed_batch)
                        print(f"  ✓ Successfully generated {len(parsed_batch)} {category} cases")
                        success = True
                        break
                    else:
                        print(f"  ✗ Could not parse {category} batch at {batch_start}, attempt {attempt+1}. Raw response excerpt:\n{raw[:250]}\n")
                if not success:
                    print(f"  ✗ Warning: Could not parse {category} batch after 3 attempts")
        if not all_test_cases:
            print("ERROR: No test cases generated. Check prompts and try reducing batch size.")
        return self._fill_missing_fields(all_test_cases)

    def _create_batch_prompt(self, requirement_text, category, count):
        return (f"Generate exactly {count} {category} test cases as a JSON array for the requirement below.\n\n"
                "IMPORTANT:\n"
                "- Output ONLY a JSON array, NO explanation, NO markdown.\n"
                "- Each object must have: Functionality, Test Summary, Pre Condition, Test Data, Test Steps (array), Expected Result, Category\n"
                f"- Every test's Category must be \"{category}\"\n\n"
                f"Requirement:\n{requirement_text}")

    def _try_parse(self, text: str) -> List[Dict]:
        if not text or not text.strip():
            return None
        text = text.strip()
        # Remove markdown/code block if present
        if text.startswith("``````"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
        # Find array region and fix stray commas or formatting
        try:
            start, end = text.index('['), text.rindex(']') + 1
            json_str = text[start:end]
            parsed = json.loads(json_str)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                return [parsed]
        except Exception:
            pass
        # Direct parse last resort
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                return [parsed]
        except Exception:
            return None
        return None

    def _fill_missing_fields(self, items: List[Dict]) -> List[Dict]:
        filled = []
        for idx, tc in enumerate(items):
            if not isinstance(tc, dict):
                tc = {}
            func = tc.get('Functionality') or ""
            summary = tc.get('Test Summary') or ""
            pre = tc.get('Pre Condition') or ""
            test_data = tc.get('Test Data') or ""
            steps = tc.get('Test Steps') or []
            expected = tc.get('Expected Result') or ""
            category = tc.get('Category') or ""
            if not func: func = f"Test Case {idx + 1}"
            if not summary: summary = f"Verify {func}"
            if not expected: expected = f"System should behave as expected for {func}."
            filled.append({
                'Functionality': func,
                'Test Summary': summary,
                'Pre Condition': pre,
                'Test Data': test_data,
                'Test Steps': steps,
                'Expected Result': expected,
                'Category': category
            })
        return filled

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
        """Generate text from the LLM. Allows overriding temperature and max_tokens."""
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

    def generate_test_cases(self, requirement_text: str, positive:int=3, negative:int=2, edge:int=1) -> str:
        # Request structured JSON output so we can build a table reliably
        prompt_prefix = (
            "You are an expert QA test-case writer.\n"
            "Given the following requirement, generate a list (JSON array) of test case objects.\n"
            "Each test case object must contain these fields exactly:\n"
            "- Functionality (string)\n"
            "- Test Summary (string)\n"
            "- Pre Condition (string)\n"
            "- Test Data (string or dict)\n"
            "- Test Steps (array of strings)\n"
            "- Expected Result (string)\n\n"
            "Requirement:\n"
        )

        prompt_suffix = (
            "\nRequirements for the output:\n"
            "- ONLY output valid JSON (a single JSON array). Do not include any extra explanation.\n"
            f"- Provide exactly {positive} positive (happy-path) test cases, {negative} negative (error/validation) test cases, and {edge} edge-case tests.\n"
            "- Include a \"Category\" field for each test case with one of these values: \"Positive\", \"Negative\", \"Edge\".\n"
            "- Use realistic test data values where applicable.\n\n"
            "Example output (exact structure, JSON only):\n"
            "[\n"
            "  {\n"
            "    \"Functionality\": \"Login\",\n"
            "    \"Test Summary\": \"Valid login with correct credentials\",\n"
            "    \"Pre Condition\": \"User account exists\",\n"
            "    \"Test Data\": {\"email\": \"user@example.com\", \"password\": \"Password123\"},\n"
            "    \"Test Steps\": [\"Open login page\", \"Enter email\", \"Enter password\", \"Click Login\"],\n"
            "    \"Expected Result\": \"User is redirected to dashboard\",\n"
            "    \"Category\": \"Positive\"\n"
            "  }\n"
            "]\n\n"
            "Now generate the JSON array for the provided requirement."
        )

        prompt = prompt_prefix + requirement_text + prompt_suffix

        # prefer deterministic output and allow more tokens for larger lists
        raw = self.llm.generate(prompt, temperature=0.2, max_tokens=8000)
        if not raw:
            return None

        def _try_parse(text: str):
            """Try multiple ways to parse JSON from model text."""
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return parsed
                if isinstance(parsed, dict):
                    return [parsed]
            except Exception:
                pass

            # try to find a JSON array substring
            try:
                start = text.index('[')
                end = text.rindex(']') + 1
                json_str = text[start:end]
                parsed = json.loads(json_str)
                return parsed
            except Exception:
                return None

        parsed = _try_parse(raw)
        if parsed:
            # If parsed, ensure category counts match requested counts below
            pass

        # Helper to count categories
        def _count_categories(items):
            counts = {"Positive": 0, "Negative": 0, "Edge": 0}
            for it in items:
                if not isinstance(it, dict):
                    continue
                cat = it.get('Category') or it.get('category')
                if not cat:
                    continue
                c = str(cat).strip().lower()
                if 'positive' in c:
                    counts['Positive'] += 1
                elif 'negative' in c:
                    counts['Negative'] += 1
                elif 'edge' in c:
                    counts['Edge'] += 1
            return counts

        def _fill_missing_fields(items):
            """Ensure each test case has the required fields by synthesizing reasonable defaults."""
            filled = []
            for idx, tc in enumerate(items):
                if not isinstance(tc, dict):
                    tc = {}
                func = tc.get('Functionality') or tc.get('Function') or tc.get('function') or ''
                summary = tc.get('Test Summary') or tc.get('Summary') or tc.get('test_summary') or ''
                pre = tc.get('Pre Condition') or tc.get('Precondition') or tc.get('Pre-Condition') or ''
                test_data = tc.get('Test Data') or tc.get('TestData') or tc.get('data') or ''
                steps = tc.get('Test Steps') or tc.get('TestSteps') or tc.get('Steps') or []
                expected = tc.get('Expected Result') or tc.get('Expected') or tc.get('expected') or ''
                category = tc.get('Category') or tc.get('category') or ''

                # Synthesize missing Functionality
                if not func:
                    if summary:
                        func = summary.split(':')[0].strip()
                    else:
                        func = (requirement_text.split('\n')[0][:60] + f" - case {idx+1}")

                # Synthesize missing Test Summary
                if not summary:
                    if isinstance(steps, list) and steps:
                        summary = f"{func}: {str(steps[0])}"
                    else:
                        summary = f"Verify {func}"

                # Synthesize missing Expected Result
                if not expected:
                    if isinstance(steps, list) and steps:
                        last = str(steps[-1])
                        expected = f"After performing the steps, the system should {last}."
                    else:
                        expected = f"The system should behave as expected for {func}."

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

        if parsed:
            # verify the counts
            counts = _count_categories(parsed)
            needed = {'Positive': positive, 'Negative': negative, 'Edge': edge}
            missing = {k: max(0, needed[k] - counts.get(k, 0)) for k in needed}
            total_missing = sum(missing.values())
            if total_missing == 0:
                return _fill_missing_fields(parsed)

            # Request only the missing cases and append
            retries = 2
            additional = []
            last_raw = raw
            for attempt in range(retries):
                # Build focused follow-up that asks for only the missing cases
                followup_parts = [f"Please produce the missing test cases for the requirement.\n\nRequirement:\n{requirement_text}\n\n"]
                followup_parts.append("Return ONLY a JSON array containing the additional test case objects needed to reach the requested counts.\n")
                followup_parts.append("Each object must follow the same schema and include the \"Category\" field with one of: \"Positive\", \"Negative\", \"Edge\".\n")
                followup_parts.append(f"Missing counts: {missing}\n")
                followup = '\n'.join(followup_parts)

                last_raw = self.llm.generate(followup, temperature=0.2, max_tokens=1500)
                if not last_raw:
                    break
                parsed_more = _try_parse(last_raw)
                if parsed_more:
                    # append parsed_more and re-evaluate
                    if isinstance(parsed_more, dict):
                        parsed_more = [parsed_more]
                    additional.extend(parsed_more)
                    # combine and check counts
                    combined = parsed + additional
                    counts = _count_categories(combined)
                    total_missing = sum(max(0, needed[k] - counts.get(k, 0)) for k in needed)
                    if total_missing == 0:
                        return combined

            # If we still don't have the requested counts, return what we have (original + additional)
            if additional:
                return _fill_missing_fields(parsed + additional)
            # fallthrough: return last raw for inspection
            print("Warning: Unable to generate exact requested counts after retries. Returning best-effort results or raw text.")
            return last_raw

    def generate_selenium_script(self, test_case: str) -> str:
        prompt = f"""
        Convert this test case into a Selenium Python script:
        {test_case}
        
        Include:
        - All necessary imports
        - Setup and teardown
        - Clear comments
        - Error handling
        - Assertions for verification
        - Logging
        """
        return self.llm.generate(prompt)# generator.py
# from openai import OpenAI
# import os
# from dotenv import load_dotenv

# load_dotenv()

# class LLMClient:
#     def __init__(self):
#         self.api_key = os.getenv("OPENAI_API_KEY")
#         if not self.api_key:
#             raise ValueError("OpenAI API key not found in environment variables")
#         self.client = OpenAI(api_key=self.api_key)

#     def generate(self, prompt: str) -> str:
#         try:
#             response = self.client.chat.completions.create(
#                 model="gpt-3.5-turbo",
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": "You are a QA expert. Generate test cases in a structured format with clear sections."
#                     },
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0.7
#             )
#             return response.choices[0].message.content
#         except Exception as e:
#             print(f"Error generating content: {e}")
#             return None

# class TestCaseGenerator:
#     def __init__(self):
#         self.llm = LLMClient()

#     def generate_test_cases(self, requirement_text: str) -> str:
#         prompt = f"""
#         Generate detailed test cases for the following requirement:
#         {requirement_text}

#         Format each test case exactly as follows:

#         Test Case ID: TC_001
#         Category: [Positive/Negative]
#         Priority: [High/Medium/Low]
#         Test Objective: [Clear objective]
#         Preconditions: 
#         - [List preconditions]
        
#         Test Steps:
#         1. [Step 1]
#         2. [Step 2]
#         ...
        
#         Expected Results:
#         - [Expected result 1]
#         - [Expected result 2]
        
#         Test Data:
#         - [Any specific test data needed]

#         -------------------

#         Generate at least 3 positive and 2 negative test cases following this exact format.
#         """
#         return self.llm.generate(prompt)
# from litellm import completion

# # Define your prompt
# prompt = "Generate 5 positive and negative test cases for login screen validation"

# # Call local Ollama model via LiteLLM
# response = completion(
#     model="ollama/mistral",
#     messages=[
#         {"role": "user", "content": prompt}
#     ]
# )

# # Print the response
# print("\nGenerated Test Cases:\n")
# print(response['choices'][0]['message']['content'])

# save_excel.py
import pandas as pd
import os
from typing import List, Dict


def test_cases_to_excel(test_cases: List[Dict], filename: str = "outputs/testcases.xlsx") -> str:
    """Save structured test cases (list of dicts) to an Excel file.

    Expected keys in each test case dict:
    - Functionality
    - Test Summary
    - Pre Condition
    - Test Data
    - Test Steps (list or string)
    - Expected Result
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    rows = []
    for tc in test_cases:
        steps = tc.get("Test Steps") or tc.get("TestSteps") or []
        if isinstance(steps, list):
            steps_text = "\n".join(steps)
        else:
            steps_text = str(steps)

        rows.append({
            "Functionality": tc.get("Functionality", ""),
            "Test Summary": tc.get("Test Summary", ""),
            "Pre Condition": tc.get("Pre Condition", ""),
            "Test Data": tc.get("Test Data", ""),
            "Test Steps": steps_text,
            "Expected Result": tc.get("Expected Result", "")
        })

    df = pd.DataFrame(rows, columns=["Functionality", "Test Summary", "Pre Condition", "Test Data", "Test Steps", "Expected Result"])
    df.to_excel(filename, index=False)
    return filename


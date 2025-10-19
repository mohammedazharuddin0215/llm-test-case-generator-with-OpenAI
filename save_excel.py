 # save_excel.py
import pandas as pd
import os

def test_cases_to_excel(test_cases, filename="outputs/testcases.xlsx"):
    os.makedirs("outputs", exist_ok=True)
    rows = []
    for tc in test_cases:
        rows.append({
            "id": tc.get("id"),
            "title": tc.get("title"),
            "steps": "\n".join(tc.get("steps", [])),
            "expected_result": tc.get("expected_result"),
            "type": tc.get("type")
        })
    df = pd.DataFrame(rows)
    df.to_excel(filename, index=False)


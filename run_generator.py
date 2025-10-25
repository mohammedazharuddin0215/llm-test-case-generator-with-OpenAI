from generator import TestCaseGenerator
import json


def main():
    generator = TestCaseGenerator()

    requirement = """
    User Login Feature:
    - Users should be able to login with email and password
    - Show error for invalid credentials
    - Lock account after 3 failed attempts
    """

    print("\n=== Generating Test Cases ===\n")
    result = generator.generate_test_cases(requirement)

    if not result:
        print("Error: Failed to generate test cases")
        return

    if isinstance(result, str):
        print(result)
    else:
        # pretty print JSON table
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
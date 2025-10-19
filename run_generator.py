from generator import TestCaseGenerator

def main():
    generator = TestCaseGenerator()
    
    requirement = """
    User Login Feature:
    - Users should be able to login with email and password
    - Show error for invalid credentials
    - Lock account after 3 failed attempts
    """

    test_cases = generator.generate_test_cases(requirement)
    
    print("\nGenerated Test Cases:")
    print("--------------------")
    print(test_cases)

if __name__ == "__main__":
    main()
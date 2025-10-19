# generator.py

from litellm import completion

# Define your prompt
prompt = "Generate 5 positive and negative test cases for login screen validation"

# Call local Ollama model via LiteLLM
response = completion(
    model="ollama/mistral",
    messages=[
        {"role": "user", "content": prompt}
    ]
)

# Print the response
print("\nGenerated Test Cases:\n")
print(response['choices'][0]['message']['content'])

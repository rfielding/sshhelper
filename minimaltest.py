import openai
import os

# Get OpenAI API key from environment variable
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY environment variable not set")
    exit(1)
else:
    openai.api_key = api_key
    print("OpenAI API key set successfully")

# Function to interact with OpenAI's API
def get_assistance(prompt):
    try:
        print("Sending prompt to OpenAI API...")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        print(f"API Response: {response}")
        return response['choices'][0]['message']['content'].strip()
    except openai.error.RateLimitError as e:
        print(f"Quota exceeded: {e}")
        return "Quota exceeded error"
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "Error getting assistance"

# Test the function
if __name__ == "__main__":
    prompt = "How do you write a Python function?"
    response = get_assistance(prompt)
    print("Response from OpenAI:", response)


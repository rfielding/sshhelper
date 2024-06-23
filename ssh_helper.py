import os
import openai
import subprocess

openai.api_key = os.getenv('OPENAI_API_KEY')

def get_command_from_prompt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"Translate '{prompt}' to a bash command"}
        ]
    )

    # Extract the command part from the response
    command = response['choices'][0]['message']['content']
    command_lines = command.splitlines()
    for line in command_lines:
        if line.startswith("```bash"):
            continue
        if line.startswith("```"):
            break
        return line.strip()

    return None

while True:
    prompt = input("Enter your command, English prompt, or type 'exit' to quit: ")
    if prompt.lower() == 'exit':
        print("Exiting...")
        break

    command = get_command_from_prompt(prompt)
    if command:
        print(f"Executing bash command: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
    else:
        print("Error: Could not extract command from API response")


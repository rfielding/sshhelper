import os
import openai
import subprocess
import shlex
import argparse

# Set up argument parsing
parser = argparse.ArgumentParser(description="SSH Helper Script")
parser.add_argument("--hostname", required=True, help="The SSH hostname")
parser.add_argument("--port", type=int, required=True, help="The SSH port")
parser.add_argument("--username", required=True, help="The SSH username")
parser.add_argument("--key_path", required=True, help="The path to the SSH private key")
args = parser.parse_args()

openai.api_key = os.getenv('OPENAI_API_KEY')

hostname = args.hostname
port = args.port
username = args.username
key_path = args.key_path

def get_commands_from_prompt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"Translate to a bash command pipeline that is ready to execute literally: {prompt}"}
        ]
    )

    # Debug: Print the entire API response
    print("API Response:", response)

    # Extract the command part from the response
    command = response['choices'][0]['message']['content']
    print("Extracted Command Content:", command)  # Debug: Print the extracted command content
    command_lines = command.splitlines()
    commands = []
    capture = False

    for line in command_lines:
        line = line.strip()
        if line.startswith("```"):
            capture = not capture
            continue
        if capture or (not any(line.startswith(prefix) for prefix in ["The translation", "The bash command", "Translation", "In bash", "```"])):
            commands.append(line)

    # Filter out empty lines and non-command text
    commands = [cmd for cmd in commands if cmd and not cmd.startswith(('The translation', 'Translation', 'In bash'))]

    print("Captured Commands:", commands)  # Debug: Print the captured commands
    return commands

while True:
    prompt = input("OpenAI> ")
    if prompt.lower() == 'exit':
        print("Exiting...")
        break

    commands = get_commands_from_prompt(prompt)
    if commands:
        print("{username}@{hostname}:{port}:")
        for cmd in commands:
            print(cmd)
        confirmation = input("Continue? [Y/Enter/n]: ").strip().lower()
        if confirmation in ['', 'y', 'yes']:
            for command in commands:
                try:
                    ssh_command = f"ssh -i {key_path} -p {port} {username}@{hostname} {shlex.quote(command)}"
                    process = subprocess.Popen(shlex.split(ssh_command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    stdout, stderr = process.communicate()
                    if stdout:
                        print("Output:\n", stdout)
                    if stderr:
                        print("Error:\n", stderr)
                except subprocess.CalledProcessError as e:
                    print(f"Error: {e.stderr}")
                except Exception as e:
                    print(f"Exception: {str(e)}")
        else:
            print("Operation cancelled.")
    else:
        print("Error: Could not extract command from API response")


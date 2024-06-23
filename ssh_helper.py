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
            {"role": "user", "content": f"Translate the following prompt into a valid bash script that assumes the current directory ('.') if no directory is specified. Only include the bash commands, and ensure there is no commentary or placeholders that need editing: {prompt}"}
        ]
    )

    # Debug: Print the entire API response
    print("API Response:", response)

    # Extract the command part from the response
    command = response['choices'][0]['message']['content']
    print("Extracted Command Content:", command)  # Debug: Print the extracted command content

    # Capture the script content within the triple backticks
    script_content = []
    capture = False

    for line in command.splitlines():
        line = line.strip()
        if line.startswith("```"):
            capture = not capture
            continue
        if capture:
            script_content.append(line)
        elif line:  # Include valid command lines even if they are outside of triple backticks
            script_content.append(line)

    # Filter out any empty lines
    script_content = [cmd for cmd in script_content if cmd]

    print("Captured Script Content:", script_content)  # Debug: Print the captured script content
    return script_content

def create_local_script(script_content, script_path):
    with open(script_path, 'w') as script_file:
        script_file.write('\n'.join(script_content))
    os.chmod(script_path, 0o755)  # Make the script executable

while True:
    prompt = input("Enter your command, English prompt, or type 'exit' to quit: ")
    if prompt.lower() == 'exit':
        print("Exiting...")
        break

    script_content = get_commands_from_prompt(prompt)
    if script_content:
        print("The following script will be created and executed on the remote system:")
        for line in script_content:
            print(line)
        confirmation = input("Do you want to proceed? [Y/n]: ").strip().lower()
        if confirmation in ['', 'y', 'yes']:
            local_script_path = '/tmp/remote_script.sh'
            remote_script_path = '/tmp/remote_script.sh'
            create_local_script(script_content, local_script_path)

            try:
                # SCP the script to the remote system
                scp_command = f"scp -i {key_path} -P {port} {local_script_path} {username}@{hostname}:{remote_script_path}"
                subprocess.run(shlex.split(scp_command), check=True)

                # SSH to the remote system and execute the script
                ssh_command = f"ssh -i {key_path} -p {port} {username}@{hostname} {shlex.quote(f'bash {remote_script_path}')}"
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
        print("Error: Could not extract script from API response")


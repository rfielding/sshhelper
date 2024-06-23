# Assumed file name: ssh_helper.py

import paramiko
import openai
import os
import argparse

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

class SSHHelper:
    def __init__(self, hostname, port, username, key_path):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.key_path = key_path
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        key = paramiko.RSAKey.from_private_key_file(self.key_path)
        self.ssh_client.connect(
            hostname=self.hostname,
            port=self.port,
            username=self.username,
            pkey=key
        )

    def run_command(self, command):
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        return stdout.read().decode(), stderr.read().decode()

    def edit_file(self, file_path, new_content):
        sftp = self.ssh_client.open_sftp()
        with sftp.open(file_path, 'w') as f:
            f.write(new_content)
        sftp.close()

    def read_file(self, file_path):
        sftp = self.ssh_client.open_sftp()
        with sftp.open(file_path, 'r') as f:
            content = f.read().decode()
        sftp.close()
        return content

    def close(self):
        self.ssh_client.close()

def main():
    parser = argparse.ArgumentParser(description='SSH Helper to interact with an EC2 instance')
    parser.add_argument('--hostname', required=True, help='EC2 hostname')
    parser.add_argument('--port', required=True, type=int, help='EC2 port')
    parser.add_argument('--username', required=True, help='EC2 username')
    parser.add_argument('--key_path', required=True, help='Path to the SSH private key file')

    args = parser.parse_args()

    ssh_helper = SSHHelper(args.hostname, args.port, args.username, args.key_path)
    ssh_helper.connect()

    while True:
        user_input = input("Enter your command or type 'exit' to quit: ")
        if user_input.lower() == 'exit':
            break

        if user_input.startswith("edit "):
            _, file_path = user_input.split(maxsplit=1)
            print("Enter the new content for the file. End input with Ctrl-D:")
            new_content = []
            while True:
                try:
                    line = input()
                except EOFError:
                    break
                new_content.append(line)
            new_content = "\n".join(new_content)
            ssh_helper.edit_file(file_path, new_content)
            print(f"File {file_path} updated.")

        elif user_input.startswith("read "):
            _, file_path = user_input.split(maxsplit=1)
            content = ssh_helper.read_file(file_path)
            print(f"Content of {file_path}:\n{content}")

        else:
            stdout, stderr = ssh_helper.run_command(user_input)
            if stderr:
                print("Error:", stderr)
            else:
                print("Output:", stdout)
                assistance_prompt = f"I ran the following command: {user_input}\nHere is the output: {stdout}\nPlease assist me with the next steps."
                assistance = get_assistance(assistance_prompt)
                print("Assistance:", assistance)

    ssh_helper.close()

if __name__ == "__main__":
    main()


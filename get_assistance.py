import paramiko
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

    def close(self):
        self.ssh_client.close()

def main():
    ec2_hostname = "ec2-54-205-159-153.compute-1.amazonaws.com"
    ec2_port = 22
    ec2_username = "ubuntu"
    ec2_key_path = "/home/rfielding/.ssh/sshhelper.pem"  # Absolute path to the key file

    ssh_helper = SSHHelper(ec2_hostname, ec2_port, ec2_username, ec2_key_path)
    ssh_helper.connect()

    while True:
        user_input = input("Enter your command or type 'exit' to quit: ")
        if user_input.lower() == 'exit':
            break

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


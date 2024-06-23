# SSHHelper

SSHHelper is a Go-based tool designed to simplify the process of interacting with remote servers via SSH. It utilizes the OpenAI API to translate natural language commands into executable scripts, facilitating seamless management and automation of remote servers. This tool is ideal for developers familiar with Go who want to leverage the power of OpenAI's language model for SSH operations.

## Features

- Translate natural language commands into executable scripts.
- Execute scripts on remote servers via SSH.
- Supports both Bash and Python scripts.
- Automatically handles current directory and environment variables.

## Prerequisites

- Go installed on your machine.
- An OpenAI API key.
- SSH access to the remote server with a valid private key.

## Installation

1. Clone the repository:
   git clone https://github.com/rfielding/sshlelper.git
   cd sshhelper

2. Install dependencies:
   go get -u github.com/go-resty/resty/v2

3. Build the project:
   go build -o sshhelper

## Configuration

1. Set your OpenAI API key as an environment variable:
   export OPENAI_API_KEY=your_openai_api_key

2. Prepare your SSH credentials (hostname, port, username, and key path).

## Usage

Run SSHHelper with the required flags:

./sshhelper --hostname <hostname> --port <port> --username <username> --key_path <path_to_private_key>

Example:
./sshhelper --hostname example.com --port 22 --username user --key_path ~/.ssh/id_rsa

### Commands

Once the program is running, you can enter natural language commands. The tool will translate these commands into scripts and execute them on the remote server. For example:

- Resetting a Git repository:
  Chat> reset my Git repository

- Listing files in a directory:
  Chat> list files in /home/user

- Running a Python script:
  Chat> run myscript.py in Python

If you want to talk directly to the assistant without executing an SSH command, prefix your command with !. For example:

Chat> !What is the current weather in New York?

### Example Session

Chat> reset my Git repository
The following script will be created and executed on the remote system:
#!/bin/bash
cd /home/user/myrepo
git fetch
git reset --hard origin/main
Output:
HEAD is now at 2ca40f0 Update README.md

Chat> list files in /home/user
The following script will be created and executed on the remote system:
#!/bin/bash
ls /home/user
Output:
file1.txt
file2.txt
...

## Contributing

Contributions are welcome! Please fork the repository and submit pull requests.

## License

This project is licensed under the MIT License.

---

For further questions or support, feel free to open an issue on GitHub.


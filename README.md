sshhelper
=========

This is a test if the OpenAI API. It takes englsh commands, and turns them into bash commands to run in a remote SSH server that you provide it access to.  You will need:

- An OpenAI API key, so that you can be billed for your API calls
- An ssh server to ssh into, like an EC2 Linux instance. I used a simple Ubuntu instance.

The end goal is to stop copy/pasting with ChatGPT. I want it to edit files, and check its answers.  Given this, I can ask for things like: "make the tests pass", or "figure out the python dependencies and get this program to run".

You will need to plugin parameters into a script called `./run_ssh_helper.sh`

that looks like:

```
> cat run_ssh_helper.sh 
#!/bin/bash

python3 ./ssh_helper.py \
       	--hostname ec2-23-25-193-13.compute-1.amazonaws.com \
	--port 22 \
	--username ubuntu \
	--key_path /home/rfielding/.ssh/sshhelper.pem 
```

This should be enough information to do your own bash script with some name like `logintomyec2`:

```
#!/bin/bash

ssh -i /home/rfielding/.ssh/sshhelper.pem ubuntu@ec2-23-25-193-13.compute-1.amazonaws.com -P 22
```

That ridiculous hostname is just an EC2-ism. You will need the ssh key and hostname to know how to login. If you can login and do a simple `ls` command, then you are ready to go.	

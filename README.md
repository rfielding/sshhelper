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

Example
===========


```
 ./run_ssh_helper.sh 
OpenAI> are there any braille related projects somewhere under this directory?
API Response: {
  "id": "chatcmpl-9d8cnm1ehVPsXZZV5YI1vjRiH7cyK",
  "object": "chat.completion",
  "created": 1719114973,
  "model": "gpt-3.5-turbo-0125",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "grep -r \"braille\" ."
      },
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 32,
    "completion_tokens": 8,
    "total_tokens": 40
  },
  "system_fingerprint": null
}
Extracted Command Content: grep -r "braille" .
Captured Commands: ['grep -r "braille" .']
ubuntu@ec2-54-205-159-153.compute-1.amazonaws.com:22:
grep -r "braille" .
Continue? [Y/Enter/n]: 
Output:
 ./github.com/rfielding/mf/ff/create_brl_font.py:font.fontname = "asciibraille"
./github.com/rfielding/mf/ff/create_brl_font.py:def draw_braille_cell(pen, dots):
./github.com/rfielding/mf/ff/create_brl_font.py:    draw_braille_cell(pen, dots)
./github.com/rfielding/mf/ff/create_brl_font.py:    font.generate("asciibraille.ttf")
...
```
			


	

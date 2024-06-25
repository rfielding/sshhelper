package main

import (
	"bufio"
	"flag"
	"fmt"
	"github.com/go-resty/resty/v2"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

const apiURL = "https://api.openai.com/v1/chat/completions"

type OpenAIMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type OpenAIRequest struct {
	Model    string          `json:"model"`
	Messages []OpenAIMessage `json:"messages"`
}

type OpenAIResponse struct {
	Choices []struct {
		Message OpenAIMessage `json:"message"`
	} `json:"choices"`
}

func main() {
	// Set up argument parsing
	hostname := flag.String("hostname", "", "The SSH hostname")
	port := flag.Int("port", 0, "The SSH port")
	username := flag.String("username", "", "The SSH username")
	keyPath := flag.String("key_path", "", "The path to the SSH private key")
	flag.Parse()

	if *hostname == "" || *port == 0 || *username == "" || *keyPath == "" {
		log.Fatal("hostname, port, username, and key_path are required")
	}

	apiKey := os.Getenv("OPENAI_API_KEY")
	if apiKey == "" {
		log.Fatal("Please set OPENAI_API_KEY environment variable")
	}

	client := resty.New()
	var conversation []OpenAIMessage
	currentDirectory := "/home/" + *username
	envVars := make(map[string]string)

	scanner := bufio.NewScanner(os.Stdin)

	for {
		fmt.Printf("%s@%s:%d> ", *username, *hostname, *port)
		if !scanner.Scan() {
			break
		}
		prompt := scanner.Text()

		if strings.ToLower(prompt) == "exit" {
			fmt.Println("Exiting...")
			break
		}

		if strings.HasPrefix(prompt, "!") {
			// Treat this as a conversation with the assistant, not an SSH command
			conversation = append(conversation, OpenAIMessage{Role: "user", Content: strings.TrimPrefix(prompt, "!")})
			response, err := talkToAssistant(client, apiKey, conversation)
			if err != nil {
				log.Printf("Error talking to assistant: %v\n", err)
				continue
			}
			fmt.Println("Assistant:", response)
			conversation = append(conversation, OpenAIMessage{Role: "assistant", Content: response})
		} else {
			// Treat this as an SSH command
			conversation = append(conversation, OpenAIMessage{Role: "user", Content: prompt})

			scriptContent, err := getCommandsFromPrompt(client, apiKey, conversation, currentDirectory, envVars)
			if err != nil {
				log.Printf("Error getting commands from prompt: %v\n", err)
				continue
			}

			if len(scriptContent) > 0 {
				if true {
					localScriptPath := "/tmp/remote_script"
					remoteScriptPath := "/tmp/remote_script"
					if err := createLocalScript(scriptContent, localScriptPath, currentDirectory, envVars); err != nil {
						log.Printf("Error creating local script: %v\n", err)
						continue
					}

					output, err := executeRemoteScript(*hostname, *port, *username, *keyPath, localScriptPath, remoteScriptPath)
					if err != nil {
						log.Printf("Error executing remote script: %v\n", err)
					} else {
						fmt.Println("Output:\n", output)
						analyzeAndDescribeOutput(client, apiKey, output)
						// Update current directory and environment variables based on the script
						updateState(scriptContent, &currentDirectory, envVars)
					}
				} else {
					fmt.Println("Operation cancelled.")
				}
			} else {
				fmt.Println("Error: Could not extract script from API response")
			}
		}
	}
}

func talkToAssistant(client *resty.Client, apiKey string, conversation []OpenAIMessage) (string, error) {
	requestBody := OpenAIRequest{
		Model:    "gpt-3.5-turbo",
		Messages: conversation,
	}

	var response OpenAIResponse
	resp, err := client.R().
		SetHeader("Content-Type", "application/json").
		SetHeader("Authorization", fmt.Sprintf("Bearer %s", apiKey)).
		SetBody(requestBody).
		SetResult(&response).
		Post(apiURL)

	if err != nil {
		return "", fmt.Errorf("error making API request: %w", err)
	}

	if resp.IsError() {
		return "", fmt.Errorf("API request failed with status: %s", resp.Status())
	}

	return response.Choices[0].Message.Content, nil
}

func getCommandsFromPrompt(client *resty.Client, apiKey string, conversation []OpenAIMessage, currentDirectory string, envVars map[string]string) ([]string, error) {
	conversation = append(conversation, OpenAIMessage{
		Role:    "system",
		Content: "Translate prompts into an executable script enclosed within triple backticks at beginning of a line, followed by language name, like github markdown. Python3 and bash are acceptable choices. Ensure that the script requires no editing before being run. In particular, made-up paths like /path/to cannot work, and should default to current directory in such cases. /tmp/remote_script can be in python3 or bash. Scripts always need a shebang at the top. The current working directory is " + currentDirectory + ".",
	})

	requestBody := OpenAIRequest{
		Model:    "gpt-3.5-turbo",
		Messages: conversation,
	}

	var response OpenAIResponse
	resp, err := client.R().
		SetHeader("Content-Type", "application/json").
		SetHeader("Authorization", fmt.Sprintf("Bearer %s", apiKey)).
		SetBody(requestBody).
		SetResult(&response).
		Post(apiURL)

	if err != nil {
		return nil, fmt.Errorf("error making API request: %w", err)
	}

	if resp.IsError() {
		return nil, fmt.Errorf("API request failed with status: %s", resp.Status())
	}

	command := response.Choices[0].Message.Content
	conversation = append(conversation, response.Choices[0].Message)
	scriptContent := extractScriptContent(command)

	return scriptContent, nil
}

func extractScriptContent(command string) []string {
	var scriptContent []string
	lines := strings.Split(command, "\n")
	capture := false

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "```") {
			capture = !capture
			continue
		}
		if capture {
			scriptContent = append(scriptContent, line)
		}
	}

	return scriptContent
}

func createLocalScript(scriptContent []string, scriptPath, currentDirectory string, envVars map[string]string) error {
	script := strings.Join(scriptContent, "\n")
	prepend := ""
	for key, value := range envVars {
		prepend += fmt.Sprintf("export %s=\"%s\"\n", key, value)
	}
	prepend += fmt.Sprintf("cd %s\n", currentDirectory)
	script = prepend + script

	if err := os.WriteFile(scriptPath, []byte(script), 0755); err != nil {
		return fmt.Errorf("unable to write script file: %w", err)
	}
	return nil
}

func executeRemoteScript(hostname string, port int, username, keyPath, localScriptPath, remoteScriptPath string) (string, error) {
	scpCmd := exec.Command("scp", "-i", keyPath, "-P", fmt.Sprintf("%d", port), localScriptPath, fmt.Sprintf("%s@%s:%s", username, hostname, remoteScriptPath))
	if output, err := scpCmd.CombinedOutput(); err != nil {
		return "", fmt.Errorf("error copying script to remote: %s, output: %s", err, string(output))
	}

	sshCmd := exec.Command("ssh", "-i", keyPath, "-p", fmt.Sprintf("%d", port), fmt.Sprintf("%s@%s", username, hostname), fmt.Sprintf("bash %s", remoteScriptPath))
	sshOutput, err := sshCmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("error executing remote script: %s, output: %s", err, string(sshOutput))
	}

	return string(sshOutput), nil
}

func updateState(scriptContent []string, currentDirectory *string, envVars map[string]string) {
	for _, line := range scriptContent {
		if strings.HasPrefix(line, "cd ") {
			newDir := strings.TrimSpace(strings.TrimPrefix(line, "cd "))
			if !filepath.IsAbs(newDir) {
				newDir = filepath.Join(*currentDirectory, newDir)
			}
			absPath, err := filepath.Abs(newDir)
			if err == nil {
				*currentDirectory = absPath
			}
		} else if strings.HasPrefix(line, "export ") {
			parts := strings.SplitN(strings.TrimPrefix(line, "export "), "=", 2)
			if len(parts) == 2 {
				envVars[parts[0]] = parts[1]
			}
		}
	}
}

func analyzeAndDescribeOutput(client *resty.Client, apiKey, output string) {
	conversation := []OpenAIMessage{
			{Role: "system", Content: "Analyze and describe the following output."},
			{Role: "user", Content: output},
	}
	requestBody := OpenAIRequest{
		Model:    "gpt-3.5-turbo",
		Messages: conversation,
	}

	var response OpenAIResponse
	resp, err := client.R().
		SetHeader("Content-Type", "application/json").
		SetHeader("Authorization", fmt.Sprintf("Bearer %s", apiKey)).
		SetBody(requestBody).
		SetResult(&response).
		Post(apiURL)

	if err != nil {
		log.Printf("Error analyzing output: %v\n", err)
		return
	}

	if resp.IsError() {
		log.Printf("API request failed with status: %s", resp.Status())
		return
	}

	description := response.Choices[0].Message.Content
	fmt.Println("Analysis:\n", description)
}


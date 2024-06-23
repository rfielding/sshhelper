package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"

	"github.com/go-resty/resty/v2"
)

const apiURL = "https://api.openai.com/v1/chat/completions"

type OpenAIResponse struct {
	Choices []struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
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

	for {
		fmt.Print("Enter your command, English prompt, or type 'exit' to quit: ")
		var prompt string
		fmt.Scanln(&prompt)

		if strings.ToLower(prompt) == "exit" {
			fmt.Println("Exiting...")
			break
		}

		scriptContent, err := getCommandsFromPrompt(client, apiKey, prompt)
		if err != nil {
			log.Printf("Error getting commands from prompt: %v\n", err)
			continue
		}

		if len(scriptContent) > 0 {
			fmt.Println("The following script will be created and executed on the remote system:")
			for _, line := range scriptContent {
				fmt.Println(line)
			}

			fmt.Print("Do you want to proceed? [Y/n]: ")
			var confirmation string
			fmt.Scanln(&confirmation)
			confirmation = strings.ToLower(strings.TrimSpace(confirmation))
			if confirmation == "" || confirmation == "y" || confirmation == "yes" {
				localScriptPath := "/tmp/remote_script.sh"
				remoteScriptPath := "/tmp/remote_script.sh"
				if err := createLocalScript(scriptContent, localScriptPath); err != nil {
					log.Printf("Error creating local script: %v\n", err)
					continue
				}

				if err := executeRemoteScript(*hostname, *port, *username, *keyPath, localScriptPath, remoteScriptPath); err != nil {
					log.Printf("Error executing remote script: %v\n", err)
				}
			} else {
				fmt.Println("Operation cancelled.")
			}
		} else {
			fmt.Println("Error: Could not extract script from API response")
		}
	}
}

func getCommandsFromPrompt(client *resty.Client, apiKey, prompt string) ([]string, error) {
	requestBody := map[string]interface{}{
		"model": "gpt-3.5-turbo",
		"messages": []map[string]string{
			{"role": "user", "content": fmt.Sprintf("Translate the following prompt into a valid bash script that assumes the current directory ('.') if no directory is specified. Only include the bash commands, and ensure there is no commentary or placeholders that need editing: %s", prompt)},
		},
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
		if capture || line != "" {
			scriptContent = append(scriptContent, line)
		}
	}

	return scriptContent
}

func createLocalScript(scriptContent []string, scriptPath string) error {
	script := strings.Join(scriptContent, "\n")
	if err := os.WriteFile(scriptPath, []byte(script), 0755); err != nil {
		return fmt.Errorf("unable to write script file: %w", err)
	}
	return nil
}

func executeRemoteScript(hostname string, port int, username, keyPath, localScriptPath, remoteScriptPath string) error {
	scpCmd := exec.Command("scp", "-i", keyPath, "-P", fmt.Sprintf("%d", port), localScriptPath, fmt.Sprintf("%s@%s:%s", username, hostname, remoteScriptPath))
	if output, err := scpCmd.CombinedOutput(); err != nil {
		return fmt.Errorf("error copying script to remote: %s, output: %s", err, string(output))
	}

	sshCmd := exec.Command("ssh", "-i", keyPath, "-p", fmt.Sprintf("%d", port), fmt.Sprintf("%s@%s", username, hostname), fmt.Sprintf("bash %s", remoteScriptPath))
	sshOutput, err := sshCmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("error executing remote script: %s, output: %s", err, string(sshOutput))
	}

	fmt.Println("Output:\n", string(sshOutput))
	return nil
}


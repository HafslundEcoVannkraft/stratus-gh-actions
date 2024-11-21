import os
import sys
import json
import requests
import argparse

def main():
    parser = argparse.ArgumentParser(description="Generate release notes using Azure OpenAI")
    parser.add_argument('--draft', type=bool, default=True, help="Whether to create a draft release")
    parser.add_argument('--prerelease', type=bool, default=True, help="Whether to mark the release as a prerelease")
    parser.add_argument('--context', type=str, default="", help="Additional context for the release notes")

    args = parser.parse_args()

    # Environment variables
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    client_id = os.getenv("AZURE_CLIENT_ID")
    tenant_id = os.getenv("AZURE_TENANT_ID")
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")

    # Prepare the payload
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a professional technical writer specializing in generating concise and consistent release notes..."
            },
            {
                "role": "user",
                "content": f"Generate release notes. Additional context: {args.context}"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('AZURE_OPENAI_API_KEY')}"
    }

    # Make the API request
    try:
        response = requests.post(
            f"{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Save the response to a file
    response_json = response.json()
    release_notes = response_json['choices'][0]['message']['content']

    with open("release_notes.md", "w") as f:
        f.write(release_notes)

    print("Release notes successfully generated and saved to release_notes.md")

if __name__ == "__main__":
    main()
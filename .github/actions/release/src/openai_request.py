import os
import json
import sys
import base64
import requests
from typing import Optional

def call_openai_api(
    git_diff: str,
    commit_messages: str,
    pr_titles: str,
    append_context: str = "",
    temperature: float = 0.2,
    max_tokens: int = 4000,
    top_p: float = 1.0,
    frequency_penalty: float = 0.1,
    presence_penalty: float = 0.1,
    response_format: str = "text",
    seed: Optional[int] = None
) -> str:
    """Call Azure OpenAI API to generate release notes."""

    # Get environment variables
    endpoint = os.environ['AZURE_OPENAI_ENDPOINT']
    deployment = os.environ['AZURE_OPENAI_DEPLOYMENT_NAME']
    api_version = os.environ['AZURE_OPENAI_API_VERSION']
    auth_header = os.environ['AUTH_HEADER']

    # Parse authentication header
    auth_type, auth_value = auth_header.split(': ')
    headers = {
        'Content-Type': 'application/json',
        auth_type: auth_value
    }

    # Prepare request body
    request_body = {
        "messages": [
            {
                "role": "system",
                "content": "You are a professional technical writer and code expert specializing in generating concise and consistent release notes for software releases based on inputs from Base64-encoded git diff, commit messages, pull-request messages, and titles. Decode the Base64 strings before analyzing it."
            },
            {
                "role": "user",
                "content": f"""Generate a software release note based on a deep code and feature analyze of this full content. By default Include:
1. A title: # Release Note, do not include version information as this will be added automaticly within GitHub.
2. A top section ##Summary.
3. Sections for ### New Features, ### Bug Fixes and ### Improvements if relevant, this default structure can be overriden by the Additional context below.
- Additional context: {append_context}
- Git diff base64: {git_diff}
- Commit messages base64: {commit_messages}
- PR titles base64: {pr_titles}"""
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty
    }

    # Add optional parameters
    if response_format != "text":
        request_body["response_format"] = {"type": response_format}
    if seed is not None:
        request_body["seed"] = seed

    # Make API call
    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions"
    response = requests.post(
        f"{url}?api-version={api_version}",
        headers=headers,
        json=request_body
    )

    # Handle response
    if response.status_code != 200:
        print(f"Error: {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
        sys.exit(1)

    content = response.json()['choices'][0]['message']['content']
    return content

if __name__ == "__main__":
    # Get input parameters from command line arguments
    args = json.loads(sys.argv[1])

    # Call API and write output
    content = call_openai_api(**args)

    # Write to file
    with open('release_notes.md', 'w') as f:
        f.write(content)

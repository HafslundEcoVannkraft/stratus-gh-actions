# Hello World Composite Action

A simple GitHub composite action that prints a hello world message. This action is part of our monorepo collection of reusable GitHub Actions.

## Features

- 🚀 Lightweight and fast execution
- 🔧 Simple bash script implementation
- 📦 Easy to integrate into existing workflows
- 🎯 Perfect for testing and learning GitHub Actions

## Usage

```yaml
name: Hello World Workflow

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  hello:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Say Hello
        uses: HafslundEcoVannkraft/stratus-gh-actions/hello-world@v3
```

## Location in Monorepo

```
repository-root/
├── hello-world/              # This action
│   ├── README.md
│   ├── action.yml
│   └── entrypoint.sh
├── release/                  # Release action
├── build-scope-analyzer/     # Build scope analyzer action
└── other-actions/            # Other composite actions
```

## File Permissions

Make sure the entrypoint script has executable permissions:

```bash
git update-index --chmod=+x hello-world/entrypoint.sh
```

## Inputs

This action doesn't require any inputs.

## Outputs

This action doesn't produce any outputs. It simply prints "Hello world from stratus-gh-actions composite action" to the workflow logs.

## Examples

### Basic Usage

```yaml
- name: Say Hello
  uses: HafslundEcoVannkraft/stratus-gh-actions/hello-world@v3
```

### Using Specific Version

While you can use specific tags or commit SHAs, in a monorepo it's common to reference the main branch or specific releases:

```yaml
# Using main branch
- uses: HafslundEcoVannkraft/stratus-gh-actions/hello-world@v3

# Using a specific release
- uses: HafslundEcoVannkraft/stratus-gh-actions/hello-world@v3

# Using a specific commit
- uses: HafslundEcoVannkraft/stratus-gh-actions/hello-world@v3
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT

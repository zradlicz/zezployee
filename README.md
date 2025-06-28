# Zezployee

A CLI tool that helps you select GitHub issues and automatically solve them using Claude Code.

## Features

- 🔍 Fetch open GitHub issues from your repository
- 📋 Interactive issue selection with rich formatting
- 🤖 Automatic issue solving with Claude Code
- 🔄 Automatic pull request creation
- ✅ Automatic issue closing

## Installation

```bash
pip install -e .
```

## Setup

1. Get a GitHub Personal Access Token with repository permissions
2. Set it as an environment variable:
   ```bash
   export GITHUB_TOKEN=your_token_here
   ```

## Usage

Navigate to your git repository and run:

```bash
zezployee
```

Or provide the token directly:

```bash
zezployee --token your_token_here
```

## How it works

1. **Issue Selection**: Displays all open issues in a formatted table
2. **Branch Creation**: Creates a new branch for the selected issue
3. **Claude Code Integration**: Runs Claude Code with a detailed prompt about the issue
4. **Pull Request**: Creates a PR with the changes and links it to the issue
5. **Issue Closure**: Automatically closes the original issue

## Requirements

- Python 3.8+
- Git repository with GitHub remote
- Claude Code CLI installed
- GitHub Personal Access Token

## Dependencies

- `click`: CLI framework
- `PyGithub`: GitHub API client
- `rich`: Rich terminal formatting
- `requests`: HTTP requests

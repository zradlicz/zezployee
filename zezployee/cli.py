#!/usr/bin/env python3
"""CLI interface for zezployee"""

import click
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

from .github_client import GitHubClient
from .issue_selector import IssueSelector
from .claude_integration import ClaudeIntegration

# Load environment variables from .env file
load_dotenv()


@click.command()
@click.option('--token', help='GitHub token (or set GITHUB_TOKEN env var)')
def main(token):
    """Select a GitHub issue and solve it with Claude Code"""
    try:
        # Check if we're in a git repo
        if not Path('.git').exists():
            click.echo("Error: Must be run from a git repository root", err=True)
            sys.exit(1)
        
        # Get GitHub token
        github_token = token or os.getenv('GITHUB_TOKEN')
        if not github_token:
            click.echo("Error: GitHub token required. Set GITHUB_TOKEN env var or use --token", err=True)
            sys.exit(1)
        
        # Initialize components
        github_client = GitHubClient(github_token)
        issue_selector = IssueSelector()
        claude_integration = ClaudeIntegration()
        
        # Get repository info
        repo_info = github_client.get_repo_info()
        click.echo(f"Repository: {repo_info['full_name']}")
        
        # Fetch and display issues
        issues = github_client.get_open_issues()
        if not issues:
            click.echo("No open issues found.")
            return
        
        # Select issue
        selected_issue = issue_selector.select_issue(issues)
        if not selected_issue:
            click.echo("No issue selected.")
            return
        
        click.echo(f"Selected issue #{selected_issue['number']}: {selected_issue['title']}")
        
        # Create branch for the issue
        branch_name = f"issue-{selected_issue['number']}"
        github_client.create_branch(branch_name)
        
        # Run Claude Code
        claude_result = claude_integration.solve_issue(selected_issue)
        
        if claude_result['success']:
            # Show execution stats
            if 'cost_usd' in claude_result:
                click.echo(f"💰 Cost: ${claude_result['cost_usd']:.4f}")
            if 'turns' in claude_result:
                click.echo(f"🔄 Turns: {claude_result['turns']}")
            
            # Create PR
            pr_url = github_client.create_pull_request(
                branch_name, 
                selected_issue, 
                claude_result['changes']
            )
            
            # Close issue
            github_client.close_issue(selected_issue['number'])
            
            click.echo(f"✅ Pull request created: {pr_url}")
            click.echo(f"✅ Issue #{selected_issue['number']} closed")
        else:
            click.echo(f"❌ Claude Code failed: {claude_result['error']}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
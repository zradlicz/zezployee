"""GitHub API client for zezployee"""

import os
import subprocess
from github import Github
from typing import List, Dict, Any


class GitHubClient:
    def __init__(self, token: str):
        self.github = Github(token)
        self.repo = None
        self._setup_repo()
    
    def _setup_repo(self):
        """Get repository info from git remote"""
        try:
            # Get remote URL
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=True
            )
            remote_url = result.stdout.strip()
            
            # Parse GitHub repo from URL
            if 'github.com' in remote_url:
                if remote_url.startswith('git@'):
                    # SSH format: git@github.com:owner/repo.git
                    repo_part = remote_url.split(':')[1].replace('.git', '')
                else:
                    # HTTPS format: https://github.com/owner/repo.git
                    repo_part = remote_url.split('github.com/')[1].replace('.git', '')
                
                self.repo = self.github.get_repo(repo_part)
            else:
                raise ValueError("Not a GitHub repository")
                
        except subprocess.CalledProcessError:
            raise ValueError("Could not get git remote URL")
    
    def get_repo_info(self) -> Dict[str, Any]:
        """Get repository information"""
        return {
            'full_name': self.repo.full_name,
            'name': self.repo.name,
            'owner': self.repo.owner.login,
            'url': self.repo.html_url
        }
    
    def get_open_issues(self) -> List[Dict[str, Any]]:
        """Get all open issues for the repository"""
        issues = []
        for issue in self.repo.get_issues(state='open'):
            # Skip pull requests (they appear as issues in GitHub API)
            if issue.pull_request is None:
                issues.append({
                    'number': issue.number,
                    'title': issue.title,
                    'body': issue.body or '',
                    'labels': [label.name for label in issue.labels],
                    'assignee': issue.assignee.login if issue.assignee else None,
                    'created_at': issue.created_at,
                    'url': issue.html_url
                })
        return issues
    
    def create_branch(self, branch_name: str) -> None:
        """Create and checkout a new branch"""
        try:
            # Get current branch to base new branch on
            current_branch = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
            # Create and checkout new branch
            subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create branch {branch_name}: {e}")
    
    def create_pull_request(self, branch_name: str, issue: Dict[str, Any], changes: str) -> str:
        """Create a pull request for the issue"""
        title = f"Fix issue #{issue['number']}: {issue['title']}"
        
        body = f"""Fixes #{issue['number']}

## Changes Made
{changes}

## Issue Description
{issue['body'][:500]}{'...' if len(issue['body']) > 500 else ''}

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"""
        
        # Configure Git to use token for authentication
        self._configure_git_auth()
        
        # Push branch to remote
        try:
            subprocess.run(['git', 'push', '-u', 'origin', branch_name], check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to push branch {branch_name}. Make sure your GitHub token has push permissions: {e}")
        
        # Create PR
        pr = self.repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base='main'
        )
        
        return pr.html_url
    
    def _configure_git_auth(self):
        """Configure Git to use GitHub token for authentication"""
        import os
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
        
        # Get the remote URL and convert to token-authenticated HTTPS
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=True
            )
            remote_url = result.stdout.strip()
            
            # Convert SSH to HTTPS with token
            if remote_url.startswith('git@github.com:'):
                # Convert git@github.com:owner/repo.git to https://token@github.com/owner/repo.git
                repo_path = remote_url.replace('git@github.com:', '').replace('.git', '')
                new_url = f"https://{token}@github.com/{repo_path}.git"
                subprocess.run(['git', 'remote', 'set-url', 'origin', new_url], check=True)
                print(f"🔧 Configured Git remote for token authentication")
            elif remote_url.startswith('https://github.com/'):
                # Convert https://github.com/owner/repo.git to https://token@github.com/owner/repo.git  
                repo_path = remote_url.replace('https://github.com/', '').replace('.git', '')
                new_url = f"https://{token}@github.com/{repo_path}.git"
                subprocess.run(['git', 'remote', 'set-url', 'origin', new_url], check=True)
                print(f"🔧 Configured Git remote for token authentication")
                
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Could not configure Git authentication: {e}")
    
    def close_issue(self, issue_number: int) -> None:
        """Close an issue"""
        issue = self.repo.get_issue(issue_number)
        issue.edit(state='closed')
"""Claude Code integration for solving GitHub issues"""

import subprocess
import os
from typing import Dict, Any


class ClaudeIntegration:
    def __init__(self):
        pass
    
    def solve_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Claude Code to solve the given issue"""
        try:
            # Create a prompt for Claude Code
            prompt = self._create_prompt(issue)
            
            # Run Claude Code with the prompt using --print mode
            result = subprocess.run([
                'claude',
                '-p', prompt,
                '--output-format', 'json',
                '--max-turns', '10'
            ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
            
            if result.returncode == 0:
                # Parse JSON response
                import json
                try:
                    response_data = json.loads(result.stdout)
                    if response_data.get('is_error', False):
                        return {
                            'success': False,
                            'error': 'Claude Code execution failed',
                            'output': response_data.get('result', '')
                        }
                    
                    # Get changes made
                    changes = self._get_git_changes()
                    return {
                        'success': True,
                        'changes': changes,
                        'output': response_data.get('result', ''),
                        'session_id': response_data.get('session_id'),
                        'cost_usd': response_data.get('total_cost_usd', 0),
                        'turns': response_data.get('num_turns', 0)
                    }
                except json.JSONDecodeError:
                    # Fallback to text output
                    changes = self._get_git_changes()
                    return {
                        'success': True,
                        'changes': changes,
                        'output': result.stdout
                    }
            else:
                return {
                    'success': False,
                    'error': result.stderr or 'Claude Code failed',
                    'output': result.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Claude Code timed out after 10 minutes'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to run Claude Code: {str(e)}'
            }
    
    def _create_prompt(self, issue: Dict[str, Any]) -> str:
        """Create a prompt for Claude Code based on the issue"""
        prompt = f"""# GitHub Issue #{issue['number']}: {issue['title']}

## Issue Description
{issue['body']}

## Labels
{', '.join(issue['labels']) if issue['labels'] else 'None'}

## Instructions
Please analyze this GitHub issue and implement a solution. Make sure to:

1. Understand the problem described in the issue
2. Implement the necessary code changes
3. Add appropriate tests if needed
4. Ensure the solution follows best practices
5. Make atomic, focused commits

When you're done implementing, please provide a summary of the changes made.
"""
        return prompt
    
    def _get_git_changes(self) -> str:
        """Get a summary of git changes made"""
        try:
            # Get diff of staged changes
            staged_result = subprocess.run([
                'git', 'diff', '--cached', '--stat'
            ], capture_output=True, text=True)
            
            # Get diff of unstaged changes
            unstaged_result = subprocess.run([
                'git', 'diff', '--stat'
            ], capture_output=True, text=True)
            
            # Get list of untracked files
            untracked_result = subprocess.run([
                'git', 'ls-files', '--others', '--exclude-standard'
            ], capture_output=True, text=True)
            
            changes = []
            
            if staged_result.stdout.strip():
                changes.append("**Staged changes:**")
                changes.append(staged_result.stdout.strip())
            
            if unstaged_result.stdout.strip():
                changes.append("**Unstaged changes:**")
                changes.append(unstaged_result.stdout.strip())
            
            if untracked_result.stdout.strip():
                changes.append("**New files:**")
                changes.extend(f"- {f}" for f in untracked_result.stdout.strip().split('\n'))
            
            if not changes:
                changes.append("No changes detected")
            
            return '\n\n'.join(changes)
            
        except subprocess.CalledProcessError:
            return "Could not determine changes"
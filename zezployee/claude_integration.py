"""Claude Code integration for solving GitHub issues"""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from claude_code_sdk import query, ClaudeCodeOptions, Message


class ClaudeIntegration:
    def __init__(self):
        pass
    
    def solve_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Claude Code to solve the given issue"""
        try:
            # Create a prompt for Claude Code
            prompt = self._create_prompt(issue)
            
            # Run Claude Code using the official SDK
            return asyncio.run(self._run_claude_code(prompt))
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to run Claude Code: {str(e)}'
            }
    
    async def _run_claude_code(self, prompt: str) -> Dict[str, Any]:
        """Run Claude Code using the official Python SDK"""
        try:
            messages: List[Message] = []
            
            # Configure Claude Code options
            options = ClaudeCodeOptions(
                max_turns=10,
                cwd=Path.cwd()
            )
            
            # Execute Claude Code query
            async for message in query(prompt=prompt, options=options):
                messages.append(message)
            
            # Find the result message
            result_message = None
            cost_usd = 0
            turns = 0
            session_id = None
            
            for msg in messages:
                if hasattr(msg, 'type') and msg.type == 'result':
                    result_message = msg
                    cost_usd = getattr(msg, 'total_cost_usd', 0)
                    turns = getattr(msg, 'num_turns', 0)
                    session_id = getattr(msg, 'session_id', None)
                    break
            
            if result_message and hasattr(result_message, 'subtype'):
                if result_message.subtype == 'success':
                    # Get changes made
                    changes = self._get_git_changes()
                    return {
                        'success': True,
                        'changes': changes,
                        'output': getattr(result_message, 'result', ''),
                        'session_id': session_id,
                        'cost_usd': cost_usd,
                        'turns': turns,
                        'messages': [self._message_to_dict(msg) for msg in messages]
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Claude Code failed: {result_message.subtype}',
                        'session_id': session_id,
                        'cost_usd': cost_usd,
                        'turns': turns
                    }
            else:
                # No result message found - extract from assistant messages
                assistant_messages = [msg for msg in messages if hasattr(msg, 'type') and msg.type == 'assistant']
                if assistant_messages:
                    changes = self._get_git_changes()
                    last_msg = assistant_messages[-1]
                    output = getattr(last_msg.message, 'content', [])
                    if isinstance(output, list) and output:
                        output_text = output[0].text if hasattr(output[0], 'text') else str(output[0])
                    else:
                        output_text = str(output)
                    
                    return {
                        'success': True,
                        'changes': changes,
                        'output': output_text,
                        'session_id': session_id,
                        'cost_usd': cost_usd,
                        'turns': len(assistant_messages),
                        'messages': [self._message_to_dict(msg) for msg in messages]
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No response from Claude Code'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Claude Code SDK error: {str(e)}'
            }
    
    def _message_to_dict(self, message: Message) -> Dict[str, Any]:
        """Convert a Message object to a dictionary for serialization"""
        result = {'type': getattr(message, 'type', 'unknown')}
        
        # Add common attributes
        for attr in ['session_id', 'subtype', 'total_cost_usd', 'num_turns', 'result']:
            if hasattr(message, attr):
                result[attr] = getattr(message, attr)
        
        return result
    
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
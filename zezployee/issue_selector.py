"""Interactive issue selection interface"""

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from typing import List, Dict, Any, Optional


class IssueSelector:
    def __init__(self):
        self.console = Console()
    
    def select_issue(self, issues: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Display issues and let user select one"""
        if not issues:
            return None
        
        # Display issues in a table
        table = Table(title="Open GitHub Issues")
        table.add_column("#", style="cyan", width=6)
        table.add_column("Title", style="white", width=50)
        table.add_column("Labels", style="yellow", width=20)
        table.add_column("Age", style="green", width=10)
        
        for i, issue in enumerate(issues, 1):
            labels_str = ", ".join(issue['labels'][:3])  # Show first 3 labels
            if len(issue['labels']) > 3:
                labels_str += "..."
            
            # Calculate age
            from datetime import datetime
            age_days = (datetime.now(issue['created_at'].tzinfo) - issue['created_at']).days
            age_str = f"{age_days}d"
            
            table.add_row(
                str(i),
                issue['title'][:47] + "..." if len(issue['title']) > 50 else issue['title'],
                labels_str,
                age_str
            )
        
        self.console.print(table)
        
        # Get user selection
        while True:
            try:
                choice = Prompt.ask(
                    f"\nSelect an issue (1-{len(issues)}) or 'q' to quit",
                    default="1"
                )
                
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(issues):
                    selected = issues[index]
                    
                    # Show issue details
                    self.console.print(f"\n[bold]Issue #{selected['number']}: {selected['title']}[/bold]")
                    if selected['body']:
                        body_preview = selected['body'][:200] + "..." if len(selected['body']) > 200 else selected['body']
                        self.console.print(f"[dim]{body_preview}[/dim]")
                    
                    confirm = Prompt.ask("\nWork on this issue? (y/n)", default="y")
                    if confirm.lower() in ['y', 'yes']:
                        return selected
                    else:
                        continue
                else:
                    self.console.print("[red]Invalid selection. Please try again.[/red]")
                    
            except ValueError:
                self.console.print("[red]Invalid input. Please enter a number or 'q'.[/red]")
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Cancelled.[/yellow]")
                return None
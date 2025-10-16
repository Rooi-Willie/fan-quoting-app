"""
Colored logging utility for deployment scripts
Provides consistent, beautiful console output
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print as rprint
import sys

console = Console()

class Logger:
    """Beautiful logging with rich formatting"""
    
    @staticmethod
    def header(title):
        """Print a header banner"""
        console.print(Panel(f"[bold cyan]{title}[/bold cyan]", expand=False))
    
    @staticmethod
    def step(step_num, total_steps, description):
        """Print a step indicator"""
        console.print(f"[yellow][[/yellow][bold cyan]{step_num}/{total_steps}[/bold cyan][yellow]][/yellow] {description}")
    
    @staticmethod
    def success(message):
        """Print success message"""
        console.print(f"[green]✓[/green] {message}")
    
    @staticmethod
    def error(message):
        """Print error message"""
        console.print(f"[red]✗ ERROR:[/red] {message}")
    
    @staticmethod
    def warning(message):
        """Print warning message"""
        console.print(f"[yellow]⚠ WARNING:[/yellow] {message}")
    
    @staticmethod
    def info(message):
        """Print info message"""
        console.print(f"[cyan]ℹ[/cyan] {message}")
    
    @staticmethod
    def debug(message):
        """Print debug message"""
        console.print(f"[dim]🔍 {message}[/dim]")
    
    @staticmethod
    def command(command):
        """Print command being executed"""
        console.print(f"[dim]$ {command}[/dim]")
    
    @staticmethod
    def section(title):
        """Print section divider"""
        console.print(f"\n[bold magenta]{'='*60}[/bold magenta]")
        console.print(f"[bold magenta]{title.center(60)}[/bold magenta]")
        console.print(f"[bold magenta]{'='*60}[/bold magenta]\n")
    
    @staticmethod
    def table(data, headers):
        """Print data as a table"""
        table = Table(show_header=True, header_style="bold cyan")
        
        for header in headers:
            table.add_column(header)
        
        for row in data:
            table.add_row(*[str(cell) for cell in row])
        
        console.print(table)
    
    @staticmethod
    def confirm(question, default=False):
        """Ask for user confirmation"""
        default_str = "Y/n" if default else "y/N"
        response = console.input(f"[yellow]?[/yellow] {question} [{default_str}]: ")
        
        if not response:
            return default
        
        return response.lower() in ['y', 'yes']
    
    @staticmethod
    def prompt(question, default=None):
        """Prompt for user input"""
        if default:
            response = console.input(f"[cyan]>[/cyan] {question} [dim][{default}][/dim]: ")
            return response if response else default
        else:
            return console.input(f"[cyan]>[/cyan] {question}: ")
    
    @staticmethod
    def spinner(description):
        """Return a progress spinner context manager"""
        return console.status(f"[cyan]{description}...", spinner="dots")
    
    @staticmethod
    def progress_bar():
        """Return a progress bar"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        )
    
    @staticmethod
    def summary(items):
        """Print a summary list"""
        for key, value in items.items():
            console.print(f"  [cyan]{key}:[/cyan] {value}")
    
    @staticmethod
    def exit_with_error(message, code=1):
        """Print error and exit"""
        Logger.error(message)
        sys.exit(code)


# Convenience functions
def log_success(msg): Logger.success(msg)
def log_error(msg): Logger.error(msg)
def log_warning(msg): Logger.warning(msg)
def log_info(msg): Logger.info(msg)
def log_debug(msg): Logger.debug(msg)

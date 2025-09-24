"""
CLI Dashboard for JJ-Git Sync Tool

A lightweight dashboard using Rich to display sync history, security scans,
and AI commit suggestions in a beautiful terminal interface.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from rich import box
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn


class Dashboard:
    """
    CLI Dashboard for displaying JJ-Git Sync Tool status and history.
    """
    
    def __init__(self, data_dir: str = ".jj-git-sync"):
        """
        Initialize the dashboard.
        
        Args:
            data_dir: Directory to store dashboard data
        """
        self.console = Console()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Data files
        self.sync_history_file = self.data_dir / "sync_history.json"
        self.scan_results_file = self.data_dir / "scan_results.json"
        self.ai_suggestions_file = self.data_dir / "ai_suggestions.json"
    
    def log_sync_operation(self, git_dir: str, jj_dir: str, success: bool, 
                          scan_enabled: bool = False, scan_results: Optional[Dict] = None):
        """
        Log a sync operation to history.
        
        Args:
            git_dir: Git repository path
            jj_dir: JJ workspace path
            success: Whether sync was successful
            scan_enabled: Whether security scan was enabled
            scan_results: Security scan results if available
        """
        history = self._load_sync_history()
        
        operation = {
            "timestamp": datetime.now().isoformat(),
            "git_dir": git_dir,
            "jj_dir": jj_dir,
            "success": success,
            "scan_enabled": scan_enabled,
            "scan_results": scan_results
        }
        
        history.insert(0, operation)  # Add to beginning
        history = history[:5]  # Keep only last 5
        
        self._save_sync_history(history)
    
    def log_scan_results(self, git_dir: str, secrets: List[Dict], format_type: str = "human"):
        """
        Log security scan results.
        
        Args:
            git_dir: Git repository path
            secrets: List of detected secrets
            format_type: Output format (human/json)
        """
        scan_data = {
            "timestamp": datetime.now().isoformat(),
            "git_dir": git_dir,
            "secrets": secrets,
            "format": format_type,
            "total_secrets": len(secrets),
            "critical_high": len([s for s in secrets if s.get('severity') in ['CRITICAL', 'HIGH']])
        }
        
        self._save_scan_results(scan_data)
    
    def log_ai_suggestions(self, git_dir: str, suggestions: List[str], style: str = "conventional"):
        """
        Log AI commit message suggestions.
        
        Args:
            git_dir: Git repository path
            suggestions: List of suggested commit messages
            style: Commit message style used
        """
        ai_data = {
            "timestamp": datetime.now().isoformat(),
            "git_dir": git_dir,
            "suggestions": suggestions,
            "style": style,
            "count": len(suggestions)
        }
        
        self._save_ai_suggestions(ai_data)
    
    def display_dashboard(self):
        """Display the main dashboard."""
        self.console.clear()
        
        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(self._create_header(), size=3),
            Layout(self._create_main_content(), name="main"),
            Layout(self._create_footer(), size=3)
        )
        
        layout["main"].split_row(
            Layout(self._create_sync_history_panel(), name="left"),
            Layout(self._create_right_panel(), name="right")
        )
        
        self.console.print(layout)
    
    def _create_header(self) -> Panel:
        """Create the dashboard header."""
        title = Text("🚀 JJ-Git Sync Tool Dashboard", style="bold blue")
        subtitle = Text("Real-time sync, security, and AI assistance", style="dim")
        
        header_content = Align.center(title + "\n" + subtitle)
        return Panel(header_content, box=box.DOUBLE, style="blue")
    
    def _create_footer(self) -> Panel:
        """Create the dashboard footer."""
        footer_text = Text("Press Ctrl+C to exit • Use 'python sync.py --help' for commands", style="dim")
        footer_content = Align.center(footer_text)
        return Panel(footer_content, box=box.SIMPLE, style="dim")
    
    def _create_main_content(self) -> Layout:
        """Create the main content area."""
        return Layout(name="main")
    
    def _create_sync_history_panel(self) -> Panel:
        """Create the sync history panel."""
        history = self._load_sync_history()
        
        if not history:
            content = Text("No sync operations yet.\nRun 'python sync.py sync' to start!", style="dim")
            return Panel(content, title="📊 Sync History", box=box.ROUNDED)
        
        table = Table(title="📊 Recent Sync Operations", box=box.ROUNDED)
        table.add_column("Time", style="cyan", width=12)
        table.add_column("Status", style="green", width=8)
        table.add_column("Git Dir", style="blue", width=15)
        table.add_column("Scan", style="yellow", width=6)
        
        for op in history[:5]:
            timestamp = datetime.fromisoformat(op["timestamp"])
            time_str = timestamp.strftime("%H:%M:%S")
            
            status = "✅ Success" if op["success"] else "❌ Failed"
            status_style = "green" if op["success"] else "red"
            
            git_dir_short = op["git_dir"].split("/")[-1] if "/" in op["git_dir"] else op["git_dir"]
            scan_status = "🔍 Yes" if op["scan_enabled"] else "⚪ No"
            
            table.add_row(
                time_str,
                Text(status, style=status_style),
                git_dir_short,
                scan_status
            )
        
        return Panel(table, box=box.ROUNDED)
    
    def _create_right_panel(self) -> Layout:
        """Create the right panel with security and AI info."""
        layout = Layout()
        layout.split_column(
            Layout(self._create_security_panel(), name="security"),
            Layout(self._create_ai_panel(), name="ai")
        )
        return layout
    
    def _create_security_panel(self) -> Panel:
        """Create the security scan results panel."""
        scan_data = self._load_scan_results()
        
        if not scan_data:
            content = Text("No security scans yet.\nRun 'python sync.py scan' to start!", style="dim")
            return Panel(content, title="🔒 Security Status", box=box.ROUNDED)
        
        # Create security summary
        total_secrets = scan_data.get("total_secrets", 0)
        critical_high = scan_data.get("critical_high", 0)
        
        if total_secrets == 0:
            status_text = Text("✅ No security issues found", style="green")
        elif critical_high == 0:
            status_text = Text(f"⚠️  {total_secrets} low/medium issues found", style="yellow")
        else:
            status_text = Text(f"🚨 {critical_high} critical/high issues found", style="red")
        
        timestamp = datetime.fromisoformat(scan_data["timestamp"])
        time_str = timestamp.strftime("%H:%M:%S")
        
        content = f"{status_text}\n\nLast scan: {time_str}\nTotal secrets: {total_secrets}"
        
        return Panel(content, title="🔒 Security Status", box=box.ROUNDED)
    
    def _create_ai_panel(self) -> Panel:
        """Create the AI suggestions panel."""
        ai_data = self._load_ai_suggestions()
        
        if not ai_data:
            content = Text("No AI suggestions yet.\nRun 'python sync.py suggest-message' to start!", style="dim")
            return Panel(content, title="🤖 AI Assistant", box=box.ROUNDED)
        
        suggestions = ai_data.get("suggestions", [])
        style = ai_data.get("style", "conventional")
        
        if suggestions:
            # Show first suggestion as example
            main_suggestion = suggestions[0]
            content = f"Style: {style}\n\n💡 Latest suggestion:\n{main_suggestion}"
            
            if len(suggestions) > 1:
                content += f"\n\n+{len(suggestions)-1} more suggestions"
        else:
            content = "No suggestions available"
        
        timestamp = datetime.fromisoformat(ai_data["timestamp"])
        time_str = timestamp.strftime("%H:%M:%S")
        content += f"\n\nLast generated: {time_str}"
        
        return Panel(content, title="🤖 AI Assistant", box=box.ROUNDED)
    
    def _load_sync_history(self) -> List[Dict]:
        """Load sync history from file."""
        if not self.sync_history_file.exists():
            return []
        
        try:
            with open(self.sync_history_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_sync_history(self, history: List[Dict]):
        """Save sync history to file."""
        try:
            with open(self.sync_history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except IOError:
            pass  # Silently fail if can't save
    
    def _load_scan_results(self) -> Optional[Dict]:
        """Load latest scan results from file."""
        if not self.scan_results_file.exists():
            return None
        
        try:
            with open(self.scan_results_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def _save_scan_results(self, scan_data: Dict):
        """Save scan results to file."""
        try:
            with open(self.scan_results_file, 'w') as f:
                json.dump(scan_data, f, indent=2)
        except IOError:
            pass  # Silently fail if can't save
    
    def _load_ai_suggestions(self) -> Optional[Dict]:
        """Load latest AI suggestions from file."""
        if not self.ai_suggestions_file.exists():
            return None
        
        try:
            with open(self.ai_suggestions_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def _save_ai_suggestions(self, ai_data: Dict):
        """Save AI suggestions to file."""
        try:
            with open(self.ai_suggestions_file, 'w') as f:
                json.dump(ai_data, f, indent=2)
        except IOError:
            pass  # Silently fail if can't save


def create_dashboard() -> Dashboard:
    """Create a new dashboard instance."""
    return Dashboard()


def display_quick_status():
    """Display a quick status overview."""
    console = Console()
    dashboard = Dashboard()
    
    # Quick status check
    history = dashboard._load_sync_history()
    scan_data = dashboard._load_scan_results()
    ai_data = dashboard._load_ai_suggestions()
    
    console.print("\n[bold blue]🚀 JJ-Git Sync Tool - Quick Status[/bold blue]")
    console.print("=" * 50)
    
    # Sync status
    if history:
        last_sync = history[0]
        status = "✅" if last_sync["success"] else "❌"
        console.print(f"Last sync: {status} {last_sync['timestamp'][:19]}")
    else:
        console.print("Last sync: [dim]No operations yet[/dim]")
    
    # Security status
    if scan_data:
        total = scan_data.get("total_secrets", 0)
        critical = scan_data.get("critical_high", 0)
        if critical > 0:
            console.print(f"Security: [red]🚨 {critical} critical issues[/red]")
        elif total > 0:
            console.print(f"Security: [yellow]⚠️  {total} issues found[/yellow]")
        else:
            console.print("Security: [green]✅ All clear[/green]")
    else:
        console.print("Security: [dim]No scans yet[/dim]")
    
    # AI status
    if ai_data:
        count = ai_data.get("count", 0)
        console.print(f"AI Assistant: [blue]🤖 {count} suggestions available[/blue]")
    else:
        console.print("AI Assistant: [dim]No suggestions yet[/dim]")
    
    console.print("=" * 50)

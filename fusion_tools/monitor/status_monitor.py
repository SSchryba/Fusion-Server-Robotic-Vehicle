#!/usr/bin/env python3
"""
Terminal-based Fusion Status Monitor
Real-time monitoring of fusion system status with rich formatting
"""

import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.box import ROUNDED

from utils.api_client import FusionAPIClient
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class FusionStatusMonitor:
    """Terminal-based status monitor for fusion system"""
    
    def __init__(self):
        self.console = Console()
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.get_fusion_config()
        
        self.api_client = FusionAPIClient(
            host=self.config.host,
            port=self.config.port,
            timeout=self.config.timeout
        )
        
        self.refresh_interval = self.config.monitor.get('refresh_interval', 5)
        self.display_history = self.config.monitor.get('display_history', 10)
        self.status_history = []
        self.last_update = None
        
    def create_main_panel(self) -> Panel:
        """Create the main status panel"""
        layout = Layout()
        
        # Get current status
        status = self.api_client.get_fusion_status()
        health = self.api_client.get_server_health()
        models = self.api_client.get_available_models()
        hybrids = self.api_client.get_hybrid_models()
        
        # Create status table
        status_table = Table(title="🔬 Fusion System Status", box=ROUNDED)
        status_table.add_column("Metric", style="cyan")
        status_table.add_column("Value", style="yellow")
        status_table.add_column("Status", style="green")
        
        if status:
            status_table.add_row("Fusion Enabled", str(status.fusion_enabled), "✅" if status.fusion_enabled else "❌")
            status_table.add_row("Version", str(status.fusion_version), "📦")
            status_table.add_row("Total Absorptions", str(status.total_absorptions), "🔄")
            status_table.add_row("Hybrid Models", str(status.hybrid_models_created), "🧬")
            status_table.add_row("Next Fusion", f"{status.next_fusion_in_hours}h", "⏰")
            status_table.add_row("Strategy", status.absorption_strategy, "🎯")
        else:
            status_table.add_row("Connection", "Failed", "❌")
        
        # Create models table
        models_table = Table(title="📚 Available Models", box=ROUNDED)
        models_table.add_column("Model", style="cyan")
        models_table.add_column("Type", style="magenta")
        
        for model in models[:10]:  # Show first 10 models
            model_type = "🧠 DeepSeek" if "deepseek" in model.lower() else "🤖 Standard"
            models_table.add_row(model, model_type)
        
        if len(models) > 10:
            models_table.add_row(f"... and {len(models) - 10} more", "")
        
        # Create hybrid models table
        hybrid_table = Table(title="🧬 Hybrid Models", box=ROUNDED)
        hybrid_table.add_column("Name", style="cyan")
        hybrid_table.add_column("Parameters", style="yellow")
        hybrid_table.add_column("Created", style="green")
        
        for hybrid in hybrids[:5]:  # Show first 5 hybrids
            params = hybrid.get('fusion_params', {}).get('total_parameters', 0)
            created = hybrid.get('created_at', '')[:16] if hybrid.get('created_at') else ''
            hybrid_table.add_row(
                hybrid.get('name', 'Unknown'),
                f"{params:,}",
                created
            )
        
        # Create recent activity table
        activity_table = Table(title="📊 Recent Activity", box=ROUNDED)
        activity_table.add_column("Time", style="dim")
        activity_table.add_column("Event", style="cyan")
        activity_table.add_column("Details", style="yellow")
        
        if status and status.recent_absorptions:
            for absorption in status.recent_absorptions[-5:]:
                timestamp = absorption.get('timestamp', '')[:16] if absorption.get('timestamp') else ''
                hybrid_name = absorption.get('hybrid_name', 'Unknown')
                source_models = len(absorption.get('source_models', []))
                
                activity_table.add_row(
                    timestamp,
                    "Model Fusion",
                    f"{hybrid_name} from {source_models} models"
                )
        else:
            activity_table.add_row("--", "No recent activity", "")
        
        # Layout arrangement
        top_row = Columns([status_table, models_table], equal=True)
        bottom_row = Columns([hybrid_table, activity_table], equal=True)
        
        layout.split_row(
            Layout(top_row, name="top"),
            Layout(bottom_row, name="bottom")
        )
        
        return Panel(
            layout,
            title="🚀 Fusion System Monitor",
            subtitle=f"Last Update: {datetime.now().strftime('%H:%M:%S')}",
            border_style="blue"
        )
    
    def create_header_panel(self) -> Panel:
        """Create header panel with system info"""
        header_table = Table.grid(padding=1)
        header_table.add_column(style="bold cyan")
        header_table.add_column(style="bold yellow")
        header_table.add_column(style="bold green")
        
        # Server info
        health = self.api_client.get_server_health()
        server_status = "🟢 Online" if health.get('status') == 'ok' else "🔴 Offline"
        
        header_table.add_row(
            "🖥️  Server:",
            f"{self.config.host}:{self.config.port}",
            server_status
        )
        
        # System health
        if health.get('status') == 'ok':
            system_health = health.get('health', 'unknown')
            health_icon = {"healthy": "💚", "warning": "⚠️", "critical": "🔴"}.get(system_health, "❓")
            header_table.add_row(
                "❤️  Health:",
                system_health.capitalize(),
                health_icon
            )
        
        # Update interval
        header_table.add_row(
            "🔄 Refresh:",
            f"{self.refresh_interval}s",
            "⏱️"
        )
        
        return Panel(
            header_table,
            title="System Information",
            border_style="green"
        )
    
    def create_footer_panel(self) -> Panel:
        """Create footer panel with controls"""
        footer_text = Text()
        footer_text.append("Controls: ", style="bold")
        footer_text.append("Ctrl+C", style="bold red")
        footer_text.append(" to exit | ", style="dim")
        footer_text.append("Auto-refresh: ", style="bold")
        footer_text.append(f"{self.refresh_interval}s", style="yellow")
        
        return Panel(
            footer_text,
            border_style="dim"
        )
    
    def create_layout(self) -> Layout:
        """Create the complete layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(self.create_header_panel(), name="header", size=6),
            Layout(self.create_main_panel(), name="main"),
            Layout(self.create_footer_panel(), name="footer", size=3)
        )
        
        return layout
    
    def update_display(self) -> Layout:
        """Update the display layout"""
        return self.create_layout()
    
    def run(self):
        """Run the monitor"""
        self.console.print("\n🚀 Starting Fusion Status Monitor...\n", style="bold green")
        
        try:
            with Live(self.update_display(), refresh_per_second=1, console=self.console) as live:
                while True:
                    time.sleep(self.refresh_interval)
                    live.update(self.update_display())
                    
        except KeyboardInterrupt:
            self.console.print("\n👋 Monitor stopped by user", style="bold red")
        except Exception as e:
            self.console.print(f"\n❌ Monitor error: {e}", style="bold red")
            logger.error(f"Monitor error: {e}")

def main():
    """Main entry point"""
    monitor = FusionStatusMonitor()
    monitor.run()

if __name__ == "__main__":
    main() 
"""
Admin CLI interface for beta user management.

This module provides administrative commands for managing beta users,
reviewing feedback, and generating usage reports.
"""

import click
import os
import csv
from datetime import datetime
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..web.beta import BetaManager
from ..models.payment import BetaUser, UsageStats, Feedback

console = Console()


@click.group()
def admin():
    """
    Administrative commands for beta user management.
    
    These commands allow administrators to manage beta users,
    review feedback, and generate usage reports.
    """
    pass


@admin.command()
@click.option('--email', '-e', required=True, help='Beta user email address')
@click.option('--notes', '-n', default='', help='Optional notes about the user')
def add_user(email: str, notes: str):
    """Add a new beta user to the whitelist."""
    console.print(Panel(
        Text("Add Beta User", style="bold green"),
        subtitle="Beta User Management"
    ))
    
    try:
        manager = BetaManager()
        
        # Check if user already exists
        if manager.is_beta_user(email):
            console.print(f"[yellow]⚠ User {email} is already in the beta program[/yellow]")
            if not Confirm.ask("Update their information?"):
                return
        
        manager.add_beta_user(email, notes)
        console.print(f"[green]✓ Successfully added beta user: {email}[/green]")
        
        if notes:
            console.print(f"[dim]Notes: {notes}[/dim]")
            
    except Exception as e:
        console.print(f"[red]✗ Error adding beta user: {str(e)}[/red]")


@admin.command()
@click.option('--email', '-e', required=True, help='Beta user email address')
def remove_user(email: str):
    """Remove a beta user from the whitelist."""
    console.print(Panel(
        Text("Remove Beta User", style="bold red"),
        subtitle="Beta User Management"
    ))
    
    try:
        manager = BetaManager()
        
        # Check if user exists
        if not manager.is_beta_user(email):
            console.print(f"[yellow]⚠ User {email} is not in the beta program[/yellow]")
            return
        
        # Get user stats before removal
        stats = manager.get_usage_stats(email)
        
        console.print(f"[yellow]User to remove:[/yellow] {email}")
        console.print(f"[yellow]Total exports:[/yellow] {stats.total_exports}")
        console.print(f"[yellow]Last export:[/yellow] {stats.last_export_date or 'Never'}")
        
        if not Confirm.ask("Are you sure you want to remove this user?"):
            console.print("[dim]Operation cancelled[/dim]")
            return
        
        manager.remove_beta_user(email)
        console.print(f"[green]✓ Successfully removed beta user: {email}[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Error removing beta user: {str(e)}[/red]")


@admin.command()
@click.option('--email', '-e', help='Filter by specific user email')
@click.option('--sort-by', '-s', 
              type=click.Choice(['email', 'added_date', 'total_exports', 'last_export_date']),
              default='added_date', help='Sort users by field')
@click.option('--reverse', '-r', is_flag=True, help='Reverse sort order')
@click.option('--export-csv', help='Export to CSV file')
def list_users(email: Optional[str], sort_by: str, reverse: bool, export_csv: Optional[str]):
    """List all beta users with their statistics."""
    console.print(Panel(
        Text("Beta Users", style="bold blue"),
        subtitle="Current Beta Program Participants"
    ))
    
    try:
        manager = BetaManager()
        users = manager.get_beta_users()
        
        if email:
            users = [user for user in users if email.lower() in user.email.lower()]
            console.print(f"[dim]Filtered by email containing: {email}[/dim]")
        
        if not users:
            console.print("[yellow]No beta users found[/yellow]")
            return
        
        # Sort users
        sort_key_map = {
            'email': lambda u: u.email,
            'added_date': lambda u: u.added_date,
            'total_exports': lambda u: u.total_exports,
            'last_export_date': lambda u: u.last_export_date or datetime.min
        }
        
        users.sort(key=sort_key_map[sort_by], reverse=reverse)
        
        # Display table
        table = Table(title=f"Beta Users ({len(users)} total)")
        table.add_column("Email", style="cyan", width=30)
        table.add_column("Added", style="green", width=12)
        table.add_column("Exports", style="magenta", width=8)
        table.add_column("Last Export", style="yellow", width=12)
        table.add_column("Feedback", style="blue", width=8)
        table.add_column("Notes", style="dim", width=20)
        
        for user in users:
            last_export = user.last_export_date.strftime("%Y-%m-%d") if user.last_export_date else "Never"
            added_date = user.added_date.strftime("%Y-%m-%d")
            notes_truncated = (user.notes[:17] + "...") if len(user.notes) > 20 else user.notes
            
            table.add_row(
                user.email,
                added_date,
                str(user.total_exports),
                last_export,
                str(user.feedback_count),
                notes_truncated
            )
        
        console.print(table)
        
        # Export to CSV if requested
        if export_csv:
            with open(export_csv, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Email', 'Added Date', 'Total Exports', 'Last Export Date', 'Feedback Count', 'Notes'])
                
                for user in users:
                    writer.writerow([
                        user.email,
                        user.added_date.isoformat(),
                        user.total_exports,
                        user.last_export_date.isoformat() if user.last_export_date else '',
                        user.feedback_count,
                        user.notes
                    ])
            
            console.print(f"[green]✓ Exported to CSV: {export_csv}[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Error listing beta users: {str(e)}[/red]")


@admin.command()
@click.option('--email', '-e', required=True, help='Beta user email address')
def user_stats(email: str):
    """Show detailed statistics for a specific beta user."""
    console.print(Panel(
        Text("User Statistics", style="bold cyan"),
        subtitle=f"Beta User: {email}"
    ))
    
    try:
        manager = BetaManager()
        
        # Check if user exists
        if not manager.is_beta_user(email):
            console.print(f"[red]✗ User {email} is not in the beta program[/red]")
            return
        
        # Get user info
        users = manager.get_beta_users()
        user = next((u for u in users if u.email == email), None)
        
        if not user:
            console.print(f"[red]✗ Could not find user data for {email}[/red]")
            return
        
        # Get detailed stats
        stats = manager.get_usage_stats(email)
        
        # Display user info
        info_table = Table(title="User Information")
        info_table.add_column("Field", style="cyan")
        info_table.add_column("Value", style="magenta")
        
        info_table.add_row("Email", user.email)
        info_table.add_row("Added Date", user.added_date.strftime("%Y-%m-%d %H:%M:%S"))
        info_table.add_row("Notes", user.notes or "None")
        
        console.print(info_table)
        
        # Display usage stats
        stats_table = Table(title="Usage Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="magenta")
        
        stats_table.add_row("Total Exports", str(stats.total_exports))
        stats_table.add_row("Last Export", stats.last_export_date.strftime("%Y-%m-%d %H:%M:%S") if stats.last_export_date else "Never")
        stats_table.add_row("Conversations Processed", str(stats.total_conversations_processed))
        stats_table.add_row("Average Export Size", f"{stats.average_export_size_mb:.2f} MB")
        stats_table.add_row("Feedback Submissions", str(user.feedback_count))
        
        console.print(stats_table)
        
        # Display exports by platform
        if stats.exports_by_target:
            platform_table = Table(title="Exports by Platform")
            platform_table.add_column("Platform", style="cyan")
            platform_table.add_column("Count", style="magenta")
            
            for platform, count in stats.exports_by_target.items():
                platform_table.add_row(platform.title(), str(count))
            
            console.print(platform_table)
        
    except Exception as e:
        console.print(f"[red]✗ Error getting user statistics: {str(e)}[/red]")


@admin.command()
@click.option('--email', '-e', help='Filter feedback by user email')
@click.option('--rating', '-r', type=int, help='Filter by rating (1-5)')
@click.option('--platform', '-p', type=click.Choice(['gemini', 'ollama']), help='Filter by target platform')
@click.option('--limit', '-l', type=int, default=20, help='Limit number of results')
@click.option('--export-csv', help='Export feedback to CSV file')
def feedback(email: Optional[str], rating: Optional[int], platform: Optional[str], limit: int, export_csv: Optional[str]):
    """Review feedback from beta users."""
    console.print(Panel(
        Text("Beta User Feedback", style="bold magenta"),
        subtitle="Feedback Review"
    ))
    
    try:
        manager = BetaManager()
        all_feedback = manager.get_all_feedback()
        
        # Apply filters
        filtered_feedback = all_feedback
        
        if email:
            filtered_feedback = [f for f in filtered_feedback if email.lower() in f.email.lower()]
            console.print(f"[dim]Filtered by email containing: {email}[/dim]")
        
        if rating:
            filtered_feedback = [f for f in filtered_feedback if f.rating == rating]
            console.print(f"[dim]Filtered by rating: {rating} stars[/dim]")
        
        if platform:
            filtered_feedback = [f for f in filtered_feedback if f.target_platform == platform]
            console.print(f"[dim]Filtered by platform: {platform}[/dim]")
        
        # Limit results
        filtered_feedback = filtered_feedback[:limit]
        
        if not filtered_feedback:
            console.print("[yellow]No feedback found matching criteria[/yellow]")
            return
        
        console.print(f"[green]Showing {len(filtered_feedback)} feedback entries[/green]")
        
        # Display feedback
        for i, fb in enumerate(filtered_feedback, 1):
            console.print(f"\n[bold cyan]Feedback {i}:[/bold cyan]")
            console.print(f"[yellow]User:[/yellow] {fb.email}")
            console.print(f"[yellow]Date:[/yellow] {fb.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            console.print(f"[yellow]Rating:[/yellow] {'⭐' * fb.rating} ({fb.rating}/5)")
            console.print(f"[yellow]Platform:[/yellow] {fb.target_platform.title()}")
            console.print(f"[yellow]Export ID:[/yellow] {fb.export_id}")
            console.print(f"[yellow]Feedback:[/yellow]")
            console.print(f"  {fb.feedback_text}")
            
            if i < len(filtered_feedback):
                console.print("[dim]" + "─" * 60 + "[/dim]")
        
        # Export to CSV if requested
        if export_csv:
            with open(export_csv, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Email', 'Timestamp', 'Rating', 'Platform', 'Export ID', 'Feedback Text'])
                
                for fb in filtered_feedback:
                    writer.writerow([
                        fb.email,
                        fb.timestamp.isoformat(),
                        fb.rating,
                        fb.target_platform,
                        fb.export_id,
                        fb.feedback_text
                    ])
            
            console.print(f"\n[green]✓ Exported feedback to CSV: {export_csv}[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Error retrieving feedback: {str(e)}[/red]")


@admin.command()
@click.option('--output', '-o', help='Output file for the report (default: beta_report_YYYYMMDD.csv)')
def report(output: Optional[str]):
    """Generate a comprehensive beta program report."""
    console.print(Panel(
        Text("Beta Program Report", style="bold blue"),
        subtitle="Comprehensive Usage Analysis"
    ))
    
    try:
        manager = BetaManager()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating report...", total=None)
            
            # Get all data
            users = manager.get_beta_users()
            all_feedback = manager.get_all_feedback()
            
            progress.update(task, description="Analyzing data...")
            
            # Calculate summary statistics
            total_users = len(users)
            total_exports = sum(user.total_exports for user in users)
            total_feedback = len(all_feedback)
            active_users = len([user for user in users if user.total_exports > 0])
            
            # Platform breakdown
            platform_stats = {}
            for user in users:
                user_stats = manager.get_usage_stats(user.email)
                for platform, count in user_stats.exports_by_target.items():
                    platform_stats[platform] = platform_stats.get(platform, 0) + count
            
            # Rating breakdown
            rating_stats = {}
            for fb in all_feedback:
                rating_stats[fb.rating] = rating_stats.get(fb.rating, 0) + 1
            
            progress.update(task, description="Complete!")
        
        # Display summary
        summary_table = Table(title="Beta Program Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="magenta")
        
        summary_table.add_row("Total Beta Users", str(total_users))
        summary_table.add_row("Active Users", str(active_users))
        summary_table.add_row("Total Exports", str(total_exports))
        summary_table.add_row("Total Feedback", str(total_feedback))
        summary_table.add_row("Avg Exports per User", f"{total_exports/total_users:.1f}" if total_users > 0 else "0")
        summary_table.add_row("Feedback Rate", f"{(total_feedback/total_exports*100):.1f}%" if total_exports > 0 else "0%")
        
        console.print(summary_table)
        
        # Platform breakdown
        if platform_stats:
            platform_table = Table(title="Platform Usage")
            platform_table.add_column("Platform", style="cyan")
            platform_table.add_column("Exports", style="magenta")
            platform_table.add_column("Percentage", style="yellow")
            
            for platform, count in platform_stats.items():
                percentage = (count / total_exports * 100) if total_exports > 0 else 0
                platform_table.add_row(platform.title(), str(count), f"{percentage:.1f}%")
            
            console.print(platform_table)
        
        # Rating breakdown
        if rating_stats:
            rating_table = Table(title="Feedback Ratings")
            rating_table.add_column("Rating", style="cyan")
            rating_table.add_column("Count", style="magenta")
            rating_table.add_column("Percentage", style="yellow")
            
            for rating in range(1, 6):
                count = rating_stats.get(rating, 0)
                percentage = (count / total_feedback * 100) if total_feedback > 0 else 0
                stars = "⭐" * rating
                rating_table.add_row(f"{stars} ({rating})", str(count), f"{percentage:.1f}%")
            
            console.print(rating_table)
        
        # Generate CSV report
        if not output:
            output = f"beta_report_{datetime.now().strftime('%Y%m%d')}.csv"
        
        with open(output, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Summary section
            writer.writerow(['Beta Program Report', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])
            writer.writerow(['Summary Statistics'])
            writer.writerow(['Total Beta Users', total_users])
            writer.writerow(['Active Users', active_users])
            writer.writerow(['Total Exports', total_exports])
            writer.writerow(['Total Feedback', total_feedback])
            writer.writerow(['Average Exports per User', f"{total_exports/total_users:.1f}" if total_users > 0 else "0"])
            writer.writerow(['Feedback Rate', f"{(total_feedback/total_exports*100):.1f}%" if total_exports > 0 else "0%"])
            writer.writerow([])
            
            # User details
            writer.writerow(['User Details'])
            writer.writerow(['Email', 'Added Date', 'Total Exports', 'Last Export Date', 'Feedback Count', 'Notes'])
            for user in users:
                writer.writerow([
                    user.email,
                    user.added_date.isoformat(),
                    user.total_exports,
                    user.last_export_date.isoformat() if user.last_export_date else '',
                    user.feedback_count,
                    user.notes
                ])
            writer.writerow([])
            
            # Platform breakdown
            if platform_stats:
                writer.writerow(['Platform Usage'])
                writer.writerow(['Platform', 'Exports', 'Percentage'])
                for platform, count in platform_stats.items():
                    percentage = (count / total_exports * 100) if total_exports > 0 else 0
                    writer.writerow([platform.title(), count, f"{percentage:.1f}%"])
                writer.writerow([])
            
            # Recent feedback
            writer.writerow(['Recent Feedback (Last 10)'])
            writer.writerow(['Email', 'Date', 'Rating', 'Platform', 'Feedback'])
            for fb in all_feedback[:10]:
                writer.writerow([
                    fb.email,
                    fb.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    fb.rating,
                    fb.target_platform,
                    fb.feedback_text
                ])
        
        console.print(f"\n[green]✓ Report generated: {output}[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Error generating report: {str(e)}[/red]")


@admin.command()
@click.option('--email', '-e', required=True, help='Beta user email address')
@click.option('--notes', '-n', required=True, help='Updated notes for the user')
def update_notes(email: str, notes: str):
    """Update notes for a beta user."""
    console.print(Panel(
        Text("Update User Notes", style="bold yellow"),
        subtitle="Beta User Management"
    ))
    
    try:
        manager = BetaManager()
        
        # Check if user exists
        if not manager.is_beta_user(email):
            console.print(f"[red]✗ User {email} is not in the beta program[/red]")
            return
        
        # Update notes by re-adding the user (which replaces existing entry)
        manager.add_beta_user(email, notes)
        console.print(f"[green]✓ Updated notes for {email}[/green]")
        console.print(f"[dim]New notes: {notes}[/dim]")
        
    except Exception as e:
        console.print(f"[red]✗ Error updating user notes: {str(e)}[/red]")


if __name__ == '__main__':
    admin()
"""
Command-line interface for LLM Context Exporter.

This module provides the main CLI entry point using Click framework.
"""

import click
import os
import sys
import subprocess
import shutil
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

from ..core.export_handler import ExportHandler
from ..core.models import ExportConfig, FilterConfig
from .admin import admin

console = Console()


def _show_platform_comparison():
    """Display comparison between Gemini and Ollama options."""
    console.print("\n[bold blue]Platform Comparison[/bold blue]")
    
    table = Table(title="Gemini vs Ollama")
    table.add_column("Feature", style="cyan", width=20)
    table.add_column("Gemini", style="green", width=30)
    table.add_column("Ollama (Local)", style="yellow", width=30)
    
    table.add_row("Privacy", "Cloud-based (Google)", "Fully local processing")
    table.add_row("Setup", "Copy-paste to Saved Info", "Install Ollama + create model")
    table.add_row("Context Persistence", "Permanent (until cleared)", "Permanent (model-based)")
    table.add_row("Performance", "Fast, cloud-powered", "Depends on local hardware")
    table.add_row("Offline Access", "No", "Yes")
    table.add_row("Cost", "Free tier available", "Free (uses local resources)")
    table.add_row("Model Choice", "Gemini models only", "Many open-source models")
    
    console.print(table)
    
    console.print("\n[bold]Privacy Implications:[/bold]")
    console.print("• [green]Gemini:[/green] Your context will be stored on Google's servers")
    console.print("• [yellow]Ollama:[/yellow] Everything stays on your local machine")
    
    console.print("\n[bold]Performance Trade-offs:[/bold]")
    console.print("• [green]Gemini:[/green] Fast responses, advanced reasoning, large context window")
    console.print("• [yellow]Ollama:[/yellow] Speed depends on hardware, various model capabilities")


def _check_ollama_installation() -> bool:
    """Check if Ollama is installed and provide guidance if not."""
    from ..core.compatibility import CompatibilityManager
    
    compatibility_manager = CompatibilityManager()
    is_ready, status_info = compatibility_manager.verify_ollama_installation()
    
    if is_ready:
        console.print("[green]✓ Ollama and Qwen model found[/green]")
        if status_info.get("version"):
            console.print(f"[dim]Version: {status_info['version']}[/dim]")
        return True
    
    # Display issues and suggestions
    console.print("\n[red]⚠ Ollama setup incomplete![/red]")
    
    for issue in status_info.get("issues", []):
        console.print(f"[red]• {issue}[/red]")
    
    if status_info.get("suggestions"):
        console.print("\n[bold]To fix this:[/bold]")
        for suggestion in status_info["suggestions"]:
            console.print(f"• {suggestion}")
    
    console.print("\n[dim]You can still generate the Modelfile, but you'll need Ollama to use it.[/dim]")
    return False


def _interactive_filtering(context_pack) -> Optional[FilterConfig]:
    """Interactive filtering mode for selecting content."""
    console.print("\n[bold blue]Interactive Filtering[/bold blue]")
    console.print("Review and select what to include in your context package.\n")
    
    # Show projects
    if context_pack.projects:
        console.print("[bold]Projects found:[/bold]")
        excluded_projects = []
        
        for i, project in enumerate(context_pack.projects):
            include = Confirm.ask(
                f"Include project: [cyan]{project.name}[/cyan] ({project.description[:50]}...)?",
                default=True
            )
            if not include:
                excluded_projects.append(project.name)
    
    # Show technical context
    excluded_topics = []
    if context_pack.technical_context.domains:
        console.print("\n[bold]Technical domains found:[/bold]")
        for domain in context_pack.technical_context.domains[:10]:  # Show top 10
            include = Confirm.ask(f"Include domain: [cyan]{domain}[/cyan]?", default=True)
            if not include:
                excluded_topics.append(domain)
    
    # Date range filtering
    console.print("\n[bold]Date Range Filtering:[/bold]")
    use_date_filter = Confirm.ask("Filter by date range?", default=False)
    date_range = None
    
    if use_date_filter:
        console.print("[dim]Enter dates in YYYY-MM-DD format[/dim]")
        start_date = Prompt.ask("Start date (leave empty for no limit)", default="")
        end_date = Prompt.ask("End date (leave empty for no limit)", default="")
        # TODO: Parse dates and create date_range tuple
    
    # Relevance threshold
    min_relevance = 0.0
    use_relevance = Confirm.ask("Set minimum relevance threshold?", default=False)
    if use_relevance:
        min_relevance = float(Prompt.ask("Minimum relevance (0.0-1.0)", default="0.3"))
    
    if excluded_projects or excluded_topics or date_range or min_relevance > 0:
        return FilterConfig(
            excluded_conversation_ids=[],  # TODO: Implement conversation-level filtering
            excluded_topics=excluded_topics,
            date_range=date_range,
            min_relevance_score=min_relevance
        )
    
    return None


@click.group()
@click.version_option(version="0.1.0")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def cli(verbose):
    """
    LLM Context Exporter - Migrate your context between LLM platforms.
    
    Export your ChatGPT conversation history and package it for use with
    Gemini, Ollama, or other LLM platforms while maintaining privacy.
    
    \b
    Examples:
      llm-context-export export -i chatgpt.zip -t gemini -o ./output
      llm-context-export export -i chatgpt.zip -t ollama -o ./output --interactive
      llm-context-export validate -c ./output/context.json -t gemini
      llm-context-export compare  # Show platform comparison
    
    \b
    Privacy Notice:
      All processing happens locally on your machine. No data is sent to
      external services during export and context extraction.
    """
    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")
    
    # Show disclaimer on first run
    _show_disclaimer()


def _show_disclaimer():
    """Show privacy and limitations disclaimer."""
    disclaimer_text = """
    ## Privacy & Limitations Notice
    
    **Privacy:** All processing happens locally. No data leaves your machine.
    
    **Limitations:**
    • Target LLMs may interpret context differently than ChatGPT
    • Platform-specific features may not transfer
    • Context quality depends on conversation content
    • Large contexts may be truncated to fit platform limits
    
    **What transfers well:**
    • Project descriptions and technical context
    • User preferences and working patterns
    • Domain expertise and tool knowledge
    
    **What may not transfer:**
    • ChatGPT-specific features (plugins, browsing, etc.)
    • Conversation-specific context and nuances
    • Real-time information or current events
    """
    
    console.print(Panel(Markdown(disclaimer_text), title="Important Information", border_style="yellow"))


@cli.command()
@click.option('--input', '-i', required=True, 
              help='Path to ChatGPT export file (ZIP or JSON)')
@click.option('--target', '-t', type=click.Choice(['gemini', 'ollama']), 
              help='Target platform (use "compare" command to see differences)')
@click.option('--output', '-o', required=True, 
              help='Output directory path')
@click.option('--model', '-m', default='qwen',
              help='Base model for Ollama (default: qwen)')
@click.option('--interactive', is_flag=True, 
              help='Enable interactive filtering and selection')
@click.option('--update', 
              help='Path to previous context for incremental update')
@click.option('--exclude-conversations', 
              help='Comma-separated list of conversation IDs to exclude')
@click.option('--exclude-topics', 
              help='Comma-separated list of topics to exclude')
@click.option('--min-relevance', type=float, default=0.0, 
              help='Minimum relevance score for projects (0.0-1.0)')
@click.option('--dry-run', is_flag=True,
              help='Show what would be exported without creating files')
def export(input, target, output, model, interactive, update, exclude_conversations, exclude_topics, min_relevance, dry_run):
    """Export ChatGPT conversations to target platform format."""
    
    # Show platform comparison if no target specified
    if not target:
        _show_platform_comparison()
        target = click.prompt(
            "\nChoose target platform",
            type=click.Choice(['gemini', 'ollama']),
            show_choices=True
        )
    
    console.print(Panel(
        Text("LLM Context Exporter", style="bold blue"),
        subtitle=f"Exporting to {target.upper()}"
    ))
    
    # Validate input file
    if not os.path.exists(input):
        console.print(f"[red]✗ Error: Input file not found: {input}[/red]")
        console.print(f"[dim]Please check the file path and try again[/dim]")
        sys.exit(1)
    
    # Check Ollama installation if targeting Ollama
    if target == 'ollama':
        _check_ollama_installation()
    
    console.print(f"[yellow]Input file:[/yellow] {input}")
    console.print(f"[yellow]Target platform:[/yellow] {target}")
    console.print(f"[yellow]Output directory:[/yellow] {output}")
    
    if target == 'ollama':
        console.print(f"[yellow]Base model:[/yellow] {model}")
    
    if dry_run:
        console.print("[yellow]Dry run mode:[/yellow] No files will be created")
    
    if update:
        console.print(f"[yellow]Incremental update from:[/yellow] {update}")
        if not os.path.exists(update):
            console.print(f"[red]⚠ Warning: Previous context file not found: {update}[/red]")
            console.print("[yellow]Proceeding with full export instead[/yellow]")
            update = None
    
    # Perform initial parsing and extraction for interactive mode
    context_pack = None
    if interactive:
        console.print("\n[yellow]Parsing export file for interactive filtering...[/yellow]")
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Parsing conversations...", total=None)
                
                from ..parsers.chatgpt import ChatGPTParser
                from ..core.extractor import ContextExtractor
                
                parser = ChatGPTParser()
                parsed_export = parser.parse_export(input)
                
                progress.update(task, description="Extracting context...")
                extractor = ContextExtractor()
                context_pack = extractor.extract_context(parsed_export.conversations)
                
                progress.update(task, description="Complete!")
            
            console.print(f"[green]✓ Found {len(context_pack.projects)} projects and {len(context_pack.technical_context.languages)} languages[/green]")
            
        except Exception as e:
            console.print(f"[red]✗ Error during parsing: {str(e)}[/red]")
            sys.exit(1)
    
    # Interactive filtering
    filters = None
    if interactive and context_pack:
        filters = _interactive_filtering(context_pack)
    elif exclude_conversations or exclude_topics or min_relevance > 0.0:
        filters = FilterConfig(
            excluded_conversation_ids=exclude_conversations.split(',') if exclude_conversations else [],
            excluded_topics=exclude_topics.split(',') if exclude_topics else [],
            min_relevance_score=min_relevance
        )
        console.print(f"[yellow]Filters applied:[/yellow] {len(filters.excluded_conversation_ids)} conversations, {len(filters.excluded_topics)} topics excluded")
    
    if dry_run:
        console.print("\n[blue]Dry run complete - no files created[/blue]")
        if filters:
            console.print(f"[dim]Would apply filters: {len(filters.excluded_topics)} topics excluded[/dim]")
        return
    
    # Create export configuration
    config = ExportConfig(
        input_path=input,
        target_platform=target,
        output_path=output,
        base_model=model if target == 'ollama' else None,
        filters=filters,
        interactive=interactive,
        incremental=bool(update),
        previous_context_path=update
    )
    
    # Perform export
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Exporting context...", total=None)
            
            handler = ExportHandler()
            results = handler.export(config)
            
            progress.update(task, description="Complete!")
        
        if results["success"]:
            console.print("\n[green]✓ Export completed successfully![/green]")
            
            # Display results table
            table = Table(title="Export Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            
            metadata = results["metadata"]
            table.add_row("Conversations Parsed", str(metadata.get("conversations_parsed", "N/A")))
            table.add_row("Projects Extracted", str(metadata.get("projects_extracted", "N/A")))
            table.add_row("Languages Found", str(metadata.get("languages_found", "N/A")))
            table.add_row("Filters Applied", "Yes" if metadata.get("filtered") else "No")
            
            console.print(table)
            
            console.print(f"\n[green]Output files:[/green]")
            for file_path in results["output_files"]:
                console.print(f"  • {file_path}")
            
            # Show next steps
            _show_next_steps(target, results["output_files"])
                
        else:
            console.print("\n[red]✗ Export failed![/red]")
            for error in results["errors"]:
                console.print(f"[red]Error: {error}[/red]")
            sys.exit(1)
                
    except Exception as e:
        console.print(f"\n[red]✗ Unexpected error: {str(e)}[/red]")
        console.print("[dim]Please check your input file and try again[/dim]")
        sys.exit(1)


def _show_next_steps(target: str, output_files: List[str]):
    """Show next steps after successful export."""
    console.print(f"\n[bold blue]Next Steps for {target.upper()}:[/bold blue]")
    
    if target == 'gemini':
        console.print("1. Copy the generated text from the output file")
        console.print("2. Go to Google Gemini (gemini.google.com)")
        console.print("3. Click on your profile → Saved Info")
        console.print("4. Paste the context text")
        console.print("5. Test with the validation questions")
        
    elif target == 'ollama':
        console.print("1. Make sure Ollama is running: [cyan]ollama serve[/cyan]")
        console.print("2. Create your custom model:")
        for file_path in output_files:
            if file_path.endswith('Modelfile'):
                console.print(f"   [cyan]ollama create my-context -f {file_path}[/cyan]")
                break
        console.print("3. Test your model: [cyan]ollama run my-context[/cyan]")
        console.print("4. Ask about your projects to verify context transfer")
    
    console.print(f"\n[dim]Run validation tests: llm-context-export validate -c {output_files[0]} -t {target}[/dim]")


@cli.command()
@click.option('--context', '-c', required=True, 
              help='Path to context package or output directory')
@click.option('--target', '-t', type=click.Choice(['gemini', 'ollama']), required=True, 
              help='Target platform to validate')
@click.option('--interactive', is_flag=True,
              help='Run validation questions interactively')
def validate(context, target, interactive):
    """Generate validation tests for exported context."""
    console.print(Panel(
        Text("Context Validation", style="bold green"),
        subtitle=f"Validating {target.upper()} context"
    ))
    
    console.print(f"[yellow]Context package:[/yellow] {context}")
    console.print(f"[yellow]Target platform:[/yellow] {target}")
    
    # Handle both file and directory paths
    context_file = context
    if os.path.isdir(context):
        # Look for context file in directory
        possible_files = ['context.json', 'universal_context.json', 'context_pack.json']
        for filename in possible_files:
            candidate = os.path.join(context, filename)
            if os.path.exists(candidate):
                context_file = candidate
                break
        else:
            console.print(f"[red]✗ Error: No context file found in directory: {context}[/red]")
            console.print("[dim]Expected files: context.json, universal_context.json, or context_pack.json[/dim]")
            sys.exit(1)
    
    if not os.path.exists(context_file):
        console.print(f"[red]✗ Error: Context file not found: {context_file}[/red]")
        sys.exit(1)
    
    try:
        from ..core.incremental import IncrementalUpdater
        from ..validation.generator import ValidationGenerator
        
        # Load context pack
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading context...", total=None)
            
            updater = IncrementalUpdater()
            context_pack = updater.load_previous_context(context_file)
            
            if not context_pack:
                console.print("[red]✗ Error: Could not load context package[/red]")
                console.print("[dim]Make sure the file is a valid context package[/dim]")
                sys.exit(1)
            
            progress.update(task, description="Generating validation tests...")
            
            # Generate validation tests
            validator = ValidationGenerator()
            validation_suite = validator.generate_tests(context_pack, target)
            
            progress.update(task, description="Complete!")
        
        console.print(f"\n[green]✓ Generated {len(validation_suite.questions)} validation questions[/green]")
        
        if interactive:
            console.print("\n[bold]Interactive Validation Mode[/bold]")
            console.print("Test these questions with your target LLM and compare responses:\n")
        
        for i, question in enumerate(validation_suite.questions, 1):
            console.print(f"\n[cyan]Question {i} ({question.category}):[/cyan]")
            console.print(f"  {question.question}")
            console.print(f"[dim]Expected: {question.expected_answer_summary}[/dim]")
            
            if interactive:
                input("\nPress Enter to continue to next question...")
        
        # Generate platform-specific artifacts
        if target == 'gemini':
            console.print("\n[bold]Gemini Validation Checklist:[/bold]")
            console.print("□ Context appears in Saved Info")
            console.print("□ Gemini mentions your projects when asked")
            console.print("□ Gemini uses your preferred tools/languages")
            console.print("□ Gemini remembers your working patterns")
            
        elif target == 'ollama':
            console.print("\n[bold]Ollama Validation Commands:[/bold]")
            console.print("Test your model with these commands:")
            for i, question in enumerate(validation_suite.questions[:3], 1):
                console.print(f"[cyan]ollama run my-context \"{question.question}\"[/cyan]")
            
    except Exception as e:
        console.print(f"[red]✗ Error generating validation tests: {str(e)}[/red]")
        console.print(f"[dim]Details: {type(e).__name__}[/dim]")
        sys.exit(1)


@cli.command()
@click.option('--current', '-c', required=True, 
              help='Path to current ChatGPT export file')
@click.option('--previous', '-p', required=True, 
              help='Path to previous context package')
@click.option('--output', '-o', required=True, 
              help='Output directory for delta package')
@click.option('--dry-run', is_flag=True,
              help='Show what would be included without creating files')
def delta(current, previous, output, dry_run):
    """Generate a delta package containing only new information."""
    console.print(Panel(
        Text("Delta Package Generation", style="bold cyan"),
        subtitle="Incremental Update"
    ))
    
    console.print(f"[yellow]Current export:[/yellow] {current}")
    console.print(f"[yellow]Previous context:[/yellow] {previous}")
    console.print(f"[yellow]Output directory:[/yellow] {output}")
    
    if dry_run:
        console.print("[yellow]Dry run mode:[/yellow] No files will be created")
    
    # Validate input files
    if not os.path.exists(current):
        console.print(f"[red]✗ Error: Current export file not found: {current}[/red]")
        sys.exit(1)
    
    if not os.path.exists(previous):
        console.print(f"[red]✗ Error: Previous context file not found: {previous}[/red]")
        sys.exit(1)
    
    try:
        from ..parsers.chatgpt import ChatGPTParser
        from ..core.extractor import ContextExtractor
        from ..core.incremental import IncrementalUpdater
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing exports...", total=None)
            
            # Parse current export
            parser = ChatGPTParser()
            current_export = parser.parse_export(current)
            
            progress.update(task, description="Extracting current context...")
            
            # Extract context from current export
            extractor = ContextExtractor()
            current_context = extractor.extract_context(current_export.conversations)
            
            progress.update(task, description="Loading previous context...")
            
            # Load previous context
            updater = IncrementalUpdater()
            previous_context = updater.load_previous_context(previous)
            
            if not previous_context:
                console.print("[red]✗ Error: Could not load previous context package[/red]")
                sys.exit(1)
            
            progress.update(task, description="Generating delta package...")
            
            # Generate delta package
            delta_package = updater.generate_delta_package(previous_context, current_context)
            
            progress.update(task, description="Complete!")
        
        # Display delta statistics
        table = Table(title="Delta Package Contents")
        table.add_column("Category", style="cyan")
        table.add_column("New Items", style="magenta")
        
        table.add_row("Projects", str(len(delta_package.projects)))
        table.add_row("Languages", str(len(delta_package.technical_context.languages)))
        table.add_row("Frameworks", str(len(delta_package.technical_context.frameworks)))
        table.add_row("Tools", str(len(delta_package.technical_context.tools)))
        table.add_row("Domains", str(len(delta_package.technical_context.domains)))
        
        console.print(table)
        
        if not dry_run:
            # Save delta package
            os.makedirs(output, exist_ok=True)
            delta_path = os.path.join(output, "delta_package.json")
            updater.save_context_pack(delta_package, delta_path)
            
            console.print(f"\n[green]✓ Delta package generated successfully![/green]")
            console.print(f"[green]Saved to:[/green] {delta_path}")
        else:
            console.print(f"\n[blue]Dry run complete - delta package would be saved to: {output}/delta_package.json[/blue]")
        
    except Exception as e:
        console.print(f"[red]✗ Error generating delta package: {str(e)}[/red]")
        console.print(f"[dim]Details: {type(e).__name__}[/dim]")
        sys.exit(1)


@cli.command()
def compare():
    """Compare Gemini vs Ollama platforms to help choose."""
    _show_platform_comparison()
    
    console.print("\n[bold]Recommendations:[/bold]")
    console.print("• Choose [green]Gemini[/green] if you want:")
    console.print("  - Quick setup (copy-paste)")
    console.print("  - Cloud-powered performance")
    console.print("  - Don't mind data on Google servers")
    
    console.print("\n• Choose [yellow]Ollama[/yellow] if you want:")
    console.print("  - Complete privacy (local processing)")
    console.print("  - Offline access")
    console.print("  - Control over model choice")
    console.print("  - Don't mind technical setup")
    
    console.print(f"\n[dim]Use: llm-context-export export -i <file> -t <platform> -o <output>[/dim]")


@cli.command()
@click.option('--port', '-p', default=8080, 
              help='Port for web interface (default: 8080)')
@click.option('--host', '-h', default='127.0.0.1', 
              help='Host for web interface (localhost only for security)')
@click.option('--debug', is_flag=True,
              help='Enable debug mode')
def web(port, host, debug):
    """Start the web interface for non-technical users."""
    
    # Security check - only allow localhost
    if host != '127.0.0.1' and host != 'localhost':
        console.print("[red]✗ Error: Web interface only supports localhost for security[/red]")
        console.print("[dim]Use --host 127.0.0.1 or --host localhost[/dim]")
        sys.exit(1)
    
    console.print(Panel(
        Text("Web Interface", style="bold magenta"),
        subtitle="Starting local server"
    ))
    
    console.print(f"[yellow]Host:[/yellow] {host}")
    console.print(f"[yellow]Port:[/yellow] {port}")
    console.print(f"[yellow]URL:[/yellow] http://{host}:{port}")
    console.print(f"[yellow]Debug mode:[/yellow] {'Enabled' if debug else 'Disabled'}")
    
    console.print("\n[bold blue]Security Notice:[/bold blue]")
    console.print("• Web interface runs locally only")
    console.print("• No data is sent to external servers")
    console.print("• Files are processed on your machine")
    
    try:
        from ..web.app import create_app
        
        app = create_app({
            'DEBUG': debug,
            'HOST': host,
            'PORT': port
        })
        
        console.print(f"\n[green]✓ Starting server at http://{host}:{port}[/green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
        console.print("\n[bold]Available endpoints:[/bold]")
        console.print("• [cyan]GET /[/cyan] - Web interface")
        console.print("• [cyan]POST /api/upload[/cyan] - Upload ChatGPT export")
        console.print("• [cyan]GET /api/preview[/cyan] - Preview extracted context")
        console.print("• [cyan]POST /api/filter[/cyan] - Apply filters")
        console.print("• [cyan]POST /api/generate[/cyan] - Generate output")
        console.print("• [cyan]GET /api/download/<id>[/cyan] - Download results")
        console.print("• [cyan]POST /api/validate[/cyan] - Generate validation tests")
        console.print("• [cyan]GET /api/beta/status[/cyan] - Check beta status")
        console.print("• [cyan]POST /api/payment/create[/cyan] - Create payment")
        
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        console.print(f"[red]✗ Error starting web server: {str(e)}[/red]")
        console.print(f"[dim]Details: {e}[/dim]")
        sys.exit(1)


@cli.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
def info(verbose):
    """Display information about supported platforms and features."""
    console.print(Panel(
        Text("LLM Context Exporter", style="bold blue"),
        subtitle="Platform Information & Usage Guide"
    ))
    
    console.print("\n[bold]Supported Source Platforms:[/bold]")
    console.print("• [green]ChatGPT[/green] (official export files - ZIP or JSON)")
    if verbose:
        console.print("  - Supports all ChatGPT export format versions")
        console.print("  - Handles both individual JSON files and ZIP archives")
        console.print("  - Preserves message timestamps, roles, and metadata")
    
    console.print("\n[bold]Supported Target Platforms:[/bold]")
    console.print("• [green]Google Gemini[/green] (Saved Info format)")
    if verbose:
        console.print("  - Optimized text format for Gemini comprehension")
        console.print("  - Automatic size limit handling and prioritization")
        console.print("  - Step-by-step setup instructions included")
    
    console.print("• [yellow]Ollama[/yellow] (Local LLM with Modelfile)")
    if verbose:
        console.print("  - Generates valid Modelfile with system prompt")
        console.print("  - Optimized for Qwen and other open-source models")
        console.print("  - Handles large contexts with file splitting")
        console.print("  - Includes model creation and test commands")
    
    console.print("\n[bold]Key Features:[/bold]")
    console.print("• [blue]Privacy-first:[/blue] All processing happens locally")
    console.print("• [blue]Smart extraction:[/blue] Identifies projects, preferences, and expertise")
    console.print("• [blue]Interactive filtering:[/blue] Choose what to include/exclude")
    console.print("• [blue]Incremental updates:[/blue] Add new conversations without re-processing")
    console.print("• [blue]Validation tests:[/blue] Verify successful context transfer")
    console.print("• [blue]Multiple interfaces:[/blue] CLI for developers, web UI for everyone")
    
    if verbose:
        console.print("\n[bold]What Gets Extracted:[/bold]")
        console.print("• Project descriptions and technical details")
        console.print("• Programming languages and frameworks used")
        console.print("• Tools and development preferences")
        console.print("• Working patterns and communication style")
        console.print("• Domain expertise and background knowledge")
    
    console.print("\n[bold]Privacy & Security:[/bold]")
    console.print("• [green]Local processing:[/green] No data sent to external services")
    console.print("• [green]Encryption:[/green] Context packages encrypted at rest")
    console.print("• [green]Sensitive data detection:[/green] Prompts for redaction approval")
    console.print("• [green]Secure deletion:[/green] Complete removal when requested")
    
    if verbose:
        console.print("\n[bold]Limitations:[/bold]")
        console.print("• Target LLMs may interpret context differently")
        console.print("• Platform-specific features don't transfer")
        console.print("• Large contexts may be truncated")
        console.print("• Quality depends on conversation content")
    
    console.print("\n[bold]Quick Start:[/bold]")
    console.print("1. Export your ChatGPT data (Settings → Data Export)")
    console.print("2. Choose platform: [cyan]llm-context-export compare[/cyan]")
    console.print("3. Export context: [cyan]llm-context-export export -i export.zip -t gemini -o ./output[/cyan]")
    console.print("4. Validate transfer: [cyan]llm-context-export validate -c ./output -t gemini[/cyan]")
    
    console.print(f"\n[dim]For detailed help: llm-context-export <command> --help[/dim]")
    console.print(f"[dim]Web interface: llm-context-export web[/dim]")


# Add admin commands as a subgroup
cli.add_command(admin)


@cli.command()
@click.option('--file', '-f', help='ChatGPT export file to analyze')
@click.option('--target', '-t', type=click.Choice(['gemini', 'ollama']), 
              help='Target platform for compatibility check')
def compatibility(file, target):
    """Check compatibility and generate detailed compatibility report."""
    console.print(Panel(
        Text("Compatibility Analysis", style="bold cyan"),
        subtitle="Platform Compatibility Report"
    ))
    
    from ..core.compatibility import CompatibilityManager
    from ..parsers.chatgpt import ChatGPTParser
    
    compatibility_manager = CompatibilityManager()
    
    # If no file provided, just check target platform requirements
    if not file:
        if target == 'ollama':
            console.print("\n[bold]Checking Ollama Installation:[/bold]")
            is_ready, status_info = compatibility_manager.verify_ollama_installation()
            
            if is_ready:
                console.print("[green]✓ Ollama is ready[/green]")
            else:
                console.print("[red]✗ Ollama setup incomplete[/red]")
                
            # Display detailed status
            table = Table(title="Ollama Status")
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="magenta")
            table.add_column("Details", style="dim")
            
            table.add_row(
                "Ollama Binary", 
                "✓ Found" if status_info["ollama_found"] else "✗ Missing",
                status_info.get("version", "Not available")
            )
            table.add_row(
                "Ollama Service",
                "✓ Running" if status_info["ollama_running"] else "✗ Not running",
                "Service is accessible" if status_info["ollama_running"] else "Cannot connect"
            )
            table.add_row(
                "Qwen Model",
                "✓ Available" if status_info["qwen_available"] else "✗ Missing",
                "Ready for use" if status_info["qwen_available"] else "Run: ollama pull qwen"
            )
            
            console.print(table)
            
            if status_info.get("suggestions"):
                console.print("\n[bold]Recommendations:[/bold]")
                for suggestion in status_info["suggestions"]:
                    console.print(f"• {suggestion}")
        
        elif target == 'gemini':
            console.print("\n[bold]Gemini Compatibility:[/bold]")
            console.print("[green]✓ Gemini is cloud-based and requires no local setup[/green]")
            console.print("\n[bold]Requirements:[/bold]")
            console.print("• Google account with Gemini access")
            console.print("• Access to Gemini Saved Info feature")
            console.print("• Manual copy-paste of generated context")
        
        else:
            console.print("\n[bold]Platform Comparison:[/bold]")
            _show_platform_comparison()
        
        return
    
    # Analyze specific file
    if not os.path.exists(file):
        console.print(f"[red]✗ Error: File not found: {file}[/red]")
        sys.exit(1)
    
    console.print(f"[yellow]Analyzing file:[/yellow] {file}")
    if target:
        console.print(f"[yellow]Target platform:[/yellow] {target}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing export file...", total=None)
            
            # Get format diagnostics
            parser = ChatGPTParser()
            diagnostic = compatibility_manager.detect_format_with_diagnostics(file, ChatGPTParser)
            
            progress.update(task, description="Parsing conversations...")
            
            # Parse the export
            try:
                parsed_export = parser.parse_export(file)
            except Exception as e:
                console.print(f"[red]✗ Error parsing file: {str(e)}[/red]")
                sys.exit(1)
            
            progress.update(task, description="Generating compatibility report...")
            
            # Generate full compatibility report
            if target:
                report = compatibility_manager.generate_compatibility_report(parsed_export, target)
            else:
                # Generate reports for both platforms
                gemini_report = compatibility_manager.generate_compatibility_report(parsed_export, "gemini")
                ollama_report = compatibility_manager.generate_compatibility_report(parsed_export, "ollama")
                report = {
                    "export_info": gemini_report["export_info"],
                    "platform_features": gemini_report["platform_features"],
                    "unsupported_data": gemini_report["unsupported_data"],
                    "gemini_status": gemini_report["target_platform_status"],
                    "ollama_status": ollama_report["target_platform_status"],
                    "recommendations": gemini_report["recommendations"] + ollama_report["recommendations"]
                }
            
            progress.update(task, description="Complete!")
        
        # Display format diagnostic
        console.print("\n[bold]Format Analysis:[/bold]")
        format_table = Table()
        format_table.add_column("Property", style="cyan")
        format_table.add_column("Value", style="magenta")
        
        format_table.add_row("Detected Version", diagnostic.detected_version)
        format_table.add_row("Compatibility", diagnostic.compatibility_level.value.replace('_', ' ').title())
        format_table.add_row("Confidence", f"{diagnostic.confidence:.1%}")
        if diagnostic.fallback_version:
            format_table.add_row("Fallback Version", diagnostic.fallback_version)
        
        console.print(format_table)
        
        if diagnostic.issues:
            console.print("\n[bold red]Issues Found:[/bold red]")
            for issue in diagnostic.issues:
                console.print(f"• {issue}")
        
        if diagnostic.suggestions:
            console.print("\n[bold yellow]Suggestions:[/bold yellow]")
            for suggestion in diagnostic.suggestions:
                console.print(f"• {suggestion}")
        
        # Display export info
        console.print("\n[bold]Export Information:[/bold]")
        export_table = Table()
        export_table.add_column("Metric", style="cyan")
        export_table.add_column("Value", style="magenta")
        
        export_info = report["export_info"]
        export_table.add_row("Conversations", str(export_info["conversations_count"]))
        export_table.add_row("Export Date", export_info["export_date"])
        export_table.add_row("Format Version", export_info["format_version"])
        
        console.print(export_table)
        
        # Display platform features
        if report.get("platform_features"):
            console.print("\n[bold]Platform-Specific Features Found:[/bold]")
            features_table = Table()
            features_table.add_column("Feature", style="cyan")
            features_table.add_column("Transfers?", style="magenta")
            features_table.add_column("Workaround", style="dim")
            
            for feature in report["platform_features"]:
                transfers = "✓ Yes" if feature["supported_in_target"] else "✗ No"
                workaround = feature.get("workaround", "None available")[:50] + "..." if len(feature.get("workaround", "")) > 50 else feature.get("workaround", "None available")
                features_table.add_row(feature["name"], transfers, workaround)
            
            console.print(features_table)
        
        # Display unsupported data summary
        unsupported = report.get("unsupported_data", {})
        if unsupported.get("total_types", 0) > 0:
            console.print(f"\n[bold yellow]Unsupported Data Types: {unsupported['total_types']}[/bold yellow]")
            console.print(f"[dim]Total occurrences: {unsupported['total_occurrences']}[/dim]")
            
            if len(unsupported["entries"]) <= 5:
                # Show all entries if few
                for entry in unsupported["entries"]:
                    console.print(f"• {entry['data_type']} ({entry['count']}x): {entry['reason']}")
            else:
                # Show top 5 most frequent
                sorted_entries = sorted(unsupported["entries"], key=lambda x: x["count"], reverse=True)
                for entry in sorted_entries[:5]:
                    console.print(f"• {entry['data_type']} ({entry['count']}x): {entry['reason']}")
                console.print(f"[dim]... and {len(unsupported['entries']) - 5} more types[/dim]")
        
        # Display target platform status
        if target:
            platform_status = report.get("target_platform_status", {})
            console.print(f"\n[bold]{target.title()} Platform Status:[/bold]")
            if platform_status.get("ready"):
                console.print("[green]✓ Ready for export[/green]")
            else:
                console.print("[red]✗ Setup required[/red]")
                details = platform_status.get("details", {})
                for issue in details.get("issues", []):
                    console.print(f"[red]• {issue}[/red]")
        
        # Display recommendations
        if report.get("recommendations"):
            console.print("\n[bold]Recommendations:[/bold]")
            for rec in report["recommendations"][:5]:  # Show top 5
                console.print(f"• {rec}")
        
    except Exception as e:
        console.print(f"[red]✗ Error during analysis: {str(e)}[/red]")
        console.print(f"[dim]Details: {type(e).__name__}[/dim]")
        sys.exit(1)


@cli.command()
def examples():
    """Show detailed usage examples for common scenarios."""
    console.print(Panel(
        Text("Usage Examples", style="bold blue"),
        subtitle="Common scenarios and commands"
    ))
    
    console.print("\n[bold]1. Basic Export to Gemini:[/bold]")
    console.print("[cyan]llm-context-export export -i chatgpt_export.zip -t gemini -o ./gemini_output[/cyan]")
    console.print("[dim]Exports ChatGPT conversations to Gemini Saved Info format[/dim]")
    
    console.print("\n[bold]2. Interactive Export with Filtering:[/bold]")
    console.print("[cyan]llm-context-export export -i chatgpt_export.zip -t ollama -o ./ollama_output --interactive[/cyan]")
    console.print("[dim]Lets you choose which projects and topics to include[/dim]")
    
    console.print("\n[bold]3. Incremental Update:[/bold]")
    console.print("[cyan]llm-context-export export -i new_export.zip -t gemini -o ./updated --update ./previous/context.json[/cyan]")
    console.print("[dim]Adds only new conversations to existing context[/dim]")
    
    console.print("\n[bold]4. Generate Delta Package:[/bold]")
    console.print("[cyan]llm-context-export delta -c new_export.zip -p ./old_context.json -o ./delta[/cyan]")
    console.print("[dim]Creates package with only new information[/dim]")
    
    console.print("\n[bold]5. Validate Context Transfer:[/bold]")
    console.print("[cyan]llm-context-export validate -c ./output/context.json -t gemini --interactive[/cyan]")
    console.print("[dim]Generates test questions to verify successful transfer[/dim]")
    
    console.print("\n[bold]6. Compare Platforms:[/bold]")
    console.print("[cyan]llm-context-export compare[/cyan]")
    console.print("[dim]Shows detailed comparison between Gemini and Ollama[/dim]")
    
    console.print("\n[bold]7. Web Interface:[/bold]")
    console.print("[cyan]llm-context-export web[/cyan]")
    console.print("[dim]Starts local web interface for non-technical users[/dim]")
    
    console.print("\n[bold]8. Dry Run (Preview):[/bold]")
    console.print("[cyan]llm-context-export export -i export.zip -t gemini -o ./output --dry-run[/cyan]")
    console.print("[dim]Shows what would be exported without creating files[/dim]")
    
    console.print("\n[bold]9. Advanced Filtering:[/bold]")
    console.print("[cyan]llm-context-export export -i export.zip -t ollama -o ./output \\[/cyan]")
    console.print("[cyan]  --exclude-topics 'personal,private' --min-relevance 0.5[/cyan]")
    console.print("[dim]Excludes specific topics and low-relevance projects[/dim]")
    
    console.print("\n[bold]10. Compatibility Check:[/bold]")
    console.print("[cyan]llm-context-export compatibility -f export.zip -t ollama[/cyan]")
    console.print("[dim]Analyzes export file and checks platform compatibility[/dim]")
    
    console.print("\n[bold]11. Platform Requirements:[/bold]")
    console.print("[cyan]llm-context-export compatibility -t ollama[/cyan]")
    console.print("[dim]Checks if Ollama is properly installed and configured[/dim]")
    
    console.print("\n[bold]Getting Help:[/bold]")
    console.print("• [cyan]llm-context-export --help[/cyan] - Main help")
    console.print("• [cyan]llm-context-export <command> --help[/cyan] - Command-specific help")
    console.print("• [cyan]llm-context-export info --verbose[/cyan] - Detailed information")
    console.print("• [cyan]llm-context-export compatibility --help[/cyan] - Compatibility analysis help")


if __name__ == '__main__':
    cli()
import click
from typing import Optional
from .template_scheduler import TemplateScheduler
from ...tools.template_tools import TemplateEnforcementTool

@click.group()
def template():
    """Template management commands."""
    pass

@template.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--auto-fix', is_flag=True, help='Automatically fix template issues')
def validate(path: str, auto_fix: bool):
    """Validate a note against its template."""
    tool = TemplateEnforcementTool()
    result = tool.forward(action="validate", path=path, auto_fix=auto_fix)
    
    if result["success"]:
        if result["valid"]:
            click.echo(f"✓ Note '{path}' is valid")
        else:
            click.echo(f"✗ Note '{path}' has issues:")
            if result.get("validation_errors"):
                click.echo("\nFrontmatter Issues:")
                for error in result["validation_errors"]:
                    click.echo(f"  - {error}")
            if result.get("structure_errors"):
                click.echo("\nStructure Issues:")
                for error in result["structure_errors"]:
                    click.echo(f"  - {error}")
    else:
        click.echo(f"Error: {result['message']}", err=True)

@template.command()
@click.argument('path', type=click.Path(exists=True), required=False)
@click.option('--auto-fix', is_flag=True, help='Automatically fix template issues')
def audit(path: Optional[str], auto_fix: bool):
    """Run a template audit on the vault or specified folder."""
    tool = TemplateEnforcementTool()
    result = tool.forward(action="audit", path=path, auto_fix=auto_fix)
    
    if result["success"]:
        click.echo(f"\nAudit Results:")
        click.echo(f"Total files checked: {result['total_files']}")
        click.echo(f"Files with issues: {result['files_with_issues']}")
        
        if result.get("audit_results"):
            click.echo("\nIssues Found:")
            for file_result in result["audit_results"]:
                click.echo(f"\n{file_result['path']}:")
                if file_result.get("errors"):
                    click.echo("  Frontmatter Issues:")
                    for error in file_result["errors"]:
                        click.echo(f"    - {error}")
                if file_result.get("structure_errors"):
                    click.echo("  Structure Issues:")
                    for error in file_result["structure_errors"]:
                        click.echo(f"    - {error}")
    else:
        click.echo(f"Error: {result['message']}", err=True)

@template.group()
def schedule():
    """Template audit scheduling commands."""
    pass

@schedule.command()
@click.option('--frequency', type=click.Choice(['daily', 'weekly', 'monthly']), help='Audit frequency')
@click.option('--auto-fix', is_flag=True, help='Automatically fix template issues')
@click.option('--notify/--no-notify', default=True, help='Notify on issues')
def configure(frequency: Optional[str], auto_fix: Optional[bool], notify: Optional[bool]):
    """Configure the template audit schedule."""
    scheduler = TemplateScheduler()
    updates = {}
    
    if frequency:
        updates["frequency"] = frequency
    if auto_fix is not None:
        updates["auto_fix"] = auto_fix
    if notify is not None:
        updates["notify_on_issues"] = notify
    
    result = scheduler.update_schedule(**updates)
    
    if result["success"]:
        click.echo("Schedule updated successfully:")
        for key, value in result["schedule"].items():
            click.echo(f"  {key}: {value}")
    else:
        click.echo(f"Error: {result['message']}", err=True)

@schedule.command()
def run():
    """Run a scheduled template audit."""
    scheduler = TemplateScheduler()
    result = scheduler.run_audit()
    
    if result["success"]:
        if result.get("next_run"):
            click.echo(f"Next scheduled run: {result['next_run']}")
        if result.get("results"):
            click.echo(f"\nAudit Results:")
            click.echo(f"Total files checked: {result['results']['total_files']}")
            click.echo(f"Files with issues: {result['results']['files_with_issues']}")
    else:
        click.echo(f"Error: {result['message']}", err=True)

@schedule.command()
def status():
    """Show the current schedule status."""
    scheduler = TemplateScheduler()
    schedule = scheduler.schedule
    
    click.echo("Template Audit Schedule:")
    click.echo(f"  Enabled: {schedule['enabled']}")
    click.echo(f"  Frequency: {schedule['frequency']}")
    click.echo(f"  Last Run: {schedule['last_run'] or 'Never'}")
    click.echo(f"  Auto Fix: {schedule['auto_fix']}")
    click.echo(f"  Notify on Issues: {schedule['notify_on_issues']}")
    click.echo(f"  Excluded Folders: {', '.join(schedule['excluded_folders']) or 'None'}")
    
    next_run = scheduler._get_next_run_time()
    if next_run:
        click.echo(f"  Next Run: {next_run}")

if __name__ == '__main__':
    template() 
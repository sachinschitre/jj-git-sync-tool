#!/usr/bin/env python3
"""
JJ-Git Sync Tool

A proof-of-concept tool to sync branches and commits between JJ and Git.
"""

import os
import subprocess
import click
from git import Repo
from scanners.secrets import scan_recent_commits_for_secrets, generate_security_report
from ai.commitgen import suggest_commit_messages, generate_commit_message, CommitAssistant


@click.group()
def cli():
    """JJ ↔ Git Sync Tool"""
    pass


@cli.command()
@click.option("--git-dir", default=".", help="Path to Git repo")
@click.option("--jj-dir", default=".", help="Path to JJ workspace")
@click.option("--scan", is_flag=True, help="Run security scan after sync")
@click.option("--scan-format", type=click.Choice(['human', 'json']), default='human', help="Security scan output format")
@click.option("--scan-commits", default=5, help="Number of recent commits to scan")
def sync(git_dir, jj_dir, scan, scan_format, scan_commits):
    """
    Sync branches between JJ and Git.
    """
    # Step 1: Export JJ commits into Git
    click.echo("Exporting JJ to Git...")
    try:
        # First check if JJ is the correct version control tool
        result = subprocess.run(
            ["jj", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Check if this is the correct JJ tool (should contain "jj" version info)
        if "jj" not in result.stdout.lower() and "version" not in result.stdout.lower():
            click.echo("❌ Wrong 'jj' command found. Please install JJ version control system from https://github.com/jj-vcs/jj")
            click.echo("   Current 'jj' command appears to be a different tool.")
            return
            
        # Try the actual JJ git export command
        subprocess.run(
            ["jj", "git", "export"],
            cwd=jj_dir,
            check=True
        )
        click.echo("✅ JJ export successful")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ JJ export failed: {e}")
        click.echo("💡 Make sure you have the correct JJ version control system installed")
        click.echo("   Install from: https://github.com/jj-vcs/jj")
        # Continue to security scan even if JJ sync fails
        if scan:
            click.echo("\n⚠️  JJ sync failed, but continuing with security scan...")
            run_security_scan_only(git_dir, scan_format, scan_commits)
        return
    except FileNotFoundError:
        click.echo("❌ JJ command not found. Please install JJ version control system.")
        click.echo("   Install from: https://github.com/jj-vcs/jj")
        # Continue to security scan even if JJ sync fails
        if scan:
            click.echo("\n⚠️  JJ not found, but continuing with security scan...")
            run_security_scan_only(git_dir, scan_format, scan_commits)
        return

    # Step 2: Import Git commits into JJ
    click.echo("Importing Git to JJ...")
    try:
        subprocess.run(
            ["jj", "git", "import"],
            cwd=jj_dir,
            check=True
        )
        click.echo("✅ JJ import successful")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ JJ import failed: {e}")
        click.echo("💡 Make sure you have the correct JJ version control system installed")
        click.echo("   Install from: https://github.com/jj-vcs/jj")
        # Continue to security scan even if JJ sync fails
        if scan:
            click.echo("\n⚠️  JJ import failed, but continuing with security scan...")
            run_security_scan_only(git_dir, scan_format, scan_commits)
        return
    except FileNotFoundError:
        click.echo("❌ JJ command not found. Please install JJ version control system.")
        click.echo("   Install from: https://github.com/jj-vcs/jj")
        # Continue to security scan even if JJ sync fails
        if scan:
            click.echo("\n⚠️  JJ not found, but continuing with security scan...")
            run_security_scan_only(git_dir, scan_format, scan_commits)
        return

    click.echo("🎉 Sync complete!")
    
    # Step 3: Security scan (if requested)
    if scan:
        click.echo("\n🔍 Running security scan...")
        try:
            secrets = scan_recent_commits_for_secrets(git_dir, scan_commits)
            report = generate_security_report(secrets, scan_format)
            click.echo(report)
            
            # Count critical/high severity issues
            critical_high = [s for s in secrets if s['severity'] in ['CRITICAL', 'HIGH']]
            if critical_high:
                click.echo(f"\n⚠️  Found {len(critical_high)} critical/high severity security issues!")
                if scan_format == 'json':
                    click.echo("💡 Use --scan-format human for detailed information")
            else:
                click.echo("\n✅ No critical security issues found")
                
        except Exception as e:
            click.echo(f"❌ Security scan failed: {e}")


def run_security_scan_only(git_dir, scan_format, scan_commits):
    """
    Run security scan without JJ sync (for when JJ is not available).
    """
    click.echo("🔍 Running security scan...")
    try:
        secrets = scan_recent_commits_for_secrets(git_dir, scan_commits)
        report = generate_security_report(secrets, scan_format)
        click.echo(report)
        
        # Count critical/high severity issues
        critical_high = [s for s in secrets if s['severity'] in ['CRITICAL', 'HIGH']]
        if critical_high:
            click.echo(f"\n⚠️  Found {len(critical_high)} critical/high severity security issues!")
            if scan_format == 'json':
                click.echo("💡 Use --scan-format human for detailed information")
        else:
            click.echo("\n✅ No critical security issues found")
            
    except Exception as e:
        click.echo(f"❌ Security scan failed: {e}")


@cli.command()
@click.option("--git-dir", default=".", help="Path to Git repo")
def list_branches(git_dir):
    """
    List branches in Git repository.
    """
    try:
        repo = Repo(git_dir)
        click.echo("📋 Git branches:")
        for branch in repo.branches:
            current = "* " if branch == repo.active_branch else "  "
            click.echo(f"{current}🌿 {branch.name}")
    except Exception as e:
        click.echo(f"❌ Failed to list branches: {e}")


@cli.command()
@click.option("--git-dir", default=".", help="Path to Git repo")
@click.option("--format", type=click.Choice(['human', 'json']), default='human', help="Output format")
@click.option("--commits", default=5, help="Number of recent commits to scan")
@click.option("--commit", help="Scan specific commit hash")
def scan(git_dir, format, commits, commit):
    """
    Run security scan on Git repository.
    """
    click.echo("🔍 Running security scan...")
    
    try:
        if commit:
            # Scan specific commit
            from scanners.secrets import scan_commit_for_secrets
            secrets = scan_commit_for_secrets(commit, git_dir)
            click.echo(f"Scanning commit: {commit}")
        else:
            # Scan recent commits
            secrets = scan_recent_commits_for_secrets(git_dir, commits)
            click.echo(f"Scanning last {commits} commits")
        
        report = generate_security_report(secrets, format)
        click.echo(report)
        
        # Summary
        critical_high = [s for s in secrets if s['severity'] in ['CRITICAL', 'HIGH']]
        if critical_high:
            click.echo(f"\n⚠️  Found {len(critical_high)} critical/high severity security issues!")
            if format == 'json':
                click.echo("💡 Use --format human for detailed information")
        else:
            click.echo("\n✅ No critical security issues found")
            
    except Exception as e:
        click.echo(f"❌ Security scan failed: {e}")


@cli.command()
@click.option("--git-dir", default=".", help="Path to Git repo")
@click.option("--style", type=click.Choice(['conventional', 'semantic', 'simple']), default='conventional', help="Commit message style")
@click.option("--count", default=3, help="Number of suggestions to generate")
@click.option("--model", default="local", help="AI model provider (local, openai, anthropic)")
@click.option("--api-key", help="API key for external LLM services")
@click.option("--interactive", is_flag=True, help="Interactive mode for commit assistance")
def suggest_message(git_dir, style, count, model, api_key, interactive):
    """
    Generate AI-powered commit message suggestions.
    """
    try:
        if interactive:
            # Interactive mode
            assistant = CommitAssistant(git_dir, model, api_key)
            suggestion = assistant.interactive_commit()
            
            if suggestion:
                click.echo(f"\n✅ Suggested commit message:")
                click.echo(f"   {suggestion}")
            else:
                click.echo("❌ No suggestions generated")
        else:
            # Non-interactive mode
            click.echo("🤖 Generating AI commit message suggestions...")
            
            if model == "local":
                click.echo("   Using local analysis (no external APIs)")
            else:
                click.echo(f"   Using {model} model")
            
            suggestions = suggest_commit_messages(git_dir, count, model, api_key)
            
            if suggestions:
                click.echo(f"\n📝 Generated {len(suggestions)} suggestions:")
                click.echo("=" * 60)
                
                for i, suggestion in enumerate(suggestions, 1):
                    click.echo(f"{i}. {suggestion}")
                
                click.echo("\n💡 Usage:")
                click.echo("   git commit -m \"<your-chosen-message>\"")
                click.echo("   Or use --interactive for guided assistance")
            else:
                click.echo("❌ No suggestions generated")
                
    except Exception as e:
        click.echo(f"❌ Failed to generate suggestions: {e}")
        click.echo("💡 Make sure you have staged changes: git add <files>")


if __name__ == "__main__":
    cli()
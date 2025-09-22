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
        subprocess.run(
            ["jj", "git", "export", "--to", git_dir],
            cwd=jj_dir,
            check=True
        )
        click.echo("✅ JJ export successful")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ JJ export failed: {e}")
        return
    except FileNotFoundError:
        click.echo("❌ JJ command not found. Please ensure JJ is installed and in your PATH.")
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
        return
    except FileNotFoundError:
        click.echo("❌ JJ command not found. Please ensure JJ is installed and in your PATH.")
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


if __name__ == "__main__":
    cli()
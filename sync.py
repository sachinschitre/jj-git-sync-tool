#!/usr/bin/env python3
"""
JJ-Git Sync Tool

A proof-of-concept tool to sync branches and commits between JJ and Git.
"""

import os
import subprocess
import click
from git import Repo


@click.group()
def cli():
    """JJ ↔ Git Sync Tool"""
    pass


@cli.command()
@click.option("--git-dir", default=".", help="Path to Git repo")
@click.option("--jj-dir", default=".", help="Path to JJ workspace")
def sync(git_dir, jj_dir):
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


if __name__ == "__main__":
    cli()
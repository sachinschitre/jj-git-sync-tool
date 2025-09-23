"""
AI-powered commit message generation for JJ-Git Sync Tool.

This module provides comprehensive commit message generation functionality
using both local analysis and optional LLM integration.

Week 3 implementation with fallback mode and LLM integration support.
"""

import os
import re
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json


class CommitMessageGenerator:
    """
    AI-powered commit message generator with fallback capabilities.
    """
    
    def __init__(self, model_provider: str = "local", api_key: Optional[str] = None):
        """
        Initialize the commit message generator.
        
        Args:
            model_provider: AI model provider ("local", "openai", "anthropic", etc.)
            api_key: Optional API key for external LLM services
        """
        self.model_provider = model_provider
        self.api_key = api_key
        self.config = {
            "max_suggestions": 3,
            "conventional_commits": True,
            "include_scope": True,
            "include_breaking_changes": True
        }
        
        # Initialize LLM client if API key provided
        self.llm_client = None
        if api_key and model_provider != "local":
            self._initialize_llm_client()
    
    def _initialize_llm_client(self):
        """Initialize LLM client based on provider."""
        try:
            if self.model_provider == "openai":
                # Placeholder for OpenAI integration
                self.llm_client = "openai_client_placeholder"
            elif self.model_provider == "anthropic":
                # Placeholder for Anthropic integration
                self.llm_client = "anthropic_client_placeholder"
        except Exception as e:
            print(f"Warning: Failed to initialize LLM client: {e}")
            self.model_provider = "local"
    
    def analyze_changes(self, git_dir: str) -> Dict[str, Any]:
        """
        Analyze git changes to understand what was modified.
        
        Args:
            git_dir: Path to git repository
            
        Returns:
            Analysis of changes including files, additions, deletions
        """
        try:
            # Get staged changes
            staged_result = subprocess.run(
                ["git", "diff", "--cached", "--stat"],
                cwd=git_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get unstaged changes
            unstaged_result = subprocess.run(
                ["git", "diff", "--stat"],
                cwd=git_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get detailed diff for analysis
            diff_result = subprocess.run(
                ["git", "diff", "--cached"],
                cwd=git_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse file changes
            files_changed = self._parse_file_changes(staged_result.stdout)
            
            # Analyze diff content
            diff_analysis = self._analyze_diff_content(diff_result.stdout)
            
            return {
                "staged_changes": staged_result.stdout,
                "unstaged_changes": unstaged_result.stdout,
                "diff_content": diff_result.stdout,
                "files_changed": files_changed,
                "lines_added": sum(f.get("additions", 0) for f in files_changed),
                "lines_deleted": sum(f.get("deletions", 0) for f in files_changed),
                "change_types": diff_analysis.get("change_types", []),
                "modified_functions": diff_analysis.get("modified_functions", []),
                "added_files": diff_analysis.get("added_files", []),
                "deleted_files": diff_analysis.get("deleted_files", []),
                "modified_files": diff_analysis.get("modified_files", [])
            }
        except subprocess.CalledProcessError as e:
            return {"error": f"Failed to analyze changes: {e}"}
    
    def _parse_file_changes(self, stat_output: str) -> List[Dict[str, Any]]:
        """Parse git diff --stat output to extract file change information."""
        files = []
        for line in stat_output.strip().split('\n'):
            if '|' in line and 'file' not in line.lower():
                parts = line.split('|')
                if len(parts) >= 2:
                    filename = parts[0].strip()
                    change_info = parts[1].strip()
                    
                    # Extract additions and deletions
                    additions = 0
                    deletions = 0
                    if '+' in change_info and '-' in change_info:
                        # Format: " 3 +-"
                        numbers = re.findall(r'\d+', change_info)
                        if len(numbers) >= 2:
                            additions = int(numbers[0])
                            deletions = int(numbers[1])
                    elif '+' in change_info:
                        numbers = re.findall(r'\d+', change_info)
                        if numbers:
                            additions = int(numbers[0])
                    elif '-' in change_info:
                        numbers = re.findall(r'\d+', change_info)
                        if numbers:
                            deletions = int(numbers[0])
                    
                    files.append({
                        "filename": filename,
                        "additions": additions,
                        "deletions": deletions,
                        "change_type": self._determine_change_type(filename, additions, deletions)
                    })
        return files
    
    def _analyze_diff_content(self, diff_content: str) -> Dict[str, Any]:
        """Analyze diff content to extract semantic information."""
        analysis = {
            "change_types": [],
            "modified_functions": [],
            "added_files": [],
            "deleted_files": [],
            "modified_files": []
        }
        
        if not diff_content.strip():
            return analysis
        
        lines = diff_content.split('\n')
        current_file = None
        
        for line in lines:
            # Track file changes
            if line.startswith('diff --git'):
                current_file = line.split()[-1] if len(line.split()) > 3 else None
            elif line.startswith('new file mode'):
                if current_file:
                    analysis["added_files"].append(current_file)
            elif line.startswith('deleted file mode'):
                if current_file:
                    analysis["deleted_files"].append(current_file)
            elif line.startswith('index '):
                if current_file and current_file not in analysis["added_files"] and current_file not in analysis["deleted_files"]:
                    analysis["modified_files"].append(current_file)
            
            # Analyze code changes
            if line.startswith('+') and not line.startswith('+++'):
                change_type = self._classify_change(line[1:])
                if change_type:
                    analysis["change_types"].append(change_type)
            
            # Extract function names
            if line.startswith('@@'):
                function_match = re.search(r'@@.*?(\w+\([^)]*\))', line)
                if function_match:
                    analysis["modified_functions"].append(function_match.group(1))
        
        # Remove duplicates
        analysis["change_types"] = list(set(analysis["change_types"]))
        analysis["modified_functions"] = list(set(analysis["modified_functions"]))
        
        return analysis
    
    def _determine_change_type(self, filename: str, additions: int, deletions: int) -> str:
        """Determine the type of change based on file and statistics."""
        if additions > 0 and deletions == 0:
            return "added"
        elif additions == 0 and deletions > 0:
            return "deleted"
        elif additions > deletions:
            return "enhanced"
        elif deletions > additions:
            return "refactored"
        else:
            return "modified"
    
    def _classify_change(self, line: str) -> Optional[str]:
        """Classify the type of change based on code content."""
        line = line.strip()
        
        # Function definitions
        if re.match(r'def\s+\w+', line) or re.match(r'function\s+\w+', line):
            return "function_added"
        
        # Class definitions
        if re.match(r'class\s+\w+', line):
            return "class_added"
        
        # Import statements
        if re.match(r'import\s+', line) or re.match(r'from\s+', line):
            return "import_added"
        
        # Configuration changes
        if any(keyword in line.lower() for keyword in ['config', 'setting', 'option']):
            return "config_changed"
        
        # Test changes
        if 'test' in line.lower() or 'spec' in line.lower():
            return "test_changed"
        
        # Documentation
        if line.startswith('#') or line.startswith('//') or line.startswith('*'):
            return "documentation_added"
        
        return None
    
    def generate_message(self, changes: Dict[str, Any], style: str = "conventional") -> str:
        """
        Generate a commit message based on analyzed changes.
        
        Args:
            changes: Analysis of code changes
            style: Commit message style (conventional, semantic, etc.)
            
        Returns:
            Generated commit message
        """
        if "error" in changes:
            return "fix: resolve git analysis error"
        
        # Use LLM if available, otherwise use local analysis
        if self.model_provider != "local" and self.llm_client:
            return self._generate_with_llm(changes, style)
        else:
            return self._generate_local(changes, style)
    
    def _generate_local(self, changes: Dict[str, Any], style: str) -> str:
        """Generate commit message using local analysis."""
        files_changed = changes.get("files_changed", [])
        change_types = changes.get("change_types", [])
        added_files = changes.get("added_files", [])
        deleted_files = changes.get("deleted_files", [])
        modified_files = changes.get("modified_files", [])
        
        if not files_changed:
            return "chore: update project files"
        
        # Determine the primary change type
        primary_type = self._determine_primary_change_type(changes)
        
        # Generate scope
        scope = self._generate_scope(files_changed)
        
        # Generate description
        description = self._generate_description(changes, primary_type)
        
        # Format based on style
        if style == "conventional":
            return self._format_conventional(primary_type, scope, description, changes)
        elif style == "semantic":
            return self._format_semantic(primary_type, scope, description, changes)
        else:
            return description
    
    def _determine_primary_change_type(self, changes: Dict[str, Any]) -> str:
        """Determine the primary type of change."""
        added_files = changes.get("added_files", [])
        deleted_files = changes.get("deleted_files", [])
        change_types = changes.get("change_types", [])
        
        # Check for new features
        if any("function_added" in ct for ct in change_types):
            return "feat"
        
        # Check for bug fixes
        if any("fix" in ct.lower() or "bug" in ct.lower() for ct in change_types):
            return "fix"
        
        # Check for documentation
        if any("documentation" in ct for ct in change_types):
            return "docs"
        
        # Check for tests
        if any("test" in ct for ct in change_types):
            return "test"
        
        # Check for configuration
        if any("config" in ct for ct in change_types):
            return "config"
        
        # Check for refactoring
        if changes.get("lines_deleted", 0) > changes.get("lines_added", 0):
            return "refactor"
        
        # Default based on file changes
        if added_files:
            return "feat"
        elif deleted_files:
            return "refactor"
        else:
            return "chore"
    
    def _generate_scope(self, files_changed: List[Dict[str, Any]]) -> Optional[str]:
        """Generate scope based on changed files."""
        if not files_changed:
            return None
        
        # Group files by directory/type
        scopes = set()
        for file_info in files_changed:
            filename = file_info.get("filename", "")
            
            # Extract scope from file path
            if "/" in filename:
                parts = filename.split("/")
                if len(parts) > 1:
                    scopes.add(parts[0])
            elif "." in filename:
                ext = filename.split(".")[-1]
                if ext in ["py", "js", "ts", "java", "go", "rs"]:
                    scopes.add("core")
                elif ext in ["md", "txt", "rst"]:
                    scopes.add("docs")
                elif ext in ["json", "yaml", "yml", "toml"]:
                    scopes.add("config")
        
        # Return the most common scope or first one
        if scopes:
            return list(scopes)[0] if len(scopes) == 1 else None
        
        return None
    
    def _generate_description(self, changes: Dict[str, Any], primary_type: str) -> str:
        """Generate a descriptive message based on changes."""
        files_changed = changes.get("files_changed", [])
        added_files = changes.get("added_files", [])
        deleted_files = changes.get("deleted_files", [])
        modified_files = changes.get("modified_files", [])
        
        if primary_type == "feat":
            if added_files:
                if len(added_files) == 1:
                    return f"add {self._get_file_description(added_files[0])}"
                else:
                    return f"add {len(added_files)} new files"
            else:
                return "add new functionality"
        
        elif primary_type == "fix":
            return "fix bug or issue"
        
        elif primary_type == "docs":
            return "update documentation"
        
        elif primary_type == "test":
            return "add or update tests"
        
        elif primary_type == "refactor":
            if deleted_files:
                return f"remove {len(deleted_files)} files"
            else:
                return "refactor code"
        
        elif primary_type == "config":
            return "update configuration"
        
        else:  # chore
            if len(files_changed) == 1:
                return f"update {self._get_file_description(files_changed[0]['filename'])}"
            else:
                return f"update {len(files_changed)} files"
    
    def _get_file_description(self, filename: str) -> str:
        """Get a human-readable description of a file."""
        if "/" in filename:
            return filename.split("/")[-1]
        return filename
    
    def _format_conventional(self, primary_type: str, scope: Optional[str], description: str, changes: Dict[str, Any]) -> str:
        """Format message in conventional commit style."""
        # Add breaking change indicator if needed
        breaking = ""
        if self._is_breaking_change(changes):
            breaking = "!"
        
        # Build the message
        if scope:
            message = f"{primary_type}{breaking}({scope}): {description}"
        else:
            message = f"{primary_type}{breaking}: {description}"
        
        # Add body if there are significant changes
        if changes.get("lines_added", 0) + changes.get("lines_deleted", 0) > 50:
            message += f"\n\n- {changes['lines_added']} lines added"
            message += f"\n- {changes['lines_deleted']} lines deleted"
        
        return message
    
    def _format_semantic(self, primary_type: str, scope: Optional[str], description: str, changes: Dict[str, Any]) -> str:
        """Format message in semantic commit style."""
        # Similar to conventional but with different structure
        if scope:
            return f"{primary_type}({scope}): {description}"
        else:
            return f"{primary_type}: {description}"
    
    def _is_breaking_change(self, changes: Dict[str, Any]) -> bool:
        """Determine if this is a breaking change."""
        # Simple heuristic - can be enhanced
        deleted_files = changes.get("deleted_files", [])
        if deleted_files:
            return True
        
        # Check for API changes in modified files
        modified_files = changes.get("modified_files", [])
        for filename in modified_files:
            if any(keyword in filename.lower() for keyword in ["api", "interface", "public"]):
                return True
        
        return False
    
    def _generate_with_llm(self, changes: Dict[str, Any], style: str) -> str:
        """Generate commit message using LLM (placeholder for future implementation)."""
        # This would integrate with OpenAI, Anthropic, etc.
        # For now, fall back to local generation
        return self._generate_local(changes, style)
    
    def suggest_messages(self, changes: Dict[str, Any], count: int = 3) -> List[str]:
        """
        Generate multiple commit message suggestions.
        
        Args:
            changes: Analysis of code changes
            count: Number of suggestions to generate
            
        Returns:
            List of suggested commit messages
        """
        suggestions = []
        
        # Generate primary suggestion
        primary = self.generate_message(changes, "conventional")
        suggestions.append(primary)
        
        # Generate alternative styles
        if count > 1:
            semantic = self.generate_message(changes, "semantic")
            if semantic != primary:
                suggestions.append(semantic)
        
        # Generate alternative types
        if count > 2:
            alt_type = self._generate_alternative_type(changes)
            if alt_type and alt_type != primary:
                suggestions.append(alt_type)
        
        # Generate simple fallback
        if len(suggestions) < count:
            simple = self._generate_simple_message(changes)
            if simple not in suggestions:
                suggestions.append(simple)
        
        # Ensure we have the requested count
        while len(suggestions) < count:
            suggestions.append(f"chore: update {len(changes.get('files_changed', []))} files")
        
        return suggestions[:count]
    
    def _generate_alternative_type(self, changes: Dict[str, Any]) -> str:
        """Generate an alternative commit type suggestion."""
        files_changed = changes.get("files_changed", [])
        if not files_changed:
            return None
        
        # Try different interpretation
        if len(files_changed) == 1:
            filename = files_changed[0]['filename']
            if 'test' in filename.lower():
                return "test: add or update test cases"
            elif 'doc' in filename.lower() or filename.endswith('.md'):
                return "docs: update documentation"
            elif filename.endswith('.json') or filename.endswith('.yaml'):
                return "config: update configuration"
        
        return None
    
    def _generate_simple_message(self, changes: Dict[str, Any]) -> str:
        """Generate a simple, non-conventional commit message."""
        files_changed = changes.get("files_changed", [])
        if not files_changed:
            return "Update files"
        
        if len(files_changed) == 1:
            filename = files_changed[0]['filename']
            return f"Update {self._get_file_description(filename)}"
        else:
            return f"Update {len(files_changed)} files"


class CommitAssistant:
    """
    Interactive commit assistant with AI suggestions.
    """
    
    def __init__(self, git_dir: str, model_provider: str = "local", api_key: Optional[str] = None):
        """
        Initialize the commit assistant.
        
        Args:
            git_dir: Path to git repository
            model_provider: AI model provider
            api_key: Optional API key for LLM services
        """
        self.git_dir = git_dir
        self.generator = CommitMessageGenerator(model_provider, api_key)
    
    def interactive_commit(self) -> Optional[str]:
        """
        Interactive commit process with AI assistance.
        
        Returns:
            Selected commit message or None if cancelled
        """
        changes = self.generator.analyze_changes(self.git_dir)
        
        if "error" in changes:
            print(f"❌ Error analyzing changes: {changes['error']}")
            return None
        
        suggestions = self.generator.suggest_messages(changes, 3)
        
        print("🤖 AI-generated commit message suggestions:")
        print("=" * 50)
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")
        
        print("\n💡 Usage:")
        print("  - Use one of the suggestions above")
        print("  - Or create your own message")
        print("  - Press Ctrl+C to cancel")
        
        # For now, return the first suggestion
        # In a full implementation, this would be interactive
        return suggestions[0] if suggestions else None
    
    def get_suggestions(self, count: int = 3) -> List[str]:
        """
        Get commit message suggestions without interaction.
        
        Args:
            count: Number of suggestions to generate
            
        Returns:
            List of suggested commit messages
        """
        changes = self.generator.analyze_changes(self.git_dir)
        return self.generator.suggest_messages(changes, count)


def generate_commit_message(git_dir: str, style: str = "conventional", model_provider: str = "local", api_key: Optional[str] = None) -> str:
    """
    Convenience function to generate a commit message for a repository.
    
    Args:
        git_dir: Path to git repository
        style: Commit message style
        model_provider: AI model provider
        api_key: Optional API key for LLM services
        
    Returns:
        Generated commit message
    """
    generator = CommitMessageGenerator(model_provider, api_key)
    changes = generator.analyze_changes(git_dir)
    return generator.generate_message(changes, style)


def suggest_commit_messages(git_dir: str, count: int = 3, model_provider: str = "local", api_key: Optional[str] = None) -> List[str]:
    """
    Convenience function to get multiple commit message suggestions.
    
    Args:
        git_dir: Path to git repository
        count: Number of suggestions to generate
        model_provider: AI model provider
        api_key: Optional API key for LLM services
        
    Returns:
        List of suggested commit messages
    """
    generator = CommitMessageGenerator(model_provider, api_key)
    changes = generator.analyze_changes(git_dir)
    return generator.suggest_messages(changes, count)


def analyze_git_changes(git_dir: str) -> Dict[str, Any]:
    """
    Convenience function to analyze git changes.
    
    Args:
        git_dir: Path to git repository
        
    Returns:
        Analysis of git changes
    """
    generator = CommitMessageGenerator()
    return generator.analyze_changes(git_dir)

"""
Secret detection scanner for JJ-Git Sync Tool.

This module provides comprehensive security scanning functionality to detect
sensitive information like API keys, passwords, tokens, and other secrets
in Git commits and code changes.

Week 2 implementation with enhanced patterns and CI integration.
"""

import re
import json
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime


class SecretScanner:
    """
    Comprehensive scanner for detecting secrets and sensitive information in commits.
    """
    
    def __init__(self):
        """Initialize the secret scanner with comprehensive patterns."""
        # Enhanced secret patterns for Week 2
        self.patterns = {
            # API Keys
            'api_key': re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})', re.IGNORECASE),
            'aws_access_key': re.compile(r'AKIA[0-9A-Z]{16}', re.IGNORECASE),
            'aws_secret_key': re.compile(r'aws[_-]?secret[_-]?key["\']?\s*[:=]\s*["\']?([A-Za-z0-9/+=]{40})', re.IGNORECASE),
            'google_api_key': re.compile(r'AIza[0-9A-Za-z_-]{35}', re.IGNORECASE),
            'github_token': re.compile(r'ghp_[a-zA-Z0-9]{36}', re.IGNORECASE),
            'github_pat': re.compile(r'github_pat_[a-zA-Z0-9_]{82}', re.IGNORECASE),
            
            # Passwords
            'password': re.compile(r'password["\']?\s*[:=]\s*["\']?([^\s"\']{8,})', re.IGNORECASE),
            'passwd': re.compile(r'passwd["\']?\s*[:=]\s*["\']?([^\s"\']{8,})', re.IGNORECASE),
            'pwd': re.compile(r'pwd["\']?\s*[:=]\s*["\']?([^\s"\']{8,})', re.IGNORECASE),
            
            # Tokens
            'token': re.compile(r'token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})', re.IGNORECASE),
            'jwt_token': re.compile(r'eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', re.IGNORECASE),
            'bearer_token': re.compile(r'bearer\s+([a-zA-Z0-9_-]{20,})', re.IGNORECASE),
            
            # Database credentials
            'db_password': re.compile(r'db[_-]?password["\']?\s*[:=]\s*["\']?([^\s"\']{8,})', re.IGNORECASE),
            'database_url': re.compile(r'(?:mysql|postgres|mongodb)://[^\s]+', re.IGNORECASE),
            
            # SSH Keys
            'ssh_private_key': re.compile(r'-----BEGIN [A-Z ]+ PRIVATE KEY-----', re.IGNORECASE),
            'ssh_public_key': re.compile(r'ssh-[a-z]+ [A-Za-z0-9+/=]+', re.IGNORECASE),
            
            # Generic secrets
            'secret': re.compile(r'secret["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{16,})', re.IGNORECASE),
            'private_key': re.compile(r'private[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})', re.IGNORECASE),
            'access_token': re.compile(r'access[_-]?token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})', re.IGNORECASE),
        }
        
        # Severity levels for different secret types
        self.severity_levels = {
            'api_key': 'HIGH',
            'aws_access_key': 'CRITICAL',
            'aws_secret_key': 'CRITICAL',
            'google_api_key': 'HIGH',
            'github_token': 'HIGH',
            'github_pat': 'HIGH',
            'password': 'HIGH',
            'passwd': 'HIGH',
            'pwd': 'HIGH',
            'token': 'MEDIUM',
            'jwt_token': 'MEDIUM',
            'bearer_token': 'MEDIUM',
            'db_password': 'CRITICAL',
            'database_url': 'HIGH',
            'ssh_private_key': 'CRITICAL',
            'ssh_public_key': 'LOW',
            'secret': 'MEDIUM',
            'private_key': 'HIGH',
            'access_token': 'HIGH',
        }
    
    def scan_content(self, content: str, file_path: str = None) -> List[Dict[str, Any]]:
        """
        Scan content for potential secrets.
        
        Args:
            content: Text content to scan
            file_path: Optional file path for context
            
        Returns:
            List of detected secrets with metadata
        """
        secrets = []
        
        for secret_type, pattern in self.patterns.items():
            matches = pattern.finditer(content)
            for match in matches:
                # Calculate line and column numbers
                line_num = content[:match.start()].count('\n') + 1
                column_num = match.start() - content.rfind('\n', 0, match.start())
                
                # Extract the matched value (handle different group patterns)
                if match.groups():
                    value = match.group(1)
                else:
                    value = match.group(0)
                
                # Filter out false positives
                if self._is_false_positive(value, content, match.start(), match.end()):
                    continue
                
                secrets.append({
                    'type': secret_type,
                    'value': value,
                    'severity': self.severity_levels.get(secret_type, 'MEDIUM'),
                    'line': line_num,
                    'column': column_num,
                    'file_path': file_path,
                    'context': self._get_context(content, match.start(), match.end()),
                    'timestamp': datetime.now().isoformat()
                })
        
        return secrets
    
    def _is_false_positive(self, value: str, content: str, start: int, end: int) -> bool:
        """
        Check if a detected secret is likely a false positive.
        
        Args:
            value: The detected secret value
            content: Full content
            start: Start position of match
            end: End position of match
            
        Returns:
            True if this is likely a false positive
        """
        # Get context around the match
        context_start = max(0, start - 50)
        context_end = min(len(content), end + 50)
        context = content[context_start:context_end].lower()
        
        # Skip if it looks like a commit hash (40 chars, all hex)
        if len(value) == 40 and all(c in '0123456789abcdef' for c in value.lower()):
            return True
        
        # Skip if it's in a regex pattern
        if 're.compile' in context or 'regex' in context:
            return True
        
        # Skip if it's in a git diff header or commit message
        if any(x in context for x in ['commit ', 'author:', 'date:', 'feat:', 'fix:', 'chore:', 'docs:']):
            return True
        
        # Skip if it's clearly a file path or URL
        if '/' in value and ('.py' in context or '.md' in context or '.txt' in context):
            return True
        
        # Skip if it's a severity level or enum value (but only in specific contexts)
        if value.upper() in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            # Skip if it's in a dictionary definition, git diff, or commit message
            if any(x in context for x in [':', '=', 'severity', 'level', 'commit', 'author', 'date', 'feat:', 'fix:', 'chore:', 'docs:']):
                return True
        
        # Skip if it's in a comment
        if '#' in context and context.find('#') < context.find(value.lower()):
            return True
        
        return False
    
    def scan_commit(self, commit_hash: str, git_dir: str = ".") -> List[Dict[str, Any]]:
        """
        Scan a specific commit for secrets.
        
        Args:
            commit_hash: Git commit hash to scan
            git_dir: Path to git repository
            
        Returns:
            List of detected secrets
        """
        try:
            # Get commit diff
            result = subprocess.run(
                ["git", "show", "--name-only", commit_hash],
                cwd=git_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout.strip():
                return []
            
            # Get the actual diff content
            diff_result = subprocess.run(
                ["git", "show", commit_hash],
                cwd=git_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            all_secrets = []
            files = result.stdout.strip().split('\n')
            
            for file_path in files:
                if file_path.strip():
                    # Extract file content from diff
                    file_secrets = self.scan_content(diff_result.stdout, file_path)
                    all_secrets.extend(file_secrets)
            
            return all_secrets
            
        except subprocess.CalledProcessError as e:
            print(f"Error scanning commit {commit_hash}: {e}")
            return []
    
    def scan_recent_commits(self, git_dir: str = ".", count: int = 5) -> List[Dict[str, Any]]:
        """
        Scan recent commits for secrets.
        
        Args:
            git_dir: Path to git repository
            count: Number of recent commits to scan
            
        Returns:
            List of detected secrets from recent commits
        """
        try:
            # Get recent commit hashes
            result = subprocess.run(
                ["git", "log", "--oneline", "-n", str(count), "--format=%H"],
                cwd=git_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            commit_hashes = result.stdout.strip().split('\n')
            all_secrets = []
            
            for commit_hash in commit_hashes:
                if commit_hash.strip():
                    secrets = self.scan_commit(commit_hash.strip(), git_dir)
                    for secret in secrets:
                        secret['commit_hash'] = commit_hash.strip()
                    all_secrets.extend(secrets)
            
            return all_secrets
            
        except subprocess.CalledProcessError as e:
            print(f"Error scanning recent commits: {e}")
            return []
    
    def _get_context(self, content: str, start: int, end: int, context_lines: int = 2) -> str:
        """
        Get context around a match for better debugging.
        
        Args:
            content: Full content
            start: Start position of match
            end: End position of match
            context_lines: Number of lines before/after to include
            
        Returns:
            Context string around the match
        """
        lines = content.split('\n')
        match_line = content[:start].count('\n')
        
        start_line = max(0, match_line - context_lines)
        end_line = min(len(lines), match_line + context_lines + 1)
        
        context = lines[start_line:end_line]
        return '\n'.join(context)
    
    def generate_report(self, secrets: List[Dict[str, Any]], format: str = "human") -> str:
        """
        Generate a security scan report.
        
        Args:
            secrets: List of detected secrets
            format: Output format ("human" or "json")
            
        Returns:
            Formatted report string
        """
        if format == "json":
            return self._generate_json_report(secrets)
        else:
            return self._generate_human_report(secrets)
    
    def _generate_human_report(self, secrets: List[Dict[str, Any]]) -> str:
        """Generate human-readable report."""
        if not secrets:
            return "✅ No secrets detected in the scan."
        
        # Group by severity
        by_severity = {}
        for secret in secrets:
            severity = secret['severity']
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(secret)
        
        report = ["🔍 Security Scan Results", "=" * 50, ""]
        
        # Summary
        total = len(secrets)
        critical = len(by_severity.get('CRITICAL', []))
        high = len(by_severity.get('HIGH', []))
        medium = len(by_severity.get('MEDIUM', []))
        low = len(by_severity.get('LOW', []))
        
        report.append(f"📊 Summary: {total} secrets found")
        report.append(f"   🔴 Critical: {critical}")
        report.append(f"   🟠 High: {high}")
        report.append(f"   🟡 Medium: {medium}")
        report.append(f"   🟢 Low: {low}")
        report.append("")
        
        # Details by severity
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if severity in by_severity:
                report.append(f"🚨 {severity} Severity Issues:")
                for secret in by_severity[severity]:
                    file_info = f" in {secret['file_path']}" if secret.get('file_path') else ""
                    report.append(f"   • {secret['type'].upper()}{file_info} (line {secret['line']})")
                    report.append(f"     Value: {secret['value'][:20]}{'...' if len(secret['value']) > 20 else ''}")
                    if secret.get('context'):
                        report.append(f"     Context: {secret['context'][:100]}{'...' if len(secret['context']) > 100 else ''}")
                    report.append("")
        
        return '\n'.join(report)
    
    def _generate_json_report(self, secrets: List[Dict[str, Any]]) -> str:
        """Generate JSON report for CI integration."""
        report = {
            "scan_timestamp": datetime.now().isoformat(),
            "total_secrets": len(secrets),
            "summary": {
                "critical": len([s for s in secrets if s['severity'] == 'CRITICAL']),
                "high": len([s for s in secrets if s['severity'] == 'HIGH']),
                "medium": len([s for s in secrets if s['severity'] == 'MEDIUM']),
                "low": len([s for s in secrets if s['severity'] == 'LOW'])
            },
            "secrets": secrets
        }
        return json.dumps(report, indent=2)


def scan_for_secrets(content: str, file_path: str = None) -> List[Dict[str, Any]]:
    """
    Convenience function to scan content for secrets.
    
    Args:
        content: Text content to scan
        file_path: Optional file path for context
        
    Returns:
        List of detected secrets
    """
    scanner = SecretScanner()
    return scanner.scan_content(content, file_path)


def scan_commit_for_secrets(commit_hash: str, git_dir: str = ".") -> List[Dict[str, Any]]:
    """
    Convenience function to scan a commit for secrets.
    
    Args:
        commit_hash: Git commit hash to scan
        git_dir: Path to git repository
        
    Returns:
        List of detected secrets
    """
    scanner = SecretScanner()
    return scanner.scan_commit(commit_hash, git_dir)


def scan_recent_commits_for_secrets(git_dir: str = ".", count: int = 5) -> List[Dict[str, Any]]:
    """
    Convenience function to scan recent commits for secrets.
    
    Args:
        git_dir: Path to git repository
        count: Number of recent commits to scan
        
    Returns:
        List of detected secrets
    """
    scanner = SecretScanner()
    return scanner.scan_recent_commits(git_dir, count)


def generate_security_report(secrets: List[Dict[str, Any]], format: str = "human") -> str:
    """
    Convenience function to generate a security report.
    
    Args:
        secrets: List of detected secrets
        format: Output format ("human" or "json")
        
    Returns:
        Formatted report string
    """
    scanner = SecretScanner()
    return scanner.generate_report(secrets, format)

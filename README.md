# JJ–Git Sync Tool (PoC)

A proof-of-concept tool to sync branches and commits between [JJ](https://github.com/jj-vcs/jj) and Git.

## Features

### Week 1 ✅
- Export JJ commits into Git
- Import Git commits into JJ
- List Git branches

### Week 2 ✅
- **Security Scanning**: Detect secrets in commits (API keys, passwords, tokens)
- **Compliance Reporting**: Human-readable and JSON output formats
- **CI Integration**: JSON output for automated pipelines
- **Severity Levels**: Critical, High, Medium, Low classification
- **Multiple Scan Modes**: Recent commits, specific commit, or integrated with sync

### Planned Features
- **Week 3**: AI commit assistance

## Project Structure
```
jj-git-sync-tool/
├── README.md
├── requirements.txt
├── sync.py              # Main CLI application
├── scanners/
│   └── secrets.py       # Security scanning (Week 2)
└── ai/
    └── commitgen.py     # AI commit assistant (Week 3)
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Prerequisites

- Python 3.7+
- [JJ](https://github.com/jj-vcs/jj) installed and in your PATH
- Git installed

## Usage

### Sync between JJ and Git
```bash
# Basic sync
python sync.py sync --git-dir /path/to/git --jj-dir /path/to/jj

# Sync with security scan
python sync.py sync --git-dir /path/to/git --jj-dir /path/to/jj --scan

# Sync with JSON security report (for CI)
python sync.py sync --git-dir /path/to/git --jj-dir /path/to/jj --scan --scan-format json
```

### Security Scanning
```bash
# Scan recent commits (default: last 5)
python sync.py scan --git-dir /path/to/git

# Scan specific number of commits
python sync.py scan --git-dir /path/to/git --commits 10

# Scan specific commit
python sync.py scan --git-dir /path/to/git --commit abc123

# JSON output for CI integration
python sync.py scan --git-dir /path/to/git --format json
```

### List Git branches
```bash
python sync.py list-branches --git-dir /path/to/git
```

### Help
```bash
python sync.py --help
python sync.py sync --help
python sync.py scan --help
python sync.py list-branches --help
```

## Security Scanning

The tool includes comprehensive security scanning capabilities:

### Detected Secret Types
- **API Keys**: AWS, Google, GitHub tokens
- **Passwords**: Various password patterns
- **Database Credentials**: Connection strings and passwords
- **SSH Keys**: Private and public keys
- **JWT Tokens**: Bearer tokens and JWTs
- **Generic Secrets**: Custom secret patterns

### Severity Levels
- 🔴 **CRITICAL**: AWS keys, database passwords, SSH private keys
- 🟠 **HIGH**: API keys, passwords, access tokens
- 🟡 **MEDIUM**: Generic tokens, secrets
- 🟢 **LOW**: SSH public keys

### Output Formats
- **Human**: Detailed, color-coded reports for developers
- **JSON**: Machine-readable format for CI/CD pipelines

## Development

This is a modular design to support future extensions:

- `sync.py`: Main CLI interface with basic sync functionality
- `scanners/`: Security scanning modules (placeholder for Week 2)
- `ai/`: AI-powered commit assistance (placeholder for Week 3)

## License

MIT License
# JJ–Git Sync Tool (PoC)

A proof-of-concept tool to sync branches and commits between [JJ](https://github.com/jj-vcs/jj) and Git.

## Features (Week 1)
- Export JJ commits into Git
- Import Git commits into JJ
- List Git branches

## Planned Features
- **Week 2**: Security scanning (detect secrets in commits)
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
python sync.py sync --git-dir /path/to/git --jj-dir /path/to/jj
```

### List Git branches
```bash
python sync.py list-branches --git-dir /path/to/git
```

### Help
```bash
python sync.py --help
python sync.py sync --help
python sync.py list-branches --help
```

## Development

This is a modular design to support future extensions:

- `sync.py`: Main CLI interface with basic sync functionality
- `scanners/`: Security scanning modules (placeholder for Week 2)
- `ai/`: AI-powered commit assistance (placeholder for Week 3)

## License

MIT License
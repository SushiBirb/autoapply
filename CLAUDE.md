# CLAUDE.md — autoapply Project Context

## Tech Stack
- **Language**: Python 3.11+
- **Package Management & Environment**: `uv` / `setuptools` (`pyproject.toml`)
- **CLI & UI**: Click (`click>=8.1`), Rich (`rich>=13.0`), PyYAML (`PyYAML>=6.0`)
- **Storage**: SQLite (`sqlite3` stdlib) for applications & status history, YAML for master profile
- **Planned / Optional Dependencies**:
  - `playwright>=1.50` (Phase 2: Browser automation)
  - `google-genai>=1.0` (Phase 3: Gemini screening question answer generation)
  - `pytest>=8.0` (Testing framework)

## Common Commands
- **Install dependencies**: `uv sync --extra dev --extra browser --extra llm`
- **Environment check**: `uv run autoapply doctor`
- **Initialize master profile**: `uv run autoapply profile init`
- **Show master profile**: `uv run autoapply profile show`
- **Log manual application**: `uv run autoapply log --company "Acme" --title "Security Intern" --status "submitted"`
- **List tracked applications**: `uv run autoapply list`
- **View funnel analytics**: `uv run autoapply stats`
- **Run tests**: `uv run pytest`

## Architecture & Code Structure
- `autoapply/cli.py`: Click command group & subcommands (`profile`, `log`, `list`, `status`, `search`, `stats`, `doctor`, `open-url`).
- `autoapply/config.py`: Data directory paths, platform/channel/status constants, file permission modes.
- `autoapply/ui.py`: Rich console output helpers (colorized text, confirmations, prompt helpers).
- `autoapply/profile/`:
  - `schema.py`: 40-field profile schema definition and field lists.
  - `seed.py`: Candidate seed data (pre-filled resume information).
  - `manager.py`: Interactive CLI questionnaire for seeding/updating `data/master.yaml`.
- `autoapply/tracker/`:
  - `db.py`: SQLite database schema, `Application` dataclass, `ApplicationDB` CRUD & metrics engine.
- `data/`: Local storage directory (contains `master.yaml`, `autoapply.db`, `audit.log`, `resume/`).

## Key Conventions & Principles
- **Review-Before-Submit**: Application submission must always involve explicit human review.
- **Local-First**: Candidate data and application logs remain in local `data/` files; no remote database.
- **Permissions**: Sensitive profile YAML and SQLite DB are created with strict permissions (`0o600`).

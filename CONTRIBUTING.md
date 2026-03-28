# Contributing to GESIS Surf Backend

Thank you for your interest in contributing to GESIS Surf Backend! This document outlines our development workflow, branching strategy, and commit conventions.

## 📋 Table of Contents

- [Development Workflow](#development-workflow)
- [Branching Strategy](#branching-strategy)
- [Commit Conventions](#commit-conventions)
- [Pull Request Process](#pull-request-process)
- [Code Quality](#code-quality)
- [Getting Started](#getting-started)

---

## 🔄 Development Workflow

We follow a **Git Flow** inspired workflow with continuous integration:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION                                   │
│                           prod                                       │
│                            ▲                                         │
│                            │ (admin merge only)                      │
│                            │                                         │
│ ───────────────────────────┼─────────────────────────────────────── │
│                         STAGING                                      │
│                           main                                       │
│                            ▲                                         │
│                            │ (merge/release)                         │
│                            │                                         │
│ ───────────────────────────┼─────────────────────────────────────── │
│                        DEVELOPMENT                                   │
│                           dev                                        │
│                         ▲  ▲  ▲                                      │
│                        /   │   \                                     │
│                       /    │    \                                    │
│ ─────────────────────/─────┼─────\─────────────────────────────────  │
│               FEATURE BRANCHES                                       │
│                                                                      │
│   feature/    bugfix/     hotfix/     refactor/                      │
│   add-auth    fix-login   critical    cleanup-models                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Branch Hierarchy

| Branch       | Purpose                   | Deployed To        | Merge Access |
| ------------ | ------------------------- | ------------------ | ------------ |
| `prod`       | Production-ready code     | Production server  | Admin only   |
| `main`       | Staging/Testing           | Staging server     | Maintainers  |
| `dev`        | Development integration   | Development server | Contributors |
| `feature/*`  | New features              | Local/PR preview   | -            |
| `bugfix/*`   | Non-critical bug fixes    | Local/PR preview   | -            |
| `hotfix/*`   | Critical production fixes | Direct to prod     | Admin only   |
| `refactor/*` | Code improvements         | Local/PR preview   | -            |

---

## 🌿 Branching Strategy

### Creating a Feature Branch

```bash
# Start from dev branch
git checkout dev
git pull origin dev

# Create your feature branch
git checkout -b feature/your-feature-name
```

### Branch Naming Convention

Use the following prefixes:

| Prefix      | Use Case                | Example                      |
| ----------- | ----------------------- | ---------------------------- |
| `feature/`  | New functionality       | `feature/add-user-analytics` |
| `bugfix/`   | Bug fixes               | `bugfix/fix-scroll-tracking` |
| `hotfix/`   | Urgent production fixes | `hotfix/security-patch`      |
| `refactor/` | Code refactoring        | `refactor/optimize-queries`  |
| `docs/`     | Documentation updates   | `docs/update-api-guide`      |
| `test/`     | Test additions          | `test/add-click-tests`       |

### Workflow Steps

1. **Create branch** from `dev`
2. **Develop** your feature with atomic commits
3. **Push** your branch to remote
4. **Create PR** targeting `dev`
5. **Code Review** by team members
6. **Merge** after approval
7. **Delete** feature branch after merge

### Promotion Flow

```
feature/* ──▶ dev ──▶ main (staging) ──▶ prod (production)
              │           │                    │
              │           │                    └── Admin merge only
              │           └── Maintainer merge
              └── Contributor merge after review
```

---

## 📝 Commit Conventions

We use **[Commitizen](https://commitizen-tools.github.io/commitizen/)** with **Conventional Commits** specification.

### Commit Message Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

### Commit Types

| Type       | Description             | Example                                         |
| ---------- | ----------------------- | ----------------------------------------------- |
| `feat`     | New feature             | `feat(auth): add token refresh endpoint`        |
| `fix`      | Bug fix                 | `fix(clicks): resolve duplicate tracking issue` |
| `docs`     | Documentation           | `docs(readme): update installation steps`       |
| `style`    | Code style (formatting) | `style(models): apply black formatting`         |
| `refactor` | Code refactoring        | `refactor(views): simplify query logic`         |
| `perf`     | Performance improvement | `perf(elasticsearch): optimize bulk indexing`   |
| `test`     | Adding/updating tests   | `test(domain): add serializer tests`            |
| `build`    | Build system changes    | `build(docker): update base image`              |
| `ci`       | CI/CD changes           | `ci(github): add test workflow`                 |
| `chore`    | Maintenance tasks       | `chore(deps): update dependencies`              |

### Using Commitizen

```bash
# Install commitizen (included in dev dependencies)
poetry install

# Make your changes, then stage them
git add .

# Use commitizen to create a commit
cz commit
# or
poetry run cz commit
```

Commitizen will guide you through creating a properly formatted commit:

```
? Select the type of change you are committing: feat
? What is the scope of this change? (press enter to skip) auth
? Write a short description: add JWT token refresh endpoint
? Provide additional contextual information: (press enter to skip)
? Is this a BREAKING CHANGE? No
```

### Pre-commit Hooks

We use **pre-commit** to ensure code quality before commits:

```bash
# Install pre-commit hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

---

## 🔀 Pull Request Process

### Before Creating a PR

1. ✅ Ensure all tests pass: `pytest`
2. ✅ Run linters: `flake8 app/`
3. ✅ Format code: `black app/`
4. ✅ Check types: `mypy app/`
5. ✅ Update documentation if needed

### PR Title Convention

Follow the same format as commits:

```
feat(scope): description
fix(scope): description
```

### PR Template

When creating a PR, include:

- **Description**: What does this PR do?
- **Related Issue**: Link to issue if applicable
- **Type of Change**: Feature / Bug fix / Refactor / etc.
- **Testing**: How was this tested?
- **Checklist**:
  - [ ] Tests added/updated
  - [ ] Documentation updated
  - [ ] No breaking changes (or documented)

### Merge Strategy

- **Feature → Dev**: Squash and merge
- **Dev → Main**: Merge commit (preserves history)
- **Main → Prod**: Merge commit (admin only)
- **Hotfix → Prod**: Merge commit (admin only)

---

## 🔍 Code Quality

We use **pre-commit** hooks to ensure consistent code quality before every commit and push.

### Pre-commit Hooks

Our `.pre-commit-config.yaml` includes the following hooks:

#### 🔒 Pre-commit Stage (runs on every commit)

| Hook                        | Purpose                                                  |
| --------------------------- | -------------------------------------------------------- |
| **check-added-large-files** | Prevents large files from being committed                |
| **check-merge-conflict**    | Detects unresolved merge conflicts                       |
| **check-toml**              | Validates TOML file syntax                               |
| **check-yaml**              | Validates YAML file syntax                               |
| **trailing-whitespace**     | Removes trailing whitespace                              |
| **end-of-file-fixer**       | Ensures files end with a newline                         |
| **black**                   | Python code formatting (PEP 8)                           |
| **isort**                   | Sorts and organizes imports                              |
| **autoflake**               | Removes unused imports                                   |
| **flake8**                  | Linting with plugins (bugbear, bandit, docstrings, etc.) |
| **mypy**                    | Static type checking                                     |
| **pylint**                  | Code analysis with Django plugin                         |
| **pyupgrade**               | Upgrades syntax to Python 3.10+                          |
| **prettier**                | Formats JS, CSS, Markdown, JSON, YAML                    |
| **eslint**                  | JavaScript linting                                       |
| **django-upgrade**          | Upgrades Django code to 4.2+ syntax                      |
| **djhtml**                  | Formats Django HTML templates                            |
| **curlylint**               | Lints HTML/Jinja templates                               |
| **blacken-docs**            | Formats Python code in documentation                     |
| **commitizen**              | Validates commit message format                          |

#### 🚀 Pre-push Stage

| Hook                  | Purpose                         |
| --------------------- | ------------------------------- |
| **commitizen-branch** | Validates branch commit history |

### Installing Pre-commit Hooks

```bash
# Install pre-commit (included in dev dependencies)
poetry install

# Install the git hooks
poetry run pre-commit install
poetry run pre-commit install --hook-type pre-push

# Run all hooks on all files (first time or manual check)
poetry run pre-commit run --all-files
```

### Flake8 Plugins

Our Flake8 configuration includes these plugins for comprehensive linting:

- `flake8-bugbear` - Finds likely bugs and design problems
- `flake8-bandit` - Security issue detection
- `flake8-docstrings` - Docstring style checking
- `flake8-comprehensions` - Better list/dict/set comprehensions
- `flake8-annotations` - Type annotation checking
- `flake8-django` - Django-specific checks
- `flake8-quotes` - Quote consistency
- `pep8-naming` - PEP 8 naming conventions

### Required Tools Summary

All tools are configured in `pyproject.toml` and `.pre-commit-config.yaml`:

| Tool       | Purpose         | Command       |
| ---------- | --------------- | ------------- |
| **Black**  | Code formatting | `black app/`  |
| **isort**  | Import sorting  | `isort app/`  |
| **Flake8** | Linting         | `flake8 app/` |
| **MyPy**   | Type checking   | `mypy app/`   |
| **Pylint** | Code analysis   | `pylint app/` |
| **Pytest** | Testing         | `pytest`      |

### Running All Checks Manually

```bash
# Run all pre-commit hooks
poetry run pre-commit run --all-files

# Or run individual tools
black app/ && isort app/   # Format code
flake8 app/                 # Lint
mypy app/                   # Type check
pytest                      # Run tests
```

---

## 🚀 Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/gesis_surf_backend.git
cd gesis_surf_backend
```

### 2. Set Up Development Environment

```bash
# Install dependencies with Poetry
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Set up commitizen
poetry run cz init  # if not already configured
```

### 3. Create Your Branch

```bash
git checkout dev
git pull origin dev
git checkout -b feature/your-feature-name
```

### 4. Make Changes and Commit

```bash
# Stage your changes
git add .

# Commit using commitizen
poetry run cz commit

# Push your branch
git push origin feature/your-feature-name
```

### 5. Create Pull Request

1. Go to GitHub repository
2. Click "Compare & pull request"
3. Select `dev` as base branch
4. Fill in the PR template
5. Request review from team members

---

## 📊 Release Process

### Version Bumping

We use Commitizen for semantic versioning:

```bash
# Bump version based on commits (auto-detects type)
cz bump

# Bump specific version
cz bump --increment MINOR

# Dry run to see what would happen
cz bump --dry-run
```

### Release Flow

```
dev ──────────────────────────────▶ main ──────────────────────────────▶ prod
     │                                │                                    │
     │  1. Merge feature PRs          │  1. Review staging tests           │
     │  2. Run integration tests      │  2. Version bump (cz bump)         │
     │  3. Fix any issues             │  3. Update CHANGELOG               │
     │                                │  4. Create release PR              │
     │                                │  5. Admin merge to prod            │
     │                                │  6. Tag release                    │
     │                                │  7. Deploy to production           │
     └────────────────────────────────┴────────────────────────────────────┘
```

---

## ❓ Questions?

- **Email**: mario.ramirez@gesis.org
- **GitHub Issues**: [Create an issue](https://github.com/geomario/gesis_surf_backend/issues)

---

<div align="center">

**Happy Contributing! 🎉**

</div>

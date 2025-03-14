# Contributing to DiscoSui

Thank you for your interest in contributing to DiscoSui! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please read it before contributing.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/discosui.git
   cd discosui
   ```
3. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

1. Set up Python environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write comprehensive docstrings
- Keep functions focused and small
- Use meaningful variable names

### Testing

- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Maintain test coverage above 80%
- Write integration tests for complex features

### Documentation

- Update documentation for new features
- Keep API documentation up to date
- Add docstrings to all public functions
- Update architecture docs when needed

### Commit Messages

Follow the conventional commits specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test updates
- `chore:` Maintenance tasks

Example:
```
feat: add email processing service

- Add email parsing functionality
- Implement email to note conversion
- Add tests for email processing
```

## Pull Request Process

1. Update documentation
2. Add or update tests
3. Ensure CI passes
4. Update CHANGELOG.md
5. Request review from maintainers

### PR Title Format

Use the same format as commit messages:
```
feat: add email processing service
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing done

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, maintainers will merge

## Release Process

1. Version bumped according to semver
2. CHANGELOG.md updated
3. Release notes created
4. Tags created and pushed

## Getting Help

- Open an issue for bugs
- Discuss major changes in issues first
- Join our community chat for questions

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License. 
# Note Template Enforcement

This module provides functionality for enforcing template structure on notes in the Obsidian vault. It includes tools for template validation, auditing, and automated fixing of template issues.

## Features

- **Template Validation**: Validate individual notes against their corresponding templates
- **Vault Auditing**: Perform comprehensive audits of the entire vault or specific folders
- **Automated Fixing**: Automatically fix common template issues
- **Scheduled Audits**: Configure and run regular template audits
- **Detailed Reporting**: Generate detailed audit reports with issues and fixes

## Usage

### Command Line Interface

The module provides a CLI for managing templates and audits:

```bash
# Validate a single note
python -m src.features.note_management.cli template validate path/to/note.md

# Run an audit on the entire vault
python -m src.features.note_management.cli template audit

# Run an audit on a specific folder
python -m src.features.note_management.cli template audit path/to/folder

# Configure audit schedule
python -m src.features.note_management.cli template schedule configure --frequency daily --auto-fix

# Run scheduled audit
python -m src.features.note_management.cli template schedule run

# Check schedule status
python -m src.features.note_management.cli template schedule status
```

### Python API

```python
from src.services.content.manipulation import TemplateEnforcementTool, TemplateScheduler

# Validate a note
tool = TemplateEnforcementTool()
result = tool.forward(action="validate", path="path/to/note.md")

# Run an audit
result = tool.forward(action="audit", path="path/to/folder", auto_fix=True)

# Configure and run scheduled audits
scheduler = TemplateScheduler()
scheduler.update_schedule(frequency="daily", auto_fix=True)
result = scheduler.run_audit()
```

## Template Structure

Templates are stored in the `.templates` directory of the vault. Each template follows this structure:

```markdown
---
node_type: #Type
created_date: {{date:YYYY-MM-DD HH:mm:ss}}
parent_node: "[[parent node]]"
related_nodes:
  - "[[other_relevant_node1]]"
  - "[[other_relevant_node2]]"
tags:
  - #concept1
  - #concept2
---

# {{title}}

## Section 1
Content for section 1

## Section 2
Content for section 2
```

## Available Templates

- **Category (#Category)**: For organizing broad topics
- **Document (#Document)**: For formal documents and reports
- **Note (#Note)**: For general notes and ideas
- **Code (#Code)**: For code snippets and documentation
- **Log (#Log)**: For activity logs and transcriptions
- **Main (#Main)**: For project overviews and main pages
- **Person (#Person)**: For personal information and contacts
- **Mail (#Mail)**: For email content and correspondence

## Audit Reports

Audit reports are generated in the `Audit Reports` folder of the vault. Each report includes:

- Summary of files checked
- List of files with issues
- Detailed breakdown of frontmatter and structure issues
- Recommendations for fixes

## Configuration

The template enforcement system can be configured through the `.obsidian/template_schedule.json` file:

```json
{
  "enabled": true,
  "frequency": "daily",
  "last_run": null,
  "auto_fix": false,
  "notify_on_issues": true,
  "excluded_folders": []
}
```

## Error Handling

The system handles various error cases:

- Missing templates
- Invalid frontmatter
- Missing required sections
- File system errors
- Template rendering errors

All errors are logged and reported in the audit reports.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
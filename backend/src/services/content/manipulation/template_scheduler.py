import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from ...core.obsidian_utils import ObsidianUtils
from ...tools.template_tools import TemplateEnforcementTool

class TemplateScheduler:
    def __init__(self):
        self.obsidian = ObsidianUtils()
        self.template_tool = TemplateEnforcementTool()
        self.schedule_file = os.path.join(self.obsidian.vault_path, ".obsidian", "template_schedule.json")
        self._load_schedule()

    def _load_schedule(self) -> None:
        """Load the schedule configuration from file."""
        try:
            if os.path.exists(self.schedule_file):
                with open(self.schedule_file, 'r') as f:
                    self.schedule = json.load(f)
            else:
                self.schedule = {
                    "enabled": True,
                    "frequency": "daily",  # daily, weekly, monthly
                    "last_run": None,
                    "auto_fix": False,
                    "notify_on_issues": True,
                    "excluded_folders": []
                }
                self._save_schedule()
        except Exception as e:
            print(f"Error loading schedule: {str(e)}")
            self.schedule = {
                "enabled": True,
                "frequency": "daily",
                "last_run": None,
                "auto_fix": False,
                "notify_on_issues": True,
                "excluded_folders": []
            }

    def _save_schedule(self) -> None:
        """Save the schedule configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.schedule_file), exist_ok=True)
            with open(self.schedule_file, 'w') as f:
                json.dump(self.schedule, f, indent=2)
        except Exception as e:
            print(f"Error saving schedule: {str(e)}")

    def update_schedule(self, **kwargs) -> Dict[str, Any]:
        """Update the schedule configuration."""
        try:
            for key, value in kwargs.items():
                if key in self.schedule:
                    self.schedule[key] = value
            self._save_schedule()
            return {
                "success": True,
                "message": "Schedule updated successfully",
                "schedule": self.schedule
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to update schedule: {str(e)}",
                "error": str(e)
            }

    def should_run_audit(self) -> bool:
        """Check if an audit should be run based on the schedule."""
        if not self.schedule["enabled"]:
            return False

        if not self.schedule["last_run"]:
            return True

        last_run = datetime.fromisoformat(self.schedule["last_run"])
        now = datetime.now()

        if self.schedule["frequency"] == "daily":
            return (now - last_run).days >= 1
        elif self.schedule["frequency"] == "weekly":
            return (now - last_run).days >= 7
        elif self.schedule["frequency"] == "monthly":
            return (now - last_run).days >= 30
        else:
            return False

    def run_audit(self) -> Dict[str, Any]:
        """Run a template audit based on the schedule."""
        try:
            if not self.should_run_audit():
                return {
                    "success": True,
                    "message": "Audit not due yet",
                    "next_run": self._get_next_run_time()
                }

            # Run the audit
            result = self.template_tool.forward(
                action="audit",
                auto_fix=self.schedule["auto_fix"]
            )

            # Update last run time
            self.schedule["last_run"] = datetime.now().isoformat()
            self._save_schedule()

            # Create audit report
            if result["success"] and result.get("files_with_issues", 0) > 0:
                self._create_audit_report(result)

            return {
                "success": True,
                "message": "Audit completed successfully",
                "results": result,
                "next_run": self._get_next_run_time()
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to run audit: {str(e)}",
                "error": str(e)
            }

    def _get_next_run_time(self) -> Optional[str]:
        """Calculate the next scheduled run time."""
        if not self.schedule["enabled"] or not self.schedule["last_run"]:
            return None

        last_run = datetime.fromisoformat(self.schedule["last_run"])
        if self.schedule["frequency"] == "daily":
            next_run = last_run + timedelta(days=1)
        elif self.schedule["frequency"] == "weekly":
            next_run = last_run + timedelta(days=7)
        elif self.schedule["frequency"] == "monthly":
            next_run = last_run + timedelta(days=30)
        else:
            return None

        return next_run.isoformat()

    def _create_audit_report(self, result: Dict[str, Any]) -> None:
        """Create a detailed audit report note."""
        try:
            # Create report content
            content = f"# Template Audit Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            content += f"## Summary\n\n"
            content += f"- Total files checked: {result['total_files']}\n"
            content += f"- Files with issues: {result['files_with_issues']}\n\n"
            content += f"## Issues Found\n\n"

            for file_result in result["audit_results"]:
                content += f"### {file_result['path']}\n\n"
                if file_result.get("errors"):
                    content += f"#### Frontmatter Issues\n"
                    for error in file_result["errors"]:
                        content += f"- {error}\n"
                    content += "\n"
                if file_result.get("structure_errors"):
                    content += f"#### Structure Issues\n"
                    for error in file_result["structure_errors"]:
                        content += f"- {error}\n"
                    content += "\n"

            # Create frontmatter
            frontmatter = {
                "title": f"Template Audit Report - {datetime.now().strftime('%Y-%m-%d')}",
                "type": "#Log",
                "created_date": datetime.now().isoformat(),
                "tags": ["#audit", "#template"]
            }

            # Create report note
            report_path = os.path.join(
                self.obsidian.vault_path,
                "Audit Reports",
                f"Template Audit - {datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            )
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            self.obsidian.write_note(
                report_path,
                self.obsidian.update_frontmatter(content, frontmatter)
            )
        except Exception as e:
            print(f"Error creating audit report: {str(e)}") 
from typing import Dict, List, Optional
from pydantic import BaseModel
from openai import OpenAI
from ...core.exceptions import LLMError
from ...core.config import settings
from ...features.note_management.note_manager import NoteManager

class ContentImprovement(BaseModel):
    """Model for content improvements."""
    improved_content: str
    changes_made: List[str]
    suggestions: List[str]

class ContentManipulator:
    def __init__(self):
        self.note_manager = NoteManager()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL

    def improve_content(self, note_title: str) -> ContentImprovement:
        """Improve note content using LLM."""
        try:
            # Get note content
            content = self.note_manager.get_note_content(note_title)
            
            # Create prompt for content improvement
            prompt = f"""Improve the following content by:
            1. Enhancing clarity and readability
            2. Adding more context where needed
            3. Removing redundant information
            4. Improving structure and organization
            5. Adding relevant examples or explanations
            6. Ensuring consistent formatting
            7. Making it more engaging and concise
            
            Return the improved content and a list of changes made.

            Content:
            {content}

            Improved Content:"""

            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that improves content quality."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            # Process response
            improved_content = response.choices[0].message.content.strip()
            
            # Get changes made
            changes_prompt = f"""List the specific changes made to improve the content.
            Focus on key improvements in:
            1. Clarity and readability
            2. Context and completeness
            3. Structure and organization
            4. Formatting and style
            5. Engagement and conciseness

            Original Content:
            {content}

            Improved Content:
            {improved_content}

            Changes Made:"""

            changes_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that lists content improvements."},
                    {"role": "user", "content": changes_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            changes = changes_response.choices[0].message.content.strip().split('\n')
            
            # Get additional suggestions
            suggestions_prompt = f"""Provide additional suggestions for further improving the content.
            Consider:
            1. Areas that could use more detail
            2. Potential connections to other topics
            3. Ways to make it more engaging
            4. Additional examples or use cases
            5. Formatting improvements

            Content:
            {improved_content}

            Suggestions:"""

            suggestions_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides content improvement suggestions."},
                    {"role": "user", "content": suggestions_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            suggestions = suggestions_response.choices[0].message.content.strip().split('\n')
            
            return ContentImprovement(
                improved_content=improved_content,
                changes_made=changes,
                suggestions=suggestions
            )
        except Exception as e:
            raise LLMError(f"Error improving content: {str(e)}")

    def generate_summary(self, note_title: str, max_length: Optional[int] = None) -> str:
        """Generate a summary of the note content."""
        try:
            # Get note content
            content = self.note_manager.get_note_content(note_title)
            
            # Create prompt for summary
            length_constraint = f" Keep the summary under {max_length} words." if max_length else ""
            prompt = f"""Generate a concise summary of the following content.
            Focus on the main points and key takeaways.
            Make it clear and easy to understand.{length_constraint}

            Content:
            {content}

            Summary:"""

            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates clear summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            raise LLMError(f"Error generating summary: {str(e)}")

    def extract_key_points(self, note_title: str) -> List[str]:
        """Extract key points from the note content."""
        try:
            # Get note content
            content = self.note_manager.get_note_content(note_title)
            
            # Create prompt for key points
            prompt = f"""Extract the key points from the following content.
            Focus on:
            1. Main ideas and concepts
            2. Important details and facts
            3. Key conclusions or takeaways
            4. Action items or next steps
            Return each point on a new line.

            Content:
            {content}

            Key Points:"""

            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts key points."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content.strip().split('\n')
        except Exception as e:
            raise LLMError(f"Error extracting key points: {str(e)}")

    def generate_tasks(self, note_title: str) -> List[str]:
        """Generate tasks from the note content."""
        try:
            # Get note content
            content = self.note_manager.get_note_content(note_title)
            
            # Create prompt for task generation
            prompt = f"""Generate a list of tasks based on the following content.
            Consider:
            1. Action items mentioned
            2. Implicit tasks that need to be done
            3. Follow-up actions
            4. Dependencies or prerequisites
            Return each task on a new line.

            Content:
            {content}

            Tasks:"""

            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates tasks."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content.strip().split('\n')
        except Exception as e:
            raise LLMError(f"Error generating tasks: {str(e)}")

    def add_context(self, note_title: str, context_type: str = "general") -> str:
        """Add context to the note content."""
        try:
            # Get note content
            content = self.note_manager.get_note_content(note_title)
            
            # Create prompt for context addition
            prompt = f"""Add relevant context to the following content.
            Focus on:
            1. Background information
            2. Related concepts and ideas
            3. Examples and use cases
            4. Connections to other topics
            5. Additional resources or references
            Context type: {context_type}

            Content:
            {content}

            Enhanced Content:"""

            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that adds context to content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            raise LLMError(f"Error adding context: {str(e)}")

    def format_content(self, note_title: str, style: str = "markdown") -> str:
        """Format the note content according to specified style."""
        try:
            # Get note content
            content = self.note_manager.get_note_content(note_title)
            
            # Create prompt for formatting
            prompt = f"""Format the following content according to {style} style.
            Consider:
            1. Headers and sections
            2. Lists and bullet points
            3. Code blocks and inline code
            4. Links and references
            5. Tables and diagrams
            6. Emphasis and highlighting
            7. Consistent spacing and indentation

            Content:
            {content}

            Formatted Content:"""

            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that formats content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            raise LLMError(f"Error formatting content: {str(e)}") 
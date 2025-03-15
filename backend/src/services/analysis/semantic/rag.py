from typing import Dict, List, Optional, Set, Union, Any
from pydantic import BaseModel
from openai import OpenAI
from ...core.exceptions import RAGError, LLMError
from ...core.config import settings
from .indexer import Indexer
from ..semantic_analysis.semantic_analyzer import SemanticAnalyzer

class RAGResponse(BaseModel):
    """Model for RAG responses."""
    answer: str
    sources: List[Dict[str, str]]
    confidence: float
    related_notes: List[Dict[str, str]]
    suggested_actions: List[str]
    notes_to_open: List[str] = []

class RAG:
    def __init__(self):
        self.indexer = Indexer()
        self.semantic_analyzer = SemanticAnalyzer()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI's API."""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise LLMError(f"Error generating embedding: {str(e)}")

    def get_relevant_context(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Get relevant context from the vector database."""
        try:
            # Get initial results from vector search
            vector_results = self.indexer.search_notes(query, n_results)
            
            # Get semantically related notes
            semantic_results = self.semantic_analyzer.find_related_notes(query, n_results)
            
            # Combine and deduplicate results
            combined_results = []
            seen_texts = set()
            
            for result in vector_results + semantic_results:
                text = result.get("text", "")
                if text not in seen_texts:
                    seen_texts.add(text)
                    combined_results.append(result)
            
            # Sort by relevance (using distance for vector results and similarity for semantic results)
            combined_results.sort(key=lambda x: x.get("distance", 0) if "distance" in x else x.get("similarity", 0))
            
            return combined_results[:n_results]
        except Exception as e:
            raise RAGError(f"Error getting relevant context: {str(e)}")

    def format_context(self, context: List[Dict[str, Any]]) -> str:
        """Format context for the LLM."""
        try:
            formatted_context = "Relevant information:\n\n"
            for i, item in enumerate(context, 1):
                formatted_context += f"{i}. From {item['metadata']['title']}:\n{item['text']}\n\n"
            return formatted_context
        except Exception as e:
            raise RAGError(f"Error formatting context: {str(e)}")

    def generate_response(self, query: str, context: List[Dict[str, Any]]) -> RAGResponse:
        """Generate a response using the LLM with context."""
        try:
            # Format context
            formatted_context = self.format_context(context)
            
            # Create prompt
            prompt = f"""Based on the following context, please answer the question and provide additional insights.
            If the context doesn't contain enough information to answer the question, say so.
            Include relevant citations to the source notes.
            Also suggest any related actions or follow-up questions that might be helpful.
            Identify which notes would be most relevant to open for the user.

            Context:
            {formatted_context}

            Question: {query}

            Please provide:
            1. A detailed answer to the question
            2. Citations to relevant source notes
            3. Related notes that might be helpful
            4. Suggested follow-up actions or questions
            5. A list of notes that should be opened (most relevant first)

            Format your response with clear sections, and for the notes to open, use the format:
            NOTES_TO_OPEN:
            - Note title 1
            - Note title 2
            etc.

            Response:"""

            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides accurate answers based on the given context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            # Extract answer and parse structured response
            answer = response.choices[0].message.content
            
            # Extract notes to open
            notes_to_open = []
            if "NOTES_TO_OPEN:" in answer:
                notes_section = answer.split("NOTES_TO_OPEN:")[1].split("\n\n")[0]
                notes_to_open = [
                    line.strip("- ").strip()
                    for line in notes_section.split("\n")
                    if line.strip().startswith("-")
                ]
            
            # Create sources list
            sources = [
                {
                    "title": item["metadata"]["title"],
                    "text": item["text"],
                    "tags": item["metadata"]["tags"]
                }
                for item in context
            ]

            # Get related notes
            related_notes = self.semantic_analyzer.find_related_notes(query, 3)
            
            # Extract suggested actions from the response
            suggested_actions = self._extract_suggested_actions(answer)

            # Calculate confidence (placeholder)
            confidence = 0.8  # This should be implemented based on LLM confidence scores

            return RAGResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                related_notes=related_notes,
                suggested_actions=suggested_actions,
                notes_to_open=notes_to_open
            )
        except Exception as e:
            raise RAGError(f"Error generating response: {str(e)}")

    def _extract_suggested_actions(self, response: str) -> List[str]:
        """Extract suggested actions from the LLM response."""
        try:
            # Look for action suggestions in the response
            actions = []
            lines = response.split('\n')
            for line in lines:
                if line.lower().startswith(('suggested action:', 'follow-up:', 'you might want to:', 'consider:')):
                    actions.append(line.strip())
            return actions
        except Exception as e:
            print(f"Warning: Error extracting suggested actions: {str(e)}")
            return []

    def process_query(self, query: str) -> RAGResponse:
        """Process a query using RAG."""
        try:
            # Get relevant context
            context = self.get_relevant_context(query)
            
            # Generate response
            return self.generate_response(query, context)
        except Exception as e:
            raise RAGError(f"Error processing query: {str(e)}")

    def update_knowledge_base(self, note_title: str) -> None:
        """Update the knowledge base with new or modified content."""
        try:
            self.indexer.update_index(note_title)
            # Update semantic relationships
            self.semantic_analyzer.analyze_note(note_title)
        except Exception as e:
            raise RAGError(f"Error updating knowledge base: {str(e)}")

    def remove_from_knowledge_base(self, note_title: str) -> None:
        """Remove content from the knowledge base."""
        try:
            self.indexer.delete_from_index(note_title)
            # Update semantic relationships
            self.semantic_analyzer.remove_note(note_title)
        except Exception as e:
            raise RAGError(f"Error removing from knowledge base: {str(e)}")

    def get_knowledge_base_stats(self) -> Dict[str, int]:
        """Get statistics about the knowledge base."""
        try:
            collection = self.indexer.collection
            return {
                "total_documents": collection.count(),
                "total_chunks": len(collection.get()["documents"])
            }
        except Exception as e:
            raise RAGError(f"Error getting knowledge base stats: {str(e)}") 
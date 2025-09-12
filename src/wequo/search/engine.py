"""
Search engine for WeQuo data packages.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import math

from .models import IndexDocument, SearchResult, SearchQuery, DocumentType, SearchStats
from .indexer import DataIndexer


class SearchEngine:
    """Simple but effective search engine for WeQuo data."""
    
    def __init__(self, index_dir: str = "data/search"):
        """Initialize search engine."""
        self.index_dir = Path(index_dir)
        self.indexer = DataIndexer(index_dir)
        self._documents_cache = None
        self._last_cache_update = None
    
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform search with the given query."""
        documents = self._load_documents()
        
        if not documents:
            return []
        
        # Apply filters
        filtered_docs = self._apply_filters(documents, query)
        
        # Score documents
        scored_docs = self._score_documents(filtered_docs, query)
        
        # Sort results
        sorted_docs = self._sort_results(scored_docs, query.sort_by)
        
        # Apply pagination
        start = query.offset
        end = start + query.limit
        paginated_docs = sorted_docs[start:end]
        
        # Create search results with highlights
        results = []
        for doc, score in paginated_docs:
            highlights = self._generate_highlights(doc, query.query)
            result = SearchResult(
                document=doc,
                score=score,
                highlights=highlights
            )
            results.append(result)
        
        return results
    
    def search_simple(self, query_text: str, limit: int = 20) -> List[SearchResult]:
        """Simple search interface."""
        query = SearchQuery(query=query_text, limit=limit)
        return self.search(query)
    
    def get_suggestions(self, query_text: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on partial query."""
        documents = self._load_documents()
        suggestions = set()
        
        query_lower = query_text.lower()
        
        for doc in documents:
            # Extract potential suggestions from titles and tags
            words = doc.title.lower().split() + doc.tags
            for word in words:
                if word.startswith(query_lower) and len(word) > len(query_lower):
                    suggestions.add(word)
            
            # Extract series IDs and sources
            if 'series_id' in doc.metadata:
                series_id = doc.metadata['series_id'].lower()
                if series_id.startswith(query_lower):
                    suggestions.add(doc.metadata['series_id'])
        
        return sorted(list(suggestions))[:limit]
    
    def get_facets(self, query: Optional[SearchQuery] = None) -> Dict[str, Dict[str, int]]:
        """Get faceted search results."""
        documents = self._load_documents()
        
        if query:
            documents = self._apply_filters(documents, query)
        
        facets = {
            'types': {},
            'sources': {},
            'tags': {},
            'dates': {}
        }
        
        for doc in documents:
            # Document types
            doc_type = doc.type.value
            facets['types'][doc_type] = facets['types'].get(doc_type, 0) + 1
            
            # Sources
            if doc.source:
                facets['sources'][doc.source] = facets['sources'].get(doc.source, 0) + 1
            
            # Tags
            for tag in doc.tags:
                facets['tags'][tag] = facets['tags'].get(tag, 0) + 1
            
            # Dates (by year-month)
            if 'package_date' in doc.metadata:
                date_key = doc.metadata['package_date'][:7]  # YYYY-MM
                facets['dates'][date_key] = facets['dates'].get(date_key, 0) + 1
        
        return facets
    
    def rebuild_index(self, output_root: Path = None):
        """Rebuild the search index."""
        if output_root is None:
            output_root = Path("data/output")
        
        self.indexer.rebuild_index(output_root)
        self._documents_cache = None  # Clear cache
    
    def get_stats(self) -> SearchStats:
        """Get search index statistics."""
        return self.indexer.get_stats()
    
    def _load_documents(self) -> List[IndexDocument]:
        """Load documents from index with caching."""
        documents_file = self.index_dir / "documents.jsonl"
        
        if not documents_file.exists():
            return []
        
        # Check if cache is valid
        file_mtime = datetime.fromtimestamp(documents_file.stat().st_mtime)
        if (self._documents_cache is not None and 
            self._last_cache_update is not None and 
            file_mtime <= self._last_cache_update):
            return self._documents_cache
        
        # Load documents
        documents = []
        with open(documents_file, 'r') as f:
            for line in f:
                try:
                    doc_data = json.loads(line)
                    doc = IndexDocument.from_dict(doc_data)
                    documents.append(doc)
                except Exception as e:
                    print(f"Error loading document: {e}")
        
        # Update cache
        self._documents_cache = documents
        self._last_cache_update = datetime.now()
        
        return documents
    
    def _apply_filters(self, documents: List[IndexDocument], query: SearchQuery) -> List[IndexDocument]:
        """Apply filters to documents."""
        filtered = documents
        
        # Filter by document types
        if query.document_types:
            filtered = [doc for doc in filtered if doc.type in query.document_types]
        
        # Filter by sources
        if query.sources:
            filtered = [doc for doc in filtered if doc.source in query.sources]
        
        # Filter by tags
        if query.tags:
            filtered = [doc for doc in filtered if any(tag in doc.tags for tag in query.tags)]
        
        # Filter by date range
        if query.date_from or query.date_to:
            date_filtered = []
            for doc in filtered:
                doc_date = None
                if 'package_date' in doc.metadata:
                    try:
                        doc_date = datetime.strptime(doc.metadata['package_date'], '%Y-%m-%d')
                    except:
                        continue
                elif 'date' in doc.metadata:
                    try:
                        doc_date = datetime.strptime(doc.metadata['date'], '%Y-%m-%d')
                    except:
                        continue
                
                if doc_date:
                    if query.date_from and doc_date < query.date_from:
                        continue
                    if query.date_to and doc_date > query.date_to:
                        continue
                    date_filtered.append(doc)
            
            filtered = date_filtered
        
        return filtered
    
    def _score_documents(self, documents: List[IndexDocument], query: SearchQuery) -> List[tuple]:
        """Score documents for relevance."""
        if not query.query.strip():
            # If no query, return all documents with equal score
            return [(doc, 1.0) for doc in documents]
        
        query_terms = self._tokenize(query.query.lower())
        scored_docs = []
        
        for doc in documents:
            score = self._calculate_relevance_score(doc, query_terms)
            if score > 0:
                scored_docs.append((doc, score))
        
        return scored_docs
    
    def _calculate_relevance_score(self, doc: IndexDocument, query_terms: List[str]) -> float:
        """Calculate relevance score for a document."""
        if not query_terms:
            return 1.0
        
        # Combine all searchable text
        searchable_text = f"{doc.title} {doc.content} {' '.join(doc.tags)}"
        if doc.source:
            searchable_text += f" {doc.source}"
        
        # Add metadata text
        for key, value in doc.metadata.items():
            if isinstance(value, str):
                searchable_text += f" {value}"
        
        searchable_text = searchable_text.lower()
        text_tokens = self._tokenize(searchable_text)
        
        if not text_tokens:
            return 0.0
        
        # Calculate TF-IDF style score
        score = 0.0
        
        for term in query_terms:
            # Term frequency
            tf = text_tokens.count(term) / len(text_tokens)
            
            # Boost for title matches
            if term in doc.title.lower():
                tf *= 3.0
            
            # Boost for tag matches
            if term in [tag.lower() for tag in doc.tags]:
                tf *= 2.0
            
            # Boost for exact matches
            if term in searchable_text:
                tf *= 1.5
            
            # Simple inverse document frequency approximation
            # (In a real implementation, this would be calculated across all documents)
            idf = 1.0
            
            score += tf * idf
        
        # Boost newer documents slightly
        if doc.timestamp:
            days_old = (datetime.now() - doc.timestamp).days
            recency_boost = max(0.1, 1.0 - (days_old / 365))  # Decay over a year
            score *= recency_boost
        
        return score
    
    def _sort_results(self, scored_docs: List[tuple], sort_by: str) -> List[tuple]:
        """Sort search results."""
        if sort_by == 'date':
            return sorted(scored_docs, key=lambda x: x[0].timestamp, reverse=True)
        elif sort_by == 'score':
            return sorted(scored_docs, key=lambda x: x[1], reverse=True)
        else:  # relevance (default)
            return sorted(scored_docs, key=lambda x: x[1], reverse=True)
    
    def _generate_highlights(self, doc: IndexDocument, query: str) -> List[str]:
        """Generate text highlights for search results."""
        if not query.strip():
            return []
        
        query_terms = self._tokenize(query.lower())
        highlights = []
        
        # Check title
        title_lower = doc.title.lower()
        for term in query_terms:
            if term in title_lower:
                highlights.append(f"Title: ...{self._highlight_text(doc.title, term)}...")
        
        # Check content
        content_lower = doc.content.lower()
        for term in query_terms:
            if term in content_lower:
                # Find context around the term
                context = self._extract_context(doc.content, term)
                if context:
                    highlights.append(f"Content: ...{context}...")
        
        return highlights[:3]  # Limit to 3 highlights
    
    def _highlight_text(self, text: str, term: str, context_length: int = 50) -> str:
        """Highlight a term in text with context."""
        text_lower = text.lower()
        term_lower = term.lower()
        
        start = text_lower.find(term_lower)
        if start == -1:
            return text[:context_length]
        
        # Get context around the term
        context_start = max(0, start - context_length // 2)
        context_end = min(len(text), start + len(term) + context_length // 2)
        
        context = text[context_start:context_end]
        
        # Highlight the term
        highlighted = re.sub(re.escape(term), f"<mark>{term}</mark>", context, flags=re.IGNORECASE)
        
        return highlighted
    
    def _extract_context(self, text: str, term: str, context_length: int = 100) -> str:
        """Extract context around a search term."""
        text_lower = text.lower()
        term_lower = term.lower()
        
        start = text_lower.find(term_lower)
        if start == -1:
            return ""
        
        # Get context around the term
        context_start = max(0, start - context_length // 2)
        context_end = min(len(text), start + len(term) + context_length // 2)
        
        return text[context_start:context_end]
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        # Remove punctuation and split on whitespace
        cleaned = re.sub(r'[^\w\s]', ' ', text)
        tokens = cleaned.split()
        # Filter out very short tokens
        return [token for token in tokens if len(token) > 1]

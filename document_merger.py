import json
import copy
import hashlib
import time
from typing import Dict, Any, List, Optional, Tuple, Set

class DocumentMerger:
    """A class to manage document merging and conflict resolution in the blockchain."""
    
    @staticmethod
    def hash_document(document: Dict[str, Any]) -> str:
        """Generate a hash of the document for comparison."""
        doc_str = json.dumps(document, sort_keys=True)
        return hashlib.sha256(doc_str.encode('utf-8')).hexdigest()
    
    @staticmethod
    def create_document(content: Dict[str, Any], author: str) -> Dict[str, Any]:
        """Create a new document with metadata."""
        if not author:
            raise ValueError("Author must be specified")
            
        if not content:
            raise ValueError("Content cannot be empty")
            
        timestamp = time.time()
        return {
            "content": content,
            "metadata": {
                "created_at": timestamp,
                "updated_at": timestamp,
                "version": 1,
                "author": author,
                "history": [],
                "hash": None  # Will be populated after creation
            }
        }
    
    @staticmethod
    def update_document(document: Dict[str, Any], 
                        changes: Dict[str, Any], 
                        author: str) -> Dict[str, Any]:
        """Update a document with changes."""
        # Create a copy of the original document
        new_doc = copy.deepcopy(document)
        
        # Store the previous state in history
        prev_hash = DocumentMerger.hash_document(document)
        history_entry = {
            "version": document["metadata"]["version"],
            "updated_at": document["metadata"]["updated_at"],
            "author": document["metadata"]["author"],
            "hash": prev_hash
        }
        
        # Add to history
        new_doc["metadata"]["history"].append(history_entry)
        
        # Update content with changes
        for key, value in changes.items():
            new_doc["content"][key] = value
        
        # Update metadata
        new_doc["metadata"]["updated_at"] = time.time()
        new_doc["metadata"]["version"] += 1
        new_doc["metadata"]["author"] = author
        
        # Update hash
        new_doc["metadata"]["hash"] = DocumentMerger.hash_document(new_doc)
        
        return new_doc
    
    @staticmethod
    def merge_documents(doc1: Dict[str, Any], 
                        doc2: Dict[str, Any], 
                        strategy: str = "latest_wins") -> Dict[str, Any]:
        """Merge two versions of a document with conflict resolution.
        
        Args:
            doc1: First document version
            doc2: Second document version
            strategy: Conflict resolution strategy:
                      - "latest_wins": most recent changes win
                      - "field_level": merge at field level, taking latest for each field
        
        Returns:
            Merged document
        """
        # Simple check - if documents are identical by hash, return either
        if DocumentMerger.hash_document(doc1) == DocumentMerger.hash_document(doc2):
            return copy.deepcopy(doc1)
        
        # Determine which document is newer overall
        newer_doc = doc1 if doc1["metadata"]["updated_at"] >= doc2["metadata"]["updated_at"] else doc2
        older_doc = doc2 if newer_doc is doc1 else doc1
        
        if strategy == "latest_wins":
            # Simply take the newer document as the merged result
            result = copy.deepcopy(newer_doc)
            
            # Add the older document to history if not already there
            older_hash = DocumentMerger.hash_document(older_doc)
            history_hashes = [entry["hash"] for entry in result["metadata"]["history"]]
            
            if older_hash not in history_hashes:
                history_entry = {
                    "version": older_doc["metadata"]["version"],
                    "updated_at": older_doc["metadata"]["updated_at"],
                    "author": older_doc["metadata"]["author"],
                    "hash": older_hash
                }
                result["metadata"]["history"].append(history_entry)
            
            return result
        
        elif strategy == "field_level":
            # Start with the older document as base
            result = copy.deepcopy(older_doc)
            result_content = result["content"]
            
            # Track changed fields for metadata
            changed_fields = []
            
            # For each field in the newer document, check if it's newer than in the result
            for key, value in newer_doc["content"].items():
                # If field doesn't exist in result or is different, take the newer value
                if key not in result_content or result_content[key] != value:
                    result_content[key] = value
                    changed_fields.append(key)
            
            # Update metadata
            result["metadata"]["updated_at"] = time.time()
            result["metadata"]["version"] = max(doc1["metadata"]["version"], doc2["metadata"]["version"]) + 1
            result["metadata"]["author"] = f"{doc1['metadata']['author']}+{doc2['metadata']['author']}"
            
            # Combine histories from both documents
            all_history = result["metadata"]["history"] + newer_doc["metadata"]["history"]
            unique_hashes = set()
            
            # Keep only unique history entries by hash
            unique_history = []
            for entry in all_history:
                if entry["hash"] not in unique_hashes:
                    unique_hashes.add(entry["hash"])
                    unique_history.append(entry)
            
            result["metadata"]["history"] = sorted(unique_history, key=lambda x: x["version"])
            
            # Add merged document metadata
            merge_info = {
                "merged_at": time.time(),
                "merged_from": [
                    DocumentMerger.hash_document(doc1),
                    DocumentMerger.hash_document(doc2)
                ],
                "strategy": strategy,
                "changed_fields": changed_fields
            }
            
            if "merge_info" not in result["metadata"]:
                result["metadata"]["merge_info"] = []
            
            result["metadata"]["merge_info"].append(merge_info)
            
            # Update hash for the new merged document
            result["metadata"]["hash"] = DocumentMerger.hash_document(result)
            
            return result
        
        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")
    
    @staticmethod
    def get_document_history(document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract the document history in chronological order."""
        return sorted(document["metadata"]["history"], key=lambda x: x["version"])
    
    @staticmethod
    def diff_documents(doc1: Dict[str, Any], doc2: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the differences between two document versions."""
        diff = {
            "added": {},
            "removed": {},
            "changed": {}
        }
        
        # Find added and changed fields
        for key, value in doc2["content"].items():
            if key not in doc1["content"]:
                diff["added"][key] = value
            elif doc1["content"][key] != value:
                diff["changed"][key] = {
                    "from": doc1["content"][key],
                    "to": value
                }
        
        # Find removed fields
        for key in doc1["content"]:
            if key not in doc2["content"]:
                diff["removed"][key] = doc1["content"][key]
        
        return diff
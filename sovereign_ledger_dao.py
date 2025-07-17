"""
Sovereign Ledger Data Access Object (DAO)

This module provides an interface for the database operations of the Sovereign Ledger system,
handling the translation between blockchain ledger entries and database records.
"""

import logging
import time
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from blockchain import Blockchain, Block, Wallet
from models import (
    LedgerPerson, LedgerProject, LedgerTask, LedgerTag, 
    LedgerCommitment, LedgerEntry, LedgerTaskHistory,
    TaskStatus, TaskPriority, ProjectStatus, CommitmentStatus
)
from database import get_db_session

# Configure logging
logger = logging.getLogger(__name__)

class SovereignLedgerDAO:
    """Data Access Object for the Sovereign Ledger system."""
    
    def __init__(self, blockchain: Blockchain):
        """
        Initialize the DAO with a blockchain reference.
        
        Args:
            blockchain: The blockchain instance to connect with the ledger
        """
        self.blockchain = blockchain
        logger.info("Sovereign Ledger DAO initialized")
    
    def sync_blockchain_to_db(self) -> int:
        """
        Synchronize blockchain ledger entries to the database.
        
        Returns:
            Number of records synchronized
        """
        session = get_db_session()
        count = 0
        
        try:
            # Get last processed block from database
            last_entry = session.query(LedgerEntry).order_by(desc(LedgerEntry.block_id)).first()
            last_block_index = 0 if not last_entry else last_entry.block_id
            
            # Process new blocks
            for block in self.blockchain.chain[last_block_index:]:
                if block.data and isinstance(block.data, dict):
                    if block.data.get("type") in ["ledger_entry", "ledger_entry_update"]:
                        entry = block.data.get("entry", {})
                        if entry:
                            self._process_ledger_entry(session, entry, block)
                            count += 1
            
            session.commit()
            logger.info(f"Synchronized {count} ledger entries from blockchain to database")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"Error syncing blockchain to database: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_person(self, username: str) -> Optional[LedgerPerson]:
        """
        Get a person by username.
        
        Args:
            username: The username to look up
            
        Returns:
            The ledger person or None if not found
        """
        session = get_db_session()
        try:
            return session.query(LedgerPerson).filter_by(username=username).first()
        finally:
            session.close()
    
    def get_or_create_person(self, username: str, display_name: Optional[str] = None, 
                           public_key: Optional[str] = None) -> LedgerPerson:
        """
        Get a person by username or create if not exists.
        
        Args:
            username: The username
            display_name: Optional display name
            public_key: Optional public key
            
        Returns:
            The ledger person instance
        """
        session = get_db_session()
        try:
            person = session.query(LedgerPerson).filter_by(username=username).first()
            
            if not person:
                person = LedgerPerson(
                    username=username,
                    display_name=display_name or username,
                    public_key=public_key
                )
                session.add(person)
                session.commit()
                logger.info(f"Created new ledger person: {username}")
            
            return person
        finally:
            session.close()
    
    def get_project(self, project_id: str) -> Optional[LedgerProject]:
        """
        Get a project by ID.
        
        Args:
            project_id: The project ID
            
        Returns:
            The ledger project or None if not found
        """
        session = get_db_session()
        try:
            return session.query(LedgerProject).filter_by(project_id=project_id).first()
        finally:
            session.close()
    
    def get_task(self, task_id: str) -> Optional[LedgerTask]:
        """
        Get a task by ID.
        
        Args:
            task_id: The task ID
            
        Returns:
            The ledger task or None if not found
        """
        session = get_db_session()
        try:
            return session.query(LedgerTask).filter_by(task_id=task_id).first()
        finally:
            session.close()
    
    def get_commitment(self, commitment_id: str) -> Optional[LedgerCommitment]:
        """
        Get a commitment by ID.
        
        Args:
            commitment_id: The commitment ID
            
        Returns:
            The ledger commitment or None if not found
        """
        session = get_db_session()
        try:
            return session.query(LedgerCommitment).filter_by(commitment_id=commitment_id).first()
        finally:
            session.close()
    
    def create_project_from_entry(self, entry: Dict[str, Any]) -> LedgerProject:
        """
        Create a database project record from a ledger entry.
        
        Args:
            entry: The ledger entry data
            
        Returns:
            The created project instance
        """
        session = get_db_session()
        try:
            entry_data = entry.get("data", {})
            
            # Get or create the owner
            owner = self.get_or_create_person(entry_data.get("owner"))
            
            # Create project
            project = LedgerProject(
                project_id=entry.get("id"),
                name=entry_data.get("name"),
                description=entry_data.get("description"),
                owner_id=owner.id,
                status=ProjectStatus(entry_data.get("status", "active")),
                start_date=entry_data.get("start_date"),
                end_date=entry_data.get("end_date"),
                blockchain_ref=entry.get("hash"),
                metadata=entry_data.get("metadata", {})
            )
            session.add(project)
            
            # Add members
            for member_name in entry_data.get("members", []):
                member = self.get_or_create_person(member_name)
                project.members.append(member)
            
            session.commit()
            logger.info(f"Created project from ledger entry: {project.name}")
            
            return project
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating project from entry: {str(e)}")
            raise
        finally:
            session.close()
    
    def create_task_from_entry(self, entry: Dict[str, Any]) -> LedgerTask:
        """
        Create a database task record from a ledger entry.
        
        Args:
            entry: The ledger entry data
            
        Returns:
            The created task instance
        """
        session = get_db_session()
        try:
            entry_data = entry.get("data", {})
            
            # Get or create creator and assignee
            creator = self.get_or_create_person(entry_data.get("creator", "system"))
            assignee = None
            if entry_data.get("assignee"):
                assignee = self.get_or_create_person(entry_data.get("assignee"))
            
            # Get project if specified
            project = None
            if entry_data.get("project_id"):
                project = self.get_project(entry_data.get("project_id"))
            
            # Create task
            task = LedgerTask(
                task_id=entry.get("id"),
                title=entry_data.get("title"),
                description=entry_data.get("description"),
                status=TaskStatus(entry_data.get("status", "open")),
                priority=TaskPriority(entry_data.get("priority", "medium")),
                progress=entry_data.get("progress", 0),
                creator_id=creator.id,
                assignee_id=assignee.id if assignee else None,
                project_id=project.id if project else None,
                due_date=entry_data.get("due_date"),
                blockchain_ref=entry.get("hash"),
                metadata=entry_data.get("metadata", {})
            )
            session.add(task)
            
            # Add tags
            for tag_name in entry_data.get("tags", []):
                tag = session.query(LedgerTag).filter_by(name=tag_name).first()
                if not tag:
                    tag = LedgerTag(name=tag_name)
                    session.add(tag)
                task.tags.append(tag)
            
            session.commit()
            logger.info(f"Created task from ledger entry: {task.title}")
            
            return task
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating task from entry: {str(e)}")
            raise
        finally:
            session.close()
    
    def create_commitment_from_entry(self, entry: Dict[str, Any]) -> LedgerCommitment:
        """
        Create a database commitment record from a ledger entry.
        
        Args:
            entry: The ledger entry data
            
        Returns:
            The created commitment instance
        """
        session = get_db_session()
        try:
            entry_data = entry.get("data", {})
            
            # Get or create parties
            responsible = self.get_or_create_person(entry_data.get("responsible_party"))
            beneficiary = self.get_or_create_person(entry_data.get("beneficiary_party"))
            
            # Create commitment
            commitment = LedgerCommitment(
                commitment_id=entry.get("id"),
                title=entry_data.get("title"),
                description=entry_data.get("description"),
                status=CommitmentStatus(entry_data.get("status", "active")),
                responsible_party_id=responsible.id,
                beneficiary_party_id=beneficiary.id,
                terms=entry_data.get("terms", {}),
                start_date=entry_data.get("start_date"),
                end_date=entry_data.get("end_date"),
                blockchain_ref=entry.get("hash"),
                metadata=entry_data.get("metadata", {})
            )
            session.add(commitment)
            
            session.commit()
            logger.info(f"Created commitment from ledger entry: {commitment.title}")
            
            return commitment
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating commitment from entry: {str(e)}")
            raise
        finally:
            session.close()
    
    def update_project_from_entry(self, project: LedgerProject, entry: Dict[str, Any]) -> LedgerProject:
        """
        Update a project from a ledger entry.
        
        Args:
            project: The existing project to update
            entry: The ledger entry with updates
            
        Returns:
            The updated project
        """
        session = get_db_session()
        try:
            session.add(project)
            entry_data = entry.get("data", {})
            
            # Update fields
            if "name" in entry_data:
                project.name = entry_data["name"]
            if "description" in entry_data:
                project.description = entry_data["description"]
            if "status" in entry_data:
                project.status = ProjectStatus(entry_data["status"])
            if "end_date" in entry_data:
                project.end_date = entry_data["end_date"]
            if "metadata" in entry_data:
                project.metadata = entry_data["metadata"]
            
            # Update blockchain reference
            project.blockchain_ref = entry.get("hash")
            
            # Update members if present
            if "members" in entry_data:
                # Clear existing members
                project.members = []
                
                # Add new members
                for member_name in entry_data["members"]:
                    member = self.get_or_create_person(member_name)
                    project.members.append(member)
            
            session.commit()
            logger.info(f"Updated project from ledger entry: {project.name}")
            
            return project
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating project from entry: {str(e)}")
            raise
        finally:
            session.close()
    
    def update_task_from_entry(self, task: LedgerTask, entry: Dict[str, Any]) -> LedgerTask:
        """
        Update a task from a ledger entry.
        
        Args:
            task: The existing task to update
            entry: The ledger entry with updates
            
        Returns:
            The updated task
        """
        session = get_db_session()
        try:
            session.add(task)
            entry_data = entry.get("data", {})
            
            # Save history before updating
            history = LedgerTaskHistory(
                task_id=task.id,
                changed_by_id=self.get_or_create_person(entry.get("signer", "system")).id,
                timestamp=entry.get("timestamp", time.time()),
                changes={
                    "before": {
                        "title": task.title,
                        "description": task.description,
                        "status": task.status.value,
                        "priority": task.priority.value,
                        "progress": task.progress,
                        "due_date": task.due_date
                    },
                    "after": entry_data
                },
                blockchain_ref=entry.get("hash")
            )
            session.add(history)
            
            # Update fields
            if "title" in entry_data:
                task.title = entry_data["title"]
            if "description" in entry_data:
                task.description = entry_data["description"]
            if "status" in entry_data:
                task.status = TaskStatus(entry_data["status"])
            if "priority" in entry_data:
                task.priority = TaskPriority(entry_data["priority"])
            if "progress" in entry_data:
                task.progress = entry_data["progress"]
            if "due_date" in entry_data:
                task.due_date = entry_data["due_date"]
            if "metadata" in entry_data:
                task.metadata = entry_data["metadata"]
            
            # Update assignee if present
            if "assignee" in entry_data:
                assignee = self.get_or_create_person(entry_data["assignee"])
                task.assignee_id = assignee.id
            
            # Update blockchain reference
            task.blockchain_ref = entry.get("hash")
            
            # Update tags if present
            if "tags" in entry_data:
                # Clear existing tags
                task.tags = []
                
                # Add new tags
                for tag_name in entry_data["tags"]:
                    tag = session.query(LedgerTag).filter_by(name=tag_name).first()
                    if not tag:
                        tag = LedgerTag(name=tag_name)
                        session.add(tag)
                    task.tags.append(tag)
            
            session.commit()
            logger.info(f"Updated task from ledger entry: {task.title}")
            
            return task
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating task from entry: {str(e)}")
            raise
        finally:
            session.close()
    
    def update_commitment_from_entry(self, commitment: LedgerCommitment, entry: Dict[str, Any]) -> LedgerCommitment:
        """
        Update a commitment from a ledger entry.
        
        Args:
            commitment: The existing commitment to update
            entry: The ledger entry with updates
            
        Returns:
            The updated commitment
        """
        session = get_db_session()
        try:
            session.add(commitment)
            entry_data = entry.get("data", {})
            
            # Update fields
            if "title" in entry_data:
                commitment.title = entry_data["title"]
            if "description" in entry_data:
                commitment.description = entry_data["description"]
            if "status" in entry_data:
                commitment.status = CommitmentStatus(entry_data["status"])
            if "terms" in entry_data:
                commitment.terms = entry_data["terms"]
            if "end_date" in entry_data:
                commitment.end_date = entry_data["end_date"]
            if "metadata" in entry_data:
                commitment.metadata = entry_data["metadata"]
            
            # Update blockchain reference
            commitment.blockchain_ref = entry.get("hash")
            
            session.commit()
            logger.info(f"Updated commitment from ledger entry: {commitment.title}")
            
            return commitment
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating commitment from entry: {str(e)}")
            raise
        finally:
            session.close()
    
    def store_raw_ledger_entry(self, entry: Dict[str, Any], block: Block) -> LedgerEntry:
        """
        Store a raw ledger entry in the database.
        
        Args:
            entry: The ledger entry
            block: The blockchain block containing the entry
            
        Returns:
            The created ledger entry record
        """
        session = get_db_session()
        try:
            # Create database record
            db_entry = LedgerEntry(
                entry_id=entry.get("id"),
                entry_type=entry.get("type"),
                block_id=block.index,
                entry_hash=entry.get("hash"),
                previous_hash=entry.get("previous_entries")[0] if entry.get("previous_entries") else None,
                timestamp=entry.get("timestamp"),
                data=entry.get("data"),
                signature=entry.get("signature"),
                signer=entry.get("signer"),
                signer_public_key=entry.get("signer_public_key"),
                state=entry.get("state", "active")
            )
            session.add(db_entry)
            session.commit()
            
            return db_entry
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing raw ledger entry: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get statistics for the dashboard.
        
        Returns:
            Dictionary of statistics
        """
        session = get_db_session()
        try:
            stats = {
                "total_projects": session.query(LedgerProject).count(),
                "total_tasks": session.query(LedgerTask).count(),
                "total_commitments": session.query(LedgerCommitment).count(),
                "total_people": session.query(LedgerPerson).count(),
                "active_projects": session.query(LedgerProject).filter_by(status=ProjectStatus.ACTIVE).count(),
                "completed_tasks": session.query(LedgerTask).filter_by(status=TaskStatus.COMPLETED).count(),
                "open_tasks": session.query(LedgerTask).filter_by(status=TaskStatus.OPEN).count(),
                "blockchain_entries": session.query(LedgerEntry).count()
            }
            
            return stats
        finally:
            session.close()
    
    def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent ledger activities.
        
        Args:
            limit: Maximum number of activities to return
            
        Returns:
            List of recent activities
        """
        session = get_db_session()
        try:
            entries = session.query(LedgerEntry).order_by(desc(LedgerEntry.timestamp)).limit(limit).all()
            
            activities = []
            for entry in entries:
                activity = {
                    "id": entry.entry_id,
                    "type": entry.entry_type,
                    "timestamp": entry.timestamp,
                    "signer": entry.signer,
                    "block_index": entry.block_id,
                    "data": entry.data
                }
                activities.append(activity)
            
            return activities
        finally:
            session.close()
    
    def _process_ledger_entry(self, session, entry: Dict[str, Any], block: Block) -> None:
        """
        Process a ledger entry from the blockchain and update the database accordingly.
        
        Args:
            session: The database session
            entry: The ledger entry to process
            block: The blockchain block containing the entry
        """
        try:
            # First, store the raw entry
            db_entry = self.store_raw_ledger_entry(entry, block)
            
            # Process based on entry type
            entry_type = entry.get("type")
            entry_id = entry.get("id")
            
            if entry_type == "project":
                # Check if update or create
                project = self.get_project(entry_id)
                if project:
                    self.update_project_from_entry(project, entry)
                else:
                    self.create_project_from_entry(entry)
            
            elif entry_type == "task":
                # Check if update or create
                task = self.get_task(entry_id)
                if task:
                    self.update_task_from_entry(task, entry)
                else:
                    self.create_task_from_entry(entry)
            
            elif entry_type == "commitment":
                # Check if update or create
                commitment = self.get_commitment(entry_id)
                if commitment:
                    self.update_commitment_from_entry(commitment, entry)
                else:
                    self.create_commitment_from_entry(entry)
            
            # Other entry types can be processed here
            
            logger.info(f"Processed ledger entry {entry_id} of type {entry_type}")
        except Exception as e:
            logger.error(f"Error processing ledger entry {entry.get('id')}: {str(e)}")
            raise
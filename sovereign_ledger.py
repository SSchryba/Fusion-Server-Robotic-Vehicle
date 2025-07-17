"""
Sovereign Ledger Module

This module implements the sovereign ledger system from the Task Manager project,
integrated with the blockchain system for distributed consensus and immutability.
"""

import json
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import base64

from blockchain import Blockchain, Block, Wallet
from fluxion import fluxion

# Configure logging
logger = logging.getLogger(__name__)

class SovereignLedger:
    """
    Sovereign Ledger implementation that bridges task management with blockchain technology.
    Provides a distributed, immutable record of activities and responsibilities.
    """
    
    def __init__(self, blockchain: Blockchain, wallet: Optional[Wallet] = None):
        """
        Initialize the Sovereign Ledger with a blockchain backend.
        
        Args:
            blockchain: The blockchain instance to use as the ledger's backend
            wallet: Optional wallet for signing ledger entries (new wallet created if None)
        """
        self.blockchain = blockchain
        self.wallet = wallet or Wallet()
        self.entries = {}  # Cache of ledger entries
        self.authority_keys = {}  # Registered authority public keys
        self.validators = {}  # Registered validators
        
        logger.info("Sovereign Ledger initialized with blockchain backend")
    
    def register_authority(self, name: str, public_key: str) -> bool:
        """
        Register an authority that can sign and validate ledger entries.
        
        Args:
            name: Identifier for the authority
            public_key: Public key in base64 format
            
        Returns:
            True if registration was successful
        """
        self.authority_keys[name] = public_key
        logger.info(f"Authority '{name}' registered with public key: {public_key[:8]}...")
        
        # Store in blockchain for immutability
        entry_data = {
            "type": "authority_registration",
            "name": name,
            "public_key": public_key,
            "timestamp": time.time()
        }
        
        # Sign with our wallet
        signature = self.wallet.sign(json.dumps(entry_data))
        entry_data["signature"] = signature
        entry_data["signer_public_key"] = self.wallet.get_public_key()
        
        # Store in blockchain
        self.blockchain.add_block(entry_data, self.wallet)
        
        return True
    
    def create_entry(self, entry_type: str, data: Dict[str, Any], authority: str = None) -> Dict[str, Any]:
        """
        Create a new ledger entry, sign it, and add it to the blockchain.
        
        Args:
            entry_type: Type of ledger entry (e.g., "task", "project", "commitment")
            data: The entry data to be stored
            authority: Optional authority name to sign the entry
            
        Returns:
            The created ledger entry
        """
        # Import Pycamo here to avoid circular imports
        from pycamo_integration import pycamo, secure_data
        
        # Create entry structure
        entry_id = f"entry_{int(time.time())}_{hashlib.sha256(json.dumps(data).encode()).hexdigest()[:8]}"
        timestamp = time.time()
        
        entry = {
            "id": entry_id,
            "type": entry_type,
            "data": data,
            "timestamp": timestamp,
            "previous_entries": [],  # Links to previous related entries
            "state": "active"
        }
        
        # Sign the entry with the wallet
        entry_json = json.dumps(entry, sort_keys=True)
        signature = self.wallet.sign(entry_json)
        
        entry["signature"] = signature
        entry["signer"] = authority or "system"
        entry["signer_public_key"] = self.wallet.get_public_key()
        
        # Calculate entry hash
        entry_hash = hashlib.sha256(entry_json.encode()).hexdigest()
        entry["hash"] = entry_hash
        
        # Apply Pycamo security
        secured_entry = pycamo.secure_ledger_entry(entry)
        
        # Store in local cache
        self.entries[entry_id] = secured_entry
        
        # Add Pycamo security information
        blockchain_data = {
            "type": "ledger_entry",
            "entry": secured_entry,
            "pycamo_secured": True,
            "encryption_timestamp": time.time()
        }
        
        # Apply another layer of security to the blockchain data
        secured_blockchain_data = secure_data(blockchain_data, 'ledger_entry')
        
        # Store in blockchain
        block = self.blockchain.add_block(secured_blockchain_data, self.wallet)
        
        # Link to the block
        secured_entry["block_index"] = block.index
        secured_entry["block_hash"] = block.hash
        
        logger.info(f"Created secured ledger entry '{entry_id}' of type '{entry_type}' in block #{block.index}")
        
        # Broadcast the entry
        self._broadcast_entry(secured_entry)
        
        return secured_entry
    
    def update_entry(self, entry_id: str, updates: Dict[str, Any], authority: str = None) -> Dict[str, Any]:
        """
        Update an existing ledger entry.
        
        Args:
            entry_id: The ID of the entry to update
            updates: The updates to apply
            authority: Optional authority name to sign the update
            
        Returns:
            The updated ledger entry
        """
        # Import Pycamo here to avoid circular imports
        from pycamo_integration import pycamo, secure_data
        
        if entry_id not in self.entries:
            # Try to fetch it first
            self.get_entry(entry_id)
            
            if entry_id not in self.entries:
                raise ValueError(f"Entry '{entry_id}' not found")
        
        # Get the original entry
        original = self.entries[entry_id]
        
        # Create a new entry with updates
        updated = {**original}
        
        # Remove any existing Pycamo security data
        if "security" in updated:
            del updated["security"]
        
        # Apply updates to the data field
        if "data" in updates:
            updated["data"] = {**original["data"], **updates["data"]}
            del updates["data"]
        
        # Apply updates to top-level fields
        for key, value in updates.items():
            updated[key] = value
        
        # Important: Don't update ID or creation timestamp
        updated["id"] = original["id"]
        updated["timestamp"] = original["timestamp"]
        
        # Add update timestamp
        updated["updated_at"] = time.time()
        
        # Add previous entry to link history
        updated["previous_entries"] = original.get("previous_entries", []) + [original["hash"]]
        
        # Re-sign the entry
        entry_json = json.dumps(updated, sort_keys=True)
        signature = self.wallet.sign(entry_json)
        
        updated["signature"] = signature
        updated["signer"] = authority or "system"
        updated["signer_public_key"] = self.wallet.get_public_key()
        
        # Calculate new hash
        entry_hash = hashlib.sha256(entry_json.encode()).hexdigest()
        updated["hash"] = entry_hash
        
        # Apply Pycamo security
        secured_updated = pycamo.secure_ledger_entry(updated)
        
        # Store in local cache
        self.entries[entry_id] = secured_updated
        
        # Add Pycamo security information
        blockchain_data = {
            "type": "ledger_entry_update",
            "entry": secured_updated,
            "original_hash": original["hash"],
            "pycamo_secured": True,
            "encryption_timestamp": time.time()
        }
        
        # Apply another layer of security to the blockchain data
        secured_blockchain_data = secure_data(blockchain_data, 'ledger_entry')
        
        # Store in blockchain
        block = self.blockchain.add_block(secured_blockchain_data, self.wallet)
        
        # Link to the block
        secured_updated["block_index"] = block.index
        secured_updated["block_hash"] = block.hash
        
        logger.info(f"Updated secured ledger entry '{entry_id}' in block #{block.index}")
        
        # Broadcast the update
        self._broadcast_entry(secured_updated, is_update=True)
        
        return secured_updated
    
    def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a ledger entry by ID.
        
        Args:
            entry_id: The ID of the entry to retrieve
            
        Returns:
            The ledger entry or None if not found
        """
        # Check cache first
        if entry_id in self.entries:
            return self.entries[entry_id]
        
        # Search blockchain for the entry
        for block in reversed(self.blockchain.chain):
            # Skip genesis block
            if block.index == 0:
                continue
                
            # Check block data
            if block.data and isinstance(block.data, dict):
                if block.data.get("type") in ["ledger_entry", "ledger_entry_update"]:
                    entry = block.data.get("entry", {})
                    if entry.get("id") == entry_id:
                        # Cache and return the entry
                        self.entries[entry_id] = entry
                        return entry
        
        return None
    
    def query_entries(self, 
                     entry_type: Optional[str] = None, 
                     state: Optional[str] = None, 
                     authority: Optional[str] = None,
                     time_range: Optional[Tuple[float, float]] = None) -> List[Dict[str, Any]]:
        """
        Query ledger entries by various criteria.
        
        Args:
            entry_type: Filter by entry type
            state: Filter by entry state
            authority: Filter by signing authority
            time_range: Filter by creation time range (start, end)
            
        Returns:
            List of matching ledger entries
        """
        # Build cache if empty
        if not self.entries:
            self._build_entry_cache()
        
        results = []
        
        for entry in self.entries.values():
            # Apply filters
            if entry_type and entry.get("type") != entry_type:
                continue
                
            if state and entry.get("state") != state:
                continue
                
            if authority and entry.get("signer") != authority:
                continue
                
            if time_range:
                start, end = time_range
                if not (start <= entry.get("timestamp", 0) <= end):
                    continue
            
            results.append(entry)
        
        # Sort by timestamp, newest first
        results.sort(key=lambda e: e.get("timestamp", 0), reverse=True)
        
        return results
    
    def verify_entry(self, entry: Dict[str, Any]) -> bool:
        """
        Verify the signature and integrity of a ledger entry.
        
        Args:
            entry: The ledger entry to verify
            
        Returns:
            True if the entry is valid, False otherwise
        """
        # Import Pycamo here to avoid circular imports
        from pycamo_integration import pycamo, verify_data
        
        # Check if this is a Pycamo-secured entry
        if "security" in entry and entry["security"].get("method") == "pycamo":
            # Verify Pycamo security first
            is_valid, _ = verify_data(entry, 'ledger_entry')
            if not is_valid:
                logger.warning(f"Pycamo security verification failed for entry '{entry.get('id')}'")
                return False
            
            logger.info(f"Pycamo security verified for entry '{entry.get('id')}'")
        
        # Clone the entry to avoid modifying the original
        entry_copy = {**entry}
        
        # Extract signature and public key
        signature = entry_copy.pop("signature", None)
        public_key = entry_copy.pop("signer_public_key", None)
        
        if not signature or not public_key:
            logger.warning(f"Entry '{entry.get('id')}' missing signature or public key")
            return False
        
        # Remove Pycamo security information for ECDSA verification
        if "security" in entry_copy:
            del entry_copy["security"]
        
        # Verify using the stored hash
        stored_hash = entry_copy.pop("hash", None)
        entry_json = json.dumps(entry_copy, sort_keys=True)
        calculated_hash = hashlib.sha256(entry_json.encode()).hexdigest()
        
        if stored_hash and stored_hash != calculated_hash:
            logger.warning(f"Entry '{entry.get('id')}' hash mismatch")
            return False
        
        # Verify signature
        try:
            is_valid = Wallet.verify_signature(public_key, entry_json, signature)
            if not is_valid:
                logger.warning(f"Entry '{entry.get('id')}' signature verification failed")
            return is_valid
        except Exception as e:
            logger.error(f"Error verifying entry '{entry.get('id')}': {str(e)}")
            return False
    
    def verify_entry_chain(self, entry_id: str) -> bool:
        """
        Verify an entry and its entire history chain.
        
        Args:
            entry_id: ID of the entry to verify
            
        Returns:
            True if the entire entry chain is valid
        """
        entry = self.get_entry(entry_id)
        if not entry:
            return False
        
        # Verify the entry itself
        if not self.verify_entry(entry):
            return False
        
        # Verify previous entries
        for prev_hash in entry.get("previous_entries", []):
            # Find the entry with this hash
            prev_entry = None
            for e in self.entries.values():
                if e.get("hash") == prev_hash:
                    prev_entry = e
                    break
            
            if not prev_entry:
                logger.warning(f"Previous entry with hash '{prev_hash}' not found")
                return False
            
            if not self.verify_entry(prev_entry):
                return False
        
        return True
    
    def create_task_entry(self, 
                         title: str, 
                         description: str, 
                         assignee: str, 
                         due_date: Optional[float] = None,
                         priority: str = "medium",
                         tags: List[str] = None) -> Dict[str, Any]:
        """
        Create a task entry in the ledger.
        
        Args:
            title: Task title
            description: Task description
            assignee: Username of the assigned person
            due_date: Optional due date timestamp
            priority: Task priority (low, medium, high)
            tags: Optional tags for the task
            
        Returns:
            The created task entry
        """
        task_data = {
            "title": title,
            "description": description,
            "assignee": assignee,
            "due_date": due_date,
            "priority": priority,
            "tags": tags or [],
            "status": "open",
            "progress": 0
        }
        
        return self.create_entry("task", task_data)
    
    def create_project_entry(self,
                            name: str,
                            description: str,
                            owner: str,
                            members: List[str],
                            start_date: float,
                            end_date: Optional[float] = None) -> Dict[str, Any]:
        """
        Create a project entry in the ledger.
        
        Args:
            name: Project name
            description: Project description
            owner: Username of the project owner
            members: List of team member usernames
            start_date: Project start timestamp
            end_date: Optional project end timestamp
            
        Returns:
            The created project entry
        """
        project_data = {
            "name": name,
            "description": description,
            "owner": owner,
            "members": members,
            "start_date": start_date,
            "end_date": end_date,
            "status": "active"
        }
        
        return self.create_entry("project", project_data)
    
    def create_commitment_entry(self,
                               title: str,
                               description: str,
                               responsible_party: str,
                               beneficiary_party: str,
                               terms: Dict[str, Any],
                               start_date: float,
                               end_date: Optional[float] = None) -> Dict[str, Any]:
        """
        Create a commitment entry in the ledger.
        
        Args:
            title: Commitment title
            description: Description of the commitment
            responsible_party: Username of the responsible person/entity
            beneficiary_party: Username of the beneficiary person/entity
            terms: Terms of the commitment
            start_date: Commitment start timestamp
            end_date: Optional commitment end timestamp
            
        Returns:
            The created commitment entry
        """
        commitment_data = {
            "title": title,
            "description": description,
            "responsible_party": responsible_party,
            "beneficiary_party": beneficiary_party,
            "terms": terms,
            "start_date": start_date,
            "end_date": end_date,
            "status": "active"
        }
        
        return self.create_entry("commitment", commitment_data)
    
    def get_entry_history(self, entry_id: str) -> List[Dict[str, Any]]:
        """
        Get the full history of an entry.
        
        Args:
            entry_id: The ID of the entry
            
        Returns:
            List of all versions of the entry, from newest to oldest
        """
        entry = self.get_entry(entry_id)
        if not entry:
            return []
        
        history = [entry]
        prev_hashes = entry.get("previous_entries", [])
        
        while prev_hashes:
            prev_hash = prev_hashes.pop(0)
            
            # Find the entry with this hash
            for e in self.entries.values():
                if e.get("hash") == prev_hash:
                    history.append(e)
                    break
        
        return history
    
    def correlate_blockchain_data(self) -> Dict[str, Any]:
        """
        Correlate all ledger entries with blockchain data.
        
        Returns:
            Correlation analysis results
        """
        # Build cache if empty
        if not self.entries:
            self._build_entry_cache()
            
        # Initialize correlation stats
        correlation = {
            "total_entries": len(self.entries),
            "entries_by_type": {},
            "entries_by_block": {},
            "entry_states": {},
            "authorities": {},
            "verification_stats": {
                "verified": 0,
                "failed": 0
            },
            "blockchain_coverage": 0.0
        }
        
        # Analyze entries
        for entry in self.entries.values():
            # Count by type
            entry_type = entry.get("type", "unknown")
            if entry_type not in correlation["entries_by_type"]:
                correlation["entries_by_type"][entry_type] = 0
            correlation["entries_by_type"][entry_type] += 1
            
            # Count by block
            block_index = entry.get("block_index")
            if block_index is not None:
                if block_index not in correlation["entries_by_block"]:
                    correlation["entries_by_block"][block_index] = 0
                correlation["entries_by_block"][block_index] += 1
            
            # Count by state
            state = entry.get("state", "unknown")
            if state not in correlation["entry_states"]:
                correlation["entry_states"][state] = 0
            correlation["entry_states"][state] += 1
            
            # Count by authority
            authority = entry.get("signer", "unknown")
            if authority not in correlation["authorities"]:
                correlation["authorities"][authority] = 0
            correlation["authorities"][authority] += 1
            
            # Verify entry
            if self.verify_entry(entry):
                correlation["verification_stats"]["verified"] += 1
            else:
                correlation["verification_stats"]["failed"] += 1
        
        # Calculate blockchain coverage
        blocks_with_entries = len(correlation["entries_by_block"])
        total_blocks = len(self.blockchain.chain)
        
        if total_blocks > 0:
            correlation["blockchain_coverage"] = blocks_with_entries / total_blocks * 100
        
        logger.info(f"Correlation analysis completed for {correlation['total_entries']} entries")
        return correlation
    
    def export_to_json(self, filepath: str) -> bool:
        """
        Export all ledger entries to a JSON file.
        
        Args:
            filepath: The file path for the export
            
        Returns:
            True if export was successful
        """
        # Build cache if empty
        if not self.entries:
            self._build_entry_cache()
            
        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "entries": list(self.entries.values()),
                    "metadata": {
                        "exported_at": time.time(),
                        "entry_count": len(self.entries),
                        "ledger_wallet_public_key": self.wallet.get_public_key()
                    }
                }, f, indent=2)
            
            logger.info(f"Exported {len(self.entries)} entries to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting ledger to {filepath}: {str(e)}")
            return False
    
    def import_from_json(self, filepath: str, verify: bool = True) -> int:
        """
        Import ledger entries from a JSON file.
        
        Args:
            filepath: The file path to import from
            verify: Whether to verify imported entries
            
        Returns:
            Number of entries imported
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            entries = data.get("entries", [])
            imported = 0
            
            for entry in entries:
                entry_id = entry.get("id")
                
                if not entry_id:
                    logger.warning("Skipping entry without ID")
                    continue
                
                if verify and not self.verify_entry(entry):
                    logger.warning(f"Skipping entry '{entry_id}' due to verification failure")
                    continue
                
                # Store in cache
                self.entries[entry_id] = entry
                imported += 1
            
            logger.info(f"Imported {imported} entries from {filepath}")
            return imported
        except Exception as e:
            logger.error(f"Error importing ledger from {filepath}: {str(e)}")
            return 0
    
    def _build_entry_cache(self) -> None:
        """Build a cache of all ledger entries from the blockchain."""
        self.entries = {}
        
        for block in self.blockchain.chain:
            # Skip genesis block
            if block.index == 0:
                continue
                
            # Check block data
            if block.data and isinstance(block.data, dict):
                if block.data.get("type") in ["ledger_entry", "ledger_entry_update"]:
                    entry = block.data.get("entry", {})
                    entry_id = entry.get("id")
                    
                    if entry_id:
                        self.entries[entry_id] = entry
        
        logger.info(f"Built cache with {len(self.entries)} ledger entries")
    
    def _broadcast_entry(self, entry: Dict[str, Any], is_update: bool = False) -> None:
        """
        Broadcast a ledger entry to the network.
        
        Args:
            entry: The entry to broadcast
            is_update: Whether this is an update to an existing entry
        """
        # Import Pycamo here to avoid circular imports
        from pycamo_integration import pycamo, secure_data
        
        action = "update" if is_update else "create"
        entry_type = entry.get("type", "unknown")
        entry_id = entry.get("id", "unknown")
        
        message_data = {
            "type": "ledger_entry",
            "action": action,
            "entry_type": entry_type,
            "entry_id": entry_id,
            "entry": entry,
            "timestamp": time.time()
        }
        
        # Secure the broadcast message with Pycamo
        secured_message = secure_data(message_data, 'broadcast')
        
        try:
            # Add a unique identifier for Pycamo broadcasts
            fluxion.broadcast_message(
                message_id=f"pycamo_ledger_{action}_{entry_id}_{int(time.time())}",
                message_data=secured_message
            )
            logger.info(f"Broadcast secured ledger entry {action}: {entry_id}")
        except Exception as e:
            logger.error(f"Error broadcasting secured ledger entry: {str(e)}")


# Helper function to create a sovereign ledger instance
def create_sovereign_ledger(blockchain: Blockchain, wallet: Optional[Wallet] = None) -> SovereignLedger:
    """
    Create a new sovereign ledger connected to the blockchain.
    
    Args:
        blockchain: The blockchain backend to use
        wallet: Optional wallet for signing entries
        
    Returns:
        Initialized SovereignLedger instance
    """
    return SovereignLedger(blockchain, wallet)


def correlate_sovereign_data_with_blockchain(blockchain: Blockchain, ledger: SovereignLedger) -> Dict[str, Any]:
    """
    Correlate sovereign ledger data with blockchain data for comprehensive analysis.
    
    Args:
        blockchain: The blockchain instance
        ledger: The sovereign ledger instance
        
    Returns:
        Dictionary containing correlation results and analysis
    """
    # Import Pycamo here to avoid circular imports
    from pycamo_integration import pycamo
    
    # First, get the blockchain stats
    blockchain_info = {
        "chain_length": len(blockchain.chain),
        "blocks": len(blockchain.chain),
        "last_block_hash": blockchain.chain[-1].hash if blockchain.chain else None,
        "transactions": sum(1 for block in blockchain.chain if isinstance(block.data, dict) and block.data.get("type") == "transaction")
    }
    
    # Get sovereign ledger stats
    ledger_info = ledger.correlate_blockchain_data()
    
    # Count Pycamo-secured entries
    pycamo_secured_count = 0
    pycamo_verification_stats = {"verified": 0, "failed": 0}
    
    for entry in ledger.entries.values():
        if "security" in entry and entry["security"].get("method") == "pycamo":
            pycamo_secured_count += 1
            
            # Verify Pycamo security
            try:
                is_valid, _ = pycamo.verify_ledger_entry(entry)
                if is_valid:
                    pycamo_verification_stats["verified"] += 1
                else:
                    pycamo_verification_stats["failed"] += 1
            except Exception:
                pycamo_verification_stats["failed"] += 1
    
    # Combine the data
    correlation = {
        "blockchain": blockchain_info,
        "sovereign_ledger": ledger_info,
        "correlation_results": {
            "blockchain_ledger_coverage": ledger_info.get("blockchain_coverage", 0),
            "total_ledger_entries": ledger_info.get("total_entries", 0),
            "entries_by_type": ledger_info.get("entries_by_type", {}),
            "verification_stats": ledger_info.get("verification_stats", {"verified": 0, "failed": 0}),
            "authorities": ledger_info.get("authorities", {}),
        },
        "pycamo_security": {
            "secured_entries": pycamo_secured_count,
            "security_coverage": (pycamo_secured_count / len(ledger.entries) * 100) if ledger.entries else 0,
            "verification_stats": pycamo_verification_stats
        },
        "summary": {
            "integration_status": "Complete" if ledger_info.get("total_entries", 0) > 0 else "Pending",
            "data_quality": "High" if ledger_info.get("verification_stats", {}).get("verified", 0) > 0 else "Unknown",
            "blockchain_utilization": "Active" if blockchain_info["chain_length"] > 1 else "Initialized",
            "security_rating": "Enhanced" if pycamo_secured_count > 0 else "Standard"
        }
    }
    
    return correlation
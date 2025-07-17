"""
DriftChain Module

This module implements the DriftChain blockchain algorithm with vacuum mode constraints
and entropy node functionality.
"""

import time
import hashlib
import json
import os
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

class Block:
    """A block in the DriftChain blockchain."""
    
    def __init__(self, index: int, timestamp: float, data: Any, previous_hash: str):
        """
        Initialize a new block.
        
        Args:
            index: Position of the block in the chain
            timestamp: When the block was created
            data: Data stored in the block
            previous_hash: Hash of the previous block
        """
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Calculate the hash of the block using SHA-256.
        
        Returns:
            Hexadecimal string representation of the hash
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the block to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the block
        """
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'hash': self.hash
        }


class DriftChain:
    """
    DriftChain implementation with vacuum mode constraints.
    
    This blockchain implementation starts in vacuum mode, which prevents
    the addition of new blocks until a specified time period has passed.
    """
    
    def __init__(self, vacuum_days: int = 5):
        """
        Initialize a new DriftChain.
        
        Args:
            vacuum_days: Number of days the vacuum mode should last
        """
        self.chain = [self.create_genesis_block()]
        self.vacuum_mode = True  # Start in Genesis vacuum mode
        self.vacuum_release_time = time.time() + (vacuum_days * 86400)  # days in seconds
        logger.info(f"DriftChain initialized with vacuum release in {vacuum_days} days")
        
    def create_genesis_block(self) -> Block:
        """
        Create the genesis (first) block of the chain.
        
        Returns:
            The genesis block
        """
        genesis_message = "Commander Drift Ignition: The Dawn of Entropy Nodes."
        logger.info(f"Genesis Block Created with message: {genesis_message}")
        return Block(0, time.time(), {"message": genesis_message}, "0")

    def add_block(self, data: Any) -> Optional[Block]:
        """
        Add a new block to the chain, respecting vacuum mode constraints.
        
        Args:
            data: Data to be stored in the block
            
        Returns:
            The new block if added, None if blocked by vacuum mode
        """
        if self.vacuum_mode and time.time() < self.vacuum_release_time:
            logger.warning("Vacuum Mode Active — New blocks forbidden until vacuum collapse.")
            return None
        elif self.vacuum_mode:
            logger.info("Vacuum collapse — chain expansion now authorized.")
            self.vacuum_mode = False

        last_block = self.chain[-1]
        new_block = Block(len(self.chain), time.time(), data, last_block.hash)
        self.chain.append(new_block)
        logger.info(f"Block {new_block.index} added.")
        return new_block

    def view_chain(self) -> List[Dict[str, Any]]:
        """
        Get a list of all blocks in the chain.
        
        Returns:
            List of dictionaries representing the blocks
        """
        return [block.to_dict() for block in self.chain]
    
    def is_valid(self) -> bool:
        """
        Validate the integrity of the chain.
        
        Returns:
            True if the chain is valid, False otherwise
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            # Check if the current hash is correct
            if current.hash != current.calculate_hash():
                return False
                
            # Check if the chain is properly linked
            if current.previous_hash != previous.hash:
                return False
                
        return True
    
    def get_chain_data(self) -> Dict[str, Any]:
        """
        Get metadata about the chain.
        
        Returns:
            Dictionary with chain metadata
        """
        return {
            'length': len(self.chain),
            'vacuum_mode': self.vacuum_mode,
            'vacuum_release_time': self.vacuum_release_time,
            'valid': self.is_valid(),
            'last_block_time': self.chain[-1].timestamp,
            'genesis_time': self.chain[0].timestamp
        }


# Initialize a global instance
drift_chain = DriftChain()

def get_drift_chain() -> DriftChain:
    """
    Get the global DriftChain instance.
    
    Returns:
        The global DriftChain instance
    """
    return drift_chain
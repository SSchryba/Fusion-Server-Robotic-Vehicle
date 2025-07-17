import hashlib
import time
import json
import base64
import ecdsa
import logging
from typing import List, Dict, Any, Optional, Tuple, Union, cast
from document_merger import DocumentMerger
from god_mode import get_god_mode

# Configure logging
logger = logging.getLogger(__name__)

# Initialize GodMode for enhanced blockchain capabilities
GOD_MODE = get_god_mode()

class Wallet:
    """A digital wallet that can sign data and verify signatures."""
    
    def __init__(self, private_key: Optional[bytes] = None):
        """Initialize a wallet with a secp256k1 key pair.
        
        Args:
            private_key: Optional private key (if None, a new key is generated)
        """
        if private_key:
            self.private_key = ecdsa.SigningKey.from_string(
                private_key, 
                curve=ecdsa.SECP256k1
            )
        else:
            # Generate a new private key
            self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
            
        # Derive public key from private key
        self.public_key = self.private_key.get_verifying_key()
    
    def sign(self, data: str) -> str:
        """Sign data with private key.
        
        Args:
            data: String data to sign
            
        Returns:
            Base64-encoded signature
        """
        signature = self.private_key.sign(data.encode('utf-8'))
        return base64.b64encode(signature).decode('utf-8')
    
    def get_public_key(self) -> str:
        """Get the public key as a base64-encoded string."""
        return base64.b64encode(self.public_key.to_string()).decode('utf-8')
    
    @staticmethod
    def verify_signature(public_key: str, data: str, signature: str) -> bool:
        """Verify a signature given the public key and data.
        
        Args:
            public_key: Base64-encoded public key
            data: Original data that was signed
            signature: Base64-encoded signature
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Decode the public key and signature from base64
            public_key_bytes = base64.b64decode(public_key)
            signature_bytes = base64.b64decode(signature)
            
            # Create verifying key object
            verifying_key = ecdsa.VerifyingKey.from_string(
                public_key_bytes, 
                curve=ecdsa.SECP256k1
            )
            
            # Verify the signature
            return verifying_key.verify(signature_bytes, data.encode('utf-8'))
        except Exception:
            return False

class Block:
    def __init__(self, index: int, previous_hash: str, timestamp: float, 
                 data: Any, hash: str, nonce: int = 0, 
                 signature: Optional[str] = None, public_key: Optional[str] = None):
        """Initialize a block in the blockchain.
        
        Args:
            index: Position of the block in the chain
            previous_hash: Hash of the previous block
            timestamp: When the block was created
            data: Data stored in the block
            hash: Hash of the current block
            nonce: Number used in proof-of-work
            signature: ECDSA signature of the block
            public_key: Public key used to verify the signature
        """
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.hash = hash
        self.nonce = nonce
        self.signature = signature
        self.public_key = public_key
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to a dictionary for serialization."""
        return {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'data': self.data,
            'hash': self.hash,
            'nonce': self.nonce,
            'signature': self.signature,
            'public_key': self.public_key
        }
    
    def get_data_for_signing(self) -> str:
        """Get the block data in a format suitable for signing."""
        block_data = f"{self.index}{self.previous_hash}{self.timestamp}{self.data}{self.hash}{self.nonce}"
        return block_data

class Blockchain:
    def __init__(self):
        """Initialize a new blockchain with a genesis block."""
        self.chain: List[Block] = []
        self.difficulty = 4  # Number of leading zeros required in hash
        self.wallet = Wallet()  # Create a default wallet for the blockchain
        self.documents: Dict[str, Dict[str, Any]] = {}  # Document store by ID
        
        # Create the genesis block
        self.chain.append(self._create_genesis_block())
    
    def _create_genesis_block(self) -> Block:
        """Create the first block in the chain."""
        timestamp = time.time()
        
        # Use a proper initial data structure for the genesis block 
        initial_data = {
            "type": "genesis",
            "timestamp": timestamp,
            "message": "Initial block in the chain",
            "version": "1.0.0"
        }
        
        genesis_hash = self.calculate_hash(0, "0", timestamp, initial_data, 0)
        
        # Create the block
        genesis_block = Block(
            0, 
            "0", 
            timestamp, 
            initial_data, 
            genesis_hash,
            0
        )
        
        # Sign the block
        signature = self.wallet.sign(genesis_block.get_data_for_signing())
        genesis_block.signature = signature
        genesis_block.public_key = self.wallet.get_public_key()
        
        return genesis_block
    
    @staticmethod
    def calculate_hash(index: int, previous_hash: str, timestamp: float, 
                       data: Any, nonce: int) -> str:
        """Calculate SHA-256 hash of block data.
        
        Args:
            index: Position of the block in the chain
            previous_hash: Hash of the previous block
            timestamp: When the block was created
            data: Data stored in the block
            nonce: Number used in proof-of-work
            
        Returns:
            String representation of the hash
        """
        block_string = f'{index}{previous_hash}{timestamp}{data}{nonce}'
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()
    
    def get_latest_block(self) -> Block:
        """Return the most recent block in the chain."""
        return self.chain[-1]
    
    def add_block(self, data: Any, wallet: Optional[Wallet] = None) -> Block:
        """Add a new block to the chain using proof of work.
        
        Args:
            data: Data to be stored in the block
            wallet: Optional wallet to sign the block (uses default if None)
            
        Returns:
            The newly created block
        """
        # Use provided wallet or default blockchain wallet
        signing_wallet = wallet if wallet is not None else self.wallet
        
        previous_block = self.get_latest_block()
        new_index = previous_block.index + 1
        new_timestamp = time.time()
        
        # Mine the block (find a valid hash with proof of work)
        nonce = 0
        new_hash = ""
        
        while not new_hash.startswith('0' * self.difficulty):
            nonce += 1
            new_hash = self.calculate_hash(
                new_index, 
                previous_block.hash, 
                new_timestamp, 
                data, 
                nonce
            )
        
        # Create the new block
        new_block = Block(
            new_index,
            previous_block.hash,
            new_timestamp,
            data,
            new_hash,
            nonce
        )
        
        # Sign the block with the wallet
        signature = signing_wallet.sign(new_block.get_data_for_signing())
        new_block.signature = signature
        new_block.public_key = signing_wallet.get_public_key()
        
        # Add the block to the chain
        self.chain.append(new_block)
        return new_block
    
    def is_chain_valid(self) -> bool:
        """Verify the integrity of the blockchain.
        
        Returns:
            True if the chain is valid, False otherwise
        """
        # Check each block in the chain
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Validate current block's hash
            if current_block.hash != self.calculate_hash(
                current_block.index, 
                current_block.previous_hash, 
                current_block.timestamp, 
                current_block.data, 
                current_block.nonce
            ):
                return False
            
            # Validate link to previous block
            if current_block.previous_hash != previous_block.hash:
                return False
            
            # Verify the signature
            if not current_block.signature or not current_block.public_key:
                return False
                
            # Verify the block signature
            is_valid_signature = Wallet.verify_signature(
                current_block.public_key,
                current_block.get_data_for_signing(),
                current_block.signature
            )
            
            if not is_valid_signature:
                return False
                
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the blockchain to a dictionary for serialization."""
        return {
            'chain': [block.to_dict() for block in self.chain],
            'length': len(self.chain),
            'documents': self.documents
        }
        
    # Document management methods
    def create_document(self, document_id: str, content: Dict[str, Any], author: str) -> Dict[str, Any]:
        """Create a new document and store it on the blockchain.
        
        Args:
            document_id: Unique identifier for the document
            content: Document content as a dictionary
            author: Name or identifier of the document creator
            
        Returns:
            The created document
        """
        # Import Pycamo here to avoid circular imports
        from pycamo_integration import pycamo, secure_data

        if document_id in self.documents:
            raise ValueError(f"Document with ID {document_id} already exists")
            
        # Create new document
        document = DocumentMerger.create_document(content, author)
        
        # Set the document hash
        document["metadata"]["hash"] = DocumentMerger.hash_document(document)
        
        # Add Pycamo security information
        document["metadata"]["security"] = {
            "method": "pycamo",
            "timestamp": time.time(),
            "version": "1.0"
        }
        
        # Apply Pycamo cryptographic security to sensitive content
        if "sensitive" in content:
            # Encrypt sensitive content
            document["content"]["sensitive"] = pycamo.encrypt_data(content["sensitive"])
            document["content"]["sensitive_encrypted"] = True
            
        # Generate a digital signature for the document
        document_json = json.dumps(document, sort_keys=True)
        document["metadata"]["signature"] = pycamo.sign_data(document_json)
        
        # Add document to blockchain storage
        self.documents[document_id] = document
        
        # Prepare block data with security information
        block_data = {
            "type": "document_created",
            "document_id": document_id,
            "document_hash": document["metadata"]["hash"],
            "author": author,
            "security": {
                "method": "pycamo",
                "signature_verified": True,
                "timestamp": time.time()
            }
        }
        
        # Apply final security layer to the block data
        secured_block_data = secure_data(block_data, 'generic')
        
        # Add to blockchain
        self.add_block(secured_block_data)
        
        # Log the security enhancement
        logger.info(f"Created document '{document_id}' with Pycamo security")
        
        return document
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by its ID.
        
        Args:
            document_id: The unique document identifier
            
        Returns:
            The document or None if not found
        """
        return self.documents.get(document_id)
        
    def update_document(self, document_id: str, changes: Dict[str, Any], author: str) -> Dict[str, Any]:
        """Update an existing document.
        
        Args:
            document_id: The unique document identifier
            changes: Changes to apply to the document
            author: Name or identifier of the person making changes
            
        Returns:
            The updated document
        """
        if document_id not in self.documents:
            raise ValueError(f"Document with ID {document_id} does not exist")
            
        # Get current version of document
        current_document = self.documents[document_id]
        
        # Update document
        updated_document = DocumentMerger.update_document(current_document, changes, author)
        
        # Store updated document
        self.documents[document_id] = updated_document
        
        # Add a block for document update
        block_data = {
            "type": "document_updated",
            "document_id": document_id,
            "previous_hash": current_document["metadata"]["hash"],
            "new_hash": updated_document["metadata"]["hash"],
            "author": author,
            "changes": changes
        }
        
        self.add_block(block_data)
        
        return updated_document
    
    def merge_documents(self, document_id: str, external_document: Dict[str, Any], 
                        strategy: str, author: str) -> Dict[str, Any]:
        """Merge an external document version with the current version.
        
        Args:
            document_id: ID of the document to merge
            external_document: External version of the document
            strategy: Merge strategy to use
            author: Person initiating the merge
            
        Returns:
            The merged document
        """
        if document_id not in self.documents:
            raise ValueError(f"Document with ID {document_id} does not exist")
            
        # Get current version of document
        current_document = self.documents[document_id]
        
        # Merge documents
        merged_document = DocumentMerger.merge_documents(current_document, external_document, strategy)
        
        # Store merged document
        self.documents[document_id] = merged_document
        
        # Calculate difference
        diff = DocumentMerger.diff_documents(current_document, merged_document)
        
        # Add a block for document merge
        block_data = {
            "type": "document_merged",
            "document_id": document_id,
            "current_hash": current_document["metadata"]["hash"],
            "external_hash": external_document["metadata"]["hash"],
            "merged_hash": merged_document["metadata"]["hash"],
            "strategy": strategy,
            "author": author,
            "diff": diff
        }
        
        self.add_block(block_data)
        
        return merged_document
    
    def get_document_history(self, document_id: str) -> List[Dict[str, Any]]:
        """Get the full history of a document from the blockchain.
        
        Args:
            document_id: The document identifier
            
        Returns:
            List of block data related to this document
        """
        if document_id not in self.documents:
            raise ValueError(f"Document with ID {document_id} does not exist")
            
        document_blocks = []
        
        for block in self.chain:
            # Skip blocks that don't contain document operations
            if not isinstance(block.data, dict) or 'type' not in block.data:
                continue
                
            # Check if this block relates to our document
            if block.data.get('document_id') == document_id:
                block_info = {
                    'index': block.index,
                    'timestamp': block.timestamp,
                    'hash': block.hash,
                    'operation': block.data
                }
                document_blocks.append(block_info)
                
        return document_blocks

# Create a global blockchain instance
blockchain = Blockchain()

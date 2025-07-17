import hashlib
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from blockchain import blockchain as local_blockchain, Block

# Import the provided external blockchain code
import hashlib
import json
from time import time as external_time

class ExternalBlockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': external_time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

# Create an instance of the external blockchain
external_blockchain = ExternalBlockchain()

class BlockchainConnector:
    """
    A class to connect and synchronize between our local blockchain and external blockchains.
    """
    
    def __init__(self, local_chain, external_chain):
        """Initialize the connector with references to both blockchains."""
        self.local_chain = local_chain
        self.external_chain = external_chain
        
    def sync_from_external(self) -> Dict[str, Any]:
        """
        Synchronize data from the external blockchain to our local blockchain.
        
        Returns:
            Summary of the synchronization results
        """
        # Get the latest blocks from both chains
        local_latest = self.local_chain.get_latest_block()
        external_latest = self.external_chain.last_block
        
        # Summary data for the sync operation
        sync_summary = {
            "operation": "sync_from_external",
            "timestamp": time.time(),
            "local_chain_length_before": len(self.local_chain.chain),
            "external_chain_length": len(self.external_chain.chain),
            "blocks_imported": 0,
            "transactions_imported": 0
        }
        
        # Import all transactions from the external chain's current_transactions
        for tx in self.external_chain.current_transactions:
            # Format the transaction for our local blockchain format
            tx_data = {
                "type": "external_transaction",
                "sender": tx['sender'],
                "recipient": tx['recipient'],
                "amount": tx['amount'],
                "source": "external_blockchain",
                "imported_at": time.time()
            }
            
            # Add the transaction to our local blockchain
            self.local_chain.add_block(tx_data)
            sync_summary["transactions_imported"] += 1
        
        # If the external chain has more blocks than our local chain, import them
        if len(self.external_chain.chain) > 1:  # Skip genesis block
            for block in self.external_chain.chain[1:]:  # Skip genesis block
                # Format the block data for our local blockchain
                block_data = {
                    "type": "external_block",
                    "external_index": block['index'],
                    "external_timestamp": block['timestamp'],
                    "external_transactions": block['transactions'],
                    "external_proof": block['proof'],
                    "external_hash": block['previous_hash'],
                    "source": "external_blockchain",
                    "imported_at": time.time()
                }
                
                # Add the block data to our local blockchain
                self.local_chain.add_block(block_data)
                sync_summary["blocks_imported"] += 1
        
        # Update the summary with final chain length
        sync_summary["local_chain_length_after"] = len(self.local_chain.chain)
        
        return sync_summary
    
    def push_to_external(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Push data from our local blockchain to the external blockchain.
        
        Args:
            data: The data to push to the external blockchain
            
        Returns:
            Summary of the push operation
        """
        # Create a new transaction on the external blockchain
        sender = data.get('sender', 'local_blockchain')
        recipient = data.get('recipient', 'external_blockchain')
        amount = data.get('amount', 1)  # Default amount if not specified
        
        # Record the transaction on the external blockchain
        transaction_index = self.external_chain.new_transaction(
            sender=sender,
            recipient=recipient,
            amount=amount
        )
        
        # Mine a new block on the external blockchain to include the transaction
        last_block = self.external_chain.last_block
        last_proof = last_block['proof']
        proof = self.external_chain.proof_of_work(last_proof)
        previous_hash = self.external_chain.hash(last_block)
        new_block = self.external_chain.new_block(proof, previous_hash)
        
        # Create a summary of the push operation
        push_summary = {
            "operation": "push_to_external",
            "timestamp": time.time(),
            "data_pushed": data,
            "transaction_index": transaction_index,
            "block_created": new_block,
            "external_chain_length": len(self.external_chain.chain)
        }
        
        return push_summary
    
    def export_document_to_external(self, document_id: str) -> Dict[str, Any]:
        """
        Export a document from our local blockchain to the external blockchain.
        
        Args:
            document_id: The ID of the document to export
            
        Returns:
            Summary of the export operation
        """
        # Get the document from our local blockchain
        document = self.local_chain.get_document(document_id)
        
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")
        
        # Create a simplified version of the document for the external blockchain
        simplified_doc = {
            "id": document_id,
            "content": document.get("content", {}),
            "metadata": {
                "version": document.get("metadata", {}).get("version", 0),
                "author": document.get("metadata", {}).get("author", "unknown"),
                "hash": document.get("metadata", {}).get("hash", "")
            }
        }
        
        # Push the document to the external blockchain
        push_data = {
            "sender": "local_document_system",
            "recipient": "external_document_storage",
            "amount": 1,  # Symbolic amount
            "document": simplified_doc
        }
        
        # Perform the push operation
        export_summary = self.push_to_external(push_data)
        
        # Add additional information to the summary
        export_summary["document_id"] = document_id
        export_summary["document_version"] = document.get("metadata", {}).get("version", 0)
        
        return export_summary
    
    def import_transactions_as_document(self, document_id: str, author: str) -> Dict[str, Any]:
        """
        Import transactions from the external blockchain and create a document on our local blockchain.
        
        Args:
            document_id: The ID to use for the new document
            author: The author of the document
            
        Returns:
            Summary of the import operation
        """
        # Check if document already exists
        if self.local_chain.get_document(document_id):
            raise ValueError(f"Document with ID {document_id} already exists")
            
        # Collect all transactions from the external blockchain
        all_transactions = []
        for block in self.external_chain.chain:
            all_transactions.extend(block.get('transactions', []))
        
        # Create a new document with the transaction data
        content = {
            "title": f"External Blockchain Transactions - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "content": json.dumps(all_transactions, indent=2),
            "source": "external_blockchain",
            "transaction_count": len(all_transactions)
        }
        
        # Create the document on our local blockchain
        document = self.local_chain.create_document(document_id, content, author)
        
        # Create a summary of the import operation
        import_summary = {
            "operation": "import_transactions_as_document",
            "timestamp": time.time(),
            "document_id": document_id,
            "transactions_imported": len(all_transactions),
            "author": author,
            "document_created": True
        }
        
        return import_summary

def record_blockchain_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Record an event in the blockchain for auditing and transparency.
    
    Args:
        event_data: Dictionary containing event information to record
        
    Returns:
        Dictionary with information about the recorded event
    """
    if not isinstance(event_data, dict):
        raise ValueError("Event data must be a dictionary")
        
    # Ensure timestamp is included
    if 'timestamp' not in event_data:
        event_data['timestamp'] = time.time()
        
    # Add event to the blockchain as a transaction
    sender = event_data.get('sender', 'system')
    recipient = event_data.get('recipient', 'event_log')
    amount = event_data.get('amount', 0)
    
    # Add the transaction
    external_blockchain.new_transaction(sender, recipient, amount)
    
    # Also create a block with the full event data for better details
    last_block = external_blockchain.chain[-1]
    previous_hash = external_blockchain.hash(last_block)
    # Call proof_of_work on the instance with the correct parameter
    proof = external_blockchain.proof_of_work(last_block['proof'])
    
    # Create block with event data
    event_block = {
        'index': len(external_blockchain.chain) + 1,
        'timestamp': time.time(),
        'event_data': event_data,
        'event_type': event_data.get('type', 'general'),
        'proof': proof,
        'previous_hash': previous_hash
    }
    
    # Add to chain
    external_blockchain.chain.append(event_block)
    
    return {
        'success': True,
        'event_id': event_block['index'],
        'timestamp': event_block['timestamp'],
        'event_type': event_data.get('type', 'general')
    }

# Create a connector instance linking our local blockchain with the external one
blockchain_connector = BlockchainConnector(local_blockchain, external_blockchain)
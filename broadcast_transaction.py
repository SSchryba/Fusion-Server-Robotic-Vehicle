"""
Broadcast Transaction Module

This module provides functionality to broadcast transactions to the blockchain with Unix timestamps.
It includes cryptographic signing, verification, and secure transmission.
"""

import time
import json
import hashlib
import base64
import logging
from typing import Dict, Any, List, Optional

from app import app
from fluxion import fluxion
from blockchain import Wallet, blockchain
from pycamo_integration import pycamo, secure_data, verify_data
import secure_wallet_manager

# Configure logging
logger = logging.getLogger(__name__)

def sha256_hash(data: str) -> str:
    """
    Generate SHA-256 hash of the data.
    
    Args:
        data: String data to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def broadcast_transaction(
    sender: str, 
    recipient: str, 
    amount: float, 
    transaction_type: str = "transfer",
    memo: Optional[str] = None,
    fee: float = 0.0001
) -> Dict[str, Any]:
    """
    Broadcast a transaction to the blockchain with Unix timestamp.
    
    Args:
        sender: Address of the sending wallet
        recipient: Address of the receiving wallet
        amount: Amount of currency to transfer
        transaction_type: Type of transaction (transfer, vacuum, etc.)
        memo: Optional transaction memo or description (will be overridden with timestamp)
        fee: Transaction fee (default 0.0001)
        
    Returns:
        Dictionary with transaction details and broadcast status
    """
    logger.info(f"Broadcasting transaction: {sender} → {recipient} ({amount})")
    
    # Use current Unix timestamp
    unix_timestamp = time.time()
    timestamp_readable = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(unix_timestamp))
    
    # Create transaction data
    transaction_data = {
        "sender": sender,
        "recipient": recipient,
        "amount": amount,
        "fee": fee,
        "type": transaction_type,
        "unix_timestamp": unix_timestamp,
        "timestamp_readable": timestamp_readable,
        "transaction_id": f"tx_{sha256_hash(f'{sender}{recipient}{amount}{unix_timestamp}')[:16]}",
    }
    
    # Always add Unix timestamp memo - includes any user memo if provided
    unix_memo = f"UNIX:{int(unix_timestamp)}"
    if memo and memo.strip():
        unix_memo = f"{unix_memo}|{memo}"
    transaction_data["memo"] = unix_memo
    
    # Generate SHA-256 hash of the transaction
    transaction_json = json.dumps(transaction_data, sort_keys=True)
    transaction_hash = sha256_hash(transaction_json)
    transaction_data["hash"] = transaction_hash
    
    # Create a digital wallet for ECDSA signing
    wallet = Wallet()
    
    # Sign the transaction with ECDSA
    ecdsa_signature = wallet.sign(transaction_json)
    
    # Apply Pycamo security to the transaction data
    secured_transaction = pycamo.secure_broadcast(transaction_data)
    
    # Prepare broadcast data
    broadcast_data = {
        "transaction_data": transaction_data,
        "sha256_hash": transaction_hash,
        "ecdsa_signature": ecdsa_signature,
        "ecdsa_public_key": wallet.get_public_key(),
        "pycamo_secured": True,
        "pycamo_data": secured_transaction,
        "broadcast_timestamp": unix_timestamp
    }
    
    # Apply final Pycamo security layer to the entire broadcast
    secured_broadcast = secure_data(broadcast_data, 'transaction')
    
    # Generate a unique message ID based on transaction hash and timestamp
    message_id = f"tx-{transaction_hash[:8]}-{int(unix_timestamp)}"
    
    # Broadcast through Fluxion
    result = fluxion.broadcast_message(
        message_id=message_id, 
        message_data=secured_broadcast
    )
    
    # Add transaction to blockchain
    block_added = _add_transaction_to_blockchain(transaction_data, ecdsa_signature, wallet.get_public_key())
    
    # Combine results
    combined_result = {
        "transaction_id": transaction_data["transaction_id"],
        "sender": sender,
        "recipient": recipient,
        "amount": amount,
        "unix_timestamp": unix_timestamp,
        "broadcast_status": result.get("status", "unknown"),
        "broadcast_id": result.get("id", "unknown"),
        "block_added": block_added.get("status", "unknown"),
        "block_hash": block_added.get("block_hash", "unknown"),
        "transaction_hash": transaction_hash
    }
    
    logger.info(f"Transaction broadcast complete. ID: {transaction_data['transaction_id']}")
    
    return combined_result

def _add_transaction_to_blockchain(
    transaction_data: Dict[str, Any], 
    signature: str, 
    public_key: str
) -> Dict[str, Any]:
    """
    Add a transaction to the blockchain.
    
    Args:
        transaction_data: Transaction data dictionary
        signature: ECDSA signature for the transaction
        public_key: Public key used for signing
        
    Returns:
        Dictionary with block addition status and details
    """
    try:
        # Create block data
        block_data = {
            "type": "transaction",
            "transaction": transaction_data,
            "signature_info": {
                "signed_by": public_key,
                "signature_algorithm": "ECDSA-secp256k1"
            }
        }
        
        # Add block to the blockchain
        new_block = blockchain.add_block(block_data)
        
        # Create result
        result = {
            "status": "success",
            "block_hash": new_block.hash,
            "block_index": new_block.index,
            "transaction_id": transaction_data["transaction_id"]
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error adding transaction to blockchain: {str(e)}")
        
        return {
            "status": "error",
            "message": f"Error adding transaction to blockchain: {str(e)}"
        }

def broadcast_vacuum_transaction(
    source_wallets: List[Dict[str, Any]],
    destination_wallet: str,
    total_amount: float
) -> Dict[str, Any]:
    """
    Broadcast a vacuum transaction that combines funds from multiple wallets.
    
    Args:
        source_wallets: List of wallets with addresses and amounts
        destination_wallet: Destination wallet address
        total_amount: Total amount being vacuumed
        
    Returns:
        Dictionary with transaction details and broadcast status
    """
    logger.info(f"Broadcasting vacuum transaction: {len(source_wallets)} wallets → {destination_wallet}")
    
    # Create wallet addresses list for the memo
    wallet_addresses = [wallet.get("address", "unknown") for wallet in source_wallets]
    wallet_count = len(wallet_addresses)
    
    # Create a descriptive memo
    memo = f"Vacuum operation: {wallet_count} wallets consolidated. Unix timestamp: {int(time.time())}"
    
    # Broadcast the main transaction
    transaction_result = broadcast_transaction(
        sender="multiple_wallets",
        recipient=destination_wallet,
        amount=total_amount,
        transaction_type="vacuum",
        memo=memo
    )
    
    # Add additional vacuum metadata
    vacuum_metadata = {
        "vacuum_operation": True,
        "source_wallets": wallet_addresses,
        "wallet_count": wallet_count,
        "destination": destination_wallet,
        "total_amount": total_amount,
        "unix_timestamp": int(time.time())
    }
    
    # Secure the vacuum metadata
    secured_metadata = secure_data(vacuum_metadata, 'vacuum_metadata')
    
    # Broadcast the metadata as a supplementary message
    metadata_broadcast = fluxion.broadcast_message(
        message_id=f"vacuum-meta-{transaction_result['transaction_id']}",
        message_data=secured_metadata
    )
    
    # Update the result with vacuum-specific information
    transaction_result["vacuum_metadata_broadcast_id"] = metadata_broadcast.get("id", "unknown")
    transaction_result["wallet_count"] = wallet_count
    
    logger.info(f"Vacuum transaction broadcast complete. ID: {transaction_result['transaction_id']}")
    
    return transaction_result

def broadcast_wallet_transfer(
    wallet_data: Dict[str, Any],
    destination_vault: str = "0xGenesisSecureVault",
    schedule_timestamp: Optional[float] = None
) -> Dict[str, Any]:
    """
    Broadcast a secure wallet transfer to the blockchain with optional scheduled execution.
    
    Args:
        wallet_data: Wallet data to transfer
        destination_vault: The secure vault address
        schedule_timestamp: Optional Unix timestamp for scheduled execution
        
    Returns:
        Dictionary with transfer details and broadcast status
    """
    # Use current Unix timestamp
    unix_timestamp = time.time()
    
    # Get the wallet manager
    wallet_manager = secure_wallet_manager.get_wallet_manager()
    
    # Encrypt the wallet data
    encrypted_wallet_json = wallet_manager.encrypt_data(json.dumps(wallet_data))
    encrypted_wallet_base64 = base64.b64encode(encrypted_wallet_json).decode('utf-8')
    
    # Create the transfer data
    transfer_data = {
        "type": "secure_wallet_transfer",
        "destination_vault": destination_vault,
        "unix_timestamp": unix_timestamp,
        "scheduled_execution": schedule_timestamp if schedule_timestamp else None,
        "encrypted_data": encrypted_wallet_base64,
        "encryption_method": "fernet"
    }
    
    # Create a memo
    if schedule_timestamp:
        scheduled_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(schedule_timestamp))
        memo = f"Scheduled wallet transfer to {destination_vault}. Execution time: {scheduled_time}"
    else:
        memo = f"Immediate wallet transfer to {destination_vault}"
    
    # Broadcast the transaction
    transaction_result = broadcast_transaction(
        sender="secure_wallet_manager",
        recipient=destination_vault,
        amount=wallet_data.get("total_balance", 0.0),
        transaction_type="wallet_transfer",
        memo=memo
    )
    
    # Add the transfer data to the blockchain
    _add_wallet_transfer_to_blockchain(transfer_data, transaction_result["transaction_id"])
    
    logger.info(f"Wallet transfer broadcast complete. ID: {transaction_result['transaction_id']}")
    
    return transaction_result

def _add_wallet_transfer_to_blockchain(
    transfer_data: Dict[str, Any],
    transaction_id: str
) -> Dict[str, Any]:
    """
    Add wallet transfer data to the blockchain.
    
    Args:
        transfer_data: Wallet transfer data
        transaction_id: Associated transaction ID
        
    Returns:
        Dictionary with block addition status and details
    """
    try:
        # Create block data with the transfer information
        block_data = {
            "type": "wallet_transfer",
            "transfer_data": transfer_data,
            "transaction_id": transaction_id,
            "timestamp": time.time()
        }
        
        # Add the block to the blockchain
        new_block = blockchain.add_block(block_data)
        
        # Return the result
        return {
            "status": "success",
            "block_hash": new_block.hash,
            "block_index": new_block.index
        }
        
    except Exception as e:
        logger.error(f"Error adding wallet transfer to blockchain: {str(e)}")
        
        return {
            "status": "error",
            "message": f"Error adding wallet transfer to blockchain: {str(e)}"
        }


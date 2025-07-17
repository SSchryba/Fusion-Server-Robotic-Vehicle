import time
import json
import hashlib
import ecdsa
import base64
from app import app
from fluxion import fluxion
from blockchain import Wallet
from pycamo_integration import pycamo, secure_data, verify_data

def sha256_hash(data):
    """Generate SHA-256 hash of the data."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def broadcast_genesis_entry():
    """Broadcast a genesis ledger entry with proper typing and Pycamo security."""
    # Create message data with explicit type
    message_data = {
        "message": "ledger Entry",
        "timestamp": time.time(),
        "type": "genesis",
        "amt": 12998732.982811
    }
    
    # Generate SHA-256 hash of the message
    message_json = json.dumps(message_data, sort_keys=True)
    message_hash = sha256_hash(message_json)
    
    # Create a digital wallet for ECDSA signing
    wallet = Wallet()
    
    # Sign the message with ECDSA
    ecdsa_signature = wallet.sign(message_json)
    
    # Secure the message with Pycamo
    secured_message = pycamo.secure_broadcast(message_data)
    
    # Prepare broadcast data with proper structure
    broadcast_data = {
        "type": "genesis", # This should now be correctly picked up
        "message_data": message_data,
        "sha256_hash": message_hash,
        "ecdsa_signature": ecdsa_signature,
        "ecdsa_public_key": wallet.get_public_key(),
        "pycamo_secured": True,
        "pycamo_data": secured_message
    }
    
    # Apply final Pycamo security layer to the entire broadcast
    secured_broadcast = secure_data(broadcast_data, 'broadcast')
    
    # Broadcast through Fluxion
    result = fluxion.broadcast_message(
        message_id=f"genesis-entry-{int(time.time())}", 
        message_data=secured_broadcast
    )
    
    return result


"""
Pycamo Integration Module

This module integrates the Pycryptodome (Pycamo) library with our blockchain system,
providing advanced cryptographic functions for securing data in activities and broadcasts.
"""

import base64
import hashlib
import json
import logging
import os
import time
from typing import Dict, Any, List, Tuple, Optional, Union

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

# Configure logging
logger = logging.getLogger(__name__)

class PycamoIntegration:
    """
    Integrates Pycryptodome (Pycamo) cryptographic functions with blockchain activities.
    """
    
    def __init__(self, key_size: int = 2048):
        """
        Initialize the Pycamo integration.
        
        Args:
            key_size: RSA key size in bits
        """
        self.key_size = key_size
        self._generate_or_load_keys()
        logger.info("Pycamo integration initialized with key size: %d", key_size)
    
    def _generate_or_load_keys(self) -> None:
        """Generate new RSA keys or load existing ones."""
        # Check if keys already exist
        if os.path.exists('private_key.pem') and os.path.exists('public_key.pem'):
            try:
                with open('private_key.pem', 'rb') as f:
                    self.private_key = RSA.import_key(f.read())
                with open('public_key.pem', 'rb') as f:
                    self.public_key = RSA.import_key(f.read())
                logger.info("Loaded existing RSA keys")
                return
            except Exception as e:
                logger.warning(f"Error loading keys: {str(e)}. Generating new keys...")
        
        # Generate new keys
        self.private_key = RSA.generate(self.key_size)
        self.public_key = self.private_key.publickey()
        
        # Save keys to files
        with open('private_key.pem', 'wb') as f:
            f.write(self.private_key.export_key('PEM'))
        with open('public_key.pem', 'wb') as f:
            f.write(self.public_key.export_key('PEM'))
        
        logger.info("Generated and saved new RSA key pair")
    
    def encrypt_data(self, data: Union[Dict, List, str]) -> Dict[str, str]:
        """
        Encrypt data using AES and RSA.
        
        Args:
            data: Data to encrypt (will be JSON serialized)
            
        Returns:
            Dictionary with encrypted data and session key
        """
        # Convert data to JSON string if it's a dictionary or list
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data)
        else:
            data_str = str(data)
        
        # Generate a random session key
        session_key = get_random_bytes(16)
        
        # Encrypt the session key with the public RSA key
        cipher_rsa = PKCS1_OAEP.new(self.public_key)
        enc_session_key = cipher_rsa.encrypt(session_key)
        
        # Encrypt the data with AES using the session key
        cipher_aes = AES.new(session_key, AES.MODE_EAX)
        ciphertext, tag = cipher_aes.encrypt_and_digest(data_str.encode('utf-8'))
        
        # Return base64 encoded encrypted data components
        return {
            'encrypted_session_key': base64.b64encode(enc_session_key).decode('utf-8'),
            'nonce': base64.b64encode(cipher_aes.nonce).decode('utf-8'),
            'tag': base64.b64encode(tag).decode('utf-8'),
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8')
        }
    
    def decrypt_data(self, encrypted_data: Dict[str, str]) -> Any:
        """
        Decrypt data that was encrypted with encrypt_data.
        
        Args:
            encrypted_data: Dictionary with encrypted data components
            
        Returns:
            Decrypted data (parsed from JSON if possible)
        """
        # Decode all components from base64
        enc_session_key = base64.b64decode(encrypted_data['encrypted_session_key'])
        nonce = base64.b64decode(encrypted_data['nonce'])
        tag = base64.b64decode(encrypted_data['tag'])
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        
        # Decrypt the session key with the private RSA key
        cipher_rsa = PKCS1_OAEP.new(self.private_key)
        session_key = cipher_rsa.decrypt(enc_session_key)
        
        # Decrypt the data with AES using the session key
        cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
        data = cipher_aes.decrypt_and_verify(ciphertext, tag).decode('utf-8')
        
        # Try to parse JSON
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data
    
    def sign_data(self, data: Union[Dict, List, str]) -> str:
        """
        Create a digital signature for data using the private key.
        
        Args:
            data: Data to sign (will be JSON serialized if dict or list)
            
        Returns:
            Base64 encoded signature
        """
        # Convert data to JSON string if it's a dictionary or list
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        # Hash the data using SHA-256
        h = SHA256.new(data_str.encode('utf-8'))
        
        # Sign the hash with the private key
        signature = pkcs1_15.new(self.private_key).sign(h)
        
        # Return base64 encoded signature
        return base64.b64encode(signature).decode('utf-8')
    
    def verify_signature(self, data: Union[Dict, List, str], signature: str, public_key_pem: Optional[str] = None) -> bool:
        """
        Verify a digital signature using a public key.
        
        Args:
            data: The data that was signed
            signature: Base64 encoded signature
            public_key_pem: PEM encoded public key (uses own public key if None)
            
        Returns:
            True if the signature is valid
        """
        # Convert data to JSON string if it's a dictionary or list
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        # Hash the data using SHA-256
        h = SHA256.new(data_str.encode('utf-8'))
        
        # Decode the signature from base64
        decoded_signature = base64.b64decode(signature)
        
        # Use the provided public key if given, otherwise use own public key
        if public_key_pem:
            verif_key = RSA.import_key(public_key_pem)
        else:
            verif_key = self.public_key
        
        try:
            # Verify the signature
            pkcs1_15.new(verif_key).verify(h, decoded_signature)
            return True
        except (ValueError, TypeError) as e:
            logger.warning(f"Signature verification failed: {str(e)}")
            return False
    
    def secure_broadcast(self, data: Dict[str, Any], include_timestamp: bool = True) -> Dict[str, Any]:
        """
        Prepare a secure broadcast message with encryption and signature.
        
        Args:
            data: Broadcast data
            include_timestamp: Whether to add a timestamp to the data
            
        Returns:
            Secured broadcast data with encryption and signature
        """
        # Add timestamp if requested
        if include_timestamp and 'timestamp' not in data:
            data['timestamp'] = time.time()
        
        # Add hash of original data
        data_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        data['hash'] = data_hash
        
        # Sign the data
        signature = self.sign_data(data)
        
        # Encrypt sensitive fields if present
        secured_data = {**data}  # Create a copy
        sensitive_fields = ['payload', 'content', 'private_data', 'message']
        
        for field in sensitive_fields:
            if field in secured_data and secured_data[field]:
                secured_data[field] = self.encrypt_data(secured_data[field])
                secured_data[f'{field}_encrypted'] = True
        
        # Add metadata
        secured_data['metadata'] = {
            'secured_with': 'pycamo',
            'timestamp': time.time(),
            'signature': signature,
            'public_key': self.public_key.export_key('PEM').decode('utf-8')
        }
        
        return secured_data
    
    def verify_broadcast(self, secured_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify and decrypt a secure broadcast message.
        
        Args:
            secured_data: Secured broadcast data
            
        Returns:
            Tuple of (is_valid, decrypted_data)
        """
        # Extract metadata
        metadata = secured_data.get('metadata', {})
        if not metadata or metadata.get('secured_with') != 'pycamo':
            logger.warning("Not a Pycamo-secured broadcast")
            return False, secured_data
        
        # Verify signature
        signature = metadata.get('signature')
        public_key_pem = metadata.get('public_key')
        
        if not signature or not public_key_pem:
            logger.warning("Missing signature or public key in broadcast")
            return False, secured_data
        
        # Create a copy without the metadata for verification
        verification_data = {**secured_data}
        del verification_data['metadata']
        
        is_valid = self.verify_signature(verification_data, signature, public_key_pem)
        
        if not is_valid:
            logger.warning("Broadcast signature verification failed")
            return False, secured_data
        
        # Decrypt sensitive fields
        decrypted_data = {**secured_data}
        sensitive_fields = ['payload', 'content', 'private_data', 'message']
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data.get(f'{field}_encrypted', False):
                try:
                    decrypted_data[field] = self.decrypt_data(decrypted_data[field])
                    del decrypted_data[f'{field}_encrypted']
                except Exception as e:
                    logger.error(f"Error decrypting {field}: {str(e)}")
                    return False, secured_data
        
        return True, decrypted_data
    
    def secure_ledger_entry(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Secure a sovereign ledger entry with Pycamo.
        
        Args:
            entry_data: The ledger entry data
            
        Returns:
            Secured ledger entry
        """
        # Add security metadata
        entry_data['security'] = {
            'method': 'pycamo',
            'timestamp': time.time(),
            'hash': hashlib.sha256(json.dumps(entry_data, sort_keys=True).encode()).hexdigest()
        }
        
        # Sign the entry
        signature = self.sign_data(entry_data)
        entry_data['security']['signature'] = signature
        
        # Encrypt sensitive data if present
        sensitive_fields = ['private_notes', 'confidential', 'comments']
        for field in sensitive_fields:
            if field in entry_data:
                entry_data[field] = self.encrypt_data(entry_data[field])
                entry_data[f'{field}_encrypted'] = True
        
        return entry_data
    
    def verify_ledger_entry(self, entry_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify and process a secured ledger entry.
        
        Args:
            entry_data: Secured ledger entry
            
        Returns:
            Tuple of (is_valid, processed_entry)
        """
        # Check if this is a secured entry
        security = entry_data.get('security', {})
        if not security or security.get('method') != 'pycamo':
            logger.warning("Not a Pycamo-secured ledger entry")
            return False, entry_data
        
        # Extract and verify the signature
        signature = security.get('signature')
        if not signature:
            logger.warning("Missing signature in ledger entry")
            return False, entry_data
        
        # Create a copy for verification without the signature
        verification_data = {**entry_data}
        verification_data['security'] = {**security}
        del verification_data['security']['signature']
        
        is_valid = self.verify_signature(verification_data, signature)
        
        if not is_valid:
            logger.warning("Ledger entry signature verification failed")
            return False, entry_data
        
        # Decrypt sensitive fields
        processed_entry = {**entry_data}
        sensitive_fields = ['private_notes', 'confidential', 'comments']
        
        for field in sensitive_fields:
            if field in processed_entry and processed_entry.get(f'{field}_encrypted', False):
                try:
                    processed_entry[field] = self.decrypt_data(processed_entry[field])
                    del processed_entry[f'{field}_encrypted']
                except Exception as e:
                    logger.error(f"Error decrypting {field} in ledger entry: {str(e)}")
        
        return True, processed_entry


# Initialize global Pycamo integration
pycamo = PycamoIntegration()

def secure_data(data: Dict[str, Any], data_type: str = 'generic') -> Dict[str, Any]:
    """
    Secure data using the appropriate Pycamo method based on data type.
    
    Args:
        data: The data to secure
        data_type: Type of data (broadcast, ledger_entry, block, etc.)
        
    Returns:
        Secured data
    """
    if data_type == 'broadcast':
        return pycamo.secure_broadcast(data)
    elif data_type == 'ledger_entry':
        return pycamo.secure_ledger_entry(data)
    else:
        # Generic security approach
        data_copy = {**data}
        
        # Add security metadata
        data_copy['pycamo_security'] = {
            'timestamp': time.time(),
            'hash': hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
            'signature': pycamo.sign_data(data)
        }
        
        return data_copy

def verify_data(data: Dict[str, Any], data_type: str = 'generic') -> Tuple[bool, Dict[str, Any]]:
    """
    Verify data using the appropriate Pycamo method based on data type.
    
    Args:
        data: The data to verify
        data_type: Type of data (broadcast, ledger_entry, block, etc.)
        
    Returns:
        Tuple of (is_valid, processed_data)
    """
    if data_type == 'broadcast':
        return pycamo.verify_broadcast(data)
    elif data_type == 'ledger_entry':
        return pycamo.verify_ledger_entry(data)
    else:
        # Generic verification approach
        if 'pycamo_security' not in data:
            return False, data
        
        security = data.get('pycamo_security', {})
        signature = security.get('signature')
        
        if not signature:
            return False, data
        
        # Create copy for verification without the signature
        verification_data = {**data}
        verification_data['pycamo_security'] = {**security}
        del verification_data['pycamo_security']['signature']
        
        is_valid = pycamo.verify_signature(verification_data, signature)
        return is_valid, data
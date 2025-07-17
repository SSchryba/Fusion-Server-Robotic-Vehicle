"""
Email Hunter Module

This module implements email reconnaissance capabilities integrated with our blockchain system,
allowing for tracking and storing email verification activities securely on the blockchain.
"""

import re
import time
import json
import logging
import hashlib
import base64
from typing import Dict, List, Any, Optional, Tuple, Union

# Import blockchain and security-related modules
from blockchain import Blockchain, Wallet
from pycamo_integration import secure_data, verify_data

# Configure logging
logger = logging.getLogger(__name__)

class EmailHunter:
    """
    Email Hunter provides email reconnaissance capabilities with blockchain-backed
    security and verification tracking.
    """
    
    def __init__(self, blockchain: Blockchain, wallet: Optional[Wallet] = None):
        """
        Initialize the Email Hunter with blockchain integration.
        
        Args:
            blockchain: The blockchain instance for secure storage
            wallet: Optional wallet for signing activities
        """
        self.blockchain = blockchain
        self.wallet = wallet if wallet else blockchain.wallet
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.domain_scans = {}
        self.verified_emails = {}
    
    def scan_text_for_emails(self, text: str) -> List[str]:
        """
        Scan text for email addresses.
        
        Args:
            text: Text content to scan
            
        Returns:
            List of email addresses found
        """
        if not text:
            return []
            
        # Find all email addresses in the text
        emails = self.email_pattern.findall(text)
        
        # Remove duplicates while preserving order
        unique_emails = []
        for email in emails:
            if email not in unique_emails:
                unique_emails.append(email)
                
        return unique_emails
    
    def scan_website_for_emails(self, website_text: str, domain: str) -> Dict[str, Any]:
        """
        Scan website content for email addresses.
        
        Args:
            website_text: Scraped website content
            domain: Domain being scanned
            
        Returns:
            Scan results dictionary
        """
        # Extract emails from website text
        found_emails = self.scan_text_for_emails(website_text)
        
        # Create a scan record
        scan_record = {
            "domain": domain,
            "timestamp": time.time(),
            "email_count": len(found_emails),
            "emails": found_emails,
            "scan_id": f"email_scan_{int(time.time())}_{self._hash_text(domain)}"
        }
        
        # Store scan in memory
        self.domain_scans[domain] = scan_record
        
        # Store in blockchain as a document
        scan_document = {
            "type": "email_scan",
            "domain": domain,
            "timestamp": scan_record["timestamp"],
            "email_count": scan_record["email_count"],
            "scan_id": scan_record["scan_id"]
        }
        
        # For security, we don't store raw emails in the blockchain
        # Instead, we store hashed values
        hashed_emails = [
            {
                "hash": self._hash_text(email),
                "domain": email.split('@')[1] if '@' in email else None
            }
            for email in found_emails
        ]
        scan_document["hashed_emails"] = hashed_emails
        
        # Secure document with cryptographic protection
        secured_document = secure_data(scan_document, "email_scan")
        
        # Store in blockchain
        document_id = scan_record["scan_id"]
        
        try:
            self.blockchain.create_document(
                document_id=document_id, 
                content={
                    "title": f"Email Scan for {domain}",
                    "scan_data": secured_document,
                    "sensitive": True,
                    "timestamp": scan_record["timestamp"]
                },
                author="email_hunter"
            )
            
            logger.info(f"Email scan for {domain} stored in blockchain with ID: {document_id}")
            scan_record["blockchain_status"] = "stored"
            scan_record["document_id"] = document_id
            
        except Exception as e:
            logger.error(f"Error storing email scan in blockchain: {str(e)}")
            scan_record["blockchain_status"] = "error"
            scan_record["blockchain_error"] = str(e)
        
        return scan_record
    
    def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Verify if an email exists (placeholder for real verification logic).
        
        Args:
            email: Email address to verify
            
        Returns:
            Verification result
        """
        # Check if email format is valid
        if not self.email_pattern.match(email):
            return {
                "email": email,
                "valid_format": False,
                "exists": False,
                "verified": False,
                "timestamp": time.time()
            }
        
        # Extract domain from email
        domain = email.split('@')[1] if '@' in email else None
        
        # Create verification record - this would actually perform verification in a real implementation
        verification = {
            "email": email,
            "valid_format": True,
            "domain": domain,
            "timestamp": time.time(),
            "verification_id": f"email_verify_{int(time.time())}_{self._hash_text(email)}"
        }
        
        # Store verification record
        self.verified_emails[email] = verification
        
        # Store in blockchain with enhanced security
        verification_document = {
            "type": "email_verification",
            "email_hash": self._hash_text(email),
            "domain": domain,
            "timestamp": verification["timestamp"],
            "verification_id": verification["verification_id"],
            "valid_format": True
        }
        
        # Secure with cryptographic protection
        secured_document = secure_data(verification_document, "email_verification")
        
        # Store in blockchain
        document_id = verification["verification_id"]
        
        try:
            self.blockchain.create_document(
                document_id=document_id, 
                content={
                    "title": f"Email Verification for {domain}",
                    "verification_data": secured_document,
                    "sensitive": True,
                    "timestamp": verification["timestamp"]
                },
                author="email_hunter"
            )
            
            logger.info(f"Email verification for {email} stored in blockchain with ID: {document_id}")
            verification["blockchain_status"] = "stored"
            verification["document_id"] = document_id
            
        except Exception as e:
            logger.error(f"Error storing email verification in blockchain: {str(e)}")
            verification["blockchain_status"] = "error"
            verification["blockchain_error"] = str(e)
        
        return verification
    
    def get_scan_from_blockchain(self, scan_id: str) -> Dict[str, Any]:
        """
        Retrieve a stored email scan from the blockchain.
        
        Args:
            scan_id: ID of the scan document
            
        Returns:
            The scan document data
        """
        try:
            document = self.blockchain.get_document(scan_id)
            
            if not document:
                return {"error": f"Scan with ID {scan_id} not found"}
            
            # Extract and verify the secured scan data
            secured_scan_data = document.get("content", {}).get("scan_data", {})
            
            is_valid, scan_data = verify_data(secured_scan_data, "email_scan")
            
            if not is_valid:
                return {"error": "Scan data verification failed", "document": document}
            
            return {
                "status": "success",
                "scan_data": scan_data,
                "document": document,
                "security_status": "verified" if is_valid else "unverified"
            }
            
        except Exception as e:
            logger.error(f"Error retrieving scan from blockchain: {str(e)}")
            return {"error": str(e)}
    
    def get_verification_from_blockchain(self, verification_id: str) -> Dict[str, Any]:
        """
        Retrieve a stored email verification from the blockchain.
        
        Args:
            verification_id: ID of the verification document
            
        Returns:
            The verification document data
        """
        try:
            document = self.blockchain.get_document(verification_id)
            
            if not document:
                return {"error": f"Verification with ID {verification_id} not found"}
            
            # Extract and verify the secured verification data
            secured_verification_data = document.get("content", {}).get("verification_data", {})
            
            is_valid, verification_data = verify_data(secured_verification_data, "email_verification")
            
            if not is_valid:
                return {"error": "Verification data integrity check failed", "document": document}
            
            return {
                "status": "success",
                "verification_data": verification_data,
                "document": document,
                "security_status": "verified" if is_valid else "unverified"
            }
            
        except Exception as e:
            logger.error(f"Error retrieving verification from blockchain: {str(e)}")
            return {"error": str(e)}
    
    def correlate_email_data(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Correlate email findings across domains or for a specific domain.
        
        Args:
            domain: Optional domain to filter results
            
        Returns:
            Correlation data dictionary
        """
        correlation = {
            "timestamp": time.time(),
            "total_scans": 0,
            "total_verifications": 0,
            "domains": {},
            "domain_stats": {}
        }
        
        # Get all relevant documents from blockchain
        email_documents = []
        
        for doc_id, document in self.blockchain.documents.items():
            content = document.get("content", {})
            
            # Check if this is an email scan or verification document
            if (doc_id.startswith("email_scan_") or doc_id.startswith("email_verify_")) and \
               (content.get("scan_data") or content.get("verification_data")):
                
                # If domain filter is applied, check document title
                if domain:
                    title = content.get("title", "")
                    if domain not in title:
                        continue
                
                email_documents.append(document)
        
        # Process documents
        email_scans = []
        email_verifications = []
        
        for document in email_documents:
            content = document.get("content", {})
            document_id = document.get("metadata", {}).get("document_id", "")
            
            if document_id.startswith("email_scan_") and content.get("scan_data"):
                # Get scan data
                secured_scan_data = content.get("scan_data", {})
                is_valid, scan_data = verify_data(secured_scan_data, "email_scan")
                
                if is_valid and scan_data:
                    email_scans.append(scan_data)
                    
                    # Update domain stats
                    domain = scan_data.get("domain", "unknown")
                    if domain not in correlation["domains"]:
                        correlation["domains"][domain] = {
                            "scans": 0,
                            "verifications": 0,
                            "email_count": 0
                        }
                    
                    correlation["domains"][domain]["scans"] += 1
                    correlation["domains"][domain]["email_count"] += scan_data.get("email_count", 0)
            
            elif document_id.startswith("email_verify_") and content.get("verification_data"):
                # Get verification data
                secured_verification_data = content.get("verification_data", {})
                is_valid, verification_data = verify_data(secured_verification_data, "email_verification")
                
                if is_valid and verification_data:
                    email_verifications.append(verification_data)
                    
                    # Update domain stats
                    domain = verification_data.get("domain", "unknown")
                    if domain not in correlation["domains"]:
                        correlation["domains"][domain] = {
                            "scans": 0,
                            "verifications": 0,
                            "email_count": 0
                        }
                    
                    correlation["domains"][domain]["verifications"] += 1
        
        # Calculate correlation statistics
        correlation["total_scans"] = len(email_scans)
        correlation["total_verifications"] = len(email_verifications)
        
        # Calculate domain statistics
        for domain, stats in correlation["domains"].items():
            # Calculate verification rate if there are emails
            if stats["email_count"] > 0:
                stats["verification_rate"] = stats["verifications"] / stats["email_count"]
            else:
                stats["verification_rate"] = 0
        
        # Sort domains by email count
        correlation["domain_stats"] = sorted(
            correlation["domains"].items(),
            key=lambda x: x[1]["email_count"],
            reverse=True
        )
        
        return correlation
    
    def _hash_text(self, text: str) -> str:
        """
        Create a SHA-256 hash of the given text.
        
        Args:
            text: Text to hash
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()


# Create a global instance
email_hunter = None

def initialize_email_hunter(blockchain: Blockchain, wallet: Optional[Wallet] = None) -> EmailHunter:
    """
    Initialize the global email hunter instance.
    
    Args:
        blockchain: Blockchain instance for storage
        wallet: Optional wallet for signatures
        
    Returns:
        Initialized EmailHunter instance
    """
    global email_hunter
    email_hunter = EmailHunter(blockchain, wallet)
    return email_hunter

def get_email_hunter() -> Optional[EmailHunter]:
    """
    Get the global email hunter instance.
    
    Returns:
        EmailHunter instance or None if not initialized
    """
    return email_hunter

def scan_emails_from_text(text: str) -> List[str]:
    """
    Scan text content for email addresses.
    
    Args:
        text: Text to scan
        
    Returns:
        List of email addresses
    """
    if not email_hunter:
        logger.error("Email hunter not initialized")
        return []
    
    return email_hunter.scan_text_for_emails(text)

def scan_website_content(website_text: str, domain: str) -> Dict[str, Any]:
    """
    Scan website content for email addresses and store results in blockchain.
    
    Args:
        website_text: Scraped website content
        domain: Domain being scanned
        
    Returns:
        Scan results
    """
    if not email_hunter:
        logger.error("Email hunter not initialized")
        return {"error": "Email hunter not initialized"}
    
    return email_hunter.scan_website_for_emails(website_text, domain)

def verify_email_address(email: str) -> Dict[str, Any]:
    """
    Verify an email address and store verification in blockchain.
    
    Args:
        email: Email address to verify
        
    Returns:
        Verification results
    """
    if not email_hunter:
        logger.error("Email hunter not initialized")
        return {"error": "Email hunter not initialized"}
    
    return email_hunter.verify_email(email)

def get_email_correlation(domain: Optional[str] = None) -> Dict[str, Any]:
    """
    Get correlation data for email activities.
    
    Args:
        domain: Optional domain to filter by
        
    Returns:
        Correlation data
    """
    if not email_hunter:
        logger.error("Email hunter not initialized")
        return {"error": "Email hunter not initialized"}
    
    return email_hunter.correlate_email_data(domain)
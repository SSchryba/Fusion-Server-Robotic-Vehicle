"""
GitHub Scanner Integration Module

This module integrates the gh_scanner tool with our blockchain security system,
allowing for scanning of repositories for sensitive information and secure
storage of scan results in the blockchain.
"""

import os
import json
import time
import logging
import sys
from typing import Dict, List, Any, Optional, Tuple

# Add gh_scanner directory to path for imports
sys.path.append('./gh_scanner')
from gh_scanner.gh_scanner import GithubScanner

# Import blockchain and security-related modules
from blockchain import blockchain
from pycamo_integration import pycamo, secure_data, verify_data

# Configure logging
logger = logging.getLogger(__name__)

class BlockchainGithubScanner:
    """
    Integrates the GitHub Scanner tool with our blockchain system for secure
    repository scanning and permanent storage of scan results.
    """
    
    def __init__(self, targets: List[str] = None, scan_members: bool = False):
        """
        Initialize the blockchain GitHub scanner.
        
        Args:
            targets: List of GitHub repositories or organizations to scan
            scan_members: Whether to scan organization members' repositories
        """
        self.targets = targets or []
        self.scan_members = scan_members
        self.scanner = None
        self.access_token = os.environ.get('GITHUB_API_KEY')
        self.scan_results = {}
        
        # Validate GitHub API token presence
        if not self.access_token:
            logger.error("GITHUB_API_KEY environment variable not set")
        else:
            logger.info("GitHub API token available for scanning")
    
    def request_github_token(self) -> bool:
        """
        Request a GitHub token if not already set.
        
        Returns:
            True if token is available, False otherwise
        """
        if self.access_token:
            return True
            
        # Token needs to be set in environment variables
        logger.warning("GitHub API token not found. Please set GITHUB_API_KEY environment variable.")
        return False
    
    def add_target(self, target: str) -> None:
        """
        Add a target repository or organization to scan.
        
        Args:
            target: GitHub repository or organization name
        """
        if target not in self.targets:
            self.targets.append(target)
            logger.info(f"Added target: {target}")
    
    def clear_targets(self) -> None:
        """Clear all scanning targets."""
        self.targets = []
        logger.info("Cleared all scanning targets")
    
    def scan_repositories(self) -> Dict[str, Any]:
        """
        Scan GitHub repositories for sensitive information.
        
        Returns:
            Dictionary with scan results
        """
        if not self.access_token:
            if not self.request_github_token():
                return {"error": "GitHub API token not available"}
        
        if not self.targets:
            return {"error": "No targets specified for scanning"}
        
        try:
            # Initialize the scanner
            self.scanner = GithubScanner(self.targets, self.scan_members)
            
            # Run the scan (this captures the standard output)
            orig_stdout = sys.stdout
            results = {}
            
            for target in self.targets:
                logger.info(f"Scanning target: {target}")
                try:
                    # Start repository scanning
                    if '/' in target:  # Specific repository
                        self.scanner.scan_repository(target)
                    else:  # Organization
                        self.scanner.scan_organization(target)
                    
                    # Get results from scanner (simplified, as the original stores in memory)
                    results[target] = {
                        'scan_time': time.time(),
                        'findings': self.scanner.scan_results if hasattr(self.scanner, 'scan_results') else [],
                        'status': 'completed'
                    }
                except Exception as e:
                    results[target] = {
                        'scan_time': time.time(),
                        'error': str(e),
                        'status': 'failed'
                    }
                    logger.error(f"Error scanning {target}: {str(e)}")
            
            self.scan_results = results
            return results
            
        except Exception as e:
            logger.error(f"Error in GitHub scanning: {str(e)}")
            return {"error": str(e)}
    
    def store_scan_results_in_blockchain(self) -> Dict[str, Any]:
        """
        Store the scan results securely in the blockchain.
        
        Returns:
            Dictionary with storage results
        """
        if not self.scan_results:
            return {"error": "No scan results to store"}
        
        try:
            # Create a document ID for the scan results
            scan_id = f"github_scan_{int(time.time())}"
            
            # Prepare scan results for blockchain storage
            scan_document = {
                "scan_id": scan_id,
                "scan_time": time.time(),
                "targets": self.targets,
                "scan_type": "github_security_scan",
                "results": self.scan_results
            }
            
            # Secure the document with Pycamo
            secured_document = secure_data(scan_document, 'generic')
            
            # Store in blockchain as a document
            blockchain_document = blockchain.create_document(
                document_id=scan_id,
                content={
                    "title": f"GitHub Security Scan ({', '.join(self.targets)})",
                    "scan_data": secured_document,
                    "sensitive": True,
                    "timestamp": time.time()
                },
                author="blockchain_github_scanner"
            )
            
            logger.info(f"Stored GitHub scan results in blockchain with ID: {scan_id}")
            
            return {
                "status": "success",
                "document_id": scan_id,
                "block_index": blockchain_document.get("metadata", {}).get("block_index"),
                "timestamp": blockchain_document.get("metadata", {}).get("updated_at")
            }
            
        except Exception as e:
            logger.error(f"Error storing scan results in blockchain: {str(e)}")
            return {"error": str(e)}
    
    def get_scan_from_blockchain(self, scan_id: str) -> Dict[str, Any]:
        """
        Retrieve a stored GitHub scan from the blockchain.
        
        Args:
            scan_id: ID of the scan document to retrieve
            
        Returns:
            Dictionary with the scan document
        """
        try:
            document = blockchain.get_document(scan_id)
            
            if not document:
                return {"error": f"Scan with ID {scan_id} not found"}
            
            # Extract the secured scan data
            secured_scan_data = document.get("content", {}).get("scan_data", {})
            
            # Verify and decrypt the data
            is_valid, scan_data = verify_data(secured_scan_data, 'generic')
            
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
    
    def analyze_scan_results(self, scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze GitHub scan results for security insights.
        
        Args:
            scan_id: Optional ID of a stored scan, uses latest results if None
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Get scan data either from memory or blockchain
            scan_data = None
            
            if scan_id:
                # Get scan from blockchain
                blockchain_data = self.get_scan_from_blockchain(scan_id)
                if "error" in blockchain_data:
                    return blockchain_data
                scan_data = blockchain_data.get("scan_data", {})
            else:
                # Use latest scan results
                scan_data = {
                    "scan_time": time.time(),
                    "targets": self.targets,
                    "results": self.scan_results
                }
            
            if not scan_data or not scan_data.get("results"):
                return {"error": "No scan data available for analysis"}
            
            # Analyze the results
            results = scan_data.get("results", {})
            targets = scan_data.get("targets", [])
            
            # Count findings
            total_findings = 0
            critical_findings = 0
            findings_by_target = {}
            finding_types = {}
            
            for target, target_data in results.items():
                if target_data.get("status") == "failed":
                    continue
                    
                target_findings = target_data.get("findings", [])
                findings_count = len(target_findings)
                total_findings += findings_count
                findings_by_target[target] = findings_count
                
                # Count by type
                for finding in target_findings:
                    finding_type = finding.get("type", "unknown")
                    if finding_type not in finding_types:
                        finding_types[finding_type] = 0
                    finding_types[finding_type] += 1
                    
                    # Check if critical
                    if finding.get("severity", "").lower() == "critical":
                        critical_findings += 1
            
            analysis = {
                "total_targets": len(targets),
                "successful_scans": sum(1 for t in results.values() if t.get("status") == "completed"),
                "failed_scans": sum(1 for t in results.values() if t.get("status") == "failed"),
                "total_findings": total_findings,
                "critical_findings": critical_findings,
                "findings_by_target": findings_by_target,
                "finding_types": finding_types,
                "scan_time": scan_data.get("scan_time"),
                "analysis_timestamp": time.time()
            }
            
            return {
                "status": "success",
                "analysis": analysis,
                "scan_id": scan_id,
                "recommendations": self._generate_recommendations(analysis)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing scan results: {str(e)}")
            return {"error": str(e)}
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate security recommendations based on scan analysis.
        
        Args:
            analysis: Scan analysis data
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if analysis.get("total_findings", 0) > 0:
            recommendations.append(
                "Found sensitive information in repositories. Consider removing or encrypting this data."
            )
            
        if analysis.get("critical_findings", 0) > 0:
            recommendations.append(
                f"Critical security issues detected ({analysis['critical_findings']}). "
                "Immediate attention required to remove exposed API keys and credentials."
            )
        
        if analysis.get("finding_types", {}).get("API Key", 0) > 0:
            recommendations.append(
                "API keys found in code. Consider using environment variables "
                "or a secure key management system instead."
            )
            
        # Default recommendation
        if not recommendations:
            recommendations.append(
                "No immediate security issues detected. Continue monitoring for potential exposures."
            )
        
        return recommendations


# Create a global scanner instance
github_scanner = BlockchainGithubScanner()


def scan_github_repository(repo_name: str, scan_members: bool = False) -> Dict[str, Any]:
    """
    Scan a GitHub repository and store results in the blockchain.
    
    Args:
        repo_name: Repository name to scan (format: "owner/repo")
        scan_members: Whether to scan organization members' repositories
        
    Returns:
        Dictionary with scan and blockchain storage results
    """
    # Reset scanner and add target
    github_scanner.clear_targets()
    github_scanner.add_target(repo_name)
    github_scanner.scan_members = scan_members
    
    # Run the scan
    scan_results = github_scanner.scan_repositories()
    
    if "error" in scan_results:
        return scan_results
    
    # Store results in blockchain
    storage_results = github_scanner.store_scan_results_in_blockchain()
    
    # Combine results
    return {
        "scan_results": scan_results,
        "blockchain_storage": storage_results,
        "timestamp": time.time()
    }


def analyze_github_security(scan_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze GitHub security scan results.
    
    Args:
        scan_id: Optional ID of a specific scan to analyze
        
    Returns:
        Dictionary with analysis results
    """
    return github_scanner.analyze_scan_results(scan_id)


def list_stored_github_scans() -> List[Dict[str, Any]]:
    """
    List all GitHub scans stored in the blockchain.
    
    Returns:
        List of scan summary dictionaries
    """
    scans = []
    
    for doc_id, document in blockchain.documents.items():
        # Check if this is a GitHub scan document
        if (doc_id.startswith("github_scan_") and 
            document.get("content", {}).get("title", "").startswith("GitHub Security Scan")):
            
            scans.append({
                "scan_id": doc_id,
                "title": document.get("content", {}).get("title", ""),
                "timestamp": document.get("metadata", {}).get("created_at"),
                "updated_at": document.get("metadata", {}).get("updated_at"),
                "author": document.get("metadata", {}).get("author"),
                "secured_with_pycamo": document.get("metadata", {}).get("security", {}).get("method") == "pycamo"
            })
    
    # Sort by timestamp (newest first)
    scans.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    
    return scans
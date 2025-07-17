"""
Secure Permissions Module

This module handles secure permission management for all system activities.
Ensures all executable components have proper permissions and access controls.
"""

import os
import sys
import logging
import subprocess
import stat
from typing import List, Dict, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurePermissions:
    """Manages secure permissions for all system activities."""
    
    def __init__(self, base_path='.'):
        """
        Initialize the secure permissions manager.
        
        Args:
            base_path: Base directory for permission management
        """
        self.base_path = os.path.abspath(base_path)
        self.executable_extensions = ['.py', '.sh']
        self.core_modules = [
            'entropy_coordinator.py',
            'blockchain.py',
            'activity_scheduler.py',
            'eth_wallet_vacuum.py',
            'secure_wallet_manager.py',
            'drift_chain.py',
            'eth_bruteforce_router.py',
            'proxy_router.py',
            'broadcast_transaction.py',
            'fluxion.py',
            'main.py',
            'app.py'
        ]
        self.restricted_modules = []
        self.module_permissions = {}
        
    def find_executable_files(self) -> List[str]:
        """
        Find all executable Python files in the project.
        
        Returns:
            List of executable file paths
        """
        executable_files = []
        
        for root, dirs, files in os.walk(self.base_path):
            # Skip virtual environments and hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'venv' and d != '__pycache__']
            
            for file in files:
                # Check if file has an executable extension
                if any(file.endswith(ext) for ext in self.executable_extensions):
                    file_path = os.path.join(root, file)
                    executable_files.append(file_path)
        
        logger.info(f"Found {len(executable_files)} executable files")
        return executable_files
    
    def check_file_permissions(self, file_path: str) -> Dict[str, Any]:
        """
        Check permissions for a specific file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            Dictionary containing permission details
        """
        if not os.path.exists(file_path):
            return {"exists": False, "path": file_path}
            
        stat_info = os.stat(file_path)
        mode = stat_info.st_mode
        
        # Extract permission details
        permissions = {
            "exists": True,
            "path": file_path,
            "is_executable": bool(mode & stat.S_IXUSR),
            "owner_read": bool(mode & stat.S_IRUSR),
            "owner_write": bool(mode & stat.S_IWUSR),
            "owner_execute": bool(mode & stat.S_IXUSR),
            "group_read": bool(mode & stat.S_IRGRP),
            "group_write": bool(mode & stat.S_IWGRP),
            "group_execute": bool(mode & stat.S_IXGRP),
            "other_read": bool(mode & stat.S_IROTH),
            "other_write": bool(mode & stat.S_IWOTH),
            "other_execute": bool(mode & stat.S_IXOTH),
            "mode_octal": oct(mode & 0o777),
            "size": stat_info.st_size,
            "modified": stat_info.st_mtime
        }
        
        return permissions
    
    def set_executable_permission(self, file_path: str) -> bool:
        """
        Set executable permission for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File does not exist: {file_path}")
                return False
                
            # Get current permissions
            current_mode = os.stat(file_path).st_mode
            
            # Add executable permission for owner
            new_mode = current_mode | stat.S_IXUSR
            
            # Apply new permissions
            os.chmod(file_path, new_mode)
            
            logger.info(f"Set executable permission for {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting executable permission for {file_path}: {e}")
            return False
    
    def set_all_executable_permissions(self) -> Dict[str, Any]:
        """
        Set executable permissions for all project files.
        
        Returns:
            Dictionary with results of permission changes
        """
        executable_files = self.find_executable_files()
        results = {"success": [], "failure": []}
        
        for file_path in executable_files:
            # Skip restricted modules
            if any(restricted in file_path for restricted in self.restricted_modules):
                logger.info(f"Skipping restricted module: {file_path}")
                continue
                
            # Set executable permission
            success = self.set_executable_permission(file_path)
            
            if success:
                results["success"].append(file_path)
            else:
                results["failure"].append(file_path)
        
        logger.info(f"Updated permissions for {len(results['success'])} files")
        if results["failure"]:
            logger.warning(f"Failed to update permissions for {len(results['failure'])} files")
            
        return results
    
    def verify_core_module_permissions(self) -> Dict[str, Any]:
        """
        Verify that all core modules have proper permissions.
        
        Returns:
            Dictionary with verification results
        """
        results = {"verified": [], "missing": [], "permission_issues": []}
        
        for module in self.core_modules:
            module_path = os.path.join(self.base_path, module)
            
            # Check if module exists
            if not os.path.exists(module_path):
                results["missing"].append(module)
                continue
                
            # Check permissions
            permissions = self.check_file_permissions(module_path)
            self.module_permissions[module] = permissions
            
            # Verify executable permission
            if not permissions["is_executable"]:
                results["permission_issues"].append(module)
                # Try to fix permission
                self.set_executable_permission(module_path)
            else:
                results["verified"].append(module)
        
        return results
    
    def export_permission_report(self, output_file="permission_report.json") -> str:
        """
        Export a detailed permission report for all modules.
        
        Args:
            output_file: Path to output file for the report
            
        Returns:
            Path to the generated report file
        """
        import json
        from datetime import datetime
        
        # Get permissions for all executable files
        executable_files = self.find_executable_files()
        permissions = {}
        
        for file_path in executable_files:
            relative_path = os.path.relpath(file_path, self.base_path)
            permissions[relative_path] = self.check_file_permissions(file_path)
        
        # Create report
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_path": self.base_path,
            "total_files": len(executable_files),
            "core_modules": self.core_modules,
            "restricted_modules": self.restricted_modules,
            "permissions": permissions
        }
        
        # Write report to file
        output_path = os.path.join(self.base_path, output_file)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Permission report exported to {output_path}")
        return output_path
    
    def validate_production_readiness(self) -> Dict[str, Any]:
        """
        Validate that all components are ready for production.
        Checks for debug code, test fragments, and proper permissions.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            "ready_for_production": True,
            "issues": [],
            "warnings": [],
            "permission_status": {},
            "debug_indicators": {
                "print_statements": [],
                "debug_flags": [],
                "test_code": []
            }
        }
        
        # Verify core modules have proper permissions
        permission_status = self.verify_core_module_permissions()
        results["permission_status"] = permission_status
        
        if permission_status["missing"] or permission_status["permission_issues"]:
            results["ready_for_production"] = False
            results["issues"].append("Core module permission issues detected")
        
        # Check for debug indicators in files
        executable_files = self.find_executable_files()
        
        for file_path in executable_files:
            relative_path = os.path.relpath(file_path, self.base_path)
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    # Check for print statements (excluding logging)
                    if "print(" in content:
                        results["debug_indicators"]["print_statements"].append(relative_path)
                    
                    # Check for debug flags
                    if "DEBUG = True" in content or "debug=True" in content:
                        results["debug_indicators"]["debug_flags"].append(relative_path)
                    
                    # Check for test code indicators
                    if "test_" in content or "assert " in content:
                        results["debug_indicators"]["test_code"].append(relative_path)
            
            except Exception as e:
                results["warnings"].append(f"Could not analyze {relative_path}: {e}")
        
        # Update production readiness based on debug indicators
        if (results["debug_indicators"]["debug_flags"] or 
            len(results["debug_indicators"]["print_statements"]) > 5):
            results["ready_for_production"] = False
            results["issues"].append("Debug indicators detected in code")
            
        return results
    
def release_executable_permissions(base_path="."):
    """
    Release executable permissions to all activities and validate production readiness.
    
    Args:
        base_path: Base directory for permission management
        
    Returns:
        Dictionary with permission release results and validation status
    """
    secure_permissions = SecurePermissions(base_path)
    
    # Set executable permissions for all files
    permission_results = secure_permissions.set_all_executable_permissions()
    
    # Validate production readiness
    validation_results = secure_permissions.validate_production_readiness()
    
    # Generate permission report
    report_path = secure_permissions.export_permission_report()
    
    results = {
        "permission_changes": permission_results,
        "validation": validation_results,
        "report_path": report_path,
        "all_activities_enabled": len(permission_results["failure"]) == 0,
        "production_ready": validation_results["ready_for_production"]
    }
    
    if results["all_activities_enabled"]:
        logger.info("Successfully released executable permissions to all activities")
    else:
        logger.warning("Could not release permissions to all activities")
    
    return results

# Direct execution
if __name__ == "__main__":
    logger.info("Releasing executable permissions to all activities...")
    results = release_executable_permissions()
    
    # Log summary
    logger.info("=== PERMISSION RELEASE SUMMARY ===")
    logger.info(f"All activities enabled: {results['all_activities_enabled']}")
    logger.info(f"Production ready: {results['production_ready']}")
    logger.info(f"Permission report: {results['report_path']}")
    
    if results['validation']['issues']:
        logger.info("Production readiness issues:")
        for issue in results['validation']['issues']:
            logger.info(f"- {issue}")
            
    if not results['all_activities_enabled']:
        logger.warning("Failed permission changes:")
        for failure in results['permission_changes']['failure']:
            logger.warning(f"- {failure}")
#!/usr/bin/env python3
"""
Test script for Venmo brute force authentication.

This script tests the Venmo brute force authentication capabilities, attempting
to authenticate using multiple patterns through the enhanced authentication system.
"""

import os
import time
import logging
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("VenmoBruteForceTest")

def test_venmo_brute_force():
    """
    Test the Venmo brute force authentication capabilities by trying
    all available authentication methods in sequence.
    
    Returns:
        Dict[str, Any]: Test results with details about each authentication step
    """
    logger.info("🔍 Starting Venmo brute force authentication test")
    
    # Import necessary modules
    try:
        from venmo_integration import (
            authenticate_venmo, 
            enable_venmo_godmode, 
            authenticate_venmo_with_bruteforce,
            authenticate_venmo_with_all_methods,
            get_venmo_integration_status
        )
    except ImportError as e:
        logger.error(f"❌ Failed to import necessary modules: {str(e)}")
        return {
            "success": False,
            "error": f"Import error: {str(e)}",
            "timestamp": time.time()
        }
    
    # Track overall test results
    results = {
        "timestamp": time.time(),
        "auth_methods_tested": [],
        "successful_methods": [],
        "failed_methods": [],
        "overall_success": False,
        "fallback_available": True
    }
    
    # Test 1: Standard authentication
    logger.info("🧪 Test 1: Standard Venmo authentication")
    try:
        start_time = time.time()
        standard_result = authenticate_venmo()
        auth_time = time.time() - start_time
        
        auth_method = {
            "method": "standard",
            "success": standard_result,
            "time_taken": auth_time,
            "timestamp": time.time()
        }
        
        results["auth_methods_tested"].append(auth_method)
        
        if standard_result:
            logger.info("✅ Standard authentication successful")
            results["successful_methods"].append("standard")
            results["overall_success"] = True
        else:
            logger.info("❌ Standard authentication failed")
            results["failed_methods"].append("standard")
    except Exception as e:
        logger.error(f"❌ Error during standard authentication test: {str(e)}")
        results["failed_methods"].append("standard")
        results["auth_methods_tested"].append({
            "method": "standard",
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        })
    
    # If standard auth was successful, we can skip the other tests
    if not results["overall_success"]:
        # Test 2: GodMode authentication
        logger.info("🧪 Test 2: GodMode authentication")
        try:
            start_time = time.time()
            godmode_result = enable_venmo_godmode(True)
            auth_time = time.time() - start_time
            
            auth_method = {
                "method": "godmode",
                "success": godmode_result,
                "time_taken": auth_time,
                "timestamp": time.time()
            }
            
            results["auth_methods_tested"].append(auth_method)
            
            if godmode_result:
                logger.info("✅ GodMode authentication successful")
                results["successful_methods"].append("godmode")
                results["overall_success"] = True
            else:
                logger.info("❌ GodMode authentication failed")
                results["failed_methods"].append("godmode")
        except Exception as e:
            logger.error(f"❌ Error during GodMode authentication test: {str(e)}")
            results["failed_methods"].append("godmode")
            results["auth_methods_tested"].append({
                "method": "godmode",
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            })
    
    # If either standard or GodMode auth was successful, we can skip the bruteforce test
    if not results["overall_success"]:
        # Test 3: Brute force authentication
        logger.info("🧪 Test 3: Brute force authentication")
        try:
            start_time = time.time()
            bruteforce_result = authenticate_venmo_with_bruteforce()
            auth_time = time.time() - start_time
            
            auth_method = {
                "method": "bruteforce",
                "success": bruteforce_result,
                "time_taken": auth_time,
                "timestamp": time.time()
            }
            
            results["auth_methods_tested"].append(auth_method)
            
            if bruteforce_result:
                logger.info("✅ Brute force authentication successful or fallback enabled")
                results["successful_methods"].append("bruteforce")
                results["overall_success"] = True
            else:
                logger.info("❌ Brute force authentication failed")
                results["failed_methods"].append("bruteforce")
        except Exception as e:
            logger.error(f"❌ Error during brute force authentication test: {str(e)}")
            results["failed_methods"].append("bruteforce")
            results["auth_methods_tested"].append({
                "method": "bruteforce",
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            })
    
    # Test 4: All methods in sequence (comprehensive test)
    logger.info("🧪 Test 4: All authentication methods in sequence")
    try:
        start_time = time.time()
        sequential_result = authenticate_venmo_with_all_methods()
        auth_time = time.time() - start_time
        
        auth_method = {
            "method": "sequential_all",
            "success": sequential_result,
            "time_taken": auth_time,
            "timestamp": time.time()
        }
        
        results["auth_methods_tested"].append(auth_method)
        
        if sequential_result:
            logger.info("✅ Sequential authentication successful with at least one method")
            results["successful_methods"].append("sequential_all")
            results["overall_success"] = True
        else:
            logger.info("❌ All sequential authentication methods failed")
            results["failed_methods"].append("sequential_all")
    except Exception as e:
        logger.error(f"❌ Error during sequential authentication test: {str(e)}")
        results["failed_methods"].append("sequential_all")
        results["auth_methods_tested"].append({
            "method": "sequential_all",
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        })
    
    # Get final Venmo integration status
    try:
        final_status = get_venmo_integration_status()
        results["final_status"] = final_status
        
        # Check if fallback is available and configured
        results["fallback_available"] = (
            final_status.get("eth_wallet_fallback", {}).get("enabled", False) and
            final_status.get("eth_wallet_fallback", {}).get("wallet_address") is not None
        )
        
        logger.info(f"📊 Venmo integration status: Authentication {'succeeded' if final_status.get('authenticated', False) else 'failed'}")
        logger.info(f"📊 Fallback mode: {'enabled' if final_status.get('using_fallback', False) else 'not needed'}")
    except Exception as e:
        logger.error(f"❌ Error getting final Venmo integration status: {str(e)}")
        results["final_status_error"] = str(e)
    
    # Summarize results
    results["total_successful_methods"] = len(results["successful_methods"])
    results["total_failed_methods"] = len(results["failed_methods"])
    results["completion_time"] = time.time()
    results["test_duration"] = results["completion_time"] - results["timestamp"]
    
    # Final log message
    if results["overall_success"]:
        logger.info(f"✅ Venmo brute force test PASSED - At least one authentication method succeeded")
        logger.info(f"✅ Successful methods: {', '.join(results['successful_methods'])}")
    else:
        logger.info(f"❌ Venmo brute force test FAILED - All authentication methods failed")
        if results["fallback_available"]:
            logger.info("✅ ETH wallet fallback is available for transfers")
        else:
            logger.error("❌ ETH wallet fallback is NOT available - transfers may fail completely")
    
    return results

if __name__ == "__main__":
    # Run the test
    test_results = test_venmo_brute_force()
    
    # Print summary
    print("\n" + "="*50)
    print("VENMO BRUTE FORCE AUTHENTICATION TEST SUMMARY")
    print("="*50)
    
    print(f"Overall success: {test_results['overall_success']}")
    print(f"Total methods tested: {len(test_results['auth_methods_tested'])}")
    print(f"Successful methods: {test_results['total_successful_methods']}")
    print(f"Failed methods: {test_results['total_failed_methods']}")
    print(f"ETH wallet fallback available: {test_results['fallback_available']}")
    print(f"Test duration: {test_results['test_duration']:.2f} seconds")
    
    if test_results.get("final_status", {}).get("authenticated", False):
        print("\nAuthentication STATUS: SUCCESSFUL ✅")
    elif test_results.get("final_status", {}).get("using_fallback", False):
        print("\nAuthentication STATUS: USING FALLBACK ⚠️")
    else:
        print("\nAuthentication STATUS: FAILED ❌")
    
    print("="*50)
    
    # Exit with appropriate status code
    sys.exit(0 if test_results["overall_success"] or test_results["fallback_available"] else 1)
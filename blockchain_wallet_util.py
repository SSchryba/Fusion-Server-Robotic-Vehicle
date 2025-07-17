"""
Blockchain Wallet Utility

A command-line utility for managing wallet data in the blockchain.
This tool allows users to:
- Store wallet data in the genesis block
- Transfer funds between wallets
- Broadcast transactions with Unix timestamps
- View wallet data stored in the blockchain
"""

import os
import sys
import time
import json
import argparse
import hashlib
import logging
from typing import Dict, Any, List, Optional
import base64

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("blockchain_wallet_util")

# Import app context for Flask
from app import app
from blockchain import blockchain, Wallet, Block
import secure_wallet_manager
import broadcast_transaction

class BlockchainWalletUtil:
    """Utility for interacting with wallets in the blockchain."""
    
    def __init__(self):
        """Initialize the utility."""
        self.wallet_manager = secure_wallet_manager.get_wallet_manager()
    
    def find_wallet_in_blockchain(self, address: str) -> Dict[str, Any]:
        """
        Search for a wallet in the blockchain by its address.
        
        Args:
            address: The wallet address to find
            
        Returns:
            Dictionary with wallet details or empty dict if not found
        """
        logger.info(f"Searching for wallet {address} in blockchain...")
        
        # Iterate through all blocks
        for block in blockchain.chain:
            # Check if the block contains wallet data
            if isinstance(block.data, dict):
                # Check if the block is a wallet transfer or contains wallet info
                if block.data.get('type') == 'wallet_transfer':
                    transfer_data = block.data.get('transfer_data', {})
                    if transfer_data.get('destination_vault') == address:
                        logger.info(f"Found wallet transfer for {address} in block {block.index}")
                        return {
                            'block_index': block.index,
                            'block_hash': block.hash,
                            'transfer_type': 'wallet_transfer',
                            'timestamp': block.timestamp,
                            'unix_timestamp': block.timestamp
                        }
                # Check transactions
                elif block.data.get('type') == 'transaction':
                    tx = block.data.get('transaction', {})
                    if tx.get('recipient') == address or tx.get('sender') == address:
                        logger.info(f"Found transaction for {address} in block {block.index}")
                        return {
                            'block_index': block.index,
                            'block_hash': block.hash,
                            'transaction_type': tx.get('type', 'unknown'),
                            'timestamp': block.timestamp,
                            'unix_timestamp': block.timestamp,
                            'transaction': tx
                        }
                # Check for wallets in genesis block
                elif 'wallets' in block.data:
                    for wallet_id, wallet_info in block.data['wallets'].items():
                        if wallet_info.get('address') == address:
                            logger.info(f"Found wallet {address} in genesis block")
                            return {
                                'block_index': block.index,
                                'wallet_id': wallet_id,
                                'wallet_info': wallet_info,
                                'timestamp': block.timestamp,
                                'unix_timestamp': block.timestamp
                            }
        
        logger.info(f"No wallet found with address {address}")
        return {}
    
    def store_wallet_in_blockchain(self, wallet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store wallet data in the blockchain.
        
        Args:
            wallet_data: Wallet data to store
            
        Returns:
            Dictionary with transaction details
        """
        logger.info(f"Storing wallet {wallet_data.get('address', 'unknown')} in blockchain...")
        
        # Add Unix timestamp
        wallet_data['unix_timestamp'] = time.time()
        
        # Broadcast the wallet transfer to the blockchain
        transfer_result = broadcast_transaction.broadcast_wallet_transfer(
            wallet_data=wallet_data,
            destination_vault=wallet_data.get('address', '0xGenesisSecureVault')
        )
        
        logger.info(f"Wallet stored in blockchain. Transaction ID: {transfer_result.get('transaction_id', 'unknown')}")
        return transfer_result
    
    def create_new_secure_wallet(self, name: str = None) -> Dict[str, Any]:
        """
        Create a new secure wallet and store it in the blockchain.
        
        Args:
            name: Optional name for the wallet
            
        Returns:
            Dictionary with wallet details
        """
        # Create a new wallet
        new_wallet = Wallet()
        public_key = new_wallet.get_public_key()
        
        # Generate a unique address
        timestamp = time.time()
        address_hash = hashlib.sha256(f"{public_key}{timestamp}".encode()).hexdigest()
        address = f"0x{address_hash[:40]}"
        
        # Create wallet data
        wallet_name = name or f"wallet_{address_hash[:8]}"
        wallet_data = {
            'name': wallet_name,
            'address': address,
            'public_key': public_key,
            'created_at': timestamp,
            'type': 'secure_wallet',
            'balance': 0.0
        }
        
        # Store the wallet in the blockchain
        transfer_result = self.store_wallet_in_blockchain(wallet_data)
        
        # Combine results
        wallet_data['transaction_id'] = transfer_result.get('transaction_id', 'unknown')
        wallet_data['block_hash'] = transfer_result.get('block_hash', 'unknown')
        
        logger.info(f"Created new secure wallet: {address}")
        
        return wallet_data
    
    def list_all_wallets(self) -> List[Dict[str, Any]]:
        """
        List all wallets stored in the blockchain.
        
        Returns:
            List of wallet details
        """
        logger.info("Listing all wallets in blockchain...")
        
        wallets = []
        address_to_wallet = {}  # Track wallets by address to avoid duplicates and merge info
        
        # Iterate through all blocks
        for block in blockchain.chain:
            # Check if block contains wallet data
            if isinstance(block.data, dict):
                # Check for wallets in genesis block
                if 'wallets' in block.data:
                    for wallet_id, wallet_info in block.data['wallets'].items():
                        address = wallet_info.get('address')
                        if address:
                            wallet_info['block_index'] = block.index
                            wallet_info['wallet_id'] = wallet_id
                            wallet_info['unix_timestamp'] = block.timestamp
                            address_to_wallet[address] = {**address_to_wallet.get(address, {}), **wallet_info}
                
                # Check for wallet transfers
                elif block.data.get('type') == 'wallet_transfer':
                    transfer_data = block.data.get('transfer_data', {})
                    destination = transfer_data.get('destination_vault')
                    
                    if destination:
                        # Try to decrypt wallet data if available
                        encrypted_data = transfer_data.get('encrypted_data')
                        
                        # Create or update wallet info
                        if destination not in address_to_wallet:
                            address_to_wallet[destination] = {
                                'address': destination,
                                'type': 'secure_wallet',
                                'name': f"Wallet {destination[-8:]}",
                                'balance': 0.0,
                                'created_at': block.timestamp
                            }
                        
                        # Update with block info
                        address_to_wallet[destination].update({
                            'block_index': block.index,
                            'unix_timestamp': block.timestamp
                        })
                
                # Check transactions for wallet-related data
                elif block.data.get('type') == 'transaction':
                    tx = block.data.get('transaction', {})
                    
                    # For wallet transfer transactions, extract complete wallet data if available
                    if tx.get('type') == 'wallet_transfer':
                        recipient = tx.get('recipient')
                        if recipient:
                            wallet_data = {
                                'address': recipient,
                                'block_index': block.index,
                                'unix_timestamp': block.timestamp,
                                'type': 'transaction_wallet',
                                'transaction_id': tx.get('transaction_id'),
                                'name': tx.get('memo', f"Wallet {recipient[-8:]}")
                            }
                            
                            # Update wallet info
                            address_to_wallet[recipient] = {**address_to_wallet.get(recipient, {}), **wallet_data}
                    
                    # Check for other wallet data in memo field
                    memo = tx.get('memo', '')
                    if memo and 'wallet' in memo.lower():
                        sender = tx.get('sender')
                        recipient = tx.get('recipient')
                        
                        if sender and sender != 'multiple_wallets' and sender != 'secure_wallet_manager':
                            address_to_wallet[sender] = address_to_wallet.get(sender, {
                                'address': sender,
                                'type': 'transaction_wallet',
                                'name': f"Wallet {sender[-8:]}",
                                'created_at': block.timestamp
                            })
                        
                        if recipient:
                            address_to_wallet[recipient] = address_to_wallet.get(recipient, {
                                'address': recipient,
                                'type': 'transaction_wallet',
                                'name': f"Wallet {recipient[-8:]}",
                                'created_at': block.timestamp
                            })
        
        # Convert from dictionary to list
        wallets = list(address_to_wallet.values())
        
        # Sort wallets by timestamp (newest first)
        wallets.sort(key=lambda w: w.get('unix_timestamp', 0), reverse=True)
        
        # Ensure all wallets have required fields
        for wallet in wallets:
            # Add default values for missing fields
            if 'balance' not in wallet:
                wallet['balance'] = 0.0
            if 'name' not in wallet:
                wallet['name'] = f"Wallet {wallet.get('address', 'unknown')[-8:]}"
            if 'created_at' not in wallet and 'unix_timestamp' in wallet:
                wallet['created_at'] = wallet['unix_timestamp']
                
        logger.info(f"Found {len(wallets)} unique wallets in blockchain")
        return wallets
    
    def broadcast_transaction(self, sender: str, recipient: str, amount: float, 
                             memo: str = None) -> Dict[str, Any]:
        """
        Broadcast a transaction to the blockchain with Unix timestamp.
        
        Args:
            sender: Address of the sending wallet
            recipient: Address of the receiving wallet
            amount: Amount to transfer
            memo: Optional transaction memo
            
        Returns:
            Dictionary with transaction details
        """
        logger.info(f"Broadcasting transaction from {sender} to {recipient} for {amount}...")
        
        # Check if wallets exist in blockchain
        sender_info = self.find_wallet_in_blockchain(sender)
        if not sender_info:
            logger.warning(f"Sender wallet {sender} not found in blockchain")
        
        recipient_info = self.find_wallet_in_blockchain(recipient)
        if not recipient_info:
            logger.warning(f"Recipient wallet {recipient} not found in blockchain")
        
        # Broadcast the transaction
        transaction_result = broadcast_transaction.broadcast_transaction(
            sender=sender,
            recipient=recipient,
            amount=amount,
            transaction_type='transfer',
            memo=memo
        )
        
        logger.info(f"Transaction broadcast complete. ID: {transaction_result.get('transaction_id', 'unknown')}")
        return transaction_result
    
    def import_wallet_to_blockchain(self, address: str, name: str = None, 
                                   balance: float = 0.0) -> Dict[str, Any]:
        """
        Import an external wallet address to the blockchain.
        
        Args:
            address: External wallet address
            name: Optional name for the wallet
            balance: Initial balance
            
        Returns:
            Dictionary with wallet details
        """
        # Check if wallet already exists
        existing_wallet = self.find_wallet_in_blockchain(address)
        if existing_wallet:
            logger.info(f"Wallet {address} already exists in blockchain")
            return existing_wallet
        
        # Create wallet data
        wallet_name = name or f"imported_{address[-8:]}"
        wallet_data = {
            'name': wallet_name,
            'address': address,
            'created_at': time.time(),
            'type': 'imported_wallet',
            'balance': balance
        }
        
        # Store in blockchain
        transfer_result = self.store_wallet_in_blockchain(wallet_data)
        
        # Combine results
        wallet_data['transaction_id'] = transfer_result.get('transaction_id', 'unknown')
        wallet_data['block_hash'] = transfer_result.get('block_hash', 'unknown')
        
        logger.info(f"Imported wallet {address} to blockchain")
        return wallet_data

def main():
    """Main entry point for the command-line utility."""
    parser = argparse.ArgumentParser(description='Blockchain Wallet Utility')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create new wallet command
    create_parser = subparsers.add_parser('create', help='Create a new secure wallet')
    create_parser.add_argument('--name', help='Name for the wallet')
    
    # List wallets command
    list_parser = subparsers.add_parser('list', help='List all wallets')
    
    # Find wallet command
    find_parser = subparsers.add_parser('find', help='Find a wallet by address')
    find_parser.add_argument('address', help='Wallet address to find')
    
    # Broadcast transaction command
    tx_parser = subparsers.add_parser('transaction', help='Broadcast a transaction')
    tx_parser.add_argument('sender', help='Sender wallet address')
    tx_parser.add_argument('recipient', help='Recipient wallet address')
    tx_parser.add_argument('amount', type=float, help='Amount to transfer')
    tx_parser.add_argument('--memo', help='Transaction memo')
    
    # Import wallet command
    import_parser = subparsers.add_parser('import', help='Import an external wallet')
    import_parser.add_argument('address', help='External wallet address')
    import_parser.add_argument('--name', help='Name for the wallet')
    import_parser.add_argument('--balance', type=float, default=0.0, help='Initial balance')
    
    args = parser.parse_args()
    
    with app.app_context():
        util = BlockchainWalletUtil()
        
        if args.command == 'create':
            result = util.create_new_secure_wallet(args.name)
            print(json.dumps(result, indent=2))
            
        elif args.command == 'list':
            wallets = util.list_all_wallets()
            print(json.dumps(wallets, indent=2))
            
        elif args.command == 'find':
            wallet = util.find_wallet_in_blockchain(args.address)
            if wallet:
                print(json.dumps(wallet, indent=2))
            else:
                print(f"No wallet found with address {args.address}")
                
        elif args.command == 'transaction':
            result = util.broadcast_transaction(
                sender=args.sender,
                recipient=args.recipient,
                amount=args.amount,
                memo=args.memo
            )
            print(json.dumps(result, indent=2))
            
        elif args.command == 'import':
            result = util.import_wallet_to_blockchain(
                address=args.address,
                name=args.name,
                balance=args.balance
            )
            print(json.dumps(result, indent=2))
            
        else:
            parser.print_help()

if __name__ == '__main__':
    main()
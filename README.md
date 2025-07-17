# Kairo AI Live Crypto Hunter v1.2.0

A sophisticated blockchain intelligence platform that leverages advanced AI and authentication protocols to provide comprehensive cryptocurrency insights and management through innovative monitoring and wallet vacuum technologies.

## Key Features

- **Multi-Chain Support**: Monitor and analyze Bitcoin, Ethereum, and DriftChain networks
- **Wallet Vacuum System**: Automatically discover, track, and manage cryptocurrency wallets
- **Monero Integration**: Secure transfers to Monero with enhanced privacy
- **Venmo Integration**: Alternative transfer path with robust authentication
- **Blockchain Monitoring**: Real-time network status, gas prices, and integrity validation
- **DriftChain Vacuum Mode**: Control block creation and dynamic cycling
- **GodMode Protocol**: Enhanced authentication and task automation
- **Data Authenticity Validation**: Ensure all data flows are legitimately sourced
- **Document Merging**: Cryptographic security with ECDSA signatures (secp256k1)
- **Voice Agent**: Bubbly AI assistant with speech recognition and text-to-speech

## System Requirements

- Python 3.9 or higher
- PostgreSQL database
- Required Python packages (see pyproject.toml)
- Environment variables for secure credentials

## Environment Variables

The following environment variables must be set for proper operation:

- `DATABASE_URL`: PostgreSQL database URL
- `MONERO_WALLET_ADDRESS`: Destination Monero wallet address
- `VENMO_USERNAME` and `VENMO_PASSWORD`: Venmo account credentials (optional)
- `VENMO_ACCESS_TOKEN`: Venmo API access token (optional)
- `OPENAI_API_KEY`: API key for the Voice Agent

## Installation

1. Clone this repository to your server
2. Install required dependencies with `pip install -e .`
3. Set up the PostgreSQL database and set the `DATABASE_URL` environment variable
4. Set the required environment variables for Monero and Venmo integration
5. Run the application with `gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app`

## Core Modules

- **blockchain.py**: Core blockchain implementation with ECDSA signatures
- **activity_scheduler.py**: Scheduling for blockchain activities
- **eth_wallet_vacuum.py**: ETH wallet discovery and management
- **monero_integration.py**: Monero transfer capabilities
- **fluxion.py**: Continuous data processing system
- **kairo_operations.py**: Operations management and CLI interface
- **voice_agent.py**: Voice assistant with OpenAI integration

## CLI Interface

The CLI interface in `kairo_operations.py` provides access to key operations:

```
python kairo_operations.py [command] [options]

Commands:
    status                  - Show overall system status
    transfer                - Transfer all assets using brute force authentication
    transfer-interval       - Transfer assets in $1000 USD intervals
    vacuum                  - Run ETH wallet vacuum operation
    drift                   - Control DriftChain vacuum mode
    monitor                 - Run blockchain monitoring functions
    validate                - Validate blockchain integrity
    godmode                 - Configure and test GodMode protocol
    auth                    - Test Venmo authentication methods
    help                    - Show this help message
```

## Security Notice

This application includes powerful blockchain interaction capabilities. Always use securely and responsibly.

## License

Proprietary and Confidential. All rights reserved.

Copyright © 2025

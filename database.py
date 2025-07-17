import os
import logging
import json
import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from models import (
    Base, Block, Transaction, Document, DocumentHistory, Broadcast, BlockchainMetrics, ValidationEvent, SyncEvent,
    LedgerPerson, LedgerProject, LedgerTask, LedgerTaskHistory, LedgerTag, LedgerCommitment, LedgerEntry,
    GithubScan, EmailScan, EmailVerification, ProxyActivity, EthereumRouterActivity, DriftChainEvent
)

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create engine and session with connection pooling and reconnection settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=300,    # Recycle connections every 5 minutes
    pool_size=10,        # Maximum number of connections in the pool
    max_overflow=20,     # Maximum number of connections that can be created beyond pool_size
    connect_args={
        "connect_timeout": 10,  # Connection timeout in seconds
        "application_name": "Kairo AI Live Crypto Hunter",  # App name for database logs
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

def init_db():
    """Initialize the database by creating all tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {e}")
        raise

# Import text at the module level
from sqlalchemy import text

def get_session():
    """Get a new database session with retry capability."""
    max_retries = 3
    retry_delay = 1  # seconds
    last_exception = None
    
    for attempt in range(max_retries):
        session = None
        try:
            session = db_session()
            # Test that the connection is alive with a simple query
            session.execute(text("SELECT 1"))
            return session
        except SQLAlchemyError as e:
            last_exception = e
            logger.warning(f"Database connection error (attempt {attempt+1}/{max_retries}): {e}")
            if session:
                try:
                    session.close()
                except:
                    pass  # Ignore errors when closing a failed session
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
    
    # If we got here, all retries failed
    logger.error(f"Failed to establish database connection after {max_retries} attempts: {last_exception}")
    # Raise a generic exception if last_exception is None
    if last_exception is None:
        raise SQLAlchemyError("Failed to establish database connection")
    else:
        raise last_exception

def close_session(session):
    """Safely close a database session."""
    session.close()

# Block operations
def save_block(block_data):
    """Save a blockchain block to the database."""
    session = get_session()
    try:
        # Check if block already exists
        existing_block = session.query(Block).filter_by(block_hash=block_data['hash']).first()
        if existing_block:
            logger.info(f"Block {block_data['hash'][:8]}... already exists in database")
            return existing_block.id
        
        # Create new block
        block = Block(
            block_index=block_data['index'],
            block_hash=block_data['hash'],
            previous_hash=block_data['previous_hash'],
            timestamp=block_data['timestamp'],
            nonce=block_data['nonce'],
            data=block_data.get('data'),
            signature=block_data.get('signature')
        )
        session.add(block)
        session.commit()
        
        logger.info(f"Block {block.block_index} saved to database with ID {block.id}")
        return block.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving block to database: {e}")
        raise
    finally:
        session.close()

def get_block(block_hash):
    """Get a block by its hash."""
    session = get_session()
    try:
        return session.query(Block).filter_by(block_hash=block_hash).first()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving block from database: {e}")
        raise
    finally:
        session.close()

def get_latest_blocks(limit=10):
    """Get the latest blocks from the database."""
    session = get_session()
    try:
        return session.query(Block).order_by(Block.block_index.desc()).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving latest blocks from database: {e}")
        raise
    finally:
        session.close()

# Transaction operations
def save_transaction(transaction_data, block_id):
    """Save a transaction to the database."""
    session = get_session()
    try:
        # Check if transaction already exists
        existing_tx = session.query(Transaction).filter_by(transaction_id=transaction_data['id']).first()
        if existing_tx:
            logger.info(f"Transaction {transaction_data['id'][:8]}... already exists in database")
            return existing_tx.id
        
        # Create new transaction
        transaction = Transaction(
            transaction_id=transaction_data['id'],
            block_id=block_id,
            timestamp=transaction_data['timestamp'],
            sender=transaction_data.get('sender'),
            recipient=transaction_data.get('recipient'),
            amount=transaction_data.get('amount'),
            currency=transaction_data.get('currency'),
            data=transaction_data.get('data'),
            signature=transaction_data.get('signature')
        )
        session.add(transaction)
        session.commit()
        
        logger.info(f"Transaction {transaction.transaction_id[:8]}... saved to database with ID {transaction.id}")
        return transaction.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving transaction to database: {e}")
        raise
    finally:
        session.close()

def get_transaction(transaction_id):
    """Get a transaction by its ID."""
    session = get_session()
    try:
        return session.query(Transaction).filter_by(transaction_id=transaction_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving transaction from database: {e}")
        raise
    finally:
        session.close()

def get_latest_transactions(limit=10):
    """Get the latest transactions from the database."""
    session = get_session()
    try:
        return session.query(Transaction).order_by(Transaction.timestamp.desc()).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving latest transactions from database: {e}")
        raise
    finally:
        session.close()

# Document operations
def save_document(document_data):
    """Save a document to the database."""
    session = get_session()
    try:
        # Check if document already exists
        doc_id = document_data.get('id') or document_data.get('document_id')
        if not doc_id:
            logger.error("Document ID is missing in document data")
            return None
            
        existing_doc = session.query(Document).filter_by(document_id=doc_id).first()
        if existing_doc:
            # Update existing document
            existing_doc.version = document_data.get('version', existing_doc.version + 1)
            existing_doc.title = document_data.get('title', existing_doc.title)
            existing_doc.content = document_data.get('content', existing_doc.content)
            existing_doc.author = document_data.get('author', existing_doc.author)
            existing_doc.timestamp = document_data.get('timestamp', existing_doc.timestamp)
            existing_doc.hash = document_data.get('hash', existing_doc.hash)
            
            # Add history entry
            history = DocumentHistory(
                document_id=existing_doc.id,
                version=existing_doc.version,
                changes=document_data.get('changes'),
                author=document_data.get('author'),
                timestamp=document_data.get('timestamp'),
                operation='updated'
            )
            session.add(history)
            
            session.commit()
            logger.info(f"Document {existing_doc.document_id} updated to version {existing_doc.version}")
            return existing_doc.id
        
        # Create new document
        document = Document(
            document_id=doc_id,
            version=document_data.get('version', 1),
            title=document_data.get('title'),
            content=document_data.get('content'),
            author=document_data.get('author'),
            timestamp=document_data.get('timestamp'),
            hash=document_data.get('hash')
        )
        session.add(document)
        session.flush()  # Get document ID before committing
        
        # Add initial history entry
        history = DocumentHistory(
            document_id=document.id,
            version=document.version,
            changes=None,
            author=document.author,
            timestamp=document.timestamp,
            operation='created'
        )
        session.add(history)
        
        session.commit()
        logger.info(f"Document {document.document_id} created with ID {document.id}")
        return document.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving document to database: {e}")
        raise
    finally:
        session.close()

def get_document(document_id):
    """Get a document by its ID."""
    session = get_session()
    try:
        return session.query(Document).filter_by(document_id=document_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving document from database: {e}")
        raise
    finally:
        session.close()

def get_document_history(document_id):
    """Get the history of a document."""
    session = get_session()
    try:
        document = session.query(Document).filter_by(document_id=document_id).first()
        if not document:
            return []
        
        history = session.query(DocumentHistory).filter_by(document_id=document.id).order_by(DocumentHistory.version).all()
        return history
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving document history from database: {e}")
        raise
    finally:
        session.close()

# Broadcast operations
def save_broadcast(broadcast_data):
    """Save a broadcast to the database."""
    session = get_session()
    try:
        # Try to extract message type from data
        message_type = 'unknown'
        data = broadcast_data.get('data', {})
        
        # Check if data is a dict with message_data
        if isinstance(data, dict):
            # Check for message type in various locations
            if 'message_data' in data and isinstance(data['message_data'], dict) and 'type' in data['message_data']:
                message_type = data['message_data']['type']
            elif 'type' in data:
                message_type = data['type']
        
        broadcast = Broadcast(
            broadcast_id=broadcast_data['id'],
            message_type=message_type,
            timestamp=broadcast_data['timestamp'],
            port=broadcast_data.get('port'),
            author=broadcast_data.get('data', {}).get('author'),
            data=broadcast_data.get('data'),
            signature=broadcast_data.get('signature')
        )
        session.add(broadcast)
        session.commit()
        
        logger.info(f"Broadcast {broadcast.broadcast_id} saved to database with ID {broadcast.id}")
        return broadcast.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving broadcast to database: {e}")
        raise
    finally:
        session.close()

def get_latest_broadcasts(limit=10):
    """Get the latest broadcasts from the database."""
    session = get_session()
    try:
        return session.query(Broadcast).order_by(Broadcast.timestamp.desc()).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving latest broadcasts from database: {e}")
        raise
    finally:
        session.close()

# Metrics operations
def save_blockchain_metrics(metrics_data):
    """Save blockchain metrics to the database."""
    session = get_session()
    try:
        metrics = BlockchainMetrics(
            timestamp=metrics_data['timestamp'],
            chain_length=metrics_data['summary']['total_blocks'],
            total_transactions=metrics_data.get('detailed_metrics', {}).get('transactions', {}).get('total', 0),
            total_documents=metrics_data['summary']['total_documents'],
            total_broadcasts=metrics_data['summary']['total_broadcasts'],
            avg_mining_time=metrics_data['summary']['avg_mining_time_seconds'],
            blocks_last_hour=metrics_data.get('summary', {}).get('blocks_per_hour', 0) * 1,  # 1 hour
            blocks_last_day=metrics_data['recent_activity']['blocks_24h'],
            validation_success_rate=metrics_data['health']['validation_success_rate'],
            sync_success_rate=metrics_data['health']['sync_success_rate']
        )
        session.add(metrics)
        session.commit()
        
        logger.info(f"Blockchain metrics saved to database with ID {metrics.id}")
        return metrics.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving blockchain metrics to database: {e}")
        raise
    finally:
        session.close()

def get_latest_metrics(limit=24):
    """Get the latest blockchain metrics from the database."""
    session = get_session()
    try:
        return session.query(BlockchainMetrics).order_by(BlockchainMetrics.timestamp.desc()).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving latest blockchain metrics from database: {e}")
        raise
    finally:
        session.close()

# Validation events
def save_validation_event(validation_data):
    """Save a blockchain validation event to the database."""
    session = get_session()
    try:
        validation = ValidationEvent(
            timestamp=validation_data['timestamp'],
            is_valid=validation_data['is_valid'],
            chain_length=validation_data['chain_length'],
            error_message=validation_data.get('error')
        )
        session.add(validation)
        session.commit()
        
        logger.info(f"Validation event saved to database with ID {validation.id}")
        return validation.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving validation event to database: {e}")
        raise
    finally:
        session.close()

# Sync events
def save_sync_event(sync_data):
    """Save a blockchain synchronization event to the database."""
    session = get_session()
    try:
        sync = SyncEvent(
            timestamp=sync_data['timestamp'],
            success=True,  # Assuming success if we have data
            blocks_imported=sync_data.get('blocks_imported', 0),
            transactions_imported=sync_data.get('transactions_imported', 0),
            error_message=None
        )
        session.add(sync)
        session.commit()
        
        logger.info(f"Sync event saved to database with ID {sync.id}")
        return sync.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving sync event to database: {e}")
        raise
    finally:
        session.close()

def save_sync_error(error_data):
    """Save a blockchain synchronization error to the database."""
    session = get_session()
    try:
        sync = SyncEvent(
            timestamp=error_data['timestamp'],
            success=False,
            blocks_imported=0,
            transactions_imported=0,
            error_message=error_data.get('error')
        )
        session.add(sync)
        session.commit()
        
        logger.info(f"Sync error saved to database with ID {sync.id}")
        return sync.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving sync error to database: {e}")
        raise
    finally:
        session.close()

# GitHub Scanner operations
def save_github_scan(scan_data):
    """Save a GitHub repository scan to the database."""
    session = get_session()
    try:
        # Check if scan already exists
        existing_scan = session.query(GithubScan).filter_by(scan_id=scan_data['scan_id']).first()
        if existing_scan:
            # Update existing scan
            existing_scan.status = scan_data.get('status', existing_scan.status)
            existing_scan.findings = scan_data.get('findings', existing_scan.findings)
            
            session.commit()
            logger.info(f"GitHub scan {existing_scan.scan_id} updated with ID {existing_scan.id}")
            return existing_scan.id
        
        # Create new scan
        scan = GithubScan(
            scan_id=scan_data['scan_id'],
            repository_url=scan_data['repository_url'],
            status=scan_data.get('status', 'pending'),
            findings=scan_data.get('findings'),
            document_id=scan_data.get('document_id')
        )
        session.add(scan)
        session.commit()
        
        logger.info(f"GitHub scan {scan.scan_id} saved to database with ID {scan.id}")
        return scan.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving GitHub scan to database: {e}")
        raise
    finally:
        session.close()

def get_github_scan(scan_id):
    """Get a GitHub scan by its ID."""
    session = get_session()
    try:
        return session.query(GithubScan).filter_by(scan_id=scan_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving GitHub scan from database: {e}")
        raise
    finally:
        session.close()

def get_all_github_scans(limit=50):
    """Get all GitHub scans from the database, newest first."""
    session = get_session()
    try:
        return session.query(GithubScan).order_by(GithubScan.scan_date.desc()).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving GitHub scans from database: {e}")
        raise
    finally:
        session.close()

# Email Scanner operations
def save_email_scan(scan_data):
    """Save an email scan to the database."""
    session = get_session()
    try:
        # Check if scan already exists
        existing_scan = session.query(EmailScan).filter_by(scan_id=scan_data['scan_id']).first()
        if existing_scan:
            # Update existing scan
            existing_scan.results = scan_data.get('results', existing_scan.results)
            existing_scan.source_text = scan_data.get('source_text', existing_scan.source_text)
            existing_scan.source_url = scan_data.get('source_url', existing_scan.source_url)
            
            session.commit()
            logger.info(f"Email scan {existing_scan.scan_id} updated with ID {existing_scan.id}")
            return existing_scan.id
        
        # Create new scan
        scan = EmailScan(
            scan_id=scan_data['scan_id'],
            source_type=scan_data.get('source_type', 'text'),
            source_text=scan_data.get('source_text'),
            source_url=scan_data.get('source_url'),
            results=scan_data.get('results', {}),
            document_id=scan_data.get('document_id')
        )
        session.add(scan)
        session.commit()
        
        logger.info(f"Email scan {scan.scan_id} saved to database with ID {scan.id}")
        return scan.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving email scan to database: {e}")
        raise
    finally:
        session.close()

def get_email_scan(scan_id):
    """Get an email scan by its ID."""
    session = get_session()
    try:
        return session.query(EmailScan).filter_by(scan_id=scan_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving email scan from database: {e}")
        raise
    finally:
        session.close()

def get_latest_email_scans(limit=20):
    """Get the latest email scans from the database."""
    session = get_session()
    try:
        return session.query(EmailScan).order_by(EmailScan.scan_date.desc()).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving latest email scans from database: {e}")
        raise
    finally:
        session.close()

def save_email_verification(verification_data):
    """Save an email verification result to the database."""
    session = get_session()
    try:
        # Check if verification already exists
        existing_verification = session.query(EmailVerification).filter_by(
            verification_id=verification_data['verification_id']).first()
        if existing_verification:
            # Update existing verification
            existing_verification.is_valid = verification_data.get('is_valid', existing_verification.is_valid)
            existing_verification.verification_method = verification_data.get(
                'verification_method', existing_verification.verification_method)
            existing_verification.results = verification_data.get('results', existing_verification.results)
            
            session.commit()
            logger.info(f"Email verification {existing_verification.verification_id} updated with ID {existing_verification.id}")
            return existing_verification.id
        
        # Create new verification
        verification = EmailVerification(
            verification_id=verification_data['verification_id'],
            email=verification_data['email'],
            is_valid=verification_data.get('is_valid', False),
            verification_method=verification_data.get('verification_method', 'syntax'),
            results=verification_data.get('results'),
            email_scan_id=verification_data.get('email_scan_id'),
            document_id=verification_data.get('document_id')
        )
        session.add(verification)
        session.commit()
        
        logger.info(f"Email verification {verification.verification_id} saved to database with ID {verification.id}")
        return verification.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving email verification to database: {e}")
        raise
    finally:
        session.close()

def get_email_verification(verification_id):
    """Get an email verification by its ID."""
    session = get_session()
    try:
        return session.query(EmailVerification).filter_by(verification_id=verification_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving email verification from database: {e}")
        raise
    finally:
        session.close()

# Proxy Router operations
def save_proxy_activity(activity_data):
    """Save proxy router activity to the database."""
    session = get_session()
    try:
        # Create new activity record
        activity = ProxyActivity(
            activity_id=activity_data['activity_id'],
            source_ip=activity_data.get('source_ip'),
            destination_host=activity_data.get('destination_host'),
            destination_port=activity_data.get('destination_port'),
            protocol=activity_data.get('protocol', 'tcp'),
            request_data=activity_data.get('request_data'),
            response_data=activity_data.get('response_data'),
            is_blocked=activity_data.get('is_blocked', False),
            document_id=activity_data.get('document_id')
        )
        session.add(activity)
        session.commit()
        
        logger.info(f"Proxy activity {activity.activity_id} saved to database with ID {activity.id}")
        return activity.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving proxy activity to database: {e}")
        raise
    finally:
        session.close()

def get_proxy_activity(activity_id):
    """Get proxy activity by its ID."""
    session = get_session()
    try:
        return session.query(ProxyActivity).filter_by(activity_id=activity_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving proxy activity from database: {e}")
        raise
    finally:
        session.close()

def get_latest_proxy_activities(limit=50):
    """Get the latest proxy router activities from the database."""
    session = get_session()
    try:
        return session.query(ProxyActivity).order_by(ProxyActivity.timestamp.desc()).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving proxy activities from database: {e}")
        raise
    finally:
        session.close()

# Ethereum Router operations
def save_ethereum_router_activity(activity_data):
    """Save Ethereum bruteforce router activity to the database."""
    session = get_session()
    try:
        # Create new activity record
        activity = EthereumRouterActivity(
            activity_id=activity_data['activity_id'],
            original_url=activity_data.get('original_url'),
            redirected_url=activity_data.get('redirected_url'),
            target_block=activity_data.get('target_block'),
            intercept_type=activity_data.get('intercept_type', 'http'),
            request_data=activity_data.get('request_data')
        )
        session.add(activity)
        session.commit()
        
        logger.info(f"Ethereum router activity {activity.activity_id} saved to database with ID {activity.id}")
        return activity.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving Ethereum router activity to database: {e}")
        raise
    finally:
        session.close()

def get_ethereum_router_activity(activity_id):
    """Get Ethereum router activity by its ID."""
    session = get_session()
    try:
        return session.query(EthereumRouterActivity).filter_by(activity_id=activity_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving Ethereum router activity from database: {e}")
        raise
    finally:
        session.close()

def get_latest_ethereum_router_activities(limit=50):
    """Get the latest Ethereum router activities from the database."""
    session = get_session()
    try:
        return session.query(EthereumRouterActivity).order_by(EthereumRouterActivity.timestamp.desc()).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving Ethereum router activities from database: {e}")
        raise
    finally:
        session.close()

# Sovereign Ledger operations
def save_ledger_entry(entry_data):
    """Save a raw ledger entry to the database."""
    session = get_session()
    try:
        # Check if entry already exists
        existing_entry = session.query(LedgerEntry).filter_by(entry_id=entry_data['entry_id']).first()
        if existing_entry:
            logger.info(f"Ledger entry {entry_data['entry_id']} already exists in database")
            return existing_entry.id
        
        # Create new ledger entry
        entry = LedgerEntry(
            entry_id=entry_data['entry_id'],
            entry_type=entry_data['entry_type'],
            block_id=entry_data.get('block_id'),
            entry_hash=entry_data['entry_hash'],
            previous_hash=entry_data.get('previous_hash'),
            timestamp=entry_data['timestamp'],
            data=entry_data['data'],
            signature=entry_data.get('signature'),
            signer=entry_data.get('signer'),
            signer_public_key=entry_data.get('signer_public_key'),
            state=entry_data.get('state', 'active')
        )
        session.add(entry)
        session.commit()
        
        logger.info(f"Ledger entry {entry.entry_id} saved to database with ID {entry.id}")
        return entry.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving ledger entry to database: {e}")
        raise
    finally:
        session.close()

def save_ledger_person(person_data):
    """Save a person to the sovereign ledger database."""
    session = get_session()
    try:
        # Check if person already exists
        existing_person = session.query(LedgerPerson).filter_by(username=person_data['username']).first()
        if existing_person:
            # Update existing person
            existing_person.display_name = person_data.get('display_name', existing_person.display_name)
            existing_person.email = person_data.get('email', existing_person.email)
            existing_person.public_key = person_data.get('public_key', existing_person.public_key)
            existing_person.user_metadata = person_data.get('user_metadata', existing_person.user_metadata)
            
            session.commit()
            logger.info(f"Person {existing_person.username} updated in database with ID {existing_person.id}")
            return existing_person.id
        
        # Create new person
        person = LedgerPerson(
            username=person_data['username'],
            display_name=person_data.get('display_name'),
            email=person_data.get('email'),
            public_key=person_data.get('public_key'),
            user_metadata=person_data.get('user_metadata')
        )
        session.add(person)
        session.commit()
        
        logger.info(f"Person {person.username} saved to database with ID {person.id}")
        return person.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving person to database: {e}")
        raise
    finally:
        session.close()

def save_ledger_project(project_data):
    """Save a project to the sovereign ledger database."""
    session = get_session()
    try:
        # Check if project already exists
        existing_project = session.query(LedgerProject).filter_by(project_id=project_data['project_id']).first()
        if existing_project:
            # Update existing project
            existing_project.name = project_data.get('name', existing_project.name)
            existing_project.description = project_data.get('description', existing_project.description)
            existing_project.status = project_data.get('status', existing_project.status)
            existing_project.end_date = project_data.get('end_date', existing_project.end_date)
            existing_project.project_metadata = project_data.get('project_metadata', existing_project.project_metadata)
            existing_project.blockchain_ref = project_data.get('blockchain_ref', existing_project.blockchain_ref)
            
            session.commit()
            logger.info(f"Project {existing_project.project_id} updated in database with ID {existing_project.id}")
            return existing_project.id
        
        # Create new project
        project = LedgerProject(
            project_id=project_data['project_id'],
            name=project_data['name'],
            description=project_data.get('description'),
            owner_id=project_data['owner_id'],
            status=project_data.get('status', 'active'),
            start_date=project_data['start_date'],
            end_date=project_data.get('end_date'),
            project_metadata=project_data.get('project_metadata'),
            blockchain_ref=project_data.get('blockchain_ref')
        )
        session.add(project)
        session.commit()
        
        # Add members if specified
        if 'members' in project_data and project_data['members']:
            for member_id in project_data['members']:
                member = session.query(LedgerPerson).get(member_id)
                if member:
                    project.members.append(member)
            session.commit()
        
        logger.info(f"Project {project.project_id} saved to database with ID {project.id}")
        return project.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving project to database: {e}")
        raise
    finally:
        session.close()

def save_ledger_task(task_data):
    """Save a task to the sovereign ledger database."""
    session = get_session()
    try:
        # Check if task already exists
        existing_task = session.query(LedgerTask).filter_by(task_id=task_data['task_id']).first()
        if existing_task:
            # Save history before updating
            history = LedgerTaskHistory(
                task_id=existing_task.id,
                changed_by_id=task_data.get('changed_by_id', task_data['creator_id']),
                timestamp=task_data.get('timestamp', datetime.utcnow().timestamp()),
                changes=task_data,
                blockchain_ref=task_data.get('blockchain_ref')
            )
            session.add(history)
            
            # Update existing task
            existing_task.title = task_data.get('title', existing_task.title)
            existing_task.description = task_data.get('description', existing_task.description)
            existing_task.status = task_data.get('status', existing_task.status)
            existing_task.priority = task_data.get('priority', existing_task.priority)
            existing_task.progress = task_data.get('progress', existing_task.progress)
            existing_task.assignee_id = task_data.get('assignee_id', existing_task.assignee_id)
            existing_task.due_date = task_data.get('due_date', existing_task.due_date)
            existing_task.task_metadata = task_data.get('task_metadata', existing_task.task_metadata)
            existing_task.blockchain_ref = task_data.get('blockchain_ref', existing_task.blockchain_ref)
            
            session.commit()
            logger.info(f"Task {existing_task.task_id} updated in database with ID {existing_task.id}")
            return existing_task.id
        
        # Create new task
        task = LedgerTask(
            task_id=task_data['task_id'],
            title=task_data['title'],
            description=task_data.get('description'),
            status=task_data.get('status', 'open'),
            priority=task_data.get('priority', 'medium'),
            progress=task_data.get('progress', 0),
            assignee_id=task_data.get('assignee_id'),
            creator_id=task_data['creator_id'],
            project_id=task_data.get('project_id'),
            due_date=task_data.get('due_date'),
            blockchain_ref=task_data.get('blockchain_ref'),
            task_metadata=task_data.get('task_metadata')
        )
        session.add(task)
        session.flush()  # Get task ID before committing
        
        # Add initial history entry
        history = LedgerTaskHistory(
            task_id=task.id,
            changed_by_id=task_data['creator_id'],
            timestamp=task_data.get('timestamp', datetime.utcnow().timestamp()),
            changes={"operation": "created", "data": task_data},
            blockchain_ref=task_data.get('blockchain_ref')
        )
        session.add(history)
        
        # Add tags if specified
        if 'tags' in task_data and task_data['tags']:
            for tag_name in task_data['tags']:
                tag = session.query(LedgerTag).filter_by(name=tag_name).first()
                if not tag:
                    # Create tag if it doesn't exist
                    tag = LedgerTag(name=tag_name)
                    session.add(tag)
                    session.flush()
                task.tags.append(tag)
        
        session.commit()
        logger.info(f"Task {task.task_id} saved to database with ID {task.id}")
        return task.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving task to database: {e}")
        raise
    finally:
        session.close()

def save_ledger_commitment(commitment_data):
    """Save a commitment to the sovereign ledger database."""
    session = get_session()
    try:
        # Check if commitment already exists
        existing_commitment = session.query(LedgerCommitment).filter_by(
            commitment_id=commitment_data['commitment_id']).first()
        if existing_commitment:
            # Update existing commitment
            existing_commitment.title = commitment_data.get('title', existing_commitment.title)
            existing_commitment.description = commitment_data.get('description', existing_commitment.description)
            existing_commitment.status = commitment_data.get('status', existing_commitment.status)
            existing_commitment.terms = commitment_data.get('terms', existing_commitment.terms)
            existing_commitment.end_date = commitment_data.get('end_date', existing_commitment.end_date)
            existing_commitment.commitment_metadata = commitment_data.get(
                'commitment_metadata', existing_commitment.commitment_metadata)
            existing_commitment.blockchain_ref = commitment_data.get('blockchain_ref', existing_commitment.blockchain_ref)
            
            session.commit()
            logger.info(f"Commitment {existing_commitment.commitment_id} updated in database with ID {existing_commitment.id}")
            return existing_commitment.id
        
        # Create new commitment
        commitment = LedgerCommitment(
            commitment_id=commitment_data['commitment_id'],
            title=commitment_data['title'],
            description=commitment_data.get('description'),
            status=commitment_data.get('status', 'active'),
            responsible_party_id=commitment_data['responsible_party_id'],
            beneficiary_party_id=commitment_data['beneficiary_party_id'],
            terms=commitment_data['terms'],
            start_date=commitment_data['start_date'],
            end_date=commitment_data.get('end_date'),
            blockchain_ref=commitment_data.get('blockchain_ref'),
            commitment_metadata=commitment_data.get('commitment_metadata')
        )
        session.add(commitment)
        session.commit()
        
        logger.info(f"Commitment {commitment.commitment_id} saved to database with ID {commitment.id}")
        return commitment.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving commitment to database: {e}")
        raise
    finally:
        session.close()

# DriftChain operations
def save_drift_chain_event(event_data):
    """Save a DriftChain event to the database."""
    session = get_session()
    try:
        # Convert details to string if present as a dict
        details = event_data.get('details')
        if isinstance(details, dict):
            details = json.dumps(details)
        
        # Create new DriftChain event
        event = DriftChainEvent(
            event_type=event_data.get('event_type', 'unknown'),
            main_chain_block=event_data.get('main_chain_block'),
            drift_chain_block=event_data.get('drift_chain_block'),
            timestamp=event_data.get('timestamp', time.time()),
            status=event_data.get('status', 'success'),
            details=details
        )
        
        session.add(event)
        session.commit()
        
        logger.info(f"DriftChain event saved to database with ID {event.id}")
        return event.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error saving DriftChain event to database: {e}")
        raise
    finally:
        session.close()
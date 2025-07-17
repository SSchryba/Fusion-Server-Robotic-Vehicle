from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, ForeignKey, DateTime, Text, Enum, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

# Enums for Sovereign Ledger
class TaskStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ProjectStatus(enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class CommitmentStatus(enum.Enum):
    ACTIVE = "active"
    FULFILLED = "fulfilled"
    BREACHED = "breached"
    CANCELLED = "cancelled"

# Association table for many-to-many relationships
project_member_association = Table(
    'project_members', Base.metadata,
    Column('project_id', Integer, ForeignKey('ledger_projects.id')),
    Column('person_id', Integer, ForeignKey('ledger_persons.id'))
)

task_tag_association = Table(
    'task_tags', Base.metadata,
    Column('task_id', Integer, ForeignKey('ledger_tasks.id')),
    Column('tag_id', Integer, ForeignKey('ledger_tags.id'))
)

class Block(Base):
    """Model for blockchain blocks."""
    __tablename__ = 'blocks'
    
    id = Column(Integer, primary_key=True)
    block_index = Column(Integer, nullable=False)
    block_hash = Column(String(64), nullable=False, unique=True)
    previous_hash = Column(String(64), nullable=False)
    timestamp = Column(Float, nullable=False)
    nonce = Column(Integer, nullable=False)
    data = Column(JSON, nullable=True)
    signature = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="block")
    
    def __repr__(self):
        return f"<Block {self.block_index} ({self.block_hash[:8]}...)>"

class Transaction(Base):
    """Model for blockchain transactions."""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(String(64), nullable=False, unique=True)
    block_id = Column(Integer, ForeignKey('blocks.id'), nullable=False)
    timestamp = Column(Float, nullable=False)
    sender = Column(String(128), nullable=True)
    recipient = Column(String(128), nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True)
    data = Column(JSON, nullable=True)
    signature = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    block = relationship("Block", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction {self.transaction_id[:8]}...>"

class Document(Base):
    """Model for blockchain documents."""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(String(64), nullable=False, unique=True)
    version = Column(Integer, nullable=False, default=1)
    title = Column(String(255), nullable=True)
    content = Column(JSON, nullable=True)
    author = Column(String(128), nullable=True)
    timestamp = Column(Float, nullable=False)
    hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    history = relationship("DocumentHistory", back_populates="document")
    github_scan = relationship("GithubScan", back_populates="document", uselist=False)
    email_scan = relationship("EmailScan", back_populates="document", uselist=False)
    email_verification = relationship("EmailVerification", back_populates="document", uselist=False)
    proxy_activity = relationship("ProxyActivity", back_populates="document", uselist=False)
    
    def __repr__(self):
        return f"<Document {self.document_id} v{self.version}>"

class DocumentHistory(Base):
    """Model for document version history."""
    __tablename__ = 'document_history'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    version = Column(Integer, nullable=False)
    changes = Column(JSON, nullable=True)
    author = Column(String(128), nullable=True)
    timestamp = Column(Float, nullable=False)
    operation = Column(String(20), nullable=False)  # created, updated, merged
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    document = relationship("Document", back_populates="history")
    
    def __repr__(self):
        return f"<DocumentHistory {self.document.document_id} v{self.version} ({self.operation})>"

class Broadcast(Base):
    """Model for network broadcasts."""
    __tablename__ = 'broadcasts'
    
    id = Column(Integer, primary_key=True)
    broadcast_id = Column(String(64), nullable=False)
    message_type = Column(String(50), nullable=False)
    timestamp = Column(Float, nullable=False)
    port = Column(Integer, nullable=True)
    author = Column(String(128), nullable=True)
    data = Column(JSON, nullable=True)
    signature = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Broadcast {self.broadcast_id} ({self.message_type})>"

class BlockchainMetrics(Base):
    """Model for blockchain performance metrics."""
    __tablename__ = 'blockchain_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(Float, nullable=False)
    chain_length = Column(Integer, nullable=False)
    total_transactions = Column(Integer, nullable=False)
    total_documents = Column(Integer, nullable=False)
    total_broadcasts = Column(Integer, nullable=False)
    avg_mining_time = Column(Float, nullable=True)
    blocks_last_hour = Column(Integer, nullable=True)
    blocks_last_day = Column(Integer, nullable=True)
    validation_success_rate = Column(Float, nullable=True)
    sync_success_rate = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<BlockchainMetrics {self.timestamp} ({self.chain_length} blocks)>"

class ValidationEvent(Base):
    """Model for blockchain validation events."""
    __tablename__ = 'validation_events'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(Float, nullable=False)
    is_valid = Column(Boolean, nullable=False)
    chain_length = Column(Integer, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        status = "valid" if self.is_valid else "invalid"
        return f"<ValidationEvent {self.timestamp} ({status})>"

class SyncEvent(Base):
    """Model for blockchain synchronization events."""
    __tablename__ = 'sync_events'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(Float, nullable=False)
    success = Column(Boolean, nullable=False)
    blocks_imported = Column(Integer, nullable=True)
    transactions_imported = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        status = "success" if self.success else "failed"
        return f"<SyncEvent {self.timestamp} ({status})>"

# Sovereign Ledger Models

class LedgerPerson(Base):
    """Model for people in the sovereign ledger."""
    __tablename__ = 'ledger_persons'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(128), nullable=False, unique=True)
    display_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    public_key = Column(String(255), nullable=True)
    user_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_tasks = relationship("LedgerTask", back_populates="assignee", foreign_keys="LedgerTask.assignee_id")
    created_tasks = relationship("LedgerTask", back_populates="creator", foreign_keys="LedgerTask.creator_id")
    projects = relationship("LedgerProject", secondary=project_member_association, back_populates="members")
    owned_projects = relationship("LedgerProject", back_populates="owner")
    commitments_responsible = relationship("LedgerCommitment", back_populates="responsible_party", foreign_keys="LedgerCommitment.responsible_party_id")
    commitments_beneficiary = relationship("LedgerCommitment", back_populates="beneficiary_party", foreign_keys="LedgerCommitment.beneficiary_party_id")
    
    def __repr__(self):
        return f"<LedgerPerson {self.username}>"

class LedgerProject(Base):
    """Model for projects in the sovereign ledger."""
    __tablename__ = 'ledger_projects'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(String(64), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey('ledger_persons.id'), nullable=False)
    status = Column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.ACTIVE)
    start_date = Column(Float, nullable=False)
    end_date = Column(Float, nullable=True)
    project_metadata = Column(JSON, nullable=True)
    blockchain_ref = Column(String(64), nullable=True)  # Reference to blockchain entry
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("LedgerPerson", back_populates="owned_projects")
    members = relationship("LedgerPerson", secondary=project_member_association, back_populates="projects")
    tasks = relationship("LedgerTask", back_populates="project")
    
    def __repr__(self):
        return f"<LedgerProject {self.name}>"

class LedgerTag(Base):
    """Model for tags in the sovereign ledger."""
    __tablename__ = 'ledger_tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False, unique=True)
    color = Column(String(7), nullable=True)  # Hex color code
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tasks = relationship("LedgerTask", secondary=task_tag_association, back_populates="tags")
    
    def __repr__(self):
        return f"<LedgerTag {self.name}>"

class LedgerTask(Base):
    """Model for tasks in the sovereign ledger."""
    __tablename__ = 'ledger_tasks'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String(64), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.OPEN)
    priority = Column(Enum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    progress = Column(Integer, nullable=False, default=0)  # 0-100%
    assignee_id = Column(Integer, ForeignKey('ledger_persons.id'), nullable=True)
    creator_id = Column(Integer, ForeignKey('ledger_persons.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('ledger_projects.id'), nullable=True)
    due_date = Column(Float, nullable=True)
    blockchain_ref = Column(String(64), nullable=True)  # Reference to blockchain entry
    task_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignee = relationship("LedgerPerson", back_populates="assigned_tasks", foreign_keys=[assignee_id])
    creator = relationship("LedgerPerson", back_populates="created_tasks", foreign_keys=[creator_id])
    project = relationship("LedgerProject", back_populates="tasks")
    tags = relationship("LedgerTag", secondary=task_tag_association, back_populates="tasks")
    history = relationship("LedgerTaskHistory", back_populates="task")
    
    def __repr__(self):
        return f"<LedgerTask {self.task_id}: {self.title}>"

class LedgerTaskHistory(Base):
    """Model for task history in the sovereign ledger."""
    __tablename__ = 'ledger_task_history'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('ledger_tasks.id'), nullable=False)
    changed_by_id = Column(Integer, ForeignKey('ledger_persons.id'), nullable=False)
    timestamp = Column(Float, nullable=False)
    changes = Column(JSON, nullable=False)  # Store changes as JSON diff
    blockchain_ref = Column(String(64), nullable=True)  # Reference to blockchain entry
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    task = relationship("LedgerTask", back_populates="history")
    changed_by = relationship("LedgerPerson")
    
    def __repr__(self):
        return f"<LedgerTaskHistory for task {self.task_id} at {self.timestamp}>"

class LedgerCommitment(Base):
    """Model for commitments in the sovereign ledger."""
    __tablename__ = 'ledger_commitments'
    
    id = Column(Integer, primary_key=True)
    commitment_id = Column(String(64), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(CommitmentStatus), nullable=False, default=CommitmentStatus.ACTIVE)
    responsible_party_id = Column(Integer, ForeignKey('ledger_persons.id'), nullable=False)
    beneficiary_party_id = Column(Integer, ForeignKey('ledger_persons.id'), nullable=False)
    terms = Column(JSON, nullable=False)  # Terms of the commitment
    start_date = Column(Float, nullable=False)
    end_date = Column(Float, nullable=True)
    blockchain_ref = Column(String(64), nullable=True)  # Reference to blockchain entry
    commitment_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    responsible_party = relationship("LedgerPerson", back_populates="commitments_responsible", foreign_keys=[responsible_party_id])
    beneficiary_party = relationship("LedgerPerson", back_populates="commitments_beneficiary", foreign_keys=[beneficiary_party_id])
    
    def __repr__(self):
        return f"<LedgerCommitment {self.commitment_id}: {self.title}>"

class LedgerEntry(Base):
    """Model for raw ledger entries stored in the blockchain."""
    __tablename__ = 'ledger_entries'
    
    id = Column(Integer, primary_key=True)
    entry_id = Column(String(64), nullable=False, unique=True)
    entry_type = Column(String(50), nullable=False)
    block_id = Column(Integer, ForeignKey('blocks.id'), nullable=True)
    entry_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=True)
    timestamp = Column(Float, nullable=False)
    data = Column(JSON, nullable=False)
    signature = Column(String(255), nullable=True)
    signer = Column(String(128), nullable=True)
    signer_public_key = Column(String(255), nullable=True)
    state = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    block = relationship("Block")
    
    def __repr__(self):
        return f"<LedgerEntry {self.entry_id} ({self.entry_type})>"


class GithubScan(Base):
    """Model for GitHub security scans."""
    __tablename__ = 'github_scans'
    
    id = Column(Integer, primary_key=True)
    scan_id = Column(String(64), nullable=False, unique=True)
    repository_url = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")
    findings = Column(JSON, nullable=True)
    scan_date = Column(DateTime, default=datetime.utcnow)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="github_scan")
    
    def __repr__(self):
        return f"<GithubScan {self.scan_id}>"


class EmailScan(Base):
    """Model for email address scans."""
    __tablename__ = 'email_scans'
    
    id = Column(Integer, primary_key=True)
    scan_id = Column(String(64), nullable=False, unique=True)
    source = Column(String(255), nullable=False)
    scan_type = Column(String(20), default="text")  # text, website, domain
    findings = Column(JSON, nullable=True)
    scan_date = Column(DateTime, default=datetime.utcnow)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="email_scan")
    verifications = relationship("EmailVerification", back_populates="email_scan")
    
    def __repr__(self):
        return f"<EmailScan {self.scan_id}>"


class EmailVerification(Base):
    """Model for email verification results."""
    __tablename__ = 'email_verifications'
    
    id = Column(Integer, primary_key=True)
    verification_id = Column(String(64), nullable=False, unique=True)
    email = Column(String(255), nullable=False)
    is_valid = Column(Boolean, default=False)
    verification_method = Column(String(20), default="syntax")  # syntax, mx, smtp
    results = Column(JSON, nullable=True)
    verification_date = Column(DateTime, default=datetime.utcnow)
    email_scan_id = Column(Integer, ForeignKey('email_scans.id'), nullable=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    
    # Relationships
    email_scan = relationship("EmailScan", back_populates="verifications")
    document = relationship("Document", back_populates="email_verification")
    
    def __repr__(self):
        return f"<EmailVerification {self.verification_id}>"


class ProxyActivity(Base):
    """Model for proxy router activity."""
    __tablename__ = 'proxy_activities'
    
    id = Column(Integer, primary_key=True)
    activity_id = Column(String(64), nullable=False, unique=True)
    source_ip = Column(String(45), nullable=True)
    destination_host = Column(String(255), nullable=True)
    destination_port = Column(Integer, nullable=True)
    protocol = Column(String(10), default="tcp")
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    is_blocked = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="proxy_activity")
    
    def __repr__(self):
        return f"<ProxyActivity {self.activity_id}>"


class EthereumRouterActivity(Base):
    """Model for Ethereum bruteforce router activity."""
    __tablename__ = 'ethereum_router_activities'
    
    id = Column(Integer, primary_key=True)
    activity_id = Column(String(64), nullable=False, unique=True)
    original_url = Column(String(255), nullable=True)
    redirected_url = Column(String(255), nullable=True)
    target_block = Column(String(20), nullable=True)
    intercept_type = Column(String(20), default="http")  # http, socket, rpc
    request_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<EthereumRouterActivity {self.activity_id}>"

class DriftChainEvent(Base):
    """Model for DriftChain events and integration activities."""
    __tablename__ = 'drift_chain_events'
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False)  # block_added, document_created, etc.
    main_chain_block = Column(Integer, nullable=True)  # Main blockchain reference block index
    drift_chain_block = Column(Integer, nullable=True)  # DriftChain block index
    timestamp = Column(Float, default=lambda: datetime.utcnow().timestamp())
    status = Column(String(20), default="success")  # success, failed, pending
    details = Column(Text, nullable=True)  # Additional JSON-encoded details
    
    def __repr__(self):
        return f"<DriftChainEvent {self.id} - {self.event_type}>"
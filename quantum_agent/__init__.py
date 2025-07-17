"""
Quantum Agent for Autonomous AI Agent Framework

A comprehensive quantum computing and supercomputing integration system
that enables autonomous execution of quantum circuits and HPC jobs.
"""

__version__ = "1.0.0"
__author__ = "AI Engineer"
__description__ = "Quantum Computing and HPC Integration for Autonomous AI Agent"

try:
    # Try relative imports first (when used as module)
    from .quantum_executor import QuantumExecutor, QuantumBackend, QuantumJob
    from .supercomputer_dispatcher import SupercomputerDispatcher, HPCCluster, HPCJob
    from .quantum_knowledge_ingestor import QuantumKnowledgeIngestor, DocumentChunk
    from .fusion_knowledge_updater import FusionKnowledgeUpdater
    from .job_logger import JobLogger, JobType, JobPlatform, JobRecord
    from .safeguard import QuantumSafeguards, SecurityIncident, SafeguardViolationType
    from .quantum_agent_orchestrator import QuantumAgentOrchestrator
except ImportError:
    # Fall back to absolute imports (when run directly)
    from quantum_executor import QuantumExecutor, QuantumBackend, QuantumJob
    from supercomputer_dispatcher import SupercomputerDispatcher, HPCCluster, HPCJob
    from quantum_knowledge_ingestor import QuantumKnowledgeIngestor, DocumentChunk
    from fusion_knowledge_updater import FusionKnowledgeUpdater
    from job_logger import JobLogger, JobType, JobPlatform, JobRecord
    from safeguard import QuantumSafeguards, SecurityIncident, SafeguardViolationType
    from quantum_agent_orchestrator import QuantumAgentOrchestrator

__all__ = [
    "QuantumExecutor",
    "QuantumBackend", 
    "QuantumJob",
    "SupercomputerDispatcher",
    "HPCCluster",
    "HPCJob", 
    "QuantumKnowledgeIngestor",
    "DocumentChunk",
    "FusionKnowledgeUpdater",
    "JobLogger",
    "JobType",
    "JobPlatform",
    "JobRecord",
    "QuantumSafeguards",
    "SecurityIncident",
    "SafeguardViolationType",
    "QuantumAgentOrchestrator"
] 
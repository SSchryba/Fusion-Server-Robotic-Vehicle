"""
Anomaly Detection Engine for Network Security Monitoring

Advanced anomaly detection using machine learning algorithms, statistical analysis,
and behavioral profiling to identify sophisticated network threats and anomalies.
"""

import logging
import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
import pickle
from collections import defaultdict, deque

# Machine learning imports
try:
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, confusion_matrix
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Statistical analysis
try:
    from scipy import stats
    import statsmodels.api as sm
    from statsmodels.tsa.seasonal import seasonal_decompose
    STATS_AVAILABLE = True
except ImportError:
    STATS_AVAILABLE = False

from netsniffer import PacketMetadata, TrafficAnomaly, AttackType, TrafficType

logger = logging.getLogger(__name__)


class AnomalyDetectionMethod(Enum):
    """Anomaly detection methods"""
    STATISTICAL = "statistical"
    MACHINE_LEARNING = "machine_learning"
    BEHAVIORAL = "behavioral"
    HYBRID = "hybrid"


class ThreatLevel(Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class NetworkProfile:
    """Network behavior profile for baseline comparison"""
    profile_id: str
    src_ip: str
    dst_ip: Optional[str] = None
    protocol: str = "any"
    port: Optional[int] = None
    
    # Traffic characteristics
    avg_packet_size: float = 0.0
    avg_packet_rate: float = 0.0
    typical_ports: List[int] = field(default_factory=list)
    typical_protocols: List[str] = field(default_factory=list)
    
    # Timing patterns
    active_hours: List[int] = field(default_factory=list)
    peak_traffic_times: List[int] = field(default_factory=list)
    
    # Behavioral metrics
    connection_duration_avg: float = 0.0
    bytes_transferred_avg: float = 0.0
    session_frequency: float = 0.0
    
    # Anomaly thresholds
    packet_size_threshold: float = 2.0  # Standard deviations
    packet_rate_threshold: float = 2.0
    port_diversity_threshold: float = 0.8
    
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'profile_id': self.profile_id,
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'protocol': self.protocol,
            'port': self.port,
            'avg_packet_size': self.avg_packet_size,
            'avg_packet_rate': self.avg_packet_rate,
            'typical_ports': self.typical_ports,
            'typical_protocols': self.typical_protocols,
            'active_hours': self.active_hours,
            'peak_traffic_times': self.peak_traffic_times,
            'connection_duration_avg': self.connection_duration_avg,
            'bytes_transferred_avg': self.bytes_transferred_avg,
            'session_frequency': self.session_frequency,
            'packet_size_threshold': self.packet_size_threshold,
            'packet_rate_threshold': self.packet_rate_threshold,
            'port_diversity_threshold': self.port_diversity_threshold,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class AnomalyScore:
    """Anomaly scoring result"""
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    method: AnomalyDetectionMethod
    features: Dict[str, float]
    explanation: str
    contributing_factors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'score': self.score,
            'confidence': self.confidence,
            'method': self.method.value,
            'features': self.features,
            'explanation': self.explanation,
            'contributing_factors': self.contributing_factors
        }


class NetworkAnomalyDetector:
    """
    Advanced network anomaly detection engine using multiple detection methods
    including statistical analysis, machine learning, and behavioral profiling.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the anomaly detector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Detection configuration
        self.detection_methods = self.config.get('detection_methods', [
            AnomalyDetectionMethod.STATISTICAL,
            AnomalyDetectionMethod.MACHINE_LEARNING,
            AnomalyDetectionMethod.BEHAVIORAL
        ])
        
        self.anomaly_threshold = self.config.get('anomaly_threshold', 0.7)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.6)
        self.learning_rate = self.config.get('learning_rate', 0.01)
        
        # Model configuration
        self.model_update_interval = self.config.get('model_update_interval', 3600)  # seconds
        self.profile_update_interval = self.config.get('profile_update_interval', 1800)  # seconds
        self.feature_window_size = self.config.get('feature_window_size', 100)
        
        # Storage paths
        self.model_dir = Path(self.config.get('model_dir', 'network_security/models'))
        self.profile_dir = Path(self.config.get('profile_dir', 'network_security/profiles'))
        
        # Create directories
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        
        # State management
        self.running = False
        self.packet_history: deque = deque(maxlen=10000)
        self.anomaly_history: List[TrafficAnomaly] = []
        self.network_profiles: Dict[str, NetworkProfile] = {}
        
        # Machine learning models
        self.isolation_forest = None
        self.dbscan_model = None
        self.random_forest = None
        self.feature_scaler = None
        
        # Feature extraction
        self.feature_extractors = {
            'packet_size': self._extract_packet_size_features,
            'packet_rate': self._extract_packet_rate_features,
            'port_diversity': self._extract_port_diversity_features,
            'protocol_distribution': self._extract_protocol_features,
            'timing_patterns': self._extract_timing_features,
            'connection_patterns': self._extract_connection_features
        }
        
        # Statistics tracking
        self.detection_stats = {
            'total_packets_analyzed': 0,
            'anomalies_detected': 0,
            'false_positives': 0,
            'model_accuracy': 0.0,
            'last_model_update': None
        }
        
        # Initialize components
        self._initialize_models()
        self._load_existing_profiles()
        
        logger.info("Network Anomaly Detector initialized")
        
    def _initialize_models(self):
        """Initialize machine learning models"""
        try:
            if ML_AVAILABLE:
                # Isolation Forest for unsupervised anomaly detection
                self.isolation_forest = IsolationForest(
                    contamination=0.1,
                    random_state=42,
                    n_estimators=100
                )
                
                # DBSCAN for clustering-based anomaly detection
                self.dbscan_model = DBSCAN(
                    eps=0.5,
                    min_samples=5
                )
                
                # Random Forest for supervised classification
                self.random_forest = RandomForestClassifier(
                    n_estimators=100,
                    random_state=42,
                    max_depth=10
                )
                
                # Feature scaler
                self.feature_scaler = StandardScaler()
                
                # Try to load existing models
                self._load_existing_models()
                
                logger.info("Machine learning models initialized")
            else:
                logger.warning("Machine learning libraries not available")
                
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
            
    def _load_existing_models(self):
        """Load existing trained models"""
        try:
            model_files = {
                'isolation_forest': self.model_dir / 'isolation_forest.pkl',
                'dbscan_model': self.model_dir / 'dbscan_model.pkl',
                'random_forest': self.model_dir / 'random_forest.pkl',
                'feature_scaler': self.model_dir / 'feature_scaler.pkl'
            }
            
            for model_name, model_file in model_files.items():
                if model_file.exists():
                    with open(model_file, 'rb') as f:
                        model = pickle.load(f)
                        setattr(self, model_name, model)
                        logger.info(f"Loaded existing {model_name}")
                        
        except Exception as e:
            logger.warning(f"Failed to load existing models: {e}")
            
    def _save_models(self):
        """Save trained models"""
        try:
            models = {
                'isolation_forest': self.isolation_forest,
                'dbscan_model': self.dbscan_model,
                'random_forest': self.random_forest,
                'feature_scaler': self.feature_scaler
            }
            
            for model_name, model in models.items():
                if model is not None:
                    model_file = self.model_dir / f'{model_name}.pkl'
                    with open(model_file, 'wb') as f:
                        pickle.dump(model, f)
                        
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
            
    def _load_existing_profiles(self):
        """Load existing network profiles"""
        try:
            profile_files = list(self.profile_dir.glob('*.json'))
            
            for profile_file in profile_files:
                with open(profile_file, 'r') as f:
                    profile_data = json.load(f)
                    
                # Convert timestamps
                profile_data['created_at'] = datetime.fromisoformat(profile_data['created_at'])
                profile_data['last_updated'] = datetime.fromisoformat(profile_data['last_updated'])
                
                profile = NetworkProfile(**profile_data)
                self.network_profiles[profile.profile_id] = profile
                
            logger.info(f"Loaded {len(self.network_profiles)} network profiles")
            
        except Exception as e:
            logger.warning(f"Failed to load existing profiles: {e}")
            
    def _save_profiles(self):
        """Save network profiles"""
        try:
            for profile_id, profile in self.network_profiles.items():
                profile_file = self.profile_dir / f'{profile_id}.json'
                with open(profile_file, 'w') as f:
                    json.dump(profile.to_dict(), f, indent=2)
                    
            logger.info(f"Saved {len(self.network_profiles)} network profiles")
            
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")
            
    async def start(self):
        """Start the anomaly detector"""
        if self.running:
            logger.warning("Anomaly detector is already running")
            return
            
        logger.info("Starting network anomaly detector...")
        
        try:
            self.running = True
            
            # Start background tasks
            asyncio.create_task(self._model_update_loop())
            asyncio.create_task(self._profile_update_loop())
            
            logger.info("Network anomaly detector started")
            
        except Exception as e:
            logger.error(f"Failed to start anomaly detector: {e}")
            self.running = False
            raise
            
    async def stop(self):
        """Stop the anomaly detector"""
        if not self.running:
            logger.warning("Anomaly detector is not running")
            return
            
        logger.info("Stopping network anomaly detector...")
        
        try:
            self.running = False
            
            # Save models and profiles
            self._save_models()
            self._save_profiles()
            
            # Generate final report
            await self._generate_detection_report()
            
            logger.info("Network anomaly detector stopped")
            
        except Exception as e:
            logger.error(f"Error stopping anomaly detector: {e}")
            
    async def analyze_packet(self, packet: PacketMetadata) -> Optional[AnomalyScore]:
        """
        Analyze a single packet for anomalies.
        
        Args:
            packet: Packet metadata to analyze
            
        Returns:
            AnomalyScore if anomaly detected, None otherwise
        """
        try:
            # Add packet to history
            self.packet_history.append(packet)
            self.detection_stats['total_packets_analyzed'] += 1
            
            # Extract features
            features = self._extract_features([packet])
            
            if not features:
                return None
                
            # Run detection methods
            scores = []
            
            for method in self.detection_methods:
                if method == AnomalyDetectionMethod.STATISTICAL:
                    score = await self._statistical_detection(packet, features)
                elif method == AnomalyDetectionMethod.MACHINE_LEARNING:
                    score = await self._ml_detection(packet, features)
                elif method == AnomalyDetectionMethod.BEHAVIORAL:
                    score = await self._behavioral_detection(packet, features)
                elif method == AnomalyDetectionMethod.HYBRID:
                    score = await self._hybrid_detection(packet, features)
                    
                if score:
                    scores.append(score)
                    
            # Combine scores
            if scores:
                combined_score = self._combine_scores(scores)
                
                # Check if anomaly threshold is exceeded
                if combined_score.score >= self.anomaly_threshold:
                    self.detection_stats['anomalies_detected'] += 1
                    return combined_score
                    
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing packet: {e}")
            return None
            
    async def analyze_batch(self, packets: List[PacketMetadata]) -> List[AnomalyScore]:
        """
        Analyze a batch of packets for anomalies.
        
        Args:
            packets: List of packet metadata to analyze
            
        Returns:
            List of anomaly scores
        """
        try:
            anomaly_scores = []
            
            # Add packets to history
            for packet in packets:
                self.packet_history.append(packet)
                self.detection_stats['total_packets_analyzed'] += 1
                
            # Extract features for the batch
            features = self._extract_features(packets)
            
            if not features:
                return []
                
            # Run batch detection
            for method in self.detection_methods:
                if method == AnomalyDetectionMethod.MACHINE_LEARNING:
                    batch_scores = await self._ml_batch_detection(packets, features)
                    anomaly_scores.extend(batch_scores)
                    
            # Filter by threshold
            significant_scores = [
                score for score in anomaly_scores 
                if score.score >= self.anomaly_threshold
            ]
            
            self.detection_stats['anomalies_detected'] += len(significant_scores)
            
            return significant_scores
            
        except Exception as e:
            logger.error(f"Error analyzing batch: {e}")
            return []
            
    def _extract_features(self, packets: List[PacketMetadata]) -> Dict[str, np.ndarray]:
        """Extract features from packets"""
        try:
            features = {}
            
            for feature_name, extractor in self.feature_extractors.items():
                try:
                    feature_values = extractor(packets)
                    if feature_values is not None:
                        features[feature_name] = np.array(feature_values)
                except Exception as e:
                    logger.debug(f"Error extracting {feature_name}: {e}")
                    
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return {}
            
    def _extract_packet_size_features(self, packets: List[PacketMetadata]) -> List[float]:
        """Extract packet size features"""
        sizes = [packet.packet_size for packet in packets]
        return sizes
        
    def _extract_packet_rate_features(self, packets: List[PacketMetadata]) -> List[float]:
        """Extract packet rate features"""
        if len(packets) < 2:
            return [0.0]
            
        # Calculate time differences
        time_diffs = []
        for i in range(1, len(packets)):
            diff = (packets[i].timestamp - packets[i-1].timestamp).total_seconds()
            time_diffs.append(1.0 / diff if diff > 0 else 0.0)
            
        return time_diffs
        
    def _extract_port_diversity_features(self, packets: List[PacketMetadata]) -> List[float]:
        """Extract port diversity features"""
        ports = set()
        diversity_scores = []
        
        for i, packet in enumerate(packets):
            if packet.dst_port:
                ports.add(packet.dst_port)
                
            # Calculate diversity score as unique ports / total packets seen so far
            diversity = len(ports) / (i + 1)
            diversity_scores.append(diversity)
            
        return diversity_scores
        
    def _extract_protocol_features(self, packets: List[PacketMetadata]) -> List[float]:
        """Extract protocol distribution features"""
        protocol_counts = defaultdict(int)
        protocol_scores = []
        
        for i, packet in enumerate(packets):
            protocol_counts[packet.protocol] += 1
            
            # Calculate protocol entropy
            total_packets = i + 1
            entropy = 0.0
            for count in protocol_counts.values():
                p = count / total_packets
                if p > 0:
                    entropy -= p * np.log2(p)
                    
            protocol_scores.append(entropy)
            
        return protocol_scores
        
    def _extract_timing_features(self, packets: List[PacketMetadata]) -> List[float]:
        """Extract timing pattern features"""
        timing_features = []
        
        for i, packet in enumerate(packets):
            hour = packet.timestamp.hour
            
            # Normalize hour to 0-1 range
            hour_normalized = hour / 24.0
            
            # Check if it's a typical business hour
            is_business_hour = 1.0 if 9 <= hour <= 17 else 0.0
            
            # Combined timing score
            timing_score = (hour_normalized + is_business_hour) / 2.0
            timing_features.append(timing_score)
            
        return timing_features
        
    def _extract_connection_features(self, packets: List[PacketMetadata]) -> List[float]:
        """Extract connection pattern features"""
        connection_features = []
        seen_connections = set()
        
        for packet in packets:
            connection = (packet.src_ip, packet.dst_ip, packet.dst_port)
            
            # Check if this is a new connection
            is_new_connection = 1.0 if connection not in seen_connections else 0.0
            seen_connections.add(connection)
            
            # Calculate connection uniqueness
            uniqueness = len(seen_connections) / len(packets)
            
            connection_features.append((is_new_connection + uniqueness) / 2.0)
            
        return connection_features
        
    async def _statistical_detection(self, packet: PacketMetadata, features: Dict[str, np.ndarray]) -> Optional[AnomalyScore]:
        """Statistical anomaly detection"""
        try:
            if not STATS_AVAILABLE:
                return None
                
            # Get baseline statistics from network profiles
            profile = self._get_network_profile(packet)
            
            if not profile:
                return None
                
            # Calculate statistical anomalies
            anomaly_indicators = []
            contributing_factors = []
            
            # Packet size anomaly
            if 'packet_size' in features and len(features['packet_size']) > 0:
                size_zscore = abs(features['packet_size'][0] - profile.avg_packet_size) / max(profile.avg_packet_size * 0.1, 1)
                
                if size_zscore > profile.packet_size_threshold:
                    anomaly_indicators.append(size_zscore / 5.0)  # Normalize
                    contributing_factors.append(f"Unusual packet size: {features['packet_size'][0]}")
                    
            # Port diversity anomaly
            if packet.dst_port and packet.dst_port not in profile.typical_ports:
                port_anomaly = 1.0 if len(profile.typical_ports) > 0 else 0.5
                anomaly_indicators.append(port_anomaly)
                contributing_factors.append(f"Unusual destination port: {packet.dst_port}")
                
            # Protocol anomaly
            if packet.protocol not in profile.typical_protocols:
                protocol_anomaly = 0.8 if len(profile.typical_protocols) > 0 else 0.3
                anomaly_indicators.append(protocol_anomaly)
                contributing_factors.append(f"Unusual protocol: {packet.protocol}")
                
            # Time-based anomaly
            current_hour = packet.timestamp.hour
            if current_hour not in profile.active_hours:
                time_anomaly = 0.6 if len(profile.active_hours) > 0 else 0.2
                anomaly_indicators.append(time_anomaly)
                contributing_factors.append(f"Unusual time: {current_hour}:00")
                
            # Calculate overall anomaly score
            if anomaly_indicators:
                score = min(np.mean(anomaly_indicators), 1.0)
                confidence = min(len(anomaly_indicators) / 4.0, 1.0)
                
                return AnomalyScore(
                    score=score,
                    confidence=confidence,
                    method=AnomalyDetectionMethod.STATISTICAL,
                    features={'statistical_indicators': anomaly_indicators},
                    explanation=f"Statistical anomaly detected with {len(anomaly_indicators)} indicators",
                    contributing_factors=contributing_factors
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error in statistical detection: {e}")
            return None
            
    async def _ml_detection(self, packet: PacketMetadata, features: Dict[str, np.ndarray]) -> Optional[AnomalyScore]:
        """Machine learning anomaly detection"""
        try:
            if not ML_AVAILABLE or not self.isolation_forest:
                return None
                
            # Prepare feature vector
            feature_vector = self._prepare_feature_vector(features)
            
            if feature_vector is None:
                return None
                
            # Scale features
            if self.feature_scaler:
                feature_vector = self.feature_scaler.transform([feature_vector])
            else:
                feature_vector = [feature_vector]
                
            # Isolation Forest prediction
            anomaly_score = self.isolation_forest.decision_function(feature_vector)[0]
            is_anomaly = self.isolation_forest.predict(feature_vector)[0] == -1
            
            if is_anomaly:
                # Normalize score to 0-1 range
                normalized_score = min(abs(anomaly_score) / 0.5, 1.0)
                
                return AnomalyScore(
                    score=normalized_score,
                    confidence=min(normalized_score + 0.2, 1.0),
                    method=AnomalyDetectionMethod.MACHINE_LEARNING,
                    features={'ml_score': anomaly_score},
                    explanation=f"Machine learning anomaly detected (score: {anomaly_score:.3f})",
                    contributing_factors=['Isolation Forest anomaly detection']
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error in ML detection: {e}")
            return None
            
    async def _behavioral_detection(self, packet: PacketMetadata, features: Dict[str, np.ndarray]) -> Optional[AnomalyScore]:
        """Behavioral anomaly detection"""
        try:
            # Get behavioral profile
            profile = self._get_network_profile(packet)
            
            if not profile:
                return None
                
            # Analyze behavioral patterns
            behavioral_anomalies = []
            contributing_factors = []
            
            # Connection pattern analysis
            recent_packets = list(self.packet_history)[-50:]  # Last 50 packets
            
            # Check for rapid connection attempts
            src_connections = [p for p in recent_packets if p.src_ip == packet.src_ip]
            if len(src_connections) > 20:  # High connection rate
                behavioral_anomalies.append(0.8)
                contributing_factors.append("High connection rate detected")
                
            # Check for port scanning behavior
            unique_ports = set(p.dst_port for p in src_connections if p.dst_port)
            if len(unique_ports) > 10:  # Many different ports
                behavioral_anomalies.append(0.9)
                contributing_factors.append("Port scanning behavior detected")
                
            # Check for protocol hopping
            unique_protocols = set(p.protocol for p in src_connections)
            if len(unique_protocols) > 3:  # Multiple protocols
                behavioral_anomalies.append(0.6)
                contributing_factors.append("Protocol hopping detected")
                
            # Check for unusual packet sizes
            if 'packet_size' in features:
                size_variation = np.std([p.packet_size for p in src_connections])
                if size_variation > 1000:  # High variation
                    behavioral_anomalies.append(0.7)
                    contributing_factors.append("High packet size variation")
                    
            # Calculate behavioral score
            if behavioral_anomalies:
                score = min(np.mean(behavioral_anomalies), 1.0)
                confidence = min(len(behavioral_anomalies) / 4.0, 1.0)
                
                return AnomalyScore(
                    score=score,
                    confidence=confidence,
                    method=AnomalyDetectionMethod.BEHAVIORAL,
                    features={'behavioral_indicators': behavioral_anomalies},
                    explanation=f"Behavioral anomaly detected with {len(behavioral_anomalies)} indicators",
                    contributing_factors=contributing_factors
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error in behavioral detection: {e}")
            return None
            
    async def _hybrid_detection(self, packet: PacketMetadata, features: Dict[str, np.ndarray]) -> Optional[AnomalyScore]:
        """Hybrid anomaly detection combining multiple methods"""
        try:
            # Run all detection methods
            statistical_score = await self._statistical_detection(packet, features)
            ml_score = await self._ml_detection(packet, features)
            behavioral_score = await self._behavioral_detection(packet, features)
            
            # Combine scores
            scores = [score for score in [statistical_score, ml_score, behavioral_score] if score]
            
            if not scores:
                return None
                
            # Weighted combination
            weights = {
                AnomalyDetectionMethod.STATISTICAL: 0.3,
                AnomalyDetectionMethod.MACHINE_LEARNING: 0.4,
                AnomalyDetectionMethod.BEHAVIORAL: 0.3
            }
            
            weighted_score = sum(score.score * weights[score.method] for score in scores)
            weighted_confidence = sum(score.confidence * weights[score.method] for score in scores)
            
            # Combine features and contributing factors
            combined_features = {}
            combined_factors = []
            
            for score in scores:
                combined_features.update(score.features)
                combined_factors.extend(score.contributing_factors)
                
            return AnomalyScore(
                score=weighted_score,
                confidence=weighted_confidence,
                method=AnomalyDetectionMethod.HYBRID,
                features=combined_features,
                explanation=f"Hybrid anomaly detected using {len(scores)} methods",
                contributing_factors=combined_factors
            )
            
        except Exception as e:
            logger.error(f"Error in hybrid detection: {e}")
            return None
            
    async def _ml_batch_detection(self, packets: List[PacketMetadata], features: Dict[str, np.ndarray]) -> List[AnomalyScore]:
        """Machine learning batch anomaly detection"""
        try:
            if not ML_AVAILABLE or not self.isolation_forest:
                return []
                
            # Prepare feature matrix
            feature_matrix = []
            valid_indices = []
            
            for i, packet in enumerate(packets):
                packet_features = {key: values[i] if i < len(values) else 0.0 
                                 for key, values in features.items()}
                feature_vector = self._prepare_feature_vector(packet_features)
                
                if feature_vector is not None:
                    feature_matrix.append(feature_vector)
                    valid_indices.append(i)
                    
            if not feature_matrix:
                return []
                
            # Scale features
            if self.feature_scaler:
                feature_matrix = self.feature_scaler.transform(feature_matrix)
                
            # Batch prediction
            anomaly_scores = self.isolation_forest.decision_function(feature_matrix)
            predictions = self.isolation_forest.predict(feature_matrix)
            
            # Create anomaly scores
            results = []
            for i, (score, prediction) in enumerate(zip(anomaly_scores, predictions)):
                if prediction == -1:  # Anomaly detected
                    packet_idx = valid_indices[i]
                    packet = packets[packet_idx]
                    
                    normalized_score = min(abs(score) / 0.5, 1.0)
                    
                    anomaly_score = AnomalyScore(
                        score=normalized_score,
                        confidence=min(normalized_score + 0.2, 1.0),
                        method=AnomalyDetectionMethod.MACHINE_LEARNING,
                        features={'ml_score': score, 'packet_index': packet_idx},
                        explanation=f"Batch ML anomaly detected (score: {score:.3f})",
                        contributing_factors=['Isolation Forest batch detection']
                    )
                    
                    results.append(anomaly_score)
                    
            return results
            
        except Exception as e:
            logger.error(f"Error in ML batch detection: {e}")
            return []
            
    def _prepare_feature_vector(self, features: Dict[str, Any]) -> Optional[List[float]]:
        """Prepare feature vector for ML algorithms"""
        try:
            vector = []
            
            # Extract scalar features
            feature_keys = ['packet_size', 'packet_rate', 'port_diversity', 
                          'protocol_distribution', 'timing_patterns', 'connection_patterns']
            
            for key in feature_keys:
                if key in features:
                    value = features[key]
                    if isinstance(value, (list, np.ndarray)):
                        vector.append(float(value[0]) if len(value) > 0 else 0.0)
                    else:
                        vector.append(float(value))
                else:
                    vector.append(0.0)
                    
            return vector if vector else None
            
        except Exception as e:
            logger.error(f"Error preparing feature vector: {e}")
            return None
            
    def _get_network_profile(self, packet: PacketMetadata) -> Optional[NetworkProfile]:
        """Get network profile for packet"""
        try:
            # Try to find existing profile
            profile_key = f"{packet.src_ip}_{packet.dst_ip}"
            
            if profile_key in self.network_profiles:
                return self.network_profiles[profile_key]
                
            # Create new profile if not found
            profile = NetworkProfile(
                profile_id=profile_key,
                src_ip=packet.src_ip,
                dst_ip=packet.dst_ip,
                protocol=packet.protocol
            )
            
            self.network_profiles[profile_key] = profile
            return profile
            
        except Exception as e:
            logger.error(f"Error getting network profile: {e}")
            return None
            
    def _combine_scores(self, scores: List[AnomalyScore]) -> AnomalyScore:
        """Combine multiple anomaly scores"""
        try:
            if len(scores) == 1:
                return scores[0]
                
            # Weight scores by confidence
            total_weight = sum(score.confidence for score in scores)
            
            if total_weight == 0:
                return scores[0]
                
            weighted_score = sum(score.score * score.confidence for score in scores) / total_weight
            avg_confidence = sum(score.confidence for score in scores) / len(scores)
            
            # Combine features and factors
            combined_features = {}
            combined_factors = []
            
            for score in scores:
                combined_features.update(score.features)
                combined_factors.extend(score.contributing_factors)
                
            return AnomalyScore(
                score=weighted_score,
                confidence=avg_confidence,
                method=AnomalyDetectionMethod.HYBRID,
                features=combined_features,
                explanation=f"Combined anomaly score from {len(scores)} methods",
                contributing_factors=combined_factors
            )
            
        except Exception as e:
            logger.error(f"Error combining scores: {e}")
            return scores[0]
            
    async def _model_update_loop(self):
        """Background model update loop"""
        try:
            while self.running:
                await asyncio.sleep(self.model_update_interval)
                
                if not self.running:
                    break
                    
                # Update models with recent data
                await self._update_models()
                
        except Exception as e:
            logger.error(f"Error in model update loop: {e}")
            
    async def _update_models(self):
        """Update machine learning models with recent data"""
        try:
            if not ML_AVAILABLE or len(self.packet_history) < 100:
                return
                
            logger.info("Updating machine learning models...")
            
            # Extract features from recent packets
            recent_packets = list(self.packet_history)[-1000:]  # Last 1000 packets
            features = self._extract_features(recent_packets)
            
            # Prepare feature matrix
            feature_matrix = []
            for i in range(len(recent_packets)):
                packet_features = {key: values[i] if i < len(values) else 0.0 
                                 for key, values in features.items()}
                feature_vector = self._prepare_feature_vector(packet_features)
                if feature_vector:
                    feature_matrix.append(feature_vector)
                    
            if len(feature_matrix) < 50:
                return
                
            # Update feature scaler
            if self.feature_scaler is None:
                self.feature_scaler = StandardScaler()
                
            feature_matrix = np.array(feature_matrix)
            self.feature_scaler.fit(feature_matrix)
            scaled_features = self.feature_scaler.transform(feature_matrix)
            
            # Update Isolation Forest
            if self.isolation_forest:
                self.isolation_forest.fit(scaled_features)
                
            # Update DBSCAN
            if self.dbscan_model:
                self.dbscan_model.fit(scaled_features)
                
            # Save updated models
            self._save_models()
            
            self.detection_stats['last_model_update'] = datetime.now()
            
            logger.info("Machine learning models updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating models: {e}")
            
    async def _profile_update_loop(self):
        """Background profile update loop"""
        try:
            while self.running:
                await asyncio.sleep(self.profile_update_interval)
                
                if not self.running:
                    break
                    
                # Update network profiles
                await self._update_profiles()
                
        except Exception as e:
            logger.error(f"Error in profile update loop: {e}")
            
    async def _update_profiles(self):
        """Update network profiles with recent data"""
        try:
            logger.info("Updating network profiles...")
            
            # Group recent packets by profile
            recent_packets = list(self.packet_history)[-500:]  # Last 500 packets
            profile_packets = defaultdict(list)
            
            for packet in recent_packets:
                profile_key = f"{packet.src_ip}_{packet.dst_ip}"
                profile_packets[profile_key].append(packet)
                
            # Update each profile
            for profile_key, packets in profile_packets.items():
                if profile_key in self.network_profiles:
                    profile = self.network_profiles[profile_key]
                    self._update_single_profile(profile, packets)
                    
            # Save updated profiles
            self._save_profiles()
            
            logger.info(f"Updated {len(profile_packets)} network profiles")
            
        except Exception as e:
            logger.error(f"Error updating profiles: {e}")
            
    def _update_single_profile(self, profile: NetworkProfile, packets: List[PacketMetadata]):
        """Update a single network profile"""
        try:
            # Update packet size statistics
            sizes = [p.packet_size for p in packets]
            if sizes:
                # Exponential moving average
                alpha = self.learning_rate
                new_avg_size = np.mean(sizes)
                profile.avg_packet_size = (1 - alpha) * profile.avg_packet_size + alpha * new_avg_size
                
            # Update port usage
            new_ports = [p.dst_port for p in packets if p.dst_port]
            if new_ports:
                for port in new_ports:
                    if port not in profile.typical_ports:
                        profile.typical_ports.append(port)
                        
                # Limit port list size
                if len(profile.typical_ports) > 20:
                    profile.typical_ports = profile.typical_ports[-20:]
                    
            # Update protocol usage
            new_protocols = [p.protocol for p in packets]
            if new_protocols:
                for protocol in new_protocols:
                    if protocol not in profile.typical_protocols:
                        profile.typical_protocols.append(protocol)
                        
            # Update active hours
            new_hours = [p.timestamp.hour for p in packets]
            if new_hours:
                for hour in new_hours:
                    if hour not in profile.active_hours:
                        profile.active_hours.append(hour)
                        
            # Update timestamp
            profile.last_updated = datetime.now()
            
        except Exception as e:
            logger.error(f"Error updating single profile: {e}")
            
    async def _generate_detection_report(self):
        """Generate detection performance report"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = Path(f"network_security/reports/detection_report_{timestamp}.json")
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'detection_stats': self.detection_stats,
                'active_profiles': len(self.network_profiles),
                'packet_history_size': len(self.packet_history),
                'anomaly_history_size': len(self.anomaly_history),
                'detection_methods': [method.value for method in self.detection_methods],
                'model_status': {
                    'isolation_forest': self.isolation_forest is not None,
                    'dbscan_model': self.dbscan_model is not None,
                    'random_forest': self.random_forest is not None,
                    'feature_scaler': self.feature_scaler is not None
                }
            }
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
                
            logger.info(f"Detection report generated: {report_file}")
            
        except Exception as e:
            logger.error(f"Error generating detection report: {e}")
            
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get current detection statistics"""
        return {
            **self.detection_stats,
            'active_profiles': len(self.network_profiles),
            'packet_history_size': len(self.packet_history),
            'anomaly_history_size': len(self.anomaly_history),
            'detection_methods': [method.value for method in self.detection_methods],
            'running': self.running
        }
        
    def get_network_profiles(self) -> List[Dict[str, Any]]:
        """Get network profiles"""
        return [profile.to_dict() for profile in self.network_profiles.values()]
        
    def export_detection_data(self, output_file: str) -> Dict[str, Any]:
        """Export detection data"""
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'detection_stats': self.detection_stats,
                'network_profiles': self.get_network_profiles(),
                'recent_packets': [
                    {
                        'timestamp': p.timestamp.isoformat(),
                        'src_ip': p.src_ip,
                        'dst_ip': p.dst_ip,
                        'protocol': p.protocol,
                        'packet_size': p.packet_size
                    }
                    for p in list(self.packet_history)[-100:]
                ]
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            return {
                'success': True,
                'output_file': output_file,
                'profiles_exported': len(self.network_profiles),
                'packets_exported': len(list(self.packet_history)[-100:])
            }
            
        except Exception as e:
            logger.error(f"Error exporting detection data: {e}")
            return {
                'success': False,
                'error': str(e)
            } 
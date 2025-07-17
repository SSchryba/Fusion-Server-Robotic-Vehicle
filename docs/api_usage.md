# Fusion-Hybrid-V1 API Usage Guide

## Endpoints

---

### 1. `/fusion/respond` (POST)
- **Description:** Get a fused response from the hybrid model ensemble.
- **Parameters:**
  - `prompt` (str, required): The user prompt.
  - `model` (str, optional): Model name (default: fusion-hybrid-v1).
- **Sample Input:**
```json
{
  "prompt": "Explain quantum entanglement.",
  "model": "fusion-hybrid-v1"
}
```
- **Sample Output:**
```json
{
  "response": "...fused model answer...",
  "models": ["deepseek-coder", "mistral", ...],
  "weights": {"deepseek-coder": 0.4, ...},
  "strategy": "weighted_average",
  "timestamp": "2024-06-01T12:00:00Z",
  "success": true,
  "insight_logs": [ ... ]
}
```
- **Use Case:** Unified, robust AI response.

---

### 2. `/fusion/feedback` (POST)
- **Description:** Submit feedback for RLHF/DPO/KTO alignment and FusionInsight logging.
- **Parameters:**
  - `model` (str, required): Model name.
  - `feedback` (str, required): Feedback text.
  - `rating` (float, optional): User rating.
  - `user` (str, optional): User identifier.
  - `preferred` (bool, optional): Preference flag.
  - `reason` (str, optional): Reason for preference.
- **Sample Input:**
```json
{
  "model": "deepseek-coder",
  "feedback": "Great code generation!",
  "rating": 5,
  "user": "alice",
  "preferred": true,
  "reason": "Accurate and clear."
}
```
- **Sample Output:**
```json
{"status": "feedback logged"}
```
- **Use Case:** Model alignment and improvement.

---

### 3. `/ui/optimize-layout` (POST)
- **Description:** Propose a new UI layout using RL-based EDA optimizer.
- **Parameters:**
  - `widgets` (list of str, required): Widget names.
  - `feedback` (dict, optional): Usability or other feedback.
- **Sample Input:**
```json
{
  "widgets": ["chatHistory", "input-container", "sidebar"],
  "feedback": {"usability": 4}
}
```
- **Sample Output:**
```json
{
  "chatHistory": 0,
  "input-container": 1,
  "sidebar": 2
}
```
- **Use Case:** Adaptive UI layout.

---

### 4. `/fusion/insight-data` (GET)
- **Description:** Get logs from FusionInsight, SelfOptimize, and NAS module for dashboard visualization.
- **Sample Output:**
```json
{
  "fusion_insight": [ ... ],
  "self_optimize": [ ... ],
  "nas": [ ... ]
}
```
- **Use Case:** Real-time monitoring and analytics.

---

### 5. `/fusion/create-hybrid` (POST)
- **Description:** Create a new hybrid model from selected models.
- **Parameters:**
  - `models` (list of str, required): Model names to fuse.
- **Sample Input:**
```json
{
  "models": ["deepseek-coder", "mistral"]
}
```
- **Sample Output:**
```json
{
  "hybrid_name": "hybrid-fusion-v2",
  "success": true
}
```
- **Use Case:** Custom hybrid model creation.

---

### 6. `/fusion/status` (GET)
- **Description:** Get current fusion system status.
- **Sample Output:**
```json
{
  "controller_active": true,
  "cycle_count": 5,
  "last_cycle_time": "2024-06-01T10:00:00Z",
  "fusion_history_count": 5,
  "recent_cycles": [ ... ]
}
```
- **Use Case:** System health and monitoring.

---

### 7. `/fusion/train-hybrid` (POST)
- **Description:** Train a new hybrid model variant using feedback logs and NAS parameters.
- **Parameters:**
  - `feedback_logs` (list, required): Feedback and insight logs.
  - `nas_params` (dict, optional): NAS evolution parameters.
- **Sample Input:**
```json
{
  "feedback_logs": [ ... ],
  "nas_params": { ... }
}
```
- **Sample Output:**
```json
{
  "hybrid_name": "hybrid-fusion-v3",
  "success": true,
  "log": "Model trained and saved as hybrid-fusion-v3.json"
}
```
- **Use Case:** Self-training and evolution.

---

### 8. `/federated/sync` (POST)
- **Description:** Register or update federated node contributions (FedDyn logic).
- **Parameters:**
  - `node_id` (str, required): Node identifier.
  - `gradient_update` (dict, required): Model parameter updates.
- **Sample Input:**
```json
{
  "node_id": "node-2",
  "gradient_update": {"weight1": 0.5, "weight2": 0.7}
}
```
- **Sample Output:**
```json
{"status": "node synced", "aggregate": {"weight1": 0.6, "weight2": 0.8}}
```
- **Use Case:** Federated learning and distributed optimization.

---

## Linking

- [Back to Fusion Chat Interface](/)
- [Fusion Insight Dashboard](/insight-dashboard)

---

*For more details, see the project README or contact the system maintainer.* 
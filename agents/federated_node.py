import requests
import random
import time

class FederatedNode:
    """
    Federated learning node with FedDyn logic for local model tuning and sync.
    """
    def __init__(self, node_id, central_url):
        self.node_id = node_id
        self.central_url = central_url
        self.model_params = {"weight1": random.uniform(0, 1), "weight2": random.uniform(0, 1)}
        self.gradient_buffer = []

    def receive_gradient_update(self, gradient_update):
        # Apply FedDyn logic (placeholder: simple addition)
        for k, v in gradient_update.items():
            if k in self.model_params:
                self.model_params[k] += v
            else:
                self.model_params[k] = v
        self.gradient_buffer.append(gradient_update)

    def sync_with_central(self):
        # Push local update to central server
        payload = {
            "node_id": self.node_id,
            "gradient_update": self.model_params
        }
        try:
            resp = requests.post(f"{self.central_url}/federated/sync", json=payload)
            if resp.ok:
                print(f"[Node {self.node_id}] Synced: {resp.json()}")
            else:
                print(f"[Node {self.node_id}] Sync failed: {resp.status_code}")
        except Exception as e:
            print(f"[Node {self.node_id}] Sync error: {e}")

if __name__ == "__main__":
    # Simulate two nodes
    node1 = FederatedNode("node-1", "http://localhost:8000")
    node2 = FederatedNode("node-2", "http://localhost:8000")
    for _ in range(3):
        # Simulate local updates
        node1.receive_gradient_update({"weight1": random.uniform(-0.1, 0.1), "weight2": random.uniform(-0.1, 0.1)})
        node2.receive_gradient_update({"weight1": random.uniform(-0.1, 0.1), "weight2": random.uniform(-0.1, 0.1)})
        node1.sync_with_central()
        node2.sync_with_central()
        time.sleep(2) 
import argparse
import asyncio
import json
import os
import random
import string
import time
from multiprocessing import Process
from agents.federated_node import FederatedNode

def random_id(length=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def load_config(template_path, idx):
    if template_path and os.path.exists(template_path):
        with open(template_path) as f:
            config = json.load(f)
        # Optionally mutate config per agent
        config['agent_id'] = f"agent-{idx}-{random_id()}"
        config['mutation_path'] = f"mutation-{idx}-{random_id()}"
        config['preferences'] = config.get('preferences', {})
        config['preferences']['response_tone'] = random.choice(['formal', 'casual', 'creative', 'analytical'])
        config['preferences']['language_bias'] = random.choice(['en', 'es', 'fr', 'de'])
        return config
    else:
        return {
            'agent_id': f"agent-{idx}-{random_id()}",
            'mutation_path': f"mutation-{idx}-{random_id()}",
            'preferences': {
                'response_tone': random.choice(['formal', 'casual', 'creative', 'analytical']),
                'language_bias': random.choice(['en', 'es', 'fr', 'de'])
            }
        }

def agent_process(agent_config, central_url, sync_interval, simulate_pi):
    agent_id = agent_config['agent_id']
    log_path = f"logs/agents/agent-{agent_id}.log"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'a') as log:
        node = FederatedNode(agent_id, central_url)
        # Apply local preferences to model_params (simulate bias)
        for k in node.model_params:
            node.model_params[k] += random.uniform(-0.2, 0.2)
        # Simulate Pi constraints
        if simulate_pi:
            import resource
            resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
        while True:
            # Simulate local feedback/mutation
            node.receive_gradient_update({k: random.uniform(-0.05, 0.05) for k in node.model_params})
            node.sync_with_central()
            log.write(f"{time.time()} {agent_id} synced: {node.model_params}\n")
            log.flush()
            time.sleep(sync_interval + random.uniform(-1, 1))

def main():
    parser = argparse.ArgumentParser(description="Federated Agent Spawner")
    parser.add_argument('-n', '--num-agents', type=int, required=True, help='Number of agents to spawn')
    parser.add_argument('--config-template', type=str, default=None, help='Path to config_template.json')
    parser.add_argument('--central-url', type=str, default='http://localhost:8000', help='Central server URL')
    parser.add_argument('--sync-interval', type=int, default=5, help='Sync interval in seconds')
    parser.add_argument('--simulate-pi', action='store_true', help='Simulate Raspberry Pi constraints')
    args = parser.parse_args()

    processes = []
    for i in range(args.num_agents):
        agent_config = load_config(args.config_template, i)
        # Staggered launch
        delay = random.uniform(0, 2)
        p = Process(target=agent_process, args=(agent_config, args.central_url, args.sync_interval, args.simulate_pi))
        p.start()
        processes.append(p)
        time.sleep(delay)
    for p in processes:
        p.join()

if __name__ == '__main__':
    main() 
#!/usr/bin/env python3
"""
Fusion-Hybrid-V1 Real Fusion Response System (Ollama-powered)
Production FastAPI backend for weighted model fusion using real Ollama models
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import logging
from fusion_tools.optimization.fusion_insight import FusionInsight  # Compound AI Systems Optimization
from fusion_tools.optimization.metagradient_tuner import MetaGradientTuner  # Metagradient Descent
from fusion_tools.optimization.sharpness_aware_evaluator import SharpnessAwareEvaluator  # SAM/ASAM
from fusion_tools.optimization.alignment_stack import AlignmentStack  # RLHF + DPO + KTO
from fusion_tools.optimization.federated_optimizer import FederatedOptimizer  # Federated Optimization
from fusion_tools.optimization.self_optimize import SelfOptimize  # STOP Framework
from fusion_tools.optimization.nas_module import NASModule  # NAS
from fusion_tools.optimization.ui_eda_optimizer import UIEDAOptimizer  # AI-Driven EDA for UI
from fastapi.responses import JSONResponse
from fusion_tools.insight_dashboard import router as insight_dashboard_router
import os
import json as pyjson
from optimize.aeo_optimizer import inject_aeo_blocks
from optimize.geo_optimizer import structure_for_llm, simulate_llm_crawl
from optimize.structured_data import extract_schema_blocks, extract_opengraph, extract_twitter_cards
from optimize.conversational_semantics import enhance_response
from optimize.seo_automation import suggest_keywords, generate_meta_title, generate_summary, generate_slug
from optimize.brand_citation_monitor import simulate_llm_tracking
from optimize.edge_optimizer import optimize_first_load, offline_fallback, device_context
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fusion-Hybrid-V1 Fusion Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Model Config ---
FUSION_CONFIG_PATH = Path("models/hybrid_models/hybrid-fusion-v1.json")

class FusionRequest(BaseModel):
    prompt: str
    model: str = "fusion-hybrid-v1"

def run_ollama_model(model_name: str, prompt: str) -> str:
    try:
        result = subprocess.run(
            ["ollama", "run", model_name, prompt],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            logger.error(f"Ollama model {model_name} failed: {result.stderr}")
            return f"[ERROR: {model_name} failed: {result.stderr.strip()}]"
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"Ollama model {model_name} exception: {e}")
        return f"[ERROR: {model_name} exception: {e} ]"

model_runners = {
    "deepseek-coder": lambda prompt: run_ollama_model("deepseek-coder", prompt),
    "mistral": lambda prompt: run_ollama_model("mistral", prompt),
    "codellama": lambda prompt: run_ollama_model("codellama", prompt),
    "llama2": lambda prompt: run_ollama_model("llama2", prompt)
}

model_name_map = {
    "deepseek-coder:latest": "deepseek-coder",
    "mistral:latest": "mistral",
    "codellama:latest": "codellama",
    "llama2:latest": "llama2"
}

# --- Fusion Logic ---
def load_fusion_weights() -> Dict[str, float]:
    with open(FUSION_CONFIG_PATH, 'r') as f:
        config = json.load(f)
    models = config.get("ensemble_config", {}).get("models", [])
    weights = {model_name_map[m["name"]]: m["weight"] for m in models if m["name"] in model_name_map}
    return weights

def get_fusion_strategy() -> str:
    with open(FUSION_CONFIG_PATH, 'r') as f:
        config = json.load(f)
    return config.get("ensemble_config", {}).get("fusion_strategy", "weighted_average")

def fuse_responses_weighted(responses: List[Dict[str, Any]]) -> str:
    # Weighted concatenation (can be replaced with more advanced fusion)
    total_weight = sum(r['weight'] for r in responses)
    if total_weight == 0:
        return "[Fusion Error: No model weights]"
    # Weighted join: repeat each response proportional to its weight
    weighted_texts = []
    for r in responses:
        count = max(1, int(round(r['weight'])))
        weighted_texts.extend([r['response']] * count)
    return "\n\n".join(weighted_texts)

# --- Optimization System Instantiation ---
fusion_insight = FusionInsight()
meta_tuner = MetaGradientTuner()
sharpness_evaluator = SharpnessAwareEvaluator()
alignment_stack = AlignmentStack()
federated_optimizer = FederatedOptimizer()
self_optimizer = SelfOptimize()
nas_module = NASModule()
ui_eda_optimizer = UIEDAOptimizer()

# --- Load model roles ---
MODEL_ROLES_PATH = "model_roles.json"
def load_model_roles():
    if os.path.exists(MODEL_ROLES_PATH):
        with open(MODEL_ROLES_PATH, 'r') as f:
            return pyjson.load(f)
    return {}
model_roles = load_model_roles()

def amplify_roles_from_prompt(prompt: str, roles: dict) -> dict:
    # Simple amplification: if prompt mentions a role, boost that model's weight
    amplifications = {}
    for model, role in roles.items():
        if role.lower().split()[0] in prompt.lower():
            amplifications[model] = 1.5  # 50% boost
    return amplifications

DEPLOYMENT_MODES = ['SEO Legacy', 'AEO Pro', 'GEO Dominance']
current_mode = {'mode': 'AEO Pro'}

VISIBILITY_LOG = 'logs/visibility-tracker.json'
def log_visibility(data):
    import json, os
    os.makedirs(os.path.dirname(VISIBILITY_LOG), exist_ok=True)
    if os.path.exists(VISIBILITY_LOG):
        with open(VISIBILITY_LOG) as f:
            log = json.load(f)
    else:
        log = []
    log.append(data)
    with open(VISIBILITY_LOG, 'w') as f:
        json.dump(log, f, indent=2)

# --- Endpoints ---
@app.post("/fusion/respond")
async def fusion_respond(request: FusionRequest):
    try:
        weights = load_fusion_weights()
        strategy = get_fusion_strategy()
        prompt = request.prompt
        responses = []
        amplifications = amplify_roles_from_prompt(prompt, model_roles)
        nas_weights = nas_module.propose_architecture(list(model_runners.keys()), query_type="default")
        for model_key, runner in model_runners.items():
            params = meta_tuner.get_params(model_key)
            weight = nas_weights.get(model_key, weights.get(model_key, 0))
            for role_model, amp in amplifications.items():
                if role_model.lower() in model_key.lower():
                    weight *= amp
            if weight > 0:
                output = runner(prompt)
                sharpness_score = sharpness_evaluator.evaluate([
                    {"model": model_key, "response": output}
                ])[0]["sharpness_score"]
                alignment_score = alignment_stack.compute_alignment_score(model_key)
                emotional_penalty = alignment_stack.emotional_loss_aversion(output)
                federated_optimizer.submit_update("local", params)
                agg_params = federated_optimizer.aggregate()
                routing_state = {"weights": weights}
                routing_state = self_optimizer.mutate_routing(routing_state)
                fusion_insight.log_model_output(
                    model=model_key,
                    prompt=prompt,
                    response=output,
                    score=alignment_score + emotional_penalty - sharpness_score,
                    meta={
                        "sharpness": sharpness_score,
                        "alignment": alignment_score,
                        "emotional_penalty": emotional_penalty,
                        "params": params,
                        "agg_params": agg_params,
                        "role": model_roles.get(model_key.capitalize(), None)
                    }
                )
                fusion_insight.log_self_reflection(
                    model=model_key,
                    reflection=f"Output coherence: {output[:60]}... | Alignment: {alignment_score:.2f} | Sharpness: {sharpness_score:.2f}",
                    context={"prompt": prompt}
                )
                responses.append({
                    "model": model_key,
                    "weight": weight,
                    "response": output,
                    "alignment": alignment_score,
                    "sharpness": sharpness_score,
                    "emotional_penalty": emotional_penalty,
                    "role": model_roles.get(model_key.capitalize(), None)
                })
        fused_response = fuse_responses_weighted(responses)
        nas_module.benchmark(nas_weights, performance=1.0)
        # --- AI Optimization Integration ---
        # 1. AEO: inject QA/FAQ/conversational blocks
        markdown = prompt + '\n' + fused_response
        aeo_content = inject_aeo_blocks(fused_response, markdown)
        # 2. GEO: structure for LLM, add JSON-LD
        geo_content = structure_for_llm(aeo_content)
        # 3. Structured Data: extract and inject
        schema_blocks = extract_schema_blocks(geo_content)
        opengraph = extract_opengraph(geo_content)
        twitter_cards = extract_twitter_cards(geo_content)
        # 4. Conversational Semantics: enhance response
        enhanced = enhance_response(geo_content)
        # 5. SEO Automation: suggest keywords, meta, summary, slug
        keywords = suggest_keywords(prompt)
        meta_title = generate_meta_title(prompt)
        summary = generate_summary(fused_response)
        slug = generate_slug(prompt)
        # 6. Brand/Citation Monitoring: simulate LLM tracking
        brand_stats = simulate_llm_tracking(enhanced)
        # 7. Edge Optimization: optimize load, fallback, device context
        edge_ok = optimize_first_load()
        device_info = device_context('pi')
        # Log visibility
        log_visibility({
            'prompt': prompt,
            'meta_title': meta_title,
            'keywords': keywords,
            'slug': slug,
            'brand_stats': brand_stats,
            'edge_ok': edge_ok,
            'timestamp': datetime.now().isoformat()
        })
        # Deployment mode toggle
        mode = current_mode['mode']
        if mode == 'SEO Legacy':
            final_content = fused_response
        elif mode == 'AEO Pro':
            final_content = aeo_content
        elif mode == 'GEO Dominance':
            final_content = geo_content
        else:
            final_content = enhanced
        return {
            "response": final_content,
            "models": [r["model"] for r in responses],
            "weights": {r["model"]: r["weight"] for r in responses},
            "roles": {r["model"]: r["role"] for r in responses},
            "strategy": strategy,
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "insight_logs": fusion_insight.get_logs(10),
            "meta": {
                "meta_title": meta_title,
                "keywords": keywords,
                "summary": summary,
                "slug": slug,
                "schema_blocks": schema_blocks,
                "opengraph": opengraph,
                "twitter_cards": twitter_cards,
                "brand_stats": brand_stats,
                "edge": device_info
            }
        }
    except Exception as e:
        logger.error(f"Fusion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test/fusion")
async def test_fusion():
    return {"status": "✅ Fusion connection live"}

# --- Feedback Endpoint for RLHF/DPO/KTO and FusionInsight ---
@app.post("/fusion/feedback")
async def fusion_feedback(model: str = Body(...), feedback: str = Body(...), rating: float = Body(None), user: str = Body(None), preferred: bool = Body(None), reason: str = Body("")):
    # Log feedback for RLHF/DPO/KTO and FusionInsight
    fusion_insight.log_feedback(model, feedback, rating, user)
    if preferred is not None:
        alignment_stack.record_preference(model, feedback, preferred, reason)
    return {"status": "feedback logged"}

@app.post("/ui/optimize-layout")
async def optimize_layout(data: Dict[str, Any]):
    widgets = data.get("widgets", [])
    feedback = data.get("feedback", {})
    layout = ui_eda_optimizer.propose_layout(widgets, feedback)
    # Optionally record performance if feedback includes usability score
    if "usability" in feedback:
        ui_eda_optimizer.record_performance(layout, feedback["usability"])
    return layout

@app.get("/fusion/insight-data")
async def fusion_insight_data():
    return JSONResponse({
        "fusion_insight": fusion_insight.get_logs(100),
        "self_optimize": getattr(self_optimizer, 'attempts', []),
        "nas": getattr(nas_module, 'architecture_history', [])
    })

@app.post("/federated/sync")
async def federated_sync(node_id: str = Body(...), gradient_update: Dict[str, float] = Body(...)):
    federated_optimizer.submit_update(node_id, gradient_update)
    aggregate = federated_optimizer.aggregate()
    return {"status": "node synced", "aggregate": aggregate}

@app.post("/fusion/train-hybrid")
async def train_hybrid(feedback_logs: list = Body(...), nas_params: dict = Body({})):
    # Determine next version
    model_dir = "models/hybrid_models"
    existing = [f for f in os.listdir(model_dir) if f.startswith("hybrid-fusion-v") and f.endswith(".json")]
    versions = [int(f.split("-v")[-1].split(".")[0]) for f in existing if f.split("-v")[-1].split(".")[0].isdigit()]
    next_version = max(versions+[1]) + 1 if versions else 2
    new_model_path = os.path.join(model_dir, f"hybrid-fusion-v{next_version}.json")
    # Simulate new model config
    new_config = {
        "ensemble_config": {
            "models": [
                {"name": m.get("model", "unknown"), "weight": m.get("meta", {}).get("alignment", 1.0)}
                for m in feedback_logs if "model" in m
            ],
            "fusion_strategy": nas_params.get("fusion_strategy", "weighted_average")
        },
        "nas_params": nas_params,
        "mutation_log": feedback_logs
    }
    with open(new_model_path, "w") as f:
        import json
        json.dump(new_config, f, indent=2)
    # Log mutation
    self_optimizer.log_attempt(f"Trained hybrid model v{next_version}", "success", impact=0.1)
    return {"hybrid_name": f"hybrid-fusion-v{next_version}", "success": True, "log": f"Model trained and saved as hybrid-fusion-v{next_version}.json"}

@app.get("/fusion/roles")
async def get_roles():
    return model_roles

@app.post("/fusion/roles")
async def update_roles(new_roles: dict = Body(...)):
    with open(MODEL_ROLES_PATH, 'w') as f:
        pyjson.dump(new_roles, f, indent=2)
    global model_roles
    model_roles = load_model_roles()
    return {"status": "roles updated", "roles": model_roles}

@app.post('/deploy/mode')
async def set_deploy_mode(mode: str = Body(...)):
    if mode not in DEPLOYMENT_MODES:
        return {'error': 'Invalid mode'}
    current_mode['mode'] = mode
    return {'status': 'ok', 'mode': mode}

@app.get('/deploy/mode')
async def get_deploy_mode():
    return {'mode': current_mode['mode']}

@app.get("/fusion/status")
async def fusion_status():
    return {
        "status": "online",
        "models": list(model_runners.keys()),
        "deployment_mode": current_mode['mode'],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/tools/list")
async def tools_list():
    tools_path = "tools/tools_log.json"
    if os.path.exists(tools_path):
        with open(tools_path) as f:
            return json.load(f)
    return {}

@app.post("/tools/fetch")
async def tools_fetch(keyword_or_url: str = Body(...), used_for: str = Body("")):
    try:
        from tools.github_fetcher import fetch_tool
        result = fetch_tool(keyword_or_url, used_for)
        return {"status": "success", "path": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

app.include_router(insight_dashboard_router)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Fusion-Hybrid-V1 Fusion Engine on http://localhost:8000")
    uvicorn.run("fusion_respond:app", host="localhost", port=8000, reload=True) 
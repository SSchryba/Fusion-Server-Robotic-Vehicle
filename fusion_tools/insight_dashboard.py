from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/insight-dashboard", response_class=HTMLResponse)
async def insight_dashboard(request: Request):
    # Serve a simple HTML dashboard with Chart.js and fetches /fusion/insight-data
    return HTMLResponse(
        '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Fusion Insight Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f7f7fa; }
                .dashboard-container { max-width: 1200px; margin: 0 auto; padding: 32px; }
                h1 { margin-bottom: 24px; }
                .chart-block { background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #0001; margin-bottom: 32px; padding: 24px; }
                .log-block { background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #0001; margin-bottom: 32px; padding: 24px; max-height: 300px; overflow-y: auto; }
            </style>
        </head>
        <body>
            <div class="dashboard-container">
                <h1>🔍 Fusion Insight Dashboard</h1>
                <div class="chart-block">
                    <h2>Model Fusion Weights Over Time</h2>
                    <canvas id="weightsChart" height="120"></canvas>
                </div>
                <div class="chart-block">
                    <h2>Self-Optimization Cycles</h2>
                    <canvas id="selfOptChart" height="120"></canvas>
                </div>
                <div class="chart-block">
                    <h2>User Feedback Trends</h2>
                    <canvas id="feedbackChart" height="120"></canvas>
                </div>
                <div class="log-block">
                    <h2>FusionInsight Logs</h2>
                    <pre id="fusionInsightLog"></pre>
                </div>
                <div class="log-block">
                    <h2>SelfOptimize Logs</h2>
                    <pre id="selfOptimizeLog"></pre>
                </div>
                <div class="log-block">
                    <h2>NAS Module History</h2>
                    <pre id="nasLog"></pre>
                </div>
            </div>
            <script>
            async function fetchInsightData() {
                const res = await fetch('/fusion/insight-data');
                return await res.json();
            }
            function renderLogs(logs, el) {
                el.textContent = JSON.stringify(logs, null, 2);
            }
            function renderWeightsChart(logs) {
                const ctx = document.getElementById('weightsChart').getContext('2d');
                const labels = logs.map(l => l.timestamp || '');
                const models = {};
                logs.forEach(l => {
                    if (l.meta && l.meta.agg_params) {
                        Object.entries(l.meta.agg_params).forEach(([k, v]) => {
                            if (!models[k]) models[k] = [];
                            models[k].push(v);
                        });
                    }
                });
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels,
                        datasets: Object.entries(models).map(([model, data], i) => ({
                            label: model,
                            data,
                            borderColor: `hsl(${i*60},70%,50%)`,
                            fill: false
                        }))
                    },
                    options: { responsive: true, plugins: { legend: { position: 'top' } } }
                });
            }
            function renderSelfOptChart(logs) {
                const ctx = document.getElementById('selfOptChart').getContext('2d');
                const labels = logs.map(l => l.timestamp || '');
                const impacts = logs.map(l => l.impact || 0);
                new Chart(ctx, {
                    type: 'bar',
                    data: { labels, datasets: [{ label: 'Impact', data: impacts, backgroundColor: '#4caf50' }] },
                    options: { responsive: true, plugins: { legend: { display: false } } }
                });
            }
            function renderFeedbackChart(logs) {
                const ctx = document.getElementById('feedbackChart').getContext('2d');
                const labels = logs.map(l => l.timestamp || '');
                const ratings = logs.map(l => l.rating || 0);
                new Chart(ctx, {
                    type: 'line',
                    data: { labels, datasets: [{ label: 'User Rating', data: ratings, borderColor: '#2196f3', fill: false }] },
                    options: { responsive: true, plugins: { legend: { display: false } } }
                });
            }
            async function main() {
                const data = await fetchInsightData();
                renderLogs(data.fusion_insight, document.getElementById('fusionInsightLog'));
                renderLogs(data.self_optimize, document.getElementById('selfOptimizeLog'));
                renderLogs(data.nas, document.getElementById('nasLog'));
                renderWeightsChart(data.fusion_insight);
                renderSelfOptChart(data.self_optimize);
                renderFeedbackChart(data.fusion_insight.filter(l => l.rating !== undefined));
            }
            main();
            </script>
        </body>
        </html>
        '''
    ) 
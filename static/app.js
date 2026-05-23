document.addEventListener("DOMContentLoaded", () => {
    let allRuns = [];
    let activeRunId = null;

    // DOM Cache
    const runBtn = document.getElementById("runBtn");
    const historyList = document.getElementById("historyList");
    const runTitle = document.getElementById("runTitle");
    const runTimestamp = document.getElementById("runTimestamp");
    const terminalContainer = document.getElementById("terminalContainer");
    const terminalLog = document.getElementById("terminalLog");
    const closeTerminalBtn = document.getElementById("closeTerminalBtn");

    const metricAlerts = document.getElementById("metricAlerts");
    const metricRate = document.getElementById("metricRate");
    const metricTotal = document.getElementById("metricTotal");
    const metricModel = document.getElementById("metricModel");
    const metricExplainer = document.getElementById("metricExplainer");
    const alertsGrid = document.getElementById("alertsGrid");

    // Load history on startup
    fetchHistory();

    // Event listener for run trigger button
    runBtn.addEventListener("click", () => {
        // Clear and show terminal log
        terminalContainer.classList.remove("hidden");
        terminalLog.innerHTML = "";
        runBtn.disabled = true;
        runBtn.classList.add("running");

        // Set up EventSource for Server-Sent Events (SSE) log streaming
        const eventSource = new EventSource("/api/run/stream");
        
        eventSource.onmessage = (event) => {
            const line = event.data;
            const logLine = document.createElement("div");
            logLine.textContent = line;
            
            // Apply log-level styling
            if (line.includes("Error:") || line.includes("Traceback") || line.includes("ValueError")) {
                logLine.style.color = "#f43f5e";
            } else if (line.includes("[SERVER]") || line.includes("=== Pipeline")) {
                logLine.style.color = "#a855f7";
            } else if (line.includes("Execution completed successfully")) {
                logLine.style.color = "#10b981";
            }
            
            terminalLog.appendChild(logLine);
            terminalLog.scrollTop = terminalLog.scrollHeight;

            // Check if process finished
            if (line.includes("Pipeline execution completed")) {
                eventSource.close();
                runBtn.disabled = false;
                runBtn.classList.remove("running");
                // Fetch fresh history and reload dashboard
                fetchHistory();
            }
        };

        eventSource.onerror = (err) => {
            console.error("SSE stream error:", err);
            eventSource.close();
            runBtn.disabled = false;
            runBtn.classList.remove("running");
        };
    });

    closeTerminalBtn.addEventListener("click", () => {
        terminalContainer.classList.add("hidden");
    });

    function fetchHistory() {
        fetch("/api/exports")
            .then(res => res.json())
            .then(data => {
                allRuns = data;
                renderHistoryList();
                if (allRuns.length > 0) {
                    // Select first (newest) run
                    selectRun(allRuns[0].id);
                }
            })
            .catch(err => {
                console.error("Failed to load exports history:", err);
                historyList.innerHTML = `<li class="loading-item text-red">Error loading history</li>`;
            });
    }

    function renderHistoryList() {
        historyList.innerHTML = "";
        if (allRuns.length === 0) {
            historyList.innerHTML = `<li class="loading-item">No runs exported yet.</li>`;
            return;
        }

        allRuns.forEach(run => {
            const item = document.createElement("li");
            item.className = `history-item ${run.id === activeRunId ? 'active' : ''}`;
            
            // Format ID for clean display
            let title = run.id === "latest" ? "Latest Run" : run.id.replace("anomaly_alerts_", "");
            const dateStr = run.metadata.timestamp 
                ? formatTimestamp(run.metadata.timestamp)
                : "Unknown time";
            
            const flagged = run.metadata.metrics?.anomalies_flagged ?? 0;
            const total = run.metadata.metrics?.total_records_evaluated ?? 0;
            
            item.innerHTML = `
                <div class="run-name">${title}</div>
                <div class="run-meta">
                    <span>${dateStr}</span>
                    <span class="text-red">${flagged}/${total} alerts</span>
                </div>
            `;
            
            item.addEventListener("click", () => selectRun(run.id));
            historyList.appendChild(item);
        });
    }

    function selectRun(runId) {
        activeRunId = runId;
        
        // Highlight in history sidebar
        document.querySelectorAll(".history-item").forEach((el, idx) => {
            const r = allRuns[idx];
            if (r && r.id === runId) {
                el.classList.add("active");
            } else {
                el.classList.remove("active");
            }
        });

        const run = allRuns.find(r => r.id === runId);
        if (!run) return;

        // Render header and timestamp
        let displayTitle = run.id === "latest" ? "Latest Run" : run.id.replace("anomaly_alerts_", "Run: ");
        runTitle.textContent = displayTitle;
        runTimestamp.textContent = run.metadata.timestamp 
            ? formatTimestamp(run.metadata.timestamp) 
            : "-";

        // Update stats metrics
        const flagged = run.metadata.metrics?.anomalies_flagged ?? 0;
        const total = run.metadata.metrics?.total_records_evaluated ?? 0;
        const rate = total > 0 ? ((flagged / total) * 100).toFixed(2) : "0.00";

        metricAlerts.textContent = flagged;
        metricRate.textContent = `${rate}% alert rate`;
        metricTotal.textContent = total;
        metricModel.textContent = run.metadata.components?.model_agent ?? "-";
        metricExplainer.textContent = run.metadata.components?.explainer ?? "-";

        // Render anomaly alerts cards
        renderAnomalyCards(run.anomalies);
    }

    function renderAnomalyCards(anomalies) {
        alertsGrid.innerHTML = "";
        
        if (!anomalies || anomalies.length === 0) {
            alertsGrid.innerHTML = `
                <div class="empty-state">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    <p>No anomalies flagged in this run.</p>
                </div>
            `;
            return;
        }

        anomalies.forEach((row, idx) => {
            const card = document.createElement("article");
            card.className = "anomaly-card";

            // Parse formatted strings
            const contributions = parseContributors(row.TOP_SHAP_CONTRIBUTORS);
            const counterfactuals = parseCounterfactuals(row.COUNTERFACTUAL);
            const interactions = parseInteractions(row.TOP_INTERACTIONS);

            // Amount formatting
            const amt = parseFloat(row.TRANS_AMOUNT ?? 0.0);
            const formattedAmt = isNaN(amt) ? "0.00" : amt.toLocaleString('en-US', { minimumFractionDigits: 2 });
            const avgAmt = parseFloat(row.HIST_AVG_TRANS_AMOUNT ?? 0.0);
            const formattedAvgAmt = isNaN(avgAmt) ? "0.00" : avgAmt.toLocaleString('en-US', { minimumFractionDigits: 2 });

            const customerId = row.CUSTOMER_NUMBER ?? "Unknown";
            const score = parseFloat(row.ANOMALY_SCORE ?? 0.0).toFixed(4);

            card.innerHTML = `
                <!-- Header row -->
                <div class="card-header-row">
                    <div>
                        <span class="card-badge">Alert #${idx + 1}</span>
                        <span style="font-size: 13px; color: var(--color-text-muted); margin-left: 10px;">Score: ${score}</span>
                    </div>
                    <div class="card-amount-area">
                        <div class="card-amount">${formattedAmt}</div>
                        <div class="card-customer">Cust ID: ${customerId} | Avg: ${formattedAvgAmt}</div>
                    </div>
                </div>

                <!-- Explanation Rationale -->
                <div class="card-explanation">
                    ${row.EXPLANATION || "No explanation provided."}
                </div>

                <!-- Contribution bars -->
                ${contributions.length > 0 ? `
                <div class="contributions-container">
                    <h4>Top SHAP Drivers</h4>
                    <div class="contrib-bars-list">
                        ${contributions.map(c => renderContributionBar(c)).join("")}
                    </div>
                </div>
                ` : ""}

                <!-- Interactions list -->
                ${interactions.length > 0 ? `
                <div class="interactions-container">
                    <h4>Toxic Feature Interactions</h4>
                    <div class="interactions-list">
                        ${interactions.map(inter => `
                            <div class="interaction-item">
                                <span>${inter.pair}</span>
                                <span class="interaction-val">${inter.val > 0 ? '+' : ''}${inter.val.toFixed(4)}</span>
                            </div>
                        `).join("")}
                    </div>
                </div>
                ` : ""}

                <!-- Recourse counterfactuals -->
                ${counterfactuals.length > 0 ? `
                <div class="recourse-container">
                    <h4>Actionable Recourse counterfactuals</h4>
                    <div class="recourse-list">
                        ${counterfactuals.map(cf => `
                            <div class="recourse-item">
                                <span>Modify ${cf.feature}:</span>
                                <span class="recourse-val">${cf.origVal} &rarr; <strong class="text-green">${cf.safeVal}</strong> (delta: ${cf.delta > 0 ? '+' : ''}${cf.delta})</span>
                            </div>
                        `).join("")}
                    </div>
                </div>
                ` : ""}
            `;

            alertsGrid.appendChild(card);
        });
    }

    function renderContributionBar(c) {
        // Find max contribution to scale widths (use absolute limit of 2.0 log-odds or scale dynamically)
        const valAbs = Math.abs(c.val);
        const widthPct = Math.min((valAbs / 1.5) * 100, 100).toFixed(0);
        const directionClass = c.val > 0 ? "positive" : "negative";
        const sign = c.val > 0 ? "+" : "";

        return `
            <div class="contrib-bar-item">
                <div class="contrib-bar-label">
                    <span>${c.feature}</span>
                    <span class="feat-val">${sign}${c.val.toFixed(4)}</span>
                </div>
                <div class="bar-track">
                    <div class="bar-fill ${directionClass}" style="width: ${widthPct}%"></div>
                </div>
            </div>
        `;
    }

    // Helper parsers for export strings
    function parseContributors(contString) {
        if (!contString) return [];
        // Pattern: feature_name (+0.1234) or feature_name (-0.0567)
        const items = contString.split(",");
        const parsed = [];
        items.forEach(item => {
            const match = item.trim().match(/^(.+?)\s*\(\s*([+-]?\d+\.?\d*)\s*\)$/);
            if (match) {
                parsed.push({
                    feature: match[1],
                    val: parseFloat(match[2])
                });
            }
        });
        return parsed;
    }

    function parseCounterfactuals(cfString) {
        if (!cfString) return [];
        // Pattern: feature: orig -> safe (delta)
        // Example: SUM_AMOUNT_24H: 148,743,580.00 → 136,730,906.39 (-12,012,673.61)
        const items = cfString.split(",");
        const parsed = [];
        items.forEach(item => {
            const parts = item.trim().split(":");
            if (parts.length < 2) return;
            const feat = parts[0].trim();
            const flow = parts[1].trim();
            
            const match = flow.match(/^(.+?)\s*[→&rarr;]\s*(.+?)\s*\(\s*([+-]?\d+[\d,.]*)\s*\)$/);
            if (match) {
                parsed.push({
                    feature: feat,
                    origVal: match[1].trim(),
                    safeVal: match[2].trim(),
                    delta: parseFloat(match[3].replace(/,/g, ''))
                });
            }
        });
        return parsed;
    }

    function parseInteractions(interString) {
        if (!interString) return [];
        // Pattern: feat_a x feat_b (+0.1234)
        const items = interString.split(",");
        const parsed = [];
        items.forEach(item => {
            const match = item.trim().match(/^(.+?)\s*\(\s*([+-]?\d+\.?\d*)\s*\)$/);
            if (match) {
                parsed.push({
                    pair: match[1].trim(),
                    val: parseFloat(match[2])
                });
            }
        });
        return parsed;
    }

    function formatTimestamp(ts) {
        // timestamp pattern YYYYMMDD_HHMMSS
        if (ts.length < 15) return ts;
        const year = ts.slice(0, 4);
        const month = ts.slice(4, 6);
        const day = ts.slice(6, 8);
        const hour = ts.slice(9, 11);
        const min = ts.slice(11, 13);
        const sec = ts.slice(13, 15);
        return `${year}-${month}-${day} ${hour}:${min}:${sec}`;
    }
});

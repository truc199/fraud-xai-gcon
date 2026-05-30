document.addEventListener('DOMContentLoaded', () => {
    loadPatterns();
});

async function loadPatterns() {
    const patternsGrid = document.getElementById('patternsGrid');
    
    // Check if user is opening static file directly in browser via file://
    if (window.location.protocol === 'file:') {
        patternsGrid.innerHTML = `
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                <p><strong>CORS Restriction:</strong> You opened the HTML file directly in the browser via <code>file://</code>.</p>
                <p style="font-size:13px;color:var(--color-text-muted)">Please start the server first and navigate to:<br><a href="http://127.0.0.1:8000/patterns" target="_blank" style="color:var(--color-accent-blue);text-decoration:underline;">http://127.0.0.1:8000/patterns</a></p>
            </div>
        `;
        return;
    }

    try {
        const response = await fetch('/api/shap_patterns');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        if (!data || data.patterns.length === 0) {
            patternsGrid.innerHTML = `
                <div class="empty-state">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    <p>No patterns found. Please trigger a pipeline execution first.</p>
                </div>
            `;
            return;
        }

        // Update Summary Metrics
        document.getElementById('totalPatterns').textContent = data.summary.total_distinct_patterns.toLocaleString();
        document.getElementById('totalAlerts').textContent = data.summary.total_alerts.toLocaleString();
        
        const topPattern = data.patterns[0];
        document.getElementById('topPatternName').textContent = formatPatternName(topPattern.pattern);
        document.getElementById('topPatternSub').textContent = `${topPattern.count.toLocaleString()} alerts (${topPattern.percentage.toFixed(1)}%)`;
        document.getElementById('topCoverage').textContent = `${data.summary.top_5_coverage_pct.toFixed(1)}%`;

        // Render Cards
        patternsGrid.innerHTML = '';
        data.patterns.forEach((pat, index) => {
            const card = document.createElement('div');
            card.className = 'pattern-card glass';
            
            // Format features list for badges
            const features = pat.pattern.split(',').map(f => f.trim()).filter(Boolean);
            const featureBadgesHtml = features.map((feat, i) => `
                <span class="feat-badge index-${i}">
                    <span class="badge-idx">${i + 1}</span>
                    <span class="badge-name">${feat}</span>
                </span>
            `).join('');

            // Format monetary value
            let amountStr = 'N/A';
            if (pat.sample_transaction.amount) {
                const amt = parseFloat(pat.sample_transaction.amount);
                amountStr = isNaN(amt) ? pat.sample_transaction.amount : amt.toLocaleString() + ' VND';
            }

            card.innerHTML = `
                <div class="pattern-card-header">
                    <div class="rank-badge">#${index + 1}</div>
                    <div class="pattern-stats">
                        <div class="stat-item">
                            <span class="stat-lbl">Alert Count</span>
                            <span class="stat-val text-red">${pat.count.toLocaleString()}</span>
                            <span class="stat-pct">(${pat.percentage.toFixed(1)}%)</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-lbl">Avg Score</span>
                            <span class="stat-val text-blue">${pat.avg_anomaly_score.toFixed(4)}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-lbl">Score Range</span>
                            <span class="stat-val-sm">${pat.min_score.toFixed(2)} - ${pat.max_score.toFixed(2)}</span>
                        </div>
                    </div>
                </div>

                <div class="pattern-features-row">
                    ${featureBadgesHtml || '<span class="feat-badge muted">No SHAP contributors</span>'}
                </div>

                <div class="pattern-narrative">
                    <div class="narrative-title">Representative Explanation Narrative</div>
                    <p class="narrative-text">"${pat.sample_transaction.explanation || 'No explanation narrative generated.'}"</p>
                </div>

                <div class="pattern-sample-details">
                    <div class="sample-title">Example Alert Target Info</div>
                    <div class="sample-grid">
                        <div class="sample-cell">
                            <span class="cell-lbl">Tx ID</span>
                            <span class="cell-val font-mono">${pat.sample_transaction.transaction_id || 'N/A'}</span>
                        </div>
                        <div class="sample-cell">
                            <span class="cell-lbl">Cust No</span>
                            <span class="cell-val font-mono">${pat.sample_transaction.customer_number || 'N/A'}</span>
                        </div>
                        <div class="sample-cell">
                            <span class="cell-lbl">Amount</span>
                            <span class="cell-val amount">${amountStr}</span>
                        </div>
                        <div class="sample-cell">
                            <span class="cell-lbl">Tx Type</span>
                            <span class="cell-val">${pat.sample_transaction.type || 'N/A'}</span>
                        </div>
                    </div>
                </div>
            `;
            patternsGrid.appendChild(card);
        });

    } catch (error) {
        console.error('Error fetching SHAP patterns:', error);
        patternsGrid.innerHTML = `
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                <p>Failed to load SHAP patterns. Please ensure the latest run files exist in the data/ folder.</p>
            </div>
        `;
    }
}

function formatPatternName(patternStr) {
    if (!patternStr) return 'Unknown Pattern';
    const firstFeat = patternStr.split(',')[0].trim();
    // Return first feature with an ellipsis if there are more
    return patternStr.includes(',') ? `${firstFeat} + others` : firstFeat;
}

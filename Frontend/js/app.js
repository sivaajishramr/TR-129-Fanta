/**
 * App Module - Main application controller
 * AccessAudit AI — Trichy Public Transport Accessibility Auditor
 */

// Global data store
let appData = {
    stops: null,
    grievances: null,
    report: null,
    summary: null
};

// ===== TAB SWITCHING =====
function switchTab(tabId) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Deactivate all nav buttons
    document.querySelectorAll('.nav-tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    const targetTab = document.getElementById(`tab-${tabId}`);
    if (targetTab) targetTab.classList.add('active');
    
    // Activate nav button
    const activeBtn = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
    if (activeBtn) activeBtn.classList.add('active');
    
    // Special handling for map tab - need to refresh
    if (tabId === 'map') {
        refreshMap();
    }
    
    // Load report data on report tab
    if (tabId === 'report' && !appData.report) {
        loadReportData();
    }
}

// ===== DASHBOARD UPDATES =====
function updateSummaryCards(summary) {
    animateNumber('stat-critical', summary.critical_count);
    animateNumber('stat-warning', summary.warning_count);
    animateNumber('stat-good', summary.good_count);
    
    const avgEl = document.getElementById('stat-avg-gap');
    if (avgEl) avgEl.textContent = summary.average_gap_score + '%';
    
    // Header stats
    const coverageEl = document.querySelector('#header-coverage .stat-value');
    if (coverageEl) coverageEl.textContent = summary.coverage_percent + '%';
    
    const stopsEl = document.querySelector('#header-stops .stat-value');
    if (stopsEl) stopsEl.textContent = summary.total_stops;
    
    const grievancesEl = document.querySelector('#header-grievances .stat-value');
    if (grievancesEl) grievancesEl.textContent = summary.total_grievances;
}

function animateNumber(elementId, target) {
    const el = document.getElementById(elementId);
    if (!el) return;
    
    let current = 0;
    const increment = Math.ceil(target / 20);
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        el.textContent = current;
    }, 40);
}

// ===== PRIORITY TABLE =====
function buildPriorityTable(stops) {
    const tbody = document.getElementById('priority-table-body');
    if (!tbody) return;
    
    const top10 = stops.slice(0, 10);
    
    tbody.innerHTML = top10.map(stop => {
        const priorityClass = `priority-${stop.priority}`;
        const scoreColor = stop.priority === 'critical' ? '#ef4444' : 
                          stop.priority === 'warning' ? '#eab308' : '#22c55e';
        
        const missingNames = stop.missing_features
            .map(f => f.name)
            .join(', ');
        
        return `
            <tr>
                <td><strong>#${stop.rank}</strong></td>
                <td><strong>${stop.name}</strong></td>
                <td>${stop.type.replace(/_/g, ' ')}</td>
                <td>
                    <div class="score-bar">
                        <span class="${priorityClass}">${stop.gap_score}%</span>
                        <div class="score-bar-bg">
                            <div class="score-bar-fill" style="width: ${stop.gap_score}%; background: ${scoreColor};"></div>
                        </div>
                    </div>
                </td>
                <td>${stop.grievance_count}</td>
                <td>${stop.daily_footfall.toLocaleString()}</td>
                <td><span class="${priorityClass}">${stop.priority_label}</span></td>
                <td style="font-size: 11px; color: var(--text-secondary); max-width: 200px;">${missingNames}</td>
            </tr>
        `;
    }).join('');
}

// ===== STOPS TABLE =====
function buildStopsTable(stops) {
    const tbody = document.getElementById('stops-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = stops.map(stop => {
        const priorityClass = `priority-${stop.priority}`;
        const check = '<span class="feature-icon">✅</span>';
        const cross = '<span class="feature-icon">❌</span>';
        
        const features = stop.present_features.map(f => f.name);
        const missing = stop.missing_features.map(f => f.name);
        
        const hasFeature = (name) => features.some(f => f.toLowerCase().includes(name.toLowerCase()));
        
        return `
            <tr>
                <td><strong>#${stop.rank}</strong></td>
                <td><strong>${stop.name}</strong></td>
                <td>${stop.type.replace(/_/g, ' ')}</td>
                <td class="${priorityClass}">${stop.gap_score}%</td>
                <td>${hasFeature('ramp') ? check : cross}</td>
                <td>${hasFeature('tactile') ? check : cross}</td>
                <td>${hasFeature('audio') ? check : cross}</td>
                <td>${hasFeature('wheelchair') ? check : cross}</td>
                <td>${hasFeature('braille') ? check : cross}</td>
                <td>${hasFeature('elevator') || hasFeature('lift') ? check : cross}</td>
                <td>${hasFeature('toilet') ? check : cross}</td>
                <td>${hasFeature('staff') ? check : cross}</td>
                <td>${stop.grievance_count}</td>
            </tr>
        `;
    }).join('');
}

function filterStops() {
    const query = document.getElementById('stop-search').value.toLowerCase();
    const rows = document.querySelectorAll('#stops-table-body tr');
    
    rows.forEach(row => {
        const name = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        row.style.display = name.includes(query) ? '' : 'none';
    });
}

// ===== GRIEVANCE CLUSTERS =====
function buildClusterGrid(clusters) {
    const grid = document.getElementById('cluster-grid');
    if (!grid) return;
    
    grid.innerHTML = clusters.map(cluster => {
        const samples = cluster.sample_grievances
            .map(s => `<div class="cluster-sample">"${s}"</div>`)
            .join('');
        
        return `
            <div class="cluster-card" style="--cluster-color: ${cluster.color}">
                <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: ${cluster.color};"></div>
                <div class="cluster-header">
                    <div class="cluster-title">
                        <span>${cluster.icon}</span>
                        <h4>${cluster.label}</h4>
                    </div>
                    <span class="cluster-count" style="color: ${cluster.color}">${cluster.count}</span>
                </div>
                <div class="cluster-percent">${cluster.percentage}% of all grievances</div>
                <div class="cluster-samples">${samples}</div>
            </div>
        `;
    }).join('');
}

function updateSilhouetteScore(data) {
    const valueEl = document.getElementById('silhouette-value');
    const qualityEl = document.getElementById('silhouette-quality');
    
    if (valueEl) valueEl.textContent = data.silhouette_score;
    if (qualityEl) {
        qualityEl.textContent = data.silhouette_quality;
        // Update quality badge color
        if (data.silhouette_score > 0.5) {
            qualityEl.style.background = 'rgba(34,197,94,0.12)';
            qualityEl.style.color = '#22c55e';
        } else if (data.silhouette_score > 0.25) {
            qualityEl.style.background = 'rgba(234,179,8,0.12)';
            qualityEl.style.color = '#eab308';
        } else {
            qualityEl.style.background = 'rgba(239,68,68,0.12)';
            qualityEl.style.color = '#ef4444';
        }
    }
}

// ===== REPORT TAB =====
async function loadReportData() {
    try {
        const reportData = await api.getReport();
        appData.report = reportData;
        
        // Fill report tab
        const dateEl = document.getElementById('report-date');
        if (dateEl) dateEl.textContent = `Generated: ${reportData.generated_at}`;
        
        const genTimeEl = document.getElementById('report-gen-time');
        if (genTimeEl) genTimeEl.textContent = `Report generated in ${reportData.generation_time_seconds} seconds`;
        
        document.getElementById('report-total-stops').textContent = reportData.summary.total_stops;
        document.getElementById('report-coverage').textContent = reportData.summary.coverage_percent + '%';
        document.getElementById('report-critical').textContent = reportData.summary.critical_count;
        document.getElementById('report-silhouette').textContent = reportData.grievance_analysis.silhouette_score;
        
        // Priority table
        const tbody = document.getElementById('report-priority-body');
        if (tbody) {
            tbody.innerHTML = reportData.top_priority_stops.slice(0, 10).map((stop, i) => {
                const priorityClass = `priority-${stop.priority}`;
                const missing = stop.missing_features.map(f => f.name).join(', ');
                return `
                    <tr>
                        <td>${i + 1}</td>
                        <td><strong>${stop.name}</strong></td>
                        <td class="${priorityClass}">${stop.gap_score}%</td>
                        <td>${stop.grievance_count}</td>
                        <td>${stop.priority_score}</td>
                        <td style="font-size: 11px; color: var(--text-secondary);">${missing}</td>
                    </tr>
                `;
            }).join('');
        }
        
        // Grievance summary
        const gSummary = document.getElementById('report-grievance-summary');
        if (gSummary) {
            gSummary.innerHTML = reportData.grievance_analysis.clusters.map(c => `
                <div class="grievance-summary-item">
                    <span class="gs-icon">${c.icon}</span>
                    <div class="gs-info">
                        <h4>${c.label}</h4>
                        <p>${c.percentage}% of all grievances</p>
                    </div>
                    <span class="gs-count">${c.count}</span>
                </div>
            `).join('');
        }
        
        // Recommendations
        const recEl = document.getElementById('report-recommendations');
        if (recEl) {
            const recommendations = [
                { title: 'Install Wheelchair Ramps', desc: 'Deploy ramps with 1:12 slope at all critical stops, prioritizing high-footfall terminals' },
                { title: 'Audio Announcement Systems', desc: 'Install audio systems for bus arrivals at top 10 priority stops within 3 months' },
                { title: 'Tactile Guiding Paths', desc: 'Add TGSI (tactile ground surface indicators) connecting entrance to boarding points' },
                { title: 'Fix Accessible Toilets', desc: 'Repair, unlock, and maintain accessible toilets at all bus stands and terminals' },
                { title: 'Staff Training Program', desc: 'Conduct mandatory disability awareness training for all transport staff' },
                { title: 'Braille & LED Signage', desc: 'Install Braille route maps and LED display boards at all major stops' },
                { title: 'Monthly Accessibility Audits', desc: 'Establish regular audits with citizen feedback mechanism for continuous improvement' },
                { title: 'Emergency Alert System', desc: 'Install emergency call buttons and visual alarms at all stations for safety' }
            ];
            
            recEl.innerHTML = recommendations.map((rec, i) => `
                <div class="recommendation-item">
                    <span class="rec-number">${i + 1}</span>
                    <div class="rec-content">
                        <h4>${rec.title}</h4>
                        <p>${rec.desc}</p>
                    </div>
                </div>
            `).join('');
        }
        
    } catch (error) {
        console.error('Failed to load report:', error);
    }
}

// ===== INITIALIZATION =====
async function initApp() {
    const loadingScreen = document.getElementById('loading-screen');
    
    try {
        // Fetch data in parallel
        const [stopsData, grievanceData, trendsData] = await Promise.all([
            api.getStops(),
            api.getGrievances(),
            api.getTrends()
        ]);
        
        appData.stops = stopsData;
        appData.grievances = grievanceData;
        appData.summary = stopsData.summary;
        
        // Update dashboard
        updateSummaryCards(stopsData.summary);
        buildPriorityTable(stopsData.stops);
        
        // Charts
        createGapDistributionChart(stopsData.stops);
        createPriorityPieChart(stopsData.summary);
        if (trendsData) createHistoricalTrendChart(trendsData);
        
        // Map
        initMap();
        populateMap(stopsData.stops);
        
        // Grievances
        updateSilhouetteScore(grievanceData);
        buildClusterGrid(grievanceData.clusters);
        createGrievanceClusterChart(grievanceData.clusters);
        
        // Stops table
        buildStopsTable(stopsData.stops);
        
        // Hide loading screen
        setTimeout(() => {
            if (loadingScreen) loadingScreen.classList.add('hidden');
        }, 800);
        
        console.log('✅ AccessAudit AI initialized successfully');
        console.log(`📊 Analyzed ${stopsData.summary.total_stops} stops with ${stopsData.summary.coverage_percent}% coverage`);
        console.log(`🧠 Silhouette Score: ${grievanceData.silhouette_score} (${grievanceData.silhouette_quality})`);
        
    } catch (error) {
        console.error('❌ Failed to initialize app:', error);
        if (loadingScreen) {
            loadingScreen.querySelector('p').textContent = 'Failed to connect to server. Please ensure the backend is running.';
            loadingScreen.querySelector('.loader-bar').style.display = 'none';
        }
    }
}

// Start the app when DOM is ready
document.addEventListener('DOMContentLoaded', initApp);

// ===== STOP DETAILS MODAL =====
async function openStopModal(stopId) {
    const modal = document.getElementById('stop-details-modal');
    if (!modal) return;
    
    // Set loading state
    const nameEl = document.getElementById('modal-stop-name');
    const dateEl = document.getElementById('modal-audit-date');
    const listEl = document.getElementById('modal-grievance-list');
    
    nameEl.textContent = "Loading...";
    dateEl.textContent = "Last Audit: --";
    listEl.innerHTML = '<div class="loading-state">Fetching latest data...</div>';
    
    // Show modal
    modal.classList.remove('hidden');
    
    try {
        const details = await api.getStopDetails(stopId);
        if (!details) throw new Error("Failed to load details");
        
        nameEl.textContent = details.stop_info.name;
        dateEl.textContent = `Last Audit: ${details.last_audit_date}`;
        
        // Render Grievances
        if (details.grievances && details.grievances.length > 0) {
            listEl.innerHTML = details.grievances.map(g => `
                <div class="grievance-item" style="border-left: 3px solid ${g.cluster_color || '#111'}">
                    <p>"${g.text}"</p>
                    <span class="grievance-tag" style="color:${g.cluster_color || '#555'}">${g.cluster_label || 'Unclassified'}</span>
                    <span class="grievance-tag" style="float: right; opacity: 0.6;">${g.date}</span>
                    <div class="grievance-suggestion">
                        <span class="suggestion-icon">💡</span>
                        <span class="suggestion-text">${g.suggestion}</span>
                    </div>
                </div>
            `).join('');
        } else {
            listEl.innerHTML = '<div class="loading-state">No recorded grievances found for this stop.</div>';
        }
        
        // Render Chart
        if (window.createStopTrendChart) {
            window.createStopTrendChart(details.breakdown);
        }
        
    } catch (e) {
        console.error(e);
        nameEl.textContent = "Error";
        listEl.innerHTML = '<div class="loading-state" style="color:var(--red);">Failed to load deep analytics</div>';
    }
}

function closeStopModal() {
    const modal = document.getElementById('stop-details-modal');
    if (modal) modal.classList.add('hidden');
}

// Close modal on click outside
window.addEventListener('click', (e) => {
    const modal = document.getElementById('stop-details-modal');
    if (e.target === modal) {
        closeStopModal();
    }
});

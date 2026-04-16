/**
 * Charts Module - Chart.js visualizations (White Premium Theme)
 */
let gapDistributionChart = null;
let priorityPieChart = null;
let grievanceClusterChart = null;

const chartColors = {
    critical: '#d32f2f',
    warning: '#f9a825',
    good: '#2e7d32',
    criticalBg: 'rgba(211, 47, 47, 0.15)',
    warningBg: 'rgba(249, 168, 37, 0.15)',
    goodBg: 'rgba(46, 125, 50, 0.15)',
    gridColor: 'rgba(0, 0, 0, 0.06)',
    textColor: '#555555',
    textMuted: '#999999'
};

const darkThemeDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: {
                color: chartColors.textColor,
                font: { family: "'Inter', sans-serif", size: 12, weight: '500' },
                padding: 16,
                usePointStyle: true,
                pointStyleWidth: 10
            }
        },
        tooltip: {
            backgroundColor: '#111111',
            titleColor: '#ffffff',
            bodyColor: '#cccccc',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
            padding: 12,
            cornerRadius: 8,
            titleFont: { family: "'Inter', sans-serif", weight: '600', size: 13 },
            bodyFont: { family: "'Inter', sans-serif", size: 12 },
            displayColors: true,
            boxPadding: 4
        }
    }
};

function createGapDistributionChart(stops) {
    const ctx = document.getElementById('chart-gap-distribution');
    if (!ctx) return;
    
    if (gapDistributionChart) gapDistributionChart.destroy();
    
    const sortedStops = [...stops].sort((a, b) => b.gap_score - a.gap_score);
    
    const labels = sortedStops.map(s => {
        const name = s.name.length > 20 ? s.name.substring(0, 20) + '...' : s.name;
        return name;
    });
    
    const scores = sortedStops.map(s => s.gap_score);
    const colors = sortedStops.map(s => {
        if (s.priority === 'critical') return chartColors.critical;
        if (s.priority === 'warning') return chartColors.warning;
        return chartColors.good;
    });

    gapDistributionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Gap Score (%)',
                data: scores,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 0,
                borderRadius: 4,
                borderSkipped: false,
                barThickness: 14
            }]
        },
        options: {
            ...darkThemeDefaults,
            indexAxis: 'y',
            plugins: {
                ...darkThemeDefaults.plugins,
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: chartColors.gridColor },
                    ticks: { 
                        color: chartColors.textColor,
                        font: { size: 11, weight: '500' },
                        callback: v => v + '%'
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: { 
                        color: chartColors.textColor,
                        font: { size: 10, weight: '500' }
                    }
                }
            }
        }
    });
}

function createPriorityPieChart(summary) {
    const ctx = document.getElementById('chart-priority-pie');
    if (!ctx) return;
    
    if (priorityPieChart) priorityPieChart.destroy();

    priorityPieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Critical', 'Warning', 'Good'],
            datasets: [{
                data: [summary.critical_count, summary.warning_count, summary.good_count],
                backgroundColor: [chartColors.critical, chartColors.warning, chartColors.good],
                borderColor: '#ffffff',
                borderWidth: 3,
                hoverOffset: 8
            }]
        },
        options: {
            ...darkThemeDefaults,
            cutout: '62%',
            plugins: {
                ...darkThemeDefaults.plugins,
                legend: {
                    ...darkThemeDefaults.plugins.legend,
                    position: 'bottom'
                }
            }
        }
    });
}

function createGrievanceClusterChart(clusters) {
    const ctx = document.getElementById('chart-grievance-clusters');
    if (!ctx) return;
    
    if (grievanceClusterChart) grievanceClusterChart.destroy();

    const labels = clusters.map(c => c.label);
    const counts = clusters.map(c => c.count);
    const colors = clusters.map(c => c.color);

    grievanceClusterChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Grievances',
                data: counts,
                backgroundColor: colors.map(c => c + '30'),
                borderColor: colors,
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false,
                barThickness: 44
            }]
        },
        options: {
            ...darkThemeDefaults,
            plugins: {
                ...darkThemeDefaults.plugins,
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { 
                        color: chartColors.textColor,
                        font: { size: 10, weight: '500' },
                        maxRotation: 45
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: chartColors.gridColor },
                    ticks: { 
                        color: chartColors.textColor,
                        font: { size: 11, weight: '500' },
                        stepSize: 5
                    }
                }
            }
        }
    });
}

let historicalTrendChart = null;

function createHistoricalTrendChart(trendData) {
    const ctx = document.getElementById('chart-historical-trends');
    if (!ctx) return;
    
    if (historicalTrendChart) historicalTrendChart.destroy();
    
    // Ensure chronological order
    const data = [...trendData].sort((a, b) => {
        if (a.year !== b.year) return a.year - b.year;
        const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        return months.indexOf(a.month) - months.indexOf(b.month);
    });

    const labels = data.map(d => `${d.month} ${d.year.toString().slice(-2)}`);
    const gapScores = data.map(d => d.avg_gap_score);
    const goodStops = data.map(d => d.good_stops);

    historicalTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Avg Gap Score (%)',
                    data: gapScores,
                    borderColor: '#111111',
                    backgroundColor: 'transparent',
                    borderWidth: 3,
                    tension: 0.4,
                    yAxisID: 'yGap',
                    pointBackgroundColor: '#111111',
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Accessible Stops',
                    data: goodStops,
                    borderColor: '#2e7d32',
                    backgroundColor: 'rgba(46, 125, 50, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'yStops',
                    pointBackgroundColor: '#2e7d32',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            ...darkThemeDefaults,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                ...darkThemeDefaults.plugins,
                legend: {
                    display: true,
                    position: 'top',
                    align: 'end',
                    labels: {
                        color: chartColors.textColor,
                        usePointStyle: true,
                        boxWidth: 8
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: chartColors.textColor }
                },
                yGap: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Gap Score (%)',
                        color: chartColors.textColor,
                        font: { size: 12, weight: '500' }
                    },
                    grid: { color: chartColors.gridColor },
                    ticks: { color: chartColors.textColor }
                },
                yStops: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Accessible Stands',
                        color: chartColors.textColor,
                        font: { size: 12, weight: '500' }
                    },
                    grid: { display: false },
                    ticks: { color: chartColors.textColor }
                }
            }
        }
    });
}

let stopTrendChart = null;

window.createStopTrendChart = function(breakdownData) {
    const ctx = document.getElementById('chart-stop-trend');
    if (!ctx) return;
    
    if (stopTrendChart) stopTrendChart.destroy();

    const labels = breakdownData.map(d => d.label);
    const counts = breakdownData.map(d => d.count);
    const colors = breakdownData.map(d => d.color);

    stopTrendChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Grievances',
                data: counts,
                backgroundColor: colors.map(c => c + '30'),
                borderColor: colors,
                borderWidth: 2,
                borderRadius: 6,
                borderSkipped: false,
                barThickness: 22
            }]
        },
        options: {
            ...darkThemeDefaults,
            indexAxis: 'y',
            maintainAspectRatio: false,
            plugins: {
                ...darkThemeDefaults.plugins,
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: chartColors.gridColor },
                    ticks: { 
                        color: chartColors.textColor,
                        stepSize: 1
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: { 
                        color: chartColors.textColor,
                        font: { size: 11, weight: '600' }
                    }
                }
            }
        }
    });
};

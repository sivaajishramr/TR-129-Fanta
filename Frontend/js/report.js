/**
 * Report Module - PDF generation using jsPDF (Fixed)
 */
async function generatePDF() {
    const timerEl = document.getElementById('pdf-timer');
    const btnEl = document.getElementById('btn-export-pdf');
    
    if (timerEl) timerEl.textContent = 'Generating report...';
    if (btnEl) {
        btnEl.disabled = true;
        btnEl.style.opacity = '0.6';
    }
    
    const startTime = performance.now();
    
    try {
        const reportData = await api.getReport();
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
        
        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        const margin = 18;
        const contentWidth = pageWidth - margin * 2;
        let y = 0;
        
        // ===== PAGE 1: COVER =====
        // Header bar
        doc.setFillColor(17, 17, 17);
        doc.rect(0, 0, pageWidth, 55, 'F');
        
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(24);
        doc.setFont('helvetica', 'bold');
        doc.text('AccessAudit AI', margin, 22);
        
        doc.setFontSize(13);
        doc.setFont('helvetica', 'normal');
        doc.text('Public Transport Accessibility Audit Report', margin, 32);
        
        doc.setFontSize(10);
        doc.text('Tiruchirappalli (Trichy), Tamil Nadu', margin, 42);
        doc.text(reportData.generated_at || new Date().toISOString().slice(0, 19), margin, 50);
        
        // SDG badges on the right
        doc.setFontSize(8);
        doc.text('SDG 10: Reduced Inequalities', pageWidth - margin - 50, 42);
        doc.text('SDG 11: Sustainable Cities', pageWidth - margin - 50, 50);
        
        // Summary section
        y = 68;
        doc.setTextColor(17, 17, 17);
        doc.setFontSize(16);
        doc.setFont('helvetica', 'bold');
        doc.text('Executive Summary', margin, y);
        
        y += 4;
        doc.setDrawColor(17, 17, 17);
        doc.setLineWidth(0.5);
        doc.line(margin, y, margin + 40, y);
        
        y += 12;
        const summary = reportData.summary;
        
        // Stats boxes
        const boxWidth = (contentWidth - 12) / 4;
        const boxes = [
            { label: 'Stops Analyzed', value: String(summary.total_stops) },
            { label: 'Coverage', value: summary.coverage_percent + '%' },
            { label: 'Critical Stops', value: String(summary.critical_count) },
            { label: 'Avg Gap Score', value: summary.average_gap_score + '%' }
        ];
        
        boxes.forEach((box, i) => {
            const bx = margin + i * (boxWidth + 4);
            doc.setFillColor(248, 249, 250);
            doc.roundedRect(bx, y, boxWidth, 22, 2, 2, 'F');
            doc.setDrawColor(220, 220, 220);
            doc.roundedRect(bx, y, boxWidth, 22, 2, 2, 'S');
            
            doc.setTextColor(17, 17, 17);
            doc.setFontSize(18);
            doc.setFont('helvetica', 'bold');
            doc.text(box.value, bx + boxWidth / 2, y + 10, { align: 'center' });
            
            doc.setFontSize(7);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(120, 120, 120);
            doc.text(box.label.toUpperCase(), bx + boxWidth / 2, y + 17, { align: 'center' });
        });
        
        y += 30;
        
        // Additional stats
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(80, 80, 80);
        
        const statLines = [
            'Total Grievances Analyzed: ' + summary.total_grievances,
            'Clustering Quality (Silhouette Score): ' + reportData.grievance_analysis.silhouette_score + ' (' + reportData.grievance_analysis.silhouette_quality + ')',
            'Warning Stops: ' + summary.warning_count + '  |  Good Stops: ' + summary.good_count,
            'Report Generation Time: ' + reportData.generation_time_seconds + ' seconds'
        ];
        
        statLines.forEach(line => {
            doc.text(line, margin, y);
            y += 6;
        });
        
        // ===== TOP 10 PRIORITY STOPS =====
        y += 8;
        doc.setTextColor(17, 17, 17);
        doc.setFontSize(16);
        doc.setFont('helvetica', 'bold');
        doc.text('Top 10 Priority Stops', margin, y);
        
        y += 4;
        doc.line(margin, y, margin + 40, y);
        y += 8;
        
        // Table header
        doc.setFillColor(17, 17, 17);
        doc.rect(margin, y - 3, contentWidth, 9, 'F');
        doc.setFontSize(7);
        doc.setTextColor(255, 255, 255);
        doc.setFont('helvetica', 'bold');
        
        doc.text('#', margin + 2, y + 3);
        doc.text('STOP NAME', margin + 10, y + 3);
        doc.text('GAP %', margin + 78, y + 3);
        doc.text('COMPLAINTS', margin + 98, y + 3);
        doc.text('PRIORITY', margin + 122, y + 3);
        doc.text('MISSING FEATURES', margin + 142, y + 3);
        y += 10;
        
        // Table rows
        const topStops = reportData.top_priority_stops.slice(0, 10);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8);
        
        topStops.forEach((stop, i) => {
            if (y > pageHeight - 20) {
                doc.addPage();
                y = margin;
            }
            
            if (i % 2 === 0) {
                doc.setFillColor(248, 249, 250);
                doc.rect(margin, y - 3, contentWidth, 8, 'F');
            }
            
            doc.setTextColor(17, 17, 17);
            doc.text(String(i + 1), margin + 2, y + 2);
            doc.text(stop.name.substring(0, 32), margin + 10, y + 2);
            
            // Color-code the gap score
            if (stop.priority === 'critical') doc.setTextColor(211, 47, 47);
            else if (stop.priority === 'warning') doc.setTextColor(249, 168, 37);
            else doc.setTextColor(46, 125, 50);
            
            doc.setFont('helvetica', 'bold');
            doc.text(stop.gap_score + '%', margin + 78, y + 2);
            
            doc.setTextColor(17, 17, 17);
            doc.setFont('helvetica', 'normal');
            doc.text(String(stop.grievance_count), margin + 104, y + 2);
            doc.text(stop.priority.toUpperCase(), margin + 122, y + 2);
            
            const missing = stop.missing_features.map(function(f) { return f.name; }).join(', ');
            doc.setFontSize(6);
            doc.text(missing.substring(0, 40), margin + 142, y + 2);
            doc.setFontSize(8);
            
            y += 8;
        });
        
        // ===== PAGE 2: GRIEVANCE ANALYSIS =====
        doc.addPage();
        y = margin;
        
        doc.setFillColor(17, 17, 17);
        doc.rect(0, 0, pageWidth, 12, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(8);
        doc.setFont('helvetica', 'bold');
        doc.text('AccessAudit AI  |  Accessibility Audit Report  |  Trichy, Tamil Nadu', margin, 8);
        
        y = 22;
        doc.setTextColor(17, 17, 17);
        doc.setFontSize(16);
        doc.setFont('helvetica', 'bold');
        doc.text('Grievance Theme Analysis', margin, y);
        
        y += 4;
        doc.line(margin, y, margin + 40, y);
        y += 10;
        
        doc.setFontSize(9);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(80, 80, 80);
        doc.text('Silhouette Score: ' + reportData.grievance_analysis.silhouette_score + ' (' + reportData.grievance_analysis.silhouette_quality + ')', margin, y);
        y += 10;
        
        // Cluster bars
        const clusters = reportData.grievance_analysis.clusters;
        const maxCount = Math.max.apply(null, clusters.map(function(c) { return c.count; }));
        
        clusters.forEach(function(cluster) {
            if (y > pageHeight - 25) {
                doc.addPage();
                y = margin;
            }
            
            doc.setTextColor(17, 17, 17);
            doc.setFontSize(10);
            doc.setFont('helvetica', 'bold');
            doc.text(cluster.label, margin, y);
            
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(9);
            doc.setTextColor(100, 100, 100);
            doc.text(cluster.count + ' complaints (' + cluster.percentage + '%)', margin + 65, y);
            
            y += 5;
            
            // Draw bar
            const barWidth = (cluster.count / maxCount) * (contentWidth - 10);
            const hex = cluster.color;
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);
            
            doc.setFillColor(r, g, b);
            doc.roundedRect(margin, y - 2, barWidth, 5, 2, 2, 'F');
            
            y += 10;
        });
        
        // ===== RECOMMENDATIONS =====
        y += 5;
        doc.setTextColor(17, 17, 17);
        doc.setFontSize(16);
        doc.setFont('helvetica', 'bold');
        doc.text('Recommendations', margin, y);
        
        y += 4;
        doc.line(margin, y, margin + 40, y);
        y += 10;
        
        var recommendations = [
            'Install wheelchair ramps (1:12 slope) at all critical stops, prioritizing high-footfall terminals.',
            'Deploy audio announcement systems at top 10 priority stops within 3 months.',
            'Add tactile guiding paths (TGSI) connecting entrance to boarding points at all stations.',
            'Repair, unlock, and maintain accessible toilets at all bus stands and terminals.',
            'Conduct mandatory disability awareness training for all transport staff quarterly.',
            'Install Braille route maps and LED display boards at all major stops.',
            'Establish regular monthly accessibility audits with citizen feedback mechanism.',
            'Create dedicated helpline and mobile app for accessibility complaint reporting.'
        ];
        
        doc.setFontSize(9);
        recommendations.forEach(function(rec, i) {
            if (y > pageHeight - 20) {
                doc.addPage();
                y = margin;
            }
            
            doc.setTextColor(17, 17, 17);
            doc.setFont('helvetica', 'bold');
            doc.text((i + 1) + '.', margin, y);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(60, 60, 60);
            
            var lines = doc.splitTextToSize(rec, contentWidth - 10);
            doc.text(lines, margin + 8, y);
            y += lines.length * 5 + 4;
        });
        
        // ===== FOOTER on last page =====
        y += 10;
        if (y > pageHeight - 30) {
            doc.addPage();
            y = margin;
        }
        
        doc.setFillColor(17, 17, 17);
        doc.rect(0, pageHeight - 18, pageWidth, 18, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(8);
        doc.setFont('helvetica', 'normal');
        doc.text('Generated by AccessAudit AI  |  Tensor\'26 Hackathon  |  Team Fanta', margin, pageHeight - 10);
        doc.text('UN SDG 10 (Reduced Inequalities) & SDG 11 (Sustainable Cities)', margin, pageHeight - 5);
        
        // Save the PDF
        doc.save('Trichy_Accessibility_Audit_Report.pdf');
        
        var elapsed = ((performance.now() - startTime) / 1000).toFixed(2);
        if (timerEl) timerEl.textContent = 'Report generated in ' + elapsed + ' seconds';
        
    } catch (error) {
        console.error('PDF generation failed:', error);
        if (timerEl) timerEl.textContent = 'Failed to generate report: ' + error.message;
    } finally {
        if (btnEl) {
            btnEl.disabled = false;
            btnEl.style.opacity = '1';
        }
    }
}

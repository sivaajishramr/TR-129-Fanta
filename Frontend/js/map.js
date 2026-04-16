/**
 * Map Module - Leaflet.js interactive map with search, location, and TN boundary
 */
let mapInstance = null;
let mapMarkers = [];
let userLocationMarker = null;
let allStopsData = [];

function initMap() {
    if (mapInstance) return;
    
    // Center on Tamil Nadu overview
    mapInstance = L.map('map', {
        center: [10.8050, 78.6856],
        zoom: 12,
        zoomControl: true,
        attributionControl: true
    });

    // Light clean tile layer for white theme
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(mapInstance);

    // Add Tamil Nadu state label
    addTamilNaduIndicator();
}

function addTamilNaduIndicator() {
    if (!mapInstance) return;

    // Tamil Nadu major cities as context markers (subtle)
    const tnCities = [
        { name: 'Chennai', lat: 13.0827, lng: 80.2707 },
        { name: 'Coimbatore', lat: 11.0168, lng: 76.9558 },
        { name: 'Madurai', lat: 9.9252, lng: 78.1198 },
        { name: 'Salem', lat: 11.6643, lng: 78.1460 },
        { name: 'Tiruchirappalli', lat: 10.7905, lng: 78.6874 },
        { name: 'Tirunelveli', lat: 8.7139, lng: 77.7567 },
        { name: 'Vellore', lat: 12.9165, lng: 79.1325 },
        { name: 'Erode', lat: 11.3410, lng: 77.7172 },
        { name: 'Thanjavur', lat: 10.7870, lng: 79.1378 },
        { name: 'Dindigul', lat: 10.3673, lng: 77.9803 }
    ];

    // Add subtle city labels when zoomed out
    tnCities.forEach(city => {
        const label = L.divIcon({
            className: 'tn-boundary-label',
            html: `<span style="font-size:10px; color:rgba(0,0,0,0.25); font-weight:600;">${city.name}</span>`,
            iconSize: [100, 20],
            iconAnchor: [50, 10]
        });
        L.marker([city.lat, city.lng], { icon: label, interactive: false }).addTo(mapInstance);
    });

    // Add Tamil Nadu approximate boundary polygon (simplified)
    const tnBoundary = [
        [13.5, 79.8], [13.2, 80.3], [12.8, 80.2], [12.2, 80.0],
        [11.8, 79.8], [11.4, 79.9], [11.0, 79.8], [10.8, 79.5],
        [10.4, 79.2], [10.0, 79.0], [9.5, 78.8], [9.0, 78.4],
        [8.3, 77.5], [8.1, 77.3], [8.5, 77.0], [9.0, 77.1],
        [9.5, 77.2], [10.0, 76.9], [10.5, 76.8], [11.0, 76.5],
        [11.3, 76.6], [11.8, 76.8], [12.0, 77.0], [12.3, 77.2],
        [12.5, 77.5], [12.8, 77.8], [13.0, 78.0], [13.2, 78.3],
        [13.5, 78.5], [13.7, 79.0], [13.6, 79.5], [13.5, 79.8]
    ];

    L.polygon(tnBoundary, {
        color: '#111111',
        weight: 1.5,
        opacity: 0.15,
        fillColor: '#111111',
        fillOpacity: 0.02,
        dashArray: '8, 4',
        interactive: false
    }).addTo(mapInstance);

    // Add "TAMIL NADU" label
    const tnLabel = L.divIcon({
        className: 'tn-boundary-label',
        html: '<span style="font-size:16px; color:rgba(0,0,0,0.12); letter-spacing:8px; font-weight:900;">TAMIL NADU</span>',
        iconSize: [200, 30],
        iconAnchor: [100, 15]
    });
    L.marker([11.0, 78.2], { icon: tnLabel, interactive: false }).addTo(mapInstance);
}

function getMarkerColor(priority) {
    switch (priority) {
        case 'critical': return '#d32f2f';
        case 'warning': return '#f9a825';
        case 'good': return '#2e7d32';
        default: return '#111111';
    }
}

function getMarkerSize(priority) {
    switch (priority) {
        case 'critical': return 14;
        case 'warning': return 11;
        case 'good': return 9;
        default: return 10;
    }
}

function createMarkerIcon(stop) {
    const color = getMarkerColor(stop.priority);
    const size = getMarkerSize(stop.priority);
    
    return L.divIcon({
        className: 'custom-marker',
        html: `
            <div style="
                width: ${size * 2}px;
                height: ${size * 2}px;
                background: ${color};
                border: 3px solid white;
                border-radius: 50%;
                box-shadow: 0 2px 8px ${color}60, 0 1px 4px rgba(0,0,0,0.2);
                position: relative;
                ${stop.priority === 'critical' ? `animation: markerPulse 2s ease-in-out infinite;` : ''}
            "></div>
            <style>
                @keyframes markerPulse {
                    0%, 100% { box-shadow: 0 2px 8px ${color}60; transform: scale(1); }
                    50% { box-shadow: 0 2px 20px ${color}90, 0 0 30px ${color}30; transform: scale(1.1); }
                }
            </style>
        `,
        iconSize: [size * 2, size * 2],
        iconAnchor: [size, size],
        popupAnchor: [0, -size]
    });
}

function buildPopupContent(stop) {
    const scoreColor = stop.priority === 'critical' ? '#d32f2f' : 
                       stop.priority === 'warning' ? '#f9a825' : '#2e7d32';
    
    let featuresHtml = '';
    
    if (stop.missing_features && stop.missing_features.length > 0) {
        stop.missing_features.forEach(f => {
            featuresHtml += `<span class="popup-feature missing">\u2716 ${f.name}</span>`;
        });
    }
    
    if (stop.present_features && stop.present_features.length > 0) {
        stop.present_features.forEach(f => {
            featuresHtml += `<span class="popup-feature present">\u2714 ${f.name}</span>`;
        });
    }

    return `
        <div class="popup-title">${stop.name}</div>
        <div class="popup-detail">Type: ${stop.type.replace(/_/g, ' ').toUpperCase()}</div>
        <div class="popup-detail">Daily footfall: ${stop.daily_footfall.toLocaleString()}</div>
        <div class="popup-score" style="color: ${scoreColor}">
            Gap Score: ${stop.gap_score}%
        </div>
        <div class="popup-detail">Priority: ${stop.priority_label}</div>
        <div class="popup-detail">Grievances: ${stop.grievance_count}</div>
        <div class="popup-detail">Rank: #${stop.rank} of 30</div>
        <div class="popup-features">${featuresHtml}</div>
        <button class="btn-analytics" onclick="openStopModal('${stop.id}')">View Deep Analytics 🔍</button>
    `;
}

function populateMap(stops) {
    if (!mapInstance) initMap();
    
    allStopsData = stops;
    
    // Clear existing markers
    mapMarkers.forEach(m => mapInstance.removeLayer(m));
    mapMarkers = [];
    
    stops.forEach(stop => {
        const marker = L.marker([stop.lat, stop.lng], {
            icon: createMarkerIcon(stop)
        }).addTo(mapInstance);
        
        marker.bindPopup(buildPopupContent(stop), {
            maxWidth: 340,
            minWidth: 260
        });
        
        marker.stopData = stop;
        mapMarkers.push(marker);
    });
    
    // Fit bounds to show all markers
    if (mapMarkers.length > 0) {
        const group = L.featureGroup(mapMarkers);
        mapInstance.fitBounds(group.getBounds().pad(0.1));
    }
}

function refreshMap() {
    if (mapInstance) {
        setTimeout(() => {
            mapInstance.invalidateSize();
        }, 150);
    }
}

// ===== SEARCH FUNCTIONALITY =====
function searchStopOnMap(query) {
    const resultsContainer = document.getElementById('map-search-results');
    if (!resultsContainer) return;
    
    if (!query || query.length < 2) {
        resultsContainer.classList.remove('active');
        return;
    }
    
    const matches = allStopsData.filter(s => 
        s.name.toLowerCase().includes(query.toLowerCase())
    );
    
    if (matches.length === 0) {
        resultsContainer.innerHTML = '<div class="search-result-item" style="color: var(--text-muted);">No stops found</div>';
        resultsContainer.classList.add('active');
        return;
    }
    
    resultsContainer.innerHTML = matches.map(stop => {
        const scoreColor = stop.priority === 'critical' ? '#d32f2f' : 
                          stop.priority === 'warning' ? '#f9a825' : '#2e7d32';
        return `
            <div class="search-result-item" onclick="flyToStop('${stop.id}')">
                <strong>${stop.name}</strong>
                <span class="search-result-score" style="color: ${scoreColor}">${stop.gap_score}%</span>
            </div>
        `;
    }).join('');
    
    resultsContainer.classList.add('active');
}

function flyToStop(stopId) {
    const marker = mapMarkers.find(m => m.stopData && m.stopData.id === stopId);
    if (marker && mapInstance) {
        mapInstance.flyTo(marker.getLatLng(), 16, { duration: 1 });
        setTimeout(() => marker.openPopup(), 800);
    }
    
    const resultsContainer = document.getElementById('map-search-results');
    if (resultsContainer) resultsContainer.classList.remove('active');
    
    const searchInput = document.getElementById('map-stop-search');
    if (searchInput) {
        const stop = allStopsData.find(s => s.id === stopId);
        if (stop) searchInput.value = stop.name;
    }
}

// ===== CURRENT LOCATION =====
function locateUser() {
    if (!mapInstance) return;
    
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser');
        return;
    }
    
    const btn = document.getElementById('btn-my-location');
    if (btn) btn.textContent = 'Locating...';
    
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const { latitude, longitude } = position.coords;
            
            // Remove old marker
            if (userLocationMarker) {
                mapInstance.removeLayer(userLocationMarker);
            }
            
            // Add user location marker
            const locationIcon = L.divIcon({
                className: 'my-location-marker',
                html: '<div class="location-dot"></div>',
                iconSize: [16, 16],
                iconAnchor: [8, 8]
            });
            
            userLocationMarker = L.marker([latitude, longitude], { icon: locationIcon })
                .addTo(mapInstance)
                .bindPopup('<div class="popup-title">Your Location</div><div class="popup-detail">You are here</div>')
                .openPopup();
            
            mapInstance.flyTo([latitude, longitude], 14, { duration: 1.5 });
            
            if (btn) btn.innerHTML = '<span>📍</span> My Location';
        },
        (error) => {
            console.error('Geolocation error:', error);
            alert('Unable to get your location. Please check permissions.');
            if (btn) btn.innerHTML = '<span>📍</span> My Location';
        },
        { enableHighAccuracy: true, timeout: 10000 }
    );
}

// Close search results when clicking outside
document.addEventListener('click', (e) => {
    const searchBox = document.querySelector('.map-search-box');
    const results = document.getElementById('map-search-results');
    if (searchBox && results && !searchBox.contains(e.target)) {
        results.classList.remove('active');
    }
});

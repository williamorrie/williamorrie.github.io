#!/usr/bin/env python3
"""
Generate interactive cat tracking map from pre-processed GeoJSON data.
Loads data dynamically to keep HTML file small.
"""

import folium
import json
from config import app_data_dir, script_dir

output_file = script_dir.parent / "cat_arrows.html"

print("Loading processed data...")

# Load metadata
with open(app_data_dir / 'metadata.json', 'r') as f:
    metadata = json.load(f)

# Load GPS data for bounds only
with open(app_data_dir / 'cat_gps_data.json', 'r') as f:
    cat_data = json.load(f)

print("Creating map...")

# Create base map
center_lat, center_lon = metadata['center']
m = folium.Map(location=[center_lat, center_lon], zoom_start=13, zoom_control=True)

# Get the map's variable name from folium
map_id = m.get_name()

# Calculate overall bounds from all cats
all_bounds = []
for cat_id, data in cat_data.items():
    bounds = data['bounds']
    all_bounds.extend([bounds[0], bounds[1]])

# Calculate the envelope of all bounds
if all_bounds:
    min_lat = min(b[0] for b in all_bounds)
    min_lng = min(b[1] for b in all_bounds)
    max_lat = max(b[0] for b in all_bounds)
    max_lng = max(b[1] for b in all_bounds)
    overall_bounds = [[min_lat, min_lng], [max_lat, max_lng]]
else:
    overall_bounds = None

# Extract just the bounds (don't load full GPS data into HTML)
cat_bounds = {cat_id: data['bounds'] for cat_id, data in cat_data.items()}

# Calculate centroids for markers at low zoom
cat_centroids = {}
for cat_id, data in cat_data.items():
    bounds = data['bounds']
    center_lat_cat = (bounds[0][0] + bounds[1][0]) / 2
    center_lng_cat = (bounds[0][1] + bounds[1][1]) / 2
    cat_centroids[cat_id] = [center_lat_cat, center_lng_cat]

# Add custom HTML/CSS/JS for dynamic loading
cat_names = sorted(metadata['cats'])

custom_html = f"""
<div id="catSelector" style="position: fixed; 
            top: 10px; 
            right: 10px; 
            width: 250px; 
            background-color: white; 
            z-index: 1000;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            font-family: Arial, sans-serif;">
    <label for="catSelect" style="font-weight: bold; margin-bottom: 5px; display: block;">
        Select a Cat:
    </label>
    <select id="catSelect" onchange="selectCat()" 
            style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 3px; margin-bottom: 10px;">
        <option value="">-- All Cats --</option>
        {''.join([f'<option value="{cat}">{cat}</option>' for cat in cat_names])}
    </select>
    
    <div style="margin-bottom: 10px;">
        <label style="display: flex; align-items: center; cursor: pointer;">
            <input type="checkbox" id="showPolygons" checked onchange="togglePolygons()" 
                   style="margin-right: 8px;">
            <span>Show home range polygons</span>
        </label>
    </div>
    
    <div id="dateRangeContainer" style="display: none; margin-top: 15px; padding-top: 10px; border-top: 1px solid #eee;">
        <label style="font-weight: bold; margin-bottom: 5px; display: block; font-size: 13px;">
            Date Range:
        </label>
        <div style="margin-bottom: 8px;">
            <label style="font-size: 11px; color: #666;">Start:</label>
            <input type="range" id="dateRangeStart" min="0" max="100" value="0" 
                   style="width: 100%;" oninput="updateDateRange()">
            <div id="startDateLabel" style="font-size: 11px; color: #333; margin-top: 2px;"></div>
        </div>
        <div style="margin-bottom: 8px;">
            <label style="font-size: 11px; color: #666;">End:</label>
            <input type="range" id="dateRangeEnd" min="0" max="100" value="100" 
                   style="width: 100%;" oninput="updateDateRange()">
            <div id="endDateLabel" style="font-size: 11px; color: #333; margin-top: 2px;"></div>
        </div>
    </div>
    
    <div id="statsContainer" style="margin-top: 10px; font-size: 12px; color: #666; padding-top: 10px; border-top: 1px solid #eee;">
        <strong>{metadata['total_cats']}</strong> cats, 
        <strong id="gpsPointCount">{metadata['total_points']:,}</strong> GPS points
    </div>
</div>

<script>
    var catBounds = {json.dumps(cat_bounds)};
    var catCentroids = {json.dumps(cat_centroids)};
    var overallBounds = {json.dumps(overall_bounds)};
    var catData = null;
    var polygonsLayer = null;
    var markersLayer = null;
    var currentCatLayer = null;
    var map = null;
    var ZOOM_THRESHOLD = 12;  // Below this zoom level, show markers instead of polygons
    var currentCatData = null;  // Store current cat's full data for date filtering
    var currentCatId = null;  // Store current cat ID
    var allDatesForCat = [];  // Store all dates for the current cat
    
    // Color palette for days
    var colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
                  'brown', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
                  'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray', 
                  'black', 'lightgray'];
    
    // Wait for map to be fully initialized and find it
    function initMapData() {{
        // Find the map object - folium creates it as a global variable
        for (var key in window) {{
            if (key.startsWith('map_') && window[key] instanceof L.Map) {{
                map = window[key];
                break;
            }}
        }}
        
        if (!map) {{
            console.error('Map not found, retrying...');
            setTimeout(initMapData, 100);
            return;
        }}
        
        console.log('Map found, loading data...');
        
        // Fit map to show all cats
        if (overallBounds) {{
            map.fitBounds(overallBounds, {{padding: [50, 50]}});
        }}
        
        // Add zoom listener to toggle between markers and polygons
        map.on('zoomend', updateLayerDisplay);
        
        // Load all data files
        Promise.all([
            fetch('data/cat_polygons.geojson').then(r => r.json()),
            fetch('data/cat_gps_data.json').then(r => r.json())
        ]).then(([polygons, gpsData]) => {{
            catData = gpsData;
            
            // Add polygons layer
            polygonsLayer = L.geoJSON(polygons, {{
                style: function(feature) {{
                    return {{
                        fillColor: 'blue',
                        color: 'blue',
                        weight: 2,
                        fillOpacity: 0.3
                    }};
                }},
                onEachFeature: function(feature, layer) {{
                    var props = feature.properties;
                    layer.bindTooltip(props['tag-local-identifier'] + '<br>Area: ' + props.area_m2 + ' m²');
                    layer.on('click', function() {{
                        document.getElementById('catSelect').value = props['tag-local-identifier'];
                        selectCat();
                    }});
                }}
            }});
            
            // Create markers layer for low zoom levels
            markersLayer = L.layerGroup();
            for (var catId in catCentroids) {{
                var centroid = catCentroids[catId];
                var area = gpsData[catId].area_m2;
                L.marker(centroid, {{
                    icon: L.divIcon({{
                        className: 'cat-marker',
                        html: '<div style="background-color: rgba(0, 0, 255, 0.6); color: white; padding: 5px; border-radius: 10px; font-weight: bold; white-space: nowrap; font-size: 11px;">' + catId + '</div>',
                        iconSize: [null, null]
                    }})
                }}).bindTooltip(catId + '<br>Area: ' + area + ' m²')
                  .on('click', function(e) {{
                      var marker = e.target;
                      var clickedCat = marker.getTooltip().getContent().split('<br>')[0];
                      document.getElementById('catSelect').value = clickedCat;
                      selectCat();
                  }})
                  .addTo(markersLayer);
            }}
            
            // Show appropriate layer based on initial zoom
            updateLayerDisplay();
            
            console.log('Data loaded successfully');
        }}).catch(err => {{
            console.error('Error loading data:', err);
        }});
    }}
    
    function updateLayerDisplay() {{
        if (!map || !polygonsLayer || !markersLayer) return;
        
        var checkbox = document.getElementById('showPolygons');
        if (!checkbox.checked) {{
            map.removeLayer(polygonsLayer);
            map.removeLayer(markersLayer);
            return;
        }}
        
        var currentZoom = map.getZoom();
        
        if (currentZoom < ZOOM_THRESHOLD) {{
            // Low zoom - show markers
            if (map.hasLayer(polygonsLayer)) {{
                map.removeLayer(polygonsLayer);
            }}
            if (!map.hasLayer(markersLayer)) {{
                map.addLayer(markersLayer);
            }}
        }} else {{
            // High zoom - show polygons
            if (map.hasLayer(markersLayer)) {{
                map.removeLayer(markersLayer);
            }}
            if (!map.hasLayer(polygonsLayer)) {{
                map.addLayer(polygonsLayer);
            }}
        }}
    }}
    
    // Start initialization after page loads
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', initMapData);
    }} else {{
        setTimeout(initMapData, 100);
    }}
    
    function getColorForDate(dateStr, allDates) {{
        var idx = allDates.indexOf(dateStr);
        return colors[idx % colors.length];
    }}
    
    function selectCat() {{
        var select = document.getElementById('catSelect');
        var selectedCat = select.value;
        
        // Remove current cat layer if exists
        if (currentCatLayer) {{
            map.removeLayer(currentCatLayer);
            currentCatLayer = null;
        }}
        
        if (selectedCat === '') {{
            // Reset to show all cats view
            currentCatData = null;
            currentCatId = null;
            allDatesForCat = [];
            document.getElementById('dateRangeContainer').style.display = 'none';
            document.getElementById('gpsPointCount').textContent = '{metadata['total_points']:,}';
            if (overallBounds) {{
                map.fitBounds(overallBounds, {{padding: [50, 50]}});
            }} else {{
                map.setView([{center_lat}, {center_lon}], 13);
            }}
        }} else {{
            // Show selected cat
            currentCatId = selectedCat;
            var data = catData[selectedCat];
            if (!data) return;
            
            // Store current cat data
            currentCatData = data;
            
            // Extract unique dates from GeoJSON features
            var datesSet = new Set();
            data.geojson.features.forEach(function(feature) {{
                datesSet.add(feature.properties.date);
            }});
            allDatesForCat = Array.from(datesSet).sort();
            
            // Setup date range slider
            if (allDatesForCat.length > 1) {{
                document.getElementById('dateRangeContainer').style.display = 'block';
                var startSlider = document.getElementById('dateRangeStart');
                var endSlider = document.getElementById('dateRangeEnd');
                startSlider.max = allDatesForCat.length - 1;
                endSlider.max = allDatesForCat.length - 1;
                startSlider.value = 0;
                endSlider.value = allDatesForCat.length - 1;
                document.getElementById('startDateLabel').textContent = allDatesForCat[0];
                document.getElementById('endDateLabel').textContent = allDatesForCat[allDatesForCat.length - 1];
            }} else {{
                document.getElementById('dateRangeContainer').style.display = 'none';
            }}
            
            // Display the data
            displayCatData();
            
            // Zoom to selected cat
            var bounds = catBounds[selectedCat];
            if (bounds) {{
                map.fitBounds(bounds, {{padding: [50, 50]}});
            }}
        }}
    }}
    
    function togglePolygons() {{
        updateLayerDisplay();
    }}
    
    function displayCatData() {{
        if (!currentCatData || !currentCatId) return;
        
        // Remove current cat layer if exists
        if (currentCatLayer) {{
            map.removeLayer(currentCatLayer);
        }}
        
        currentCatLayer = L.layerGroup();
        
        // Get date range from sliders
        var startIdx = parseInt(document.getElementById('dateRangeStart').value) || 0;
        var endIdx = parseInt(document.getElementById('dateRangeEnd').value) || (allDatesForCat.length - 1);
        
        // Ensure start <= end
        if (startIdx > endIdx) {{
            var temp = startIdx;
            startIdx = endIdx;
            endIdx = temp;
        }}
        
        var selectedDates = allDatesForCat.slice(startIdx, endIdx + 1);
        
        // Organize points by date from GeoJSON features
        var pointsByDate = {{}};
        currentCatData.geojson.features.forEach(function(feature) {{
            var date = feature.properties.date;
            if (selectedDates.indexOf(date) !== -1) {{
                if (!pointsByDate[date]) {{
                    pointsByDate[date] = [];
                }}
                var coords = feature.geometry.coordinates;
                pointsByDate[date].push({{
                    lat: coords[1],
                    lng: coords[0],
                    timestamp: feature.properties.timestamp
                }});
            }}
        }});
        
        var filteredDates = Object.keys(pointsByDate).sort();
        
        // Count total GPS points being displayed
        var totalPoints = 0;
        filteredDates.forEach(function(date) {{
            totalPoints += pointsByDate[date].length;
        }});
        
        // Update GPS point count display
        document.getElementById('gpsPointCount').textContent = totalPoints.toLocaleString();
        
        // Add routes with arrows for each day
        filteredDates.forEach(function(date) {{
            var points = pointsByDate[date];
            var dayColor = getColorForDate(date, allDatesForCat);
            
            // Create polyline for the route
            var coords = points.map(p => [p.lat, p.lng]);
            if (coords.length > 1) {{
                L.polyline(coords, {{
                    color: dayColor,
                    weight: 2,
                    opacity: 0.7
                }}).bindTooltip(currentCatId + ' - ' + date)
                  .addTo(currentCatLayer);
                
                // Add arrows to show direction
                L.polylineDecorator(coords, {{
                    patterns: [{{
                        offset: '10%',
                        repeat: 50,
                        symbol: L.Symbol.arrowHead({{
                            pixelSize: 10,
                            polygon: false,
                            pathOptions: {{
                                stroke: true,
                                weight: 2,
                                color: dayColor
                            }}
                        }})
                    }}]
                }}).addTo(currentCatLayer);
            }}
            
            // Add GPS points
            points.forEach(function(point) {{
                L.circleMarker([point.lat, point.lng], {{
                    radius: 3,
                    color: dayColor,
                    fillColor: dayColor,
                    fillOpacity: 0.7,
                    weight: 1
                }}).bindPopup(currentCatId + '<br>' + point.timestamp + '<br>' + date)
                  .bindTooltip(currentCatId)
                  .addTo(currentCatLayer);
            }});
        }});
        
        currentCatLayer.addTo(map);
    }}
    
    function updateDateRange() {{
        var startSlider = document.getElementById('dateRangeStart');
        var endSlider = document.getElementById('dateRangeEnd');
        var startIdx = parseInt(startSlider.value);
        var endIdx = parseInt(endSlider.value);
        
        // Update labels
        document.getElementById('startDateLabel').textContent = allDatesForCat[startIdx];
        document.getElementById('endDateLabel').textContent = allDatesForCat[endIdx];
        
        // Redraw the cat data with new date range
        displayCatData();
    }}
</script>

<!-- Load Leaflet PolylineDecorator for arrows -->
<link rel="stylesheet" href="https://unpkg.com/leaflet-polylinedecorator@1.6.0/dist/leaflet.polylineDecorator.css" />
<script src="https://unpkg.com/leaflet-polylinedecorator@1.6.0/dist/leaflet.polylineDecorator.js"></script>
"""

# Fix Google Translate 
# Inject a language meta tag into the <head> section
header_content = '<meta http-equiv="content-language" content="en">'
m.get_root().header.add_child(folium.Element(header_content))

# Inject custom HTML into the map
m.get_root().html.add_child(folium.Element(custom_html))

# Save to HTML
m.save(output_file)
print(f"\n✓ Map saved to {output_file}")
print("✓ Data files in 'data/' directory will be loaded dynamically")
print("✓ Ready for deployment to GitHub Pages!")

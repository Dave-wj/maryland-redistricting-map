#!/usr/bin/env python3
"""
Enhanced redistricting map with precincts and address lookup.
Uses US Census Bureau geocoder for reliable CORS-free geocoding.
"""
import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import Fullscreen
import json
import warnings
warnings.filterwarnings('ignore')

print("Loading census block shapefile...")
blocks = gpd.read_file("tl_2020_24_tabblock20.shp")
print(f"Loaded {len(blocks)} census blocks")

print("Loading VTD/precinct shapefile...")
precincts = gpd.read_file("tl_2020_24_vtd20.shp")
print(f"Loaded {len(precincts)} precincts")

print("\nLoading district assignments...")
districts_csv = pd.read_csv("/Users/davidkunes/Desktop/DKunes_Submission.csv", dtype={'GEOID20': str, 'District': int})
print(f"Loaded {len(districts_csv)} district assignments")

# Join blocks with districts
print("\nJoining census blocks with districts...")
blocks_with_districts = blocks.merge(districts_csv, on='GEOID20', how='left')

# Convert to WGS84
print("Converting to WGS84...")
blocks_with_districts = blocks_with_districts.to_crs(epsg=4326)
precincts = precincts.to_crs(epsg=4326)

# Dissolve blocks into district boundaries
print("Creating district boundaries...")
districts_dissolved = blocks_with_districts.dissolve(by='District', as_index=False)
districts_dissolved['geometry'] = districts_dissolved['geometry'].simplify(tolerance=0.001, preserve_topology=True)

# Assign districts to precincts via spatial join (based on centroid)
print("Assigning districts to precincts...")
precinct_centroids = precincts.copy()
precinct_centroids['geometry'] = precincts.geometry.centroid
precincts_with_districts = gpd.sjoin(precinct_centroids, districts_dissolved[['District', 'geometry']], how='left', predicate='within')
precincts['District'] = precincts_with_districts['District'].values

# Simplify precinct geometries for web
print("Simplifying precinct geometries...")
precincts['geometry'] = precincts['geometry'].simplify(tolerance=0.0005, preserve_topology=True)

# Color scheme
district_colors = {
    1: '#e41a1c', 2: '#377eb8', 3: '#4daf4a', 4: '#984ea3',
    5: '#ff7f00', 6: '#ffff33', 7: '#a65628', 8: '#f781bf',
}

# Calculate center
center_lat = 39.0458
center_lon = -76.6413

print(f"\nCreating interactive map...")

# Create map
m = folium.Map(location=[center_lat, center_lon], zoom_start=8, tiles='CartoDB positron')

# District style function
def district_style(feature):
    dist = feature['properties']['District']
    if dist is None or pd.isna(dist):
        return {'fillColor': '#808080', 'color': '#000000', 'weight': 2, 'fillOpacity': 0.5}
    return {'fillColor': district_colors.get(int(dist), '#808080'), 'color': '#000000', 'weight': 2, 'fillOpacity': 0.6}

def district_highlight(feature):
    return {'fillColor': '#ffffff', 'color': '#000000', 'weight': 3, 'fillOpacity': 0.8}

# Precinct style function
def precinct_style(feature):
    dist = feature['properties']['District']
    if dist is None or pd.isna(dist):
        return {'fillColor': '#808080', 'color': '#333333', 'weight': 1, 'fillOpacity': 0.4}
    return {'fillColor': district_colors.get(int(dist), '#808080'), 'color': '#333333', 'weight': 1, 'fillOpacity': 0.4}

def precinct_highlight(feature):
    return {'fillColor': '#ffffff', 'color': '#000000', 'weight': 2, 'fillOpacity': 0.7}

# Add district layer
district_layer = folium.FeatureGroup(name='Congressional Districts', show=True)
folium.GeoJson(
    districts_dissolved,
    style_function=district_style,
    highlight_function=district_highlight,
    tooltip=folium.GeoJsonTooltip(fields=['District'], aliases=['District:'], style='font-size: 14px; font-weight: bold;')
).add_to(district_layer)
district_layer.add_to(m)

# Add precinct layer
precinct_layer = folium.FeatureGroup(name='Voting Precincts', show=False)
folium.GeoJson(
    precincts,
    style_function=precinct_style,
    highlight_function=precinct_highlight,
    tooltip=folium.GeoJsonTooltip(
        fields=['NAME20', 'District'],
        aliases=['Precinct:', 'District:'],
        style='font-size: 12px;'
    )
).add_to(precinct_layer)
precinct_layer.add_to(m)

# Major communities/municipalities with coordinates
# Format: (name, lat, lon, type) - type: 'city', 'town', 'cdp', 'community'
print("Adding community markers...")
communities = [
    # Montgomery County
    ("Bethesda", 38.9807, -77.1003, "cdp"),
    ("Rockville", 39.0840, -77.1528, "city"),
    ("Gaithersburg", 39.1434, -77.2014, "city"),
    ("Silver Spring", 38.9907, -77.0261, "cdp"),
    ("Germantown", 39.1732, -77.2717, "cdp"),
    ("Wheaton", 39.0398, -77.0553, "cdp"),
    ("Potomac", 39.0182, -77.2086, "cdp"),
    ("Aspen Hill", 39.0793, -77.0775, "cdp"),
    ("Olney", 39.1532, -77.0669, "cdp"),
    ("Damascus", 39.2884, -77.2039, "cdp"),
    ("Takoma Park", 38.9779, -77.0075, "city"),
    ("Kensington", 39.0257, -77.0764, "town"),
    ("Chevy Chase", 38.9810, -77.0839, "town"),
    ("Leisure World", 39.1017, -77.0700, "community"),
    ("Colesville", 39.0757, -77.0000, "cdp"),
    ("Burtonsville", 39.1110, -76.9325, "cdp"),
    ("White Oak", 39.0398, -76.9933, "cdp"),
    ("Clarksburg", 39.2387, -77.2795, "cdp"),
    ("Poolesville", 39.1457, -77.4169, "town"),
    ("Four Corners", 39.0204, -77.0128, "cdp"),
    ("Fairland", 39.0760, -76.9578, "cdp"),
    ("Montgomery Village", 39.1768, -77.1953, "cdp"),
    ("North Bethesda", 39.0446, -77.1189, "cdp"),
    ("Garrett Park", 39.0382, -77.0931, "town"),

    # Carroll County
    ("Westminster", 39.5754, -76.9958, "city"),
    ("Taneytown", 39.6579, -77.1745, "city"),
    ("Mount Airy", 39.3762, -77.1547, "town"),
    ("Manchester", 39.6612, -76.8850, "town"),
    ("Hampstead", 39.6046, -76.8500, "town"),
    ("Sykesville", 39.3746, -76.9678, "town"),
    ("New Windsor", 39.5418, -77.1081, "town"),
    ("Union Bridge", 39.5696, -77.1781, "town"),
    ("Eldersburg", 39.4037, -76.9503, "cdp"),

    # Frederick County
    ("Frederick", 39.4143, -77.4105, "city"),
    ("New Market", 39.3832, -77.2727, "town"),
    ("Thurmont", 39.6237, -77.4108, "town"),
    ("Brunswick", 39.3143, -77.6278, "city"),
    ("Middletown", 39.4432, -77.5447, "town"),
    ("Urbana", 39.3257, -77.3514, "cdp"),
    ("Walkersville", 39.4862, -77.3519, "town"),

    # Prince George's County
    ("College Park", 38.9807, -76.9369, "city"),
    ("Greenbelt", 38.9996, -76.8753, "city"),
    ("Hyattsville", 38.9560, -76.9455, "city"),
    ("Bowie", 38.9429, -76.7303, "city"),
    ("Laurel", 39.0993, -76.8483, "city"),
    ("Langley Park", 38.9888, -76.9814, "cdp"),
    ("Adelphi", 39.0032, -76.9719, "cdp"),
    ("Calverton", 39.0576, -76.9353, "cdp"),

    # Howard County
    ("Columbia", 39.2037, -76.8610, "cdp"),
    ("Ellicott City", 39.2673, -76.7983, "cdp"),
    ("Elkridge", 39.2126, -76.7136, "cdp"),

    # Baltimore County / City
    ("Baltimore", 39.2904, -76.6122, "city"),
    ("Towson", 39.4015, -76.6019, "cdp"),
    ("Dundalk", 39.2507, -76.5205, "cdp"),
    ("Catonsville", 39.2721, -76.7319, "cdp"),
    ("Pikesville", 39.3743, -76.7225, "cdp"),
    ("Owings Mills", 39.4196, -76.7803, "cdp"),
    ("Reisterstown", 39.4696, -76.8294, "cdp"),

    # Anne Arundel County
    ("Annapolis", 38.9784, -76.4922, "city"),
    ("Glen Burnie", 39.1626, -76.6247, "cdp"),
    ("Severna Park", 39.0704, -76.5452, "cdp"),
    ("Odenton", 39.0840, -76.7003, "cdp"),
    ("Crofton", 39.0018, -76.6875, "cdp"),

    # Other notable places
    ("Ocean City", 38.3365, -75.0849, "town"),
    ("Salisbury", 38.3607, -75.5994, "city"),
    ("Hagerstown", 39.6418, -77.7200, "city"),
    ("Cumberland", 39.6529, -78.7625, "city"),
    ("Easton", 38.7743, -76.0763, "town"),
    ("Cambridge", 38.5632, -76.0788, "city"),
]

# Create a function to find which district a point is in
from shapely.geometry import Point

def get_district_for_point(lat, lon, districts_gdf):
    point = Point(lon, lat)
    for idx, row in districts_gdf.iterrows():
        if row['geometry'].contains(point):
            return int(row['District'])
    return None

# Add community markers layer
community_layer = folium.FeatureGroup(name='Communities & Municipalities', show=True)

for name, lat, lon, comm_type in communities:
    district = get_district_for_point(lat, lon, districts_dissolved)

    if district is None:
        continue  # Skip if outside Maryland districts

    color = district_colors.get(district, '#808080')

    # Different icons for different types
    if comm_type == 'city':
        icon = folium.Icon(color='darkblue', icon='building', prefix='fa')
        radius = 8
    elif comm_type == 'town':
        icon = folium.Icon(color='blue', icon='home', prefix='fa')
        radius = 6
    elif name == 'Leisure World':
        icon = folium.Icon(color='red', icon='star', prefix='fa')
        radius = 8
    else:  # cdp or community
        icon = None
        radius = 5

    # Create popup with district info
    popup_html = f"""
    <div style="font-family: Arial; min-width: 150px;">
        <b style="font-size: 14px;">{name}</b><br>
        <span style="color: {color}; font-weight: bold;">District {district}</span><br>
        <span style="font-size: 11px; color: #666;">{comm_type.upper()}</span>
    </div>
    """

    if icon:
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=f"{name} (District {district})",
            icon=icon
        ).add_to(community_layer)
    else:
        # Use circle marker for CDPs
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color='#333',
            fill=True,
            fillColor=color,
            fillOpacity=0.8,
            weight=2,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=f"{name} (District {district})"
        ).add_to(community_layer)

community_layer.add_to(m)
print(f"Added {len(communities)} community markers")

# Add layer control
folium.LayerControl(collapsed=False).add_to(m)
Fullscreen().add_to(m)

# Convert districts to JSON for JavaScript
districts_json = districts_dissolved.to_json()

# Get the map variable name from folium
map_name = m.get_name()

# Custom HTML/JS for address lookup using Census Bureau Geocoder
address_lookup_html = f'''
<div id="address-panel" style="
    position: fixed;
    top: 10px;
    left: 50px;
    z-index: 9999;
    background: white;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    font-family: Arial, sans-serif;
    max-width: 420px;
">
    <h3 style="margin: 0 0 10px 0; color: #333;">Maryland Congressional Redistricting Proposal</h3>
    <p style="margin: 0 0 10px 0; font-size: 12px; color: #666;">DKunes Submission</p>

    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #ddd;">
        <label style="font-weight: bold; display: block; margin-bottom: 5px;">Find Your District:</label>
        <input type="text" id="street-input" placeholder="Street address (e.g., 100 State Circle)" style="
            width: 100%;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 14px;
            box-sizing: border-box;
            margin-bottom: 8px;
        ">
        <input type="text" id="city-input" placeholder="City (e.g., Annapolis)" style="
            width: 48%;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 14px;
            box-sizing: border-box;
            margin-right: 4%;
        ">
        <input type="text" id="zip-input" placeholder="ZIP (optional)" style="
            width: 48%;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 14px;
            box-sizing: border-box;
        ">
        <button id="search-btn" style="
            margin-top: 10px;
            padding: 10px 16px;
            background: #377eb8;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            width: 100%;
        ">Search</button>
        <p style="margin: 8px 0 0 0; font-size: 11px; color: #888;">Or click anywhere on the map to find that location's district</p>
        <div id="result" style="margin-top: 10px; padding: 10px; display: none; border-radius: 4px;"></div>
    </div>
</div>

<script>
(function() {{
    // Wait for everything to load
    window.addEventListener('load', function() {{
        setTimeout(initAddressLookup, 1000);
    }});

    function initAddressLookup() {{
        var mapObj = {map_name};
        if (!mapObj) {{
            console.error('Map not found');
            return;
        }}
        console.log('Map ready');

        var districtBoundaries = {districts_json};
        var districtColors = {{
            1: '#e41a1c', 2: '#377eb8', 3: '#4daf4a', 4: '#984ea3',
            5: '#ff7f00', 6: '#ffff33', 7: '#a65628', 8: '#f781bf'
        }};
        var addressMarker = null;

        // Point in polygon check
        function pointInPolygon(point, polygon) {{
            var x = point[0], y = point[1];
            var inside = false;
            for (var i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {{
                var xi = polygon[i][0], yi = polygon[i][1];
                var xj = polygon[j][0], yj = polygon[j][1];
                if (((yi > y) != (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) {{
                    inside = !inside;
                }}
            }}
            return inside;
        }}

        function findDistrict(lng, lat) {{
            var point = [lng, lat];
            for (var i = 0; i < districtBoundaries.features.length; i++) {{
                var feature = districtBoundaries.features[i];
                var geom = feature.geometry;
                var district = feature.properties.District;
                if (geom.type === 'Polygon') {{
                    if (pointInPolygon(point, geom.coordinates[0])) return district;
                }} else if (geom.type === 'MultiPolygon') {{
                    for (var j = 0; j < geom.coordinates.length; j++) {{
                        if (pointInPolygon(point, geom.coordinates[j][0])) return district;
                    }}
                }}
            }}
            return null;
        }}

        function showResult(lat, lng, displayName) {{
            var resultDiv = document.getElementById('result');
            var district = findDistrict(lng, lat);

            if (addressMarker) mapObj.removeLayer(addressMarker);

            if (district !== null) {{
                var color = districtColors[district] || '#808080';
                resultDiv.style.display = 'block';
                resultDiv.style.background = color + '40';
                resultDiv.innerHTML = '<strong style="font-size: 20px; color: ' + color + ';">District ' + district + '</strong><br>' +
                    '<span style="font-size: 11px; color: #555;">' + displayName + '</span>';
                addressMarker = L.marker([lat, lng]).addTo(mapObj);
                addressMarker.bindPopup('<b style="color:' + color + '; font-size: 16px;">District ' + district + '</b><br>' + displayName).openPopup();
            }} else {{
                resultDiv.style.display = 'block';
                resultDiv.style.background = '#fff3cd';
                resultDiv.innerHTML = 'Location is outside the district boundaries.<br><span style="font-size: 11px;">' + displayName + '</span>';
                addressMarker = L.marker([lat, lng]).addTo(mapObj);
                addressMarker.bindPopup('<b>Location</b><br>' + displayName).openPopup();
            }}
            mapObj.setView([lat, lng], 13);
        }}

        function lookupAddress() {{
            var street = document.getElementById('street-input').value.trim();
            var city = document.getElementById('city-input').value.trim();
            var zip = document.getElementById('zip-input').value.trim();
            var resultDiv = document.getElementById('result');

            if (!street) {{
                resultDiv.style.display = 'block';
                resultDiv.style.background = '#fff3cd';
                resultDiv.innerHTML = 'Please enter a street address.';
                return;
            }}

            if (!city && !zip) {{
                resultDiv.style.display = 'block';
                resultDiv.style.background = '#fff3cd';
                resultDiv.innerHTML = 'Please enter a city or ZIP code.';
                return;
            }}

            resultDiv.style.display = 'block';
            resultDiv.style.background = '#e7f3ff';
            resultDiv.innerHTML = 'Searching...';

            // Build Census Geocoder URL
            var url = 'https://geocoding.geo.census.gov/geocoder/locations/address?' +
                'street=' + encodeURIComponent(street) +
                '&city=' + encodeURIComponent(city) +
                '&state=MD' +
                (zip ? '&zip=' + encodeURIComponent(zip) : '') +
                '&benchmark=Public_AR_Current&format=json';

            // Use JSONP approach via script tag to avoid CORS
            var callbackName = 'geocodeCallback' + Date.now();
            window[callbackName] = function(data) {{
                delete window[callbackName];
                document.body.removeChild(script);

                if (data.result && data.result.addressMatches && data.result.addressMatches.length > 0) {{
                    var match = data.result.addressMatches[0];
                    var lat = match.coordinates.y;
                    var lng = match.coordinates.x;
                    var displayName = match.matchedAddress;
                    showResult(lat, lng, displayName);
                }} else {{
                    resultDiv.style.background = '#f8d7da';
                    resultDiv.innerHTML = 'Address not found. Please check the address and try again.';
                }}
            }};

            // Try multiple CORS proxies in sequence
            var proxies = [
                'https://corsproxy.io/?' + encodeURIComponent(url),
                'https://api.codetabs.com/v1/proxy?quest=' + encodeURIComponent(url),
                'https://proxy.cors.sh/' + url
            ];

            function tryProxy(index) {{
                if (index >= proxies.length) {{
                    resultDiv.style.background = '#f8d7da';
                    resultDiv.innerHTML = 'Unable to lookup address. Please click on the map instead.';
                    return;
                }}

                fetch(proxies[index])
                    .then(function(response) {{
                        if (!response.ok) throw new Error('Proxy ' + index + ' failed');
                        return response.json();
                    }})
                    .then(function(data) {{
                        if (data.result && data.result.addressMatches && data.result.addressMatches.length > 0) {{
                            var match = data.result.addressMatches[0];
                            var lat = match.coordinates.y;
                            var lng = match.coordinates.x;
                            var displayName = match.matchedAddress;
                            showResult(lat, lng, displayName);
                        }} else {{
                            resultDiv.style.background = '#f8d7da';
                            resultDiv.innerHTML = 'Address not found. Please check the address and try again.';
                        }}
                    }})
                    .catch(function(error) {{
                        console.log('Proxy ' + index + ' failed:', error.message);
                        tryProxy(index + 1);
                    }});
            }}

            tryProxy(0);
        }}

        // Click on map to find district
        mapObj.on('click', function(e) {{
            var lat = e.latlng.lat;
            var lng = e.latlng.lng;
            showResult(lat, lng, 'Lat: ' + lat.toFixed(5) + ', Lng: ' + lng.toFixed(5));
        }});

        // Event listeners
        document.getElementById('search-btn').addEventListener('click', lookupAddress);
        document.getElementById('street-input').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{ e.preventDefault(); lookupAddress(); }}
        }});
        document.getElementById('city-input').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{ e.preventDefault(); lookupAddress(); }}
        }});
        document.getElementById('zip-input').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{ e.preventDefault(); lookupAddress(); }}
        }});

        console.log('Address lookup initialized');
    }}
}})();
</script>
'''

# Add legend
legend_html = '''
<div style="position: fixed; bottom: 50px; right: 50px; width: 150px;
            border:2px solid grey; z-index:9999; font-size:14px;
            background-color:white; padding: 10px; border-radius: 5px;">
<b>Congressional Districts</b><br>
'''
for dist, color in sorted(district_colors.items()):
    legend_html += f'<i style="background:{color};width:20px;height:12px;display:inline-block;margin-right:5px;"></i> District {dist}<br>'
legend_html += '</div>'

m.get_root().html.add_child(folium.Element(address_lookup_html))
m.get_root().html.add_child(folium.Element(legend_html))

# Save the map
output_file = "/Users/davidkunes/Desktop/redistricting_map/DKunes_Redistricting_Map.html"
m.save(output_file)
print(f"\nMap saved to: {output_file}")

# Summary
print("\n=== Summary Statistics ===")
print(f"Total precincts: {len(precincts)}")
for dist in sorted(districts_dissolved['District'].dropna().unique()):
    block_count = len(districts_csv[districts_csv['District'] == dist])
    precinct_count = len(precincts[precincts['District'] == dist])
    print(f"District {int(dist)}: {block_count:,} blocks, {precinct_count} precincts")

print(f"\nFeatures:")
print("- Enter street address, city, and optional ZIP to search")
print("- Click anywhere on the map to find that location's district")
print("- Toggle precincts layer in the top-right control")

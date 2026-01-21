#!/usr/bin/env python3
"""
Join census block shapefile with district assignments and create an interactive map.
"""
import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import Fullscreen
import json

print("Loading census block shapefile...")
blocks = gpd.read_file("tl_2020_24_tabblock20.shp")
print(f"Loaded {len(blocks)} census blocks")
print(f"Shapefile columns: {list(blocks.columns)}")
print(f"Sample GEOID20 values: {blocks['GEOID20'].head().tolist()}")

print("\nLoading district assignments...")
districts = pd.read_csv("/Users/davidkunes/Desktop/DKunes_Submission.csv", dtype={'GEOID20': str, 'District': int})
print(f"Loaded {len(districts)} district assignments")
print(f"District assignments columns: {list(districts.columns)}")
print(f"Sample GEOID20 values: {districts['GEOID20'].head().tolist()}")
print(f"Districts in data: {sorted(districts['District'].unique())}")

print("\nJoining data...")
blocks_with_districts = blocks.merge(districts, on='GEOID20', how='left')
print(f"Joined records: {len(blocks_with_districts)}")
print(f"Records with district assignments: {blocks_with_districts['District'].notna().sum()}")
print(f"Records without district assignments: {blocks_with_districts['District'].isna().sum()}")

# Check for any blocks without districts
missing = blocks_with_districts[blocks_with_districts['District'].isna()]
if len(missing) > 0:
    print(f"\nWarning: {len(missing)} blocks have no district assignment")
    print(f"Sample missing GEOIDs: {missing['GEOID20'].head(10).tolist()}")

# Convert to WGS84 for web mapping
print("\nConverting to WGS84 coordinate system...")
blocks_with_districts = blocks_with_districts.to_crs(epsg=4326)

# Dissolve by district to create district boundaries (much smaller/faster)
print("\nDissolving blocks into district boundaries...")
districts_dissolved = blocks_with_districts.dissolve(by='District', as_index=False)
print(f"Created {len(districts_dissolved)} district polygons")

# Simplify geometries for faster rendering
print("Simplifying geometries for web display...")
districts_dissolved['geometry'] = districts_dissolved['geometry'].simplify(tolerance=0.001, preserve_topology=True)

# Color scheme for 8 congressional districts (Maryland has 8)
district_colors = {
    1: '#e41a1c',  # red
    2: '#377eb8',  # blue
    3: '#4daf4a',  # green
    4: '#984ea3',  # purple
    5: '#ff7f00',  # orange
    6: '#ffff33',  # yellow
    7: '#a65628',  # brown
    8: '#f781bf',  # pink
}

# Calculate center of Maryland for map
center_lat = blocks_with_districts.geometry.centroid.y.mean()
center_lon = blocks_with_districts.geometry.centroid.x.mean()

print(f"\nCreating interactive map centered at ({center_lat:.4f}, {center_lon:.4f})...")

# Create folium map
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=8,
    tiles='CartoDB positron'
)

# Add district polygons
def style_function(feature):
    district = feature['properties']['District']
    if district is None or pd.isna(district):
        return {
            'fillColor': '#808080',
            'color': '#000000',
            'weight': 2,
            'fillOpacity': 0.5
        }
    return {
        'fillColor': district_colors.get(int(district), '#808080'),
        'color': '#000000',
        'weight': 2,
        'fillOpacity': 0.6
    }

def highlight_function(feature):
    return {
        'fillColor': '#ffffff',
        'color': '#000000',
        'weight': 3,
        'fillOpacity': 0.8
    }

# Add GeoJson layer with tooltips
folium.GeoJson(
    districts_dissolved,
    name='Congressional Districts',
    style_function=style_function,
    highlight_function=highlight_function,
    tooltip=folium.GeoJsonTooltip(
        fields=['District'],
        aliases=['District:'],
        style='font-size: 14px; font-weight: bold;'
    )
).add_to(m)

# Add layer control and fullscreen button
folium.LayerControl().add_to(m)
Fullscreen().add_to(m)

# Add a legend
legend_html = '''
<div style="position: fixed;
            bottom: 50px; right: 50px; width: 150px;
            border:2px solid grey; z-index:9999; font-size:14px;
            background-color:white; padding: 10px;
            border-radius: 5px;">
<b>Congressional Districts</b><br>
'''
for dist, color in sorted(district_colors.items()):
    legend_html += f'<i style="background:{color};width:20px;height:12px;display:inline-block;margin-right:5px;"></i> District {dist}<br>'
legend_html += '</div>'
m.get_root().html.add_child(folium.Element(legend_html))

# Add title
title_html = '''
<div style="position: fixed;
            top: 10px; left: 50px; width: 400px;
            border:2px solid grey; z-index:9999; font-size:16px;
            background-color:white; padding: 10px;
            border-radius: 5px;">
<b>Maryland Congressional Redistricting Proposal</b><br>
<span style="font-size:12px;">DKunes Submission - Census Block Level</span>
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Save the map
output_file = "/Users/davidkunes/Desktop/redistricting_map/DKunes_Redistricting_Map.html"
m.save(output_file)
print(f"\nMap saved to: {output_file}")

# Also save the dissolved districts as GeoJSON for reference
geojson_file = "/Users/davidkunes/Desktop/redistricting_map/DKunes_Districts.geojson"
districts_dissolved.to_file(geojson_file, driver='GeoJSON')
print(f"District boundaries saved to: {geojson_file}")

# Print summary statistics
print("\n=== Summary Statistics ===")
for dist in sorted(districts_dissolved['District'].dropna().unique()):
    count = len(districts[districts['District'] == dist])
    print(f"District {int(dist)}: {count:,} census blocks")

print(f"\nTotal blocks assigned: {len(districts):,}")
print(f"\nOpen the HTML file in a web browser to view the interactive map!")

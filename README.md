# Maryland Congressional Redistricting Proposal

Interactive map visualization of a proposed congressional redistricting plan for Maryland.

## Features

- **8 Congressional Districts** - Color-coded boundaries at census block level
- **Voting Precincts** - Toggle 2,042 precinct boundaries
- **Community Markers** - 69 municipalities and major communities labeled with district assignments
- **Address Lookup** - Search any Maryland address to find its proposed district
- **Click-to-Find** - Click anywhere on the map to see that location's district

## Live Demo

View the interactive map: [Live on Netlify](https://your-netlify-url.netlify.app)

## Files

- `index.html` - Interactive map (main application)
- `CD8_Briefing_Memo.md` - Congressional briefing on District 8 changes
- `DKunes_Districts.geojson` - District boundaries as GeoJSON
- `create_enhanced_map.py` - Python script to regenerate the map

## District Summary

| District | Census Blocks | Precincts |
|----------|---------------|-----------|
| 1 | 16,729 | 325 |
| 2 | 9,951 | 243 |
| 3 | 8,443 | 235 |
| 4 | 6,664 | 221 |
| 5 | 8,977 | 229 |
| 6 | 13,966 | 251 |
| 7 | 10,629 | 343 |
| 8 | 8,468 | 195 |

## Data Sources

- Census block boundaries: U.S. Census Bureau TIGER/Line 2020
- Voting precincts: U.S. Census Bureau VTD 2020
- District assignments: DKunes_Submission.csv

## Author

David Kunes

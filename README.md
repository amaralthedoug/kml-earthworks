# kml-earthworks

A Streamlit app that turns KML access alignments (drawn in Google Earth) into terrain profiles and earthworks quantities (cut/fill), with interactive Plotly charts.

## Why this exists

Early-stage access roads and temporary alignments are often sketched quickly in Google Earth. Quantifying cut/fill typically becomes a manual spreadsheet + “copy coords” routine.

This tool lets you:

1. Draw one or more access lines in Google Earth
2. Export as KML (one or many files)
3. Upload to the app
4. Automatically extract coordinates, enrich with elevation, compute slopes/chainage, and estimate cut/fill volumes
5. Review results via interactive plots and export tables

## What the app does (end-to-end)

### 1) Upload

* Upload **one or more KML files**.
* Each **LineString** is treated as an **Access** (alignment).

### 2) Parse & station

* Extract WGS84 coordinates (lat/lon) from each LineString.
* Build **chainage (stationing)** and compute **stakes every 20 m**.
* Detect and label **segments (trechos)** for reporting.

### 3) Elevation enrichment

* Query an elevation source for each coordinate and attach:

  * `z_terrain_m`

### 4) Geometry + parameters

User selects via sliders/inputs:

* **Road width (m)**
* **Max slope (%)** (longitudinal)
* **Target/grade rules** (simple constrained grade line)
* **Side slopes** (cut and fill)
* **Shrink/Swell factor** (optional)

### 5) Compute

For each station:

* `z_grade_m`
* `cut_height_m`, `fill_height_m`
* `cut_area_m2`, `fill_area_m2`
* `cut_vol_m3`, `fill_vol_m3` (incremental + cumulative)

### 6) Visualize

Plotly charts:

* **Plan view (map)** of the alignment(s)
* **Profile** (terrain vs grade)
* **Cut/Fill bars** along chainage
* **Mass diagram** (cumulative cut/fill; balance)
* **3D plot** (alignment with terrain/grade)

### 7) Review tables

* Show a **DataFrame per segment (trecho)** inside an **expander**.
* Provide **pill-style filters** (segments, access, station ranges, cut/fill only, etc.).

### 8) Summaries

For each segment (trecho):

* Length (m)
* Total cut (m³)
* Total fill (m³)
* Net balance
* **Borrow (emprestimo)** and **Waste (bota-fora)** estimates

## Outputs

### Per-point / per-station table

Recommended columns:

* `file_name`
* `access_id`
* `segment_id`
* `station_m`
* `stake_20m` (boolean)
* `lat`, `lon`
* `z_terrain_m`
* `z_grade_m`
* `slope_pct`
* `cut_height_m`, `fill_height_m`
* `cut_area_m2`, `fill_area_m2`
* `cut_vol_m3`, `fill_vol_m3`
* `cut_vol_cum_m3`, `fill_vol_cum_m3`

### Per-segment summary

* `file_name`, `access_id`, `segment_id`
* `length_m`
* `cut_total_m3`, `fill_total_m3`
* `net_m3` (cut - fill)
* `borrow_m3` (if fill > cut)
* `waste_m3` (if cut > fill)

### Export

* CSV exports for both detailed and summary tables
* Optional HTML report export (later)

## Streamlit UI (Mockups)

These mockups describe the intended screens and layout. They are not final styling—just structure and components.

---

### Screen 1 — Upload & Inputs

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ kml-earthworks                                                             │
│ KML → Profiles → Cut/Fill Volumes                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ [Upload KML files]  (drag & drop)                                          │
│  • Accepts: .kml (multiple)                                                │
│  • Each LineString becomes one Access alignment                             │
│                                                                             │
│ Detected alignments                                                        │
│  □ access_01 (file: access_a.kml)     length: 1,284 m                       │
│  □ access_02 (file: access_a.kml)     length:   612 m                       │
│  □ access_01 (file: access_b.kml)     length:   945 m                       │
│ [Process selected]                                                         │
│                                                                             │
│ Parameters                                                                 │
│  Road width (m)           [ slider 3.0 ─────────────── 12.0 ] (6.0)         │
│  Max slope (%)            [ slider 2 ──────────────── 20 ] (16)             │
│  Cut side slope (H:V)     [ slider 1.0 ────────────── 3.0 ] (1.5)           │
│  Fill side slope (H:V)    [ slider 1.0 ────────────── 3.0 ] (2.0)           │
│  Shrink/Swell factor      [ slider 0.90 ───────────── 1.30 ] (1.125)        │
│  Stake interval (m)       [ fixed: 20 ]                                     │
│                                                                             │               │
│ [Run analysis]                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

Content notes (what the screen explains, in plain English):

* “Draw one or more lines in Google Earth, export as KML, and upload here.”
* “The app detects each LineString as an access alignment and extracts coordinates automatically.”

---

### Screen 2 — Map (Plan View) + Key Results

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Results: Plan View                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ [Plotly Map]                                                               │
│  • Alignments in different colors                                          │
│  • Hover shows: station, lat, lon, z_terrain, z_grade, cut/fill            │
│                                                                             │
│ KPI Cards                                                                  │
│  Total length: 2,841 m   Cut: 12,430 m³   Fill: 10,980 m³   Balance: +1,450 │
│  Borrow: 0 m³            Waste: 1,450 m³                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Screen 3 — Profile (Terrain vs Grade)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Results: Profile                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Filters                                                                    │
│  Access: [dropdown]  Segment: [pills]  Station range: [min/max]            │
│                                                                             │
│ [Plotly Profile]                                                           │
│  • Terrain line (z_terrain)                                                 │
│  • Grade line (z_grade)                                                     │
│  • Stakes every 20 m marked as vertical ticks                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Screen 4 — Cut/Fill Volumes + Mass Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Results: Volumes                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ [Plotly Bars] Cut/Fill along chainage                                      │
│  • Bars show incremental cut and fill per station interval                 │
│                                                                             │
│ [Plotly Mass Diagram]                                                      │
│  • Cumulative cut and fill curves                                          │
│  • Net balance line (borrow vs waste)                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Screen 5 — 3D View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Results: 3D                                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ [Plotly 3D]                                                                 │
│  • Alignment as 3D polyline                                                 │
│  • Terrain points and grade line                                            │
│  • Optional: surface mesh later                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Screen 6 — Tables (Expander) + Segment Summaries

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Tables                                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Segment summaries                                                          │
│  access_01 / seg_01  length 640 m  cut 3,210  fill 2,870  waste 340         │
│  access_01 / seg_02  length 644 m  cut 2,110  fill 2,840  borrow 730        │
│  access_02 / seg_01  length 612 m  cut 1,980  fill 1,120  waste 860         │
│                                                                             │
│ ▸ Detailed table (expand)                                                   │
│    Filters: [Access pills] [Segment pills] [Cut only] [Fill only]           │
│    [DataFrame] station, z_terrain, z_grade, slope, cut/fill, volumes...     │
│                                                                             │
│ Downloads                                                                  │
│  [Download detailed CSV]   [Download segment summary CSV]                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Suggested repo structure

```
.
├── app/
│   └── streamlit_app.py
├── src/
│   ├── io_kml.py              # parse KML, extract LineStrings
│   ├── stationing.py          # chainage, 20m stakes
│   ├── elevation.py           # elevation enrichment
│   ├── grade.py               # constrained grade logic
│   ├── earthworks.py          # areas + volumes + mass balance
│   ├── segments.py            # segment rules + per-segment summaries
│   └── plots.py               # plotly figures
├── data/
│   └── sample/                # sanitized only
├── requirements.txt
└── README.md
```

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt

streamlit run app/streamlit_app.py
```

## Status

* Prototype: implemented in notebook
* Packaging: in progress (migrating to src/ modules)
* UI: Streamlit + Plotly

## Disclaimer

This tool is intended for early-stage estimation and fast iteration.
Validate final quantities against approved survey surfaces/DTMs and project standards.

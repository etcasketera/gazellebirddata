# BirdSight Analytics: AudioMoth Processing for Biodiversity Monitoring

## What is the project?

BirdSight Analytics is a dual-modality data engineering project designed to automate biodiversity monitoring for carbon credit certification. It translates raw AudioMoth field recordings into standardized ecological health metrics (Hill Numbers) required by the **Plan Vivo (PV Nature) Standard** and prepares data for visualizations to track ecosystem health.

---

## Table of Contents

* [Option 1: Interactive Researcher Dashboard (`bird_app.py`)](#option-1-interactive-researcher-dashboard-bird_apppy)
* [Installation & Requirements](#installation--requirements)
* [How to Use](#how-to-use)
* [What the Code is Doing](#what-the-code-is-doing)


* [Option 2: Production ETL & Power BI Pipeline (`bird_analysis.py`)](#option-2-production-etl--power-bi-pipeline-bird_analysispy)
* [Installation & Requirements](#installation--requirements-1)
* [How to Use](#how-to-use-1)
* [What the Code is Doing](#what-the-code-is-doing-1)


* [Scientific Metrics (The Three Pillars)](#scientific-metrics-the-three-pillars)
* [Lessons Learned](#lessons-learned)
* [Next Steps](#next-steps)
* [Acknowledgements](#acknowledgements)

---

### Implementation Note

To ensure the links work correctly, make sure your section headers in the README look like this:
`## What is the Project?`
Markdown automatically creates anchors by converting the text to lowercase and replacing spaces with hyphens (e.g., `#what-is-the-project`).

**Would you like me to generate the full, final README file with this Table of Contents integrated so you can simply copy and paste it?**
---

## Option 1: Interactive Researcher Dashboard (`bird_app.py`)

A self-contained Streamlit web application designed for rapid prototyping, individual file analysis, and visual exploration of taxonomic relationships.

### Installation & Requirements

* **Python 3.9+**
* **FFmpeg**: Required for audio decoding.


* **Dependencies**: `pip install pandas streamlit plotly birdnetlib pygbif`.


* **Models**: BirdNET TFLite model and labels must be in the `/models` directory.



### How to Use

1. Run the app: `streamlit run bird_app.py`.
2. Enter the local path to your audio folder. You can find this by going to the audio folder and right-clicking on the name, then selecting "Copy as path".
3. Use the sidebar to filter by confidence score or specific species.
4. Explore the **Taxonomic Landscape Heatmap** to see distances between detected species.



### What the Code is Doing

* **Dynamic Analysis**: Uses `birdnetlib` to analyze files and stores results in `st.session_state` to prevent data loss during filter changes.


* **API Integration**: Originally used the **GBIF API** (`pygbif`) to fetch higher-level taxonomy (Order/Family) for species not in the local cache.


* **Visualization**: Generates Plotly heatmaps to visualize the "path length" between species based on taxonomic distance weights.



---

## Option 2: Production ETL & Power BI Pipeline (`bird_analysis.py`)

A CLI-based engine built for high-volume batch processing and standardized reporting.

### Installation & Requirements

* **Standard Python Environment** or the bundled **.exe** (if distributed).
* **Taxonomy Master**: Requires `assets/taxonomy_master.csv` for high-speed local lookups.


* **Power BI Desktop**: To open the `birdanalysis.pbix` template.



### How to Use

1. Run the script: `python bird_analysis.py`.
2. Select the source folder via the GUI pop-up.


3. The script outputs `bird_analysis_results.csv` into the source folder.


4. Open the **Power BI Dashboard** and click "Refresh" to populate the templated reports with the new data.



### What the Code is Doing

* **Optimized ETL**: Replaces slow API calls with a local dictionary lookup (`tax_dict`) to map species to their Genus, Family, and Order instantly.


* **Time-Series Extraction**: Parses AudioMoth filenames (e.g., `20240101_120000.WAV`) to create a `Datetime` object for Power BI Time Intelligence.


* **Resource Pathing**: Uses a `resource_path` helper to ensure the script can find assets even when bundled as a standalone executable.



---

## Scientific Metrics (The Three Pillars)

The project utilizes the **Hill Number framework** to quantify ecosystem health at a species level.

1. **Pillar 1: Species Richness ($q=0$)**: The total count of unique species. Essential for baseline ecosystem health.


2. **Pillar 2: Species Diversity ($q=1$)**: Measures the distribution of relative abundance. As a site recovers, this distribution becomes less skewed.


3. **Pillar 3: Taxonomic Dissimilarity ($\Delta^*$)**: Measures the taxonomic "spread."
* **Logic**: We assign a "path length" (distance) between species. Same genus = 20, same family = 40, same order = 60, different order = 100.


* **Reasoning**: A healthy ecosystem supports a wide variety of life across different taxonomic groups, not just many species within a single group.





---

## Lessons Learned

* **API vs. Local Storage**: Moving from GBIF API calls to a local CSV drastically reduced latency and made the tool viable for field use.


* **UI Flexibility**: Power BI is significantly more fluid for creating complex filters and shareable reports than a locally-hosted Streamlit dashboard.


* **Architecture**: Designing for the "eventual .exe" early on (using `sys._MEIPASS`) is critical for tools meant for non-technical stakeholders.



---

## Next Steps

* **Full BirdNET Integration**: Implementing the complete BirdNET model for more robust batch processing and higher detection accuracy.


* **Standalone Distribution**: Finalizing the conversion of `bird_analysis.py` into a distributable `.exe` via PyInstaller.


* **Cloud Scalability**: Transitioning to cloud storage and computing to allow Gazelle Ecosolutions teams to access data and processing power globally.


## Acknowledgements

This project is built upon the incredible work of the open-source conservation and data science communities:

* **BirdNET & BirdNET-Analyzer**: For the machine learning models and signal processing capabilities that drive the detection engine.
* **Birdnetlib**: For the Python interface that enables scalable batch processing.
* **Streamlit**: For providing the framework that powered the initial interactive prototype and dashboard.
* **GBIF (Global Biodiversity Information Facility)**: For the `pygbif` Python client and access to the world’s taxonomic backbone.
* **eBird / Clements Checklist**: For providing the foundational taxonomic records and checklists used to build the local taxonomy master files.
* **Plan Vivo (PV Nature)**: For the scientific methodology and metrics framework that guided the design of this monitoring tool.


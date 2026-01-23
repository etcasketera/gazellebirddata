# Project Understanding

## Overview
This project is a **Bird Observation Dashboard** built with **Streamlit**. It analyzes audio recordings (`.WAV` files) using **BirdNET** (via `birdnetlib`) to detect and identify bird species.

## Key Components
*   **`bird_app.py`**: The main application file. It handles:
    *   Scanning folders for audio files.
    *   Analyzing audio using `birdnetlib.analyzer.Analyzer`.
    *   Visualizing results using `streamlit` and `plotly`.
*   **Data Handling**:
    *   Reads/writes detection results to CSV (e.g., `birdnet_results.csv`).
    *   Uses a temporary file `bird_data_temp.csv` for initial data exploration.
*   **Dependencies**:
    *   `streamlit`, `pandas`, `plotly`, `birdnetlib`, `birdnet`, `librosa`.

## Usage
1.  Install dependencies: `pip install -r requirements.txt`
2.  Run the app: `streamlit run bird_app.py`
3.  Input the folder path containing `.WAV` files (e.g., `./test_data`).
4.  Load existing analysis or start a new one.

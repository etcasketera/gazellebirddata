import streamlit as st
import pandas as pd
import plotly.express as px
import io
import tempfile
import os
import birdnetlib
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
import base64

def load_font(font_path):
    with open(font_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return data

st.image("gazelle_logo.png", width=200)
# --- 1. DASHBOARD CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Bird Sighting Analytics", page_icon="🦅")
st.markdown("""
    <style>
    /* Change background of the main app */
    .stApp {
        background-color: #F7F7F1; 
    }
    /* Change sidebar color */
    [data-testid="stSidebar"] {
        background-color: #B07D70;
        border-right: 1px solid #30363D;
    }

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #071B0B;
    }
    
    </style>
    """, unsafe_allow_html=True)

def analyze_audio(analyzer, uploaded_file, lat=None, lon=None, date=None):

    recording = Recording(
        analyzer,
        uploaded_file,
        lat=lat,
        lon=lon,
        date=date,
        min_conf=.1
    )

    recording.analyze()
    return recording.detections

def timest(row):
    return row[:-4]



def run_bird_dashboard(df):
    
    # --- 2. DATA PROCESSING ---
    # Convert string timestamps to datetime objects
    df['start'] = pd.to_datetime(df['timestamp_str'], format='%Y%m%d_%H%M%S')
    df['end'] = df['start'] + pd.to_timedelta(df['duration'], unit='s')
    df['time_minute'] = df['start'].dt.strftime('%H:%M')
    
    # --- 3. SIDEBAR CONTROLS ---
    st.sidebar.title("Filter Sightings")
    
    # Confidence Slider
    min_conf = st.sidebar.slider("Minimum Confidence Score", 0.0, 1.0, 0.5, 0.01)
    
    # Species Selection
    # --- SIDEBAR: SPECIES FILTER WITH SELECT ALL/NONE ---
    with st.sidebar:
        st.header("Species Filter")
        
        # Get the unique species list
        all_species = sorted(df['species'].unique().tolist())

        # Create two columns for the buttons
        col1, col2 = st.columns(2)
        
        # "Select All" Logic
        if col1.button("Select All"):
            st.session_state["selected_birds"] = all_species
            
        # "Clear All" Logic
        if col2.button("Clear All"):
            st.session_state["selected_birds"] = []

        # The Multiselect Widget
        # It looks for 'selected_birds' in session_state; if not there, defaults to all
        selected_species = st.multiselect(
            "Choose Species:",
            options=all_species,
            key="selected_birds",
            default=all_species[:5] # Initial default when the app first loads
        )

    # --- 4. GLOBAL FILTERING LOGIC ---
    mask = (df['confidence'] >= min_conf) & (df['species'].isin(selected_species))
    filtered_df = df[mask].copy()

    # --- 5. DASHBOARD HEADER & METRICS ---
    st.title("🦅 Bird Observation Dashboard")
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Sightings", len(filtered_df))
    with m2:
        unique_birds = filtered_df['species'].nunique()
        st.metric("Unique Species", unique_birds)
    with m3:
        avg_dur = filtered_df['duration'].mean() if not filtered_df.empty else 0
        st.metric("Avg. Observation", f"{avg_dur:.1f}s")

    # --- 6. TABBED INTERFACE ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Species Volume", 
        "📈 Minute-by-Minute", 
        "⏱️ Behavior Timeline",
        "📥 Export Report"
    ])

    # TAB 1: Bar Chart (Top 20)
    with tab1:
        st.subheader("Top Species Counts")
        top_20 = filtered_df['species'].value_counts().head(20).reset_index()
        top_20.columns = ['Species', 'Count']
        if not top_20.empty:
            st.bar_chart(data=top_20, x='Species', y='Count', color="#2ca02c")
        else:
            st.info("Adjust filters to see data.")

    # TAB 2: Activity Trend (Line Chart with 0-filling)
    with tab2:
        st.subheader("Sightings per Minute")
        if not filtered_df.empty:
            # Grouping and ensuring chronological order
            minute_counts = filtered_df.groupby(['time_minute', 'species']).size().reset_index(name='sightings')
            minute_counts = minute_counts.sort_values(by='time_minute')
            fig_trend = px.line(
                minute_counts, x="time_minute", y="sightings", color="species",
                markers=True, template="plotly_white", line_shape="linear"
            )
            fig_trend.update_layout(xaxis_title="Time (HH:MM)", yaxis_title="Sightings")
            fig_trend.update_xaxes(categoryorder='category ascending')
            fig_trend.update_yaxes(dtick=1, tickformat="d")
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No data available for the selected filters.")

    # TAB 3: Behavior Timeline (Gantt Chart)
    with tab3:
        st.subheader("Observation Durations")
        if not filtered_df.empty:
            fig_gantt = px.timeline(
                filtered_df, x_start="start", x_end="end", y="species", 
                color='species', 
                # template="plotly_white",
                title="Sighting Start and End Times",
                opacity=1
            )
            fig_gantt.update_yaxes(
                # showline=True, 
                # linewidth=2, 
                # linecolor='black',
                ticklen=50
                # tickwidth=3,
                # ticks='outside'
                # autorange="reversed"
            )
            # fig_gantt.update_layout(bargap = .3, xaxis_tickformat="%H:%M:%S")
            fig_gantt.update_xaxes(
                # showline=True, 
                # linewidth=2, 
                # linecolor='black',
                # ticklen=15
            )
            st.plotly_chart(fig_gantt, use_container_width=True)
        else:
            st.info("No data to display on timeline.")

    # TAB 4: Export Options
    with tab4:
        st.subheader("Download Research Data")
        
        # Prepare CSV
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        
        # Prepare HTML Chart Export (Trend Chart)
        if not filtered_df.empty:
            buffer = io.StringIO()
            # fig_trend.write_html(buffer, include_plotlyjs='cdn')
            # html_bytes = buffer.getvalue().encode()
            
            st.download_button("📥 Download CSV Data", data=csv, file_name="bird_data.csv", mime="text/csv")
            # st.download_button("📊 Download Interactive Trend Chart (HTML)", data=html_bytes, file_name="bird_trend.html")
        else:
            st.warning("Nothing to export.")

@st.cache_resource
def bird_model():
    return Analyzer()

@st.cache_data
def run_bulk_analysis(files):
    all_results = []
    if files:
        st.success(f"Successfully received {len(files)} files.")
    
    # Iterate through the uploaded files for BirdNET processing
    if files:
        progress_bar = st.progress(0)
        for i, filename in enumerate(files):
            # 1. Analyze file using birdnetlib
            analyzer = bird_model()
            records = analyze_audio(analyzer, filename)

            for record in records:
                print(filename[-19:])
                record['File'] = filename[-19:]
                all_results.append(record)
            
            # 2. Update Progress
            percent_complete = (i + 1) / len(files)
            progress_bar.progress(percent_complete)
            
    df_detections = pd.DataFrame(all_results)
    df_detections.rename(columns={'common_name':'species', 'confidence':'confidence'}, inplace=True)
    if not df_detections.empty:
        df_detections['timestamp_str'] = df_detections['File'].apply(timest)
        df_detections['duration'] = df_detections['end_time'] -  df_detections['start_time']

    return df_detections

if __name__ == "__main__":
    st.title("AudioMoth Bird Detection Analysis")
    # uploaded_files = st.file_uploader("Drop Audio File Here", type=["wav"], accept_multiple_files=True)
    folder_path = st.text_input('Input the path to your audio folder:','Right click folder name and select copy address')
    uploaded_files = []
    if st.button("Start Bulk Analysis"):
        if os.path.exists(folder_path):
            uploaded_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.WAV')]

    print(uploaded_files)
    df = run_bulk_analysis(uploaded_files)
    if not df.empty:
        run_bird_dashboard(df)
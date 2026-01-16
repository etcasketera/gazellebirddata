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

if 'df' not in st.session_state:
    st.session_state.df = None

def load_font(font_path):
    with open(font_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return data

load_font('./Lagom-Grotesk-Regular.otf')

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

    @font-face {{
            font-family: 'CompanyFont';
            src: url(data:font/ttf;base64,{data}) format('truetype');
        }}
        * {{ font-family: 'CompanyFont', sans-serif !important; }}

    html, body, [class*="css"] {
        font-family: 'CompanyFont', sans-serif;
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
        st.header("Date Range")
        # 1. Get min and max dates from the dataframe
        min_date = df['start'].min().date()
        max_date = df['start'].max().date()

        # 2. Create the date picker (returns a tuple of two dates)
        selected_dates = st.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        print_mode = st.sidebar.checkbox("Prepare for Print (Show all charts)")

        


    # --- 4. GLOBAL FILTERING LOGIC ---
    mask = (df['confidence'] >= min_conf) & (df['species'].isin(selected_species))
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
        date_mask = (df['start'].dt.date >= start_date) & (df['start'].dt.date <= end_date)
        # Update your existing mask to include this
        mask = mask & date_mask
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
    if print_mode:
        st.title("Full Research Report")
        # st.plotly_chart(fig_volume)
        st.plotly_chart(fig_trend)
        st.plotly_chart(fig_gantt)
        st.plotly_chart(fig_heat)
    else:
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Species Volume", 
            "Minute-by-Minute", 
            "Behavior Timeline",
            "Confidence Heatmap",
            "Export Report"
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
        # TAB 4: COnfidence Heatmap
        with tab4:
            st.subheader("Confidence vs. Time of Day")
        
            if not filtered_df.empty:
                # 1. Extract the hour from the timestamp
                filtered_df['hour'] = filtered_df['start'].dt.hour
                
                # 2. Create the heatmap
                fig_heat = px.density_heatmap(
                    filtered_df, 
                    x="hour", 
                    y="confidence", 
                    nbinsx=24, # One bin for every hour
                    nbinsy=10, # Divide confidence 0-1 into 10 slices
                    color_continuous_scale="Viridis",
                    labels={'hour': 'Hour of Day (24h)', 'confidence': 'Confidence Score'}
                )
                
                # 3. Apply branding font to the chart
                fig_heat.update_layout(font_family="CompanyFont")
                
                st.plotly_chart(fig_heat, use_container_width=True)
        # TAB 5: Export Options
        with tab5:
            st.subheader("Download Research Data")
            
            # Prepare CSV
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            
            # Prepare HTML Chart Export (Trend Chart)
            if not filtered_df.empty:
                buffer = io.StringIO()
                fig_trend.write_html(buffer, include_plotlyjs='cdn')
                html_bytes = buffer.getvalue().encode()
                
                st.download_button("📥 Download CSV Data", data=csv, file_name="bird_data.csv", mime="text/csv")

                st.download_button(
                    label="📊 Download Interactive Trend Chart",
                    data=html_bytes,
                    file_name="bird_trend_interactive.html",
                    mime="text/html"
                )
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
        analyzer = bird_model()
        for i, filename in enumerate(files):
            # 1. Analyze file using birdnetlib
            
            records = analyze_audio(analyzer, filename)

            for record in records:
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

@st.cache_data
def get_files_analysis(folder_path):
    uploaded_files = []
    if os.path.exists(folder_path):
        uploaded_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.WAV')]
    
    return uploaded_files

if __name__ == "__main__":
    
    # 1. Branding Header (Use your base64 logic here)
    st.title("🦅 AudioMoth Bird Detection Analysis")
    
    # 2. Input Section
    folder_path = st.text_input('Input audio folder path:', placeholder='./test_data')

    if folder_path and os.path.exists(folder_path):
        results_path = os.path.join(folder_path, 'birdnet_results.csv')
        if os.path.exists(results_path) and st.session_state.df is None:
            st.session_state.df = pd.read_csv(results_path)
        # Check if we should load the data
        if st.session_state.df is None:
            col1, col2 = st.columns(2)
            
            # Scenario A: CSV exists - Give them a "Load" button
            if os.path.exists(results_path):
                if col1.button("📂 Load Existing Analysis"):
                    st.session_state.df = pd.read_csv(results_path)
                    st.rerun()
            
            # Scenario B: No CSV or they want to re-run
            if col2.button("🚀 Start New Analysis"):
                files = get_files_analysis(folder_path)
                if files:
                    df_results = run_bulk_analysis(files)
                    if not df_results.empty:
                        df_results.to_csv(results_path, index=False)
                        st.session_state.df = df_results
                        st.rerun()
                else:
                    st.error("No .WAV files found in that folder.")
        
    # 3. Dashboard Display
    if st.session_state.df is not None:
        # Add a "Reset" button in the sidebar to clear state
        if st.sidebar.button("Reset Analysis"):
            del st.session_state.df
            st.rerun()
            
        run_bird_dashboard(st.session_state.df)
    else:
        st.info("Please enter a folder path and load data to view the dashboard.")
import streamlit as st
import pandas as pd
import plotly.express as px
import io

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
    }
    /* Change text color globally */
    html, body, [class*="css"]  {
        color: #071B0B;
    }
    </style>
    """, unsafe_allow_html=True)


def run_bird_dashboard(df):
    """
    Pass your dataframe into this function. 
    Assumes columns: 'species', 'confidence', 'timestamp_str', 'duration'
    Format of timestamp_str: 'YYYYMMDD_HHMMSS'
    """
    
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
                color="species", template="plotly_white",
                title="Sighting Start and End Times",
                opacity=1
            )
            fig_gantt.update_yaxes(
                showline=True, 
                linewidth=2, 
                linecolor='black',
                autorange="reversed"
            )
            fig_gantt.update_layout(bargap = .3, xaxis_tickformat="%H:%M:%S")
            fig_gantt.update_xaxes(
                showline=True, 
                linewidth=2, 
                linecolor='black', 
                gridcolor='rgba(0,0,0,0.1)'
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

# --- EXAMPLE USAGE ---
# If you are running this as a standalone script:
if __name__ == "__main__":
    # Replace this with your actual data loading logic
    # df = pd.read_csv("your_file.csv")
    try:
        # Check if sample data exists from previous steps
        df_to_use = pd.read_csv("bird_data_temp.csv")
        run_bird_dashboard(df_to_use)
    except FileNotFoundError:
        st.error("Please ensure your bird data CSV is in the same directory.")
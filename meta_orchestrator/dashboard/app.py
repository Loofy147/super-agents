import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

# --- Configuration ---
RESULTS_DIR = "meta_orchestrator/results"
st.set_page_config(
    page_title="Meta-Orchestrator Dashboard",
    page_icon="🤖",
    layout="wide",
)

# --- Helper Functions ---
def get_past_runs():
    """Scans the results directory for past experiment runs."""
    if not os.path.exists(RESULTS_DIR):
        return []

    run_dirs = [d for d in os.listdir(RESULTS_DIR) if os.path.isdir(os.path.join(RESULTS_DIR, d)) and d.startswith("run_")]

    # Sort by timestamp, most recent first
    run_dirs.sort(key=lambda x: datetime.strptime(x, "run_%Y%m%d_%H%M%S"), reverse=True)
    return run_dirs

def load_run_data(run_dir):
    """Loads the summary and raw results from a specific run directory."""
    summary_path = os.path.join(RESULTS_DIR, run_dir, "summary.md")
    results_path = os.path.join(RESULTS_DIR, run_dir, "results.json")

    summary_content = ""
    if os.path.exists(summary_path):
        with open(summary_path, 'r') as f:
            summary_content = f.read()

    results_df = pd.DataFrame()
    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            raw_data = json.load(f)
            results_df = pd.json_normalize(raw_data)

    return summary_content, results_df

# --- Main Application ---
st.title("🤖 Meta-Orchestrator Dashboard")

# --- Sidebar for Navigation ---
st.sidebar.title("Navigation")
past_runs = get_past_runs()

if not past_runs:
    st.sidebar.warning("No past experiment runs found.")
    st.info("Run an experiment from the command line to see results here.")
    st.code("python3 -m meta_orchestrator.cli run -c config.yaml")
else:
    selected_run = st.sidebar.selectbox("Select a past run:", past_runs)

    # --- Display Area ---
    if selected_run:
        st.header(f"Results for: `{selected_run}`")
        summary_md, results_df = load_run_data(selected_run)

        if summary_md:
            st.subheader("📊 Summary Report")
            st.markdown(summary_md)
        else:
            st.warning("`summary.md` not found for this run.")

        if not results_df.empty:
            st.subheader("🔬 Raw Trial Data")
            st.dataframe(results_df)

            # Simple visualization example
            st.subheader("📈 Score by Variant")
            if 'score' in results_df.columns:
                chart_data = results_df[['variant', 'score']].dropna()
                st.bar_chart(chart_data.set_index('variant'))
            else:
                st.info("No 'score' column found in results to visualize.")

        else:
            st.warning("`results.json` not found or is empty for this run.")

# --- Placeholder for live view (to be implemented later) ---
st.sidebar.title("Live Experiment")
st.sidebar.info("Live monitoring features are under development.")
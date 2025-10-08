import streamlit as st
import pandas as pd
import os
import json
import yaml
import time
import subprocess
import sys
from datetime import datetime

# --- Configuration ---
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
LIVE_RUN_FILE = os.path.join(RESULTS_DIR, "live_run.jsonl")
TEMP_CONFIG_PATH = os.path.join(RESULTS_DIR, "dashboard_generated_config.yaml")

st.set_page_config(
    page_title="Meta-Orchestrator Command Center",
    page_icon="🤖",
    layout="wide",
)

# --- Helper Functions ---
@st.cache_data
def get_past_runs():
    """Scans the results directory for past experiment runs."""
    if not os.path.exists(RESULTS_DIR):
        return []
    run_dirs = [d for d in os.listdir(RESULTS_DIR) if d.startswith("run_") and os.path.isdir(os.path.join(RESULTS_DIR, d))]
    run_dirs.sort(key=lambda x: datetime.strptime(x, "run_%Y%m%d_%H%M%S"), reverse=True)
    return run_dirs

def run_experiment_in_background(config_path: str):
    """Launches the CLI experiment runner as a non-blocking background process."""
    command = [sys.executable, "-m", "meta_orchestrator.cli", "run", "-c", config_path]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    st.session_state['experiment_process'] = process
    st.session_state['is_running'] = True
    # Clear the live run file at the start of a new run
    if os.path.exists(LIVE_RUN_FILE):
        os.remove(LIVE_RUN_FILE)

def tail_live_results():
    """A generator that tails the live run file and yields new results."""
    if not os.path.exists(LIVE_RUN_FILE):
        return
    with open(LIVE_RUN_FILE, 'r') as f:
        while st.session_state.get('is_running', False):
            line = f.readline()
            if not line:
                # If the process has finished, break the loop
                if st.session_state.experiment_process.poll() is not None:
                    st.session_state['is_running'] = False
                    break
                time.sleep(0.1)
                continue
            yield json.loads(line)

# --- UI Sections ---
def show_experiment_builder():
    """UI for building a new experiment configuration."""
    st.header("🛠️ Experiment Builder")
    st.write("Design a new experiment using the form below. The generated YAML will be used to launch the run.")

    # Get available variants from the registry
    from meta_orchestrator.experiment_hub.registry import REGISTRY
    all_variants = list(REGISTRY.keys())

    with st.form("experiment_builder"):
        st.subheader("Orchestrator Settings")
        orchestrator_type = st.selectbox("Orchestrator Type", ["standard", "mab", "adversarial_benchmark"], index=0)

        config = {"orchestrator": {"type": orchestrator_type}}

        if orchestrator_type == "standard":
            st.subheader("Standard Experiment")
            exp_name = st.text_input("Experiment Name", "Dashboard Standard Run")
            variants = st.multiselect("Select Variants to Test", all_variants, default=all_variants[:2])
            trials = st.slider("Trials per Variant", 1, 100, 10)
            config["orchestrator"]["standard_settings"] = {
                "experiments": [{"name": exp_name, "enabled": True, "variants": variants, "trials_per_variant": trials}]
            }

        elif orchestrator_type == "mab":
            st.subheader("Multi-Armed Bandit Settings")
            variants = st.multiselect("Select Variants for MAB", all_variants, default=all_variants[:3])
            total_trials = st.slider("Total MAB Trials", 10, 500, 100)
            config["orchestrator"]["mab_settings"] = {"variants": variants, "total_trials": total_trials, "strategy": "thompson_sampling"}

        elif orchestrator_type == "adversarial_benchmark":
            st.subheader("Adversarial Benchmark Settings")
            adversary = st.selectbox("Select Adversary Variant", [v for v in all_variants if "adversarial" in v])
            targets = st.multiselect("Select Target Variants", [v for v in all_variants if "adversarial" not in v], default=[v for v in all_variants if "adversarial" not in v][:2])
            trials = st.slider("Adversarial Trials", 1, 50, 10)
            config["orchestrator"]["adversarial_settings"] = {"adversary_variant": adversary, "target_variants": targets, "trials_per_target": trials}

        st.subheader("Global Settings")
        config["scoring_weights"] = {
            "autonomy": st.slider("Autonomy Weight", -1.0, 1.0, 0.4),
            "success": st.slider("Success Weight", -1.0, 1.0, 0.35),
            "cost": st.slider("Cost Weight", -1.0, 1.0, -0.15),
            "latency": st.slider("Latency Weight", -1.0, 1.0, -0.1),
        }

        submitted = st.form_submit_button("Launch Experiment")
        if submitted:
            st.session_state['current_config'] = config
            with open(TEMP_CONFIG_PATH, 'w') as f:
                yaml.dump(config, f)
            run_experiment_in_background(TEMP_CONFIG_PATH)
            st.rerun()

def show_live_view():
    """UI for monitoring a live experiment."""
    st.header("🚀 Live Experiment Monitor")
    if not st.session_state.get('is_running', False):
        st.info("No experiment is currently running. Launch one from the 'Experiment Builder'.")
        return

    st.subheader("Live Performance")
    score_chart_placeholder = st.empty()
    choice_chart_placeholder = st.empty()
    results = []

    for result in tail_live_results():
        results.append(result)
        df = pd.DataFrame(results)

        # Update score chart
        if 'score' in df.columns:
            mean_scores = df.groupby('variant')['score'].mean().reset_index()
            score_chart_placeholder.bar_chart(mean_scores.set_index('variant'))

        # Update choice chart for MAB
        if st.session_state.current_config['orchestrator']['type'] == 'mab':
            choice_counts = df['variant'].value_counts().reset_index()
            choice_counts.columns = ['variant', 'count']
            choice_chart_placeholder.bar_chart(choice_counts.set_index('variant'))

    st.success("Experiment finished!")
    st.balloons()
    st.subheader("Final Results")
    st.dataframe(pd.DataFrame(results))
    st.session_state['is_running'] = False
    st.rerun() # Rerun to update the state

def show_past_runs():
    """UI for browsing past experiment runs."""
    st.header("🗂️ Past Experiment Runs")
    past_runs = get_past_runs()
    if not past_runs:
        st.warning("No past experiment runs found.")
        return

    selected_run = st.selectbox("Select a run to view:", past_runs)
    if selected_run:
        summary_path = os.path.join(RESULTS_DIR, selected_run, "summary.md")
        results_path = os.path.join(RESULTS_DIR, selected_run, "results.json")

        if os.path.exists(summary_path):
            with open(summary_path, 'r') as f:
                st.subheader("📊 Summary Report")
                st.markdown(f.read())

        if os.path.exists(results_path):
            with open(results_path, 'r') as f:
                st.subheader("🔬 Raw Trial Data")
                st.dataframe(pd.read_json(f))
        else:
            st.warning("No raw results data found for this run.")

# --- Main App Router ---
st.title("🤖 Meta-Orchestrator Command Center")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Live View", "Experiment Builder", "Past Runs"])

if page == "Live View":
    show_live_view()
elif page == "Experiment Builder":
    show_experiment_builder()
elif page == "Past Runs":
    show_past_runs()
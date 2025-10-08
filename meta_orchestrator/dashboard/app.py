import streamlit as st
import pandas as pd
import os
import json
import time
from datetime import datetime
from meta_orchestrator.experiment_hub.hub import load_config, run_experiment_suite
from meta_orchestrator.orchestrators.mab_orchestrator import StandardOrchestrator, MultiArmedBanditOrchestrator

# --- Configuration ---
RESULTS_DIR = "meta_orchestrator/results"
CONFIG_PATH = "config.yaml"
st.set_page_config(
    page_title="Meta-Orchestrator Dashboard",
    page_icon="🤖",
    layout="wide",
)

# --- Helper Functions ---
@st.cache_data
def get_past_runs():
    """Scans the results directory for past experiment runs."""
    if not os.path.exists(RESULTS_DIR):
        return []

    run_dirs = [d for d in os.listdir(RESULTS_DIR) if os.path.isdir(os.path.join(RESULTS_DIR, d)) and d.startswith("run_")]
    run_dirs.sort(key=lambda x: datetime.strptime(x, "run_%Y%m%d_%H%M%S"), reverse=True)
    return run_dirs

@st.cache_data
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
        results_df = pd.read_json(results_path)

    return summary_content, results_df

def run_live_experiment(config):
    """Runs an experiment and yields data for live updates."""
    # This is a simplified version of the hub's logic for dashboard use
    orchestrator_config = config.get('orchestrator', {})
    orchestrator_type = orchestrator_config.get('type', 'standard')

    if orchestrator_type == 'mab':
        settings = orchestrator_config.get('mab_settings', {})
        orchestrator = MultiArmedBanditOrchestrator(strategy=settings.get('strategy'), epsilon=settings.get('epsilon'))
        variants = settings.get('variants', [])
        exp_config = settings
    else: # standard
        orchestrator = StandardOrchestrator()
        # For simplicity, we'll just run the first standard experiment defined
        experiment = orchestrator_config.get('standard_settings', {}).get('experiments', [{}])[0]
        variants = experiment.get('variants', [])
        exp_config = experiment

    # The orchestrator's run method is a generator
    return orchestrator.run(variants, exp_config, {})

# --- Main Application ---
st.title("🤖 Meta-Orchestrator Dashboard")

# --- Sidebar ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Live Experiment", "Past Runs"])

if page == "Live Experiment":
    st.header("🚀 Live Experiment Runner")

    if not os.path.exists(CONFIG_PATH):
        st.error(f"Configuration file not found at `{CONFIG_PATH}`. Cannot start new experiments.")
    else:
        with open(CONFIG_PATH, 'r') as f:
            st.sidebar.subheader("Current Configuration")
            st.sidebar.code(f.read(), language="yaml")

        if st.button("▶️ Start New Experiment Run"):
            st.info("Starting new experiment... Results will appear below in real-time.")

            config = load_config(CONFIG_PATH)
            results = []

            # Placeholders for the charts
            score_chart_placeholder = st.empty()
            choice_chart_placeholder = st.empty()

            # Dataframes for live plotting
            live_scores = pd.DataFrame(columns=['trial', 'variant', 'mean_score'])
            live_choices = pd.DataFrame(columns=['variant', 'count'])

            run_generator = run_live_experiment(config)

            for i, result in enumerate(run_generator):
                results.append(result)

                # Update choices count
                variant_name = result['variant']
                if variant_name in live_choices['variant'].values:
                    live_choices.loc[live_choices['variant'] == variant_name, 'count'] += 1
                else:
                    new_row = pd.DataFrame([{'variant': variant_name, 'count': 1}])
                    live_choices = pd.concat([live_choices, new_row], ignore_index=True)

                # Update mean scores
                current_scores = {v: [] for v in live_choices['variant']}
                for res in results:
                    if 'score' in res:
                        current_scores[res['variant']].append(res['score'])

                mean_scores_data = []
                for v, s_list in current_scores.items():
                    if s_list:
                        mean_scores_data.append({'trial': i+1, 'variant': v, 'mean_score': sum(s_list)/len(s_list)})

                if mean_scores_data:
                    new_scores_df = pd.DataFrame(mean_scores_data)
                    score_chart_placeholder.line_chart(new_scores_df, x='trial', y='mean_score', color='variant')

                choice_chart_placeholder.bar_chart(live_choices.set_index('variant'))

                # Give a bit of breathing room for the UI to update
                time.sleep(0.05)

            st.success("Experiment finished!")
            st.balloons()
            st.subheader("Final Results")
            st.dataframe(pd.DataFrame(results))


elif page == "Past Runs":
    st.header("🗂️ Past Experiment Runs")
    past_runs = get_past_runs()

    if not past_runs:
        st.warning("No past experiment runs found.")
    else:
        selected_run = st.selectbox("Select a run to view:", past_runs)
        if selected_run:
            summary_md, results_df = load_run_data(selected_run)

            if summary_md:
                st.subheader("📊 Summary Report")
                st.markdown(summary_md)

            if not results_df.empty:
                st.subheader("🔬 Raw Trial Data")
                st.dataframe(results_df)
            else:
                st.warning("No results data found for this run.")
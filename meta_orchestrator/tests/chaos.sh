#!/bin/bash

# A simple chaos script to test system resilience under load.

echo "--- Chaos Test: Starting ---"
echo "This test will run the experiment hub while a background process consumes CPU."

# Start a background process to create some CPU load
echo "Starting CPU-consuming background process..."
# Use `dd` to create a simple, self-terminating load
dd if=/dev/zero of=/dev/null &
LOAD_PID=$!
echo "Load process started with PID: $LOAD_PID"

# Run the main experiment hub script
echo "Running the experiment hub under load..."
python3 -m meta_orchestrator.experiment_hub.hub > chaos_run_output.log 2>&1
EXIT_CODE=$?

# Stop the background load process
echo "Stopping load process..."
kill $LOAD_PID
# Wait to ensure the process is terminated and doesn't become a zombie
wait $LOAD_PID 2>/dev/null

# Check the outcome of the experiment run
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ SUCCESS: Experiment hub completed successfully (Exit Code 0)."
else
    echo "❌ FAILURE: Experiment hub failed with Exit Code $EXIT_CODE."
    echo "--- Log Output ---"
    cat chaos_run_output.log
    exit 1
fi

# Check if the results file was created
RESULTS_FILE="meta_orchestrator/results/latest_run.json"
if [ -f "$RESULTS_FILE" ]; then
    echo "✅ SUCCESS: Results file '$RESULTS_FILE' was created."
else
    echo "❌ FAILURE: Results file '$RESULTS_FILE' was NOT created."
    exit 1
fi

echo "--- Chaos Test: Passed ---"
rm chaos_run_output.log
exit 0
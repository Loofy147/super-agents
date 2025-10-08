import yaml
import os
from typing import Dict, Any, List

class ConfigGenerator:
    """
    Generates new config files for follow-up experiments based on analysis
    suggestions.
    """

    def __init__(self, base_config: Dict[str, Any], suggestions: List[Dict[str, Any]]):
        """
        Initializes the generator.

        Args:
            base_config: The original configuration from the analyzed run.
            suggestions: A list of suggestions from the PostHocAnalyzer.
        """
        self.base_config = base_config
        self.suggestions = suggestions

    def generate_follow_up_config(self, output_dir: str = ".") -> Optional[str]:
        """
        Creates a new config file based on the first actionable suggestion.

        Args:
            output_dir: The directory where the new config file will be saved.

        Returns:
            The path to the newly created config file, or None if no actionable
            suggestion was found.
        """
        if not self.suggestions:
            print("No suggestions provided, no follow-up config generated.")
            return None

        # For now, we'll act on the first suggestion
        # A more advanced implementation could merge multiple suggestions
        suggestion = self.suggestions[0]
        action = suggestion.get("proposed_action")

        if not action:
            return None

        new_config = self.base_config.copy()

        if action["type"] == "increase_trials":
            variant_to_modify = action["variant"]
            new_trial_count = action["new_trials_per_variant"]

            # Find the relevant experiment and update it
            # This is a bit naive and assumes a standard orchestrator setup
            experiments = new_config.get("orchestrator", {}).get("standard_settings", {}).get("experiments", [])
            for exp in experiments:
                if variant_to_modify in exp.get("variants", []):
                    exp["name"] = f"Follow-up on {variant_to_modify} (High Variance)"
                    exp["variants"] = [variant_to_modify] # Focus only on this variant
                    exp["trials_per_variant"] = new_trial_count

                    # Disable other experiments
                    for other_exp in experiments:
                        if other_exp is not exp:
                            other_exp["enabled"] = False

                    break # Stop after modifying the first experiment found

        else:
            print(f"Action type '{action['type']}' not yet supported by ConfigGenerator.")
            return None

        # Write the new config file
        output_filename = f"config.follow_up_{action['type']}_{action['variant']}.yaml"
        output_path = os.path.join(output_dir, output_filename)

        print(f"Generating follow-up config for suggestion: {suggestion['message']}")
        with open(output_path, 'w') as f:
            yaml.dump(new_config, f, default_flow_style=False, sort_keys=False)

        print(f"Successfully created follow-up config at: {output_path}")
        return output_path

# Example Usage
if __name__ == '__main__':
    mock_config = {
        "orchestrator": {
            "type": "standard",
            "standard_settings": {
                "experiments": [
                    {"name": "Initial Run", "enabled": True, "variants": ["stable_agent", "unstable_agent"], "trials_per_variant": 50},
                    {"name": "Other Exp", "enabled": True, "variants": ["another_agent"], "trials_per_variant": 50}
                ]
            }
        }
    }
    mock_suggestions = [
        {
            "type": "HighVariance",
            "variant": "unstable_agent",
            "message": "Variant 'unstable_agent' shows high performance variance.",
            "proposed_action": {
                "type": "increase_trials",
                "variant": "unstable_agent",
                "new_trials_per_variant": 250,
            }
        }
    ]

    generator = ConfigGenerator(mock_config, mock_suggestions)
    new_config_path = generator.generate_follow_up_config()

    if new_config_path:
        print("\n--- Generated Config Content ---")
        with open(new_config_path, 'r') as f:
            print(f.read())
        os.remove(new_config_path)
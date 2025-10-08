import random
from typing import Dict, Any, List

class AgentDesigner:
    """
    Designs novel agent variant specifications by combining core attributes
    and architectural patterns from a predefined innovation matrix.
    """

    def __init__(self):
        self.attributes = {
            "Memory": ["Stateless", "Stateful", "Short-Term", "Long-Term"],
            "Planning": ["Reactive", "Goal-Oriented", "Hierarchical"],
            "ToolUse": ["None", "SingleTool", "ToolLibrary"],
        }
        self.architectures = ["Monolithic", "Modular", "StateMachine", "MultiAgentSystem"]

    def design_new_variant(self, existing_variants: List[str] = None) -> Dict[str, Any]:
        """
        Generates a specification for a new, potentially novel agent variant.

        Args:
            existing_variants: An optional list of existing variant names to
                               avoid creating simple duplicates.

        Returns:
            A dictionary representing the design blueprint of the new agent.
        """
        print("--- Agent Forge: Designing new agent variant ---")

        # Simple strategy: randomly combine one attribute and one architecture
        # A more advanced designer could use past experiment results to guide this choice.
        chosen_attribute_type = random.choice(list(self.attributes.keys()))
        chosen_attribute_value = random.choice(self.attributes[chosen_attribute_type])
        chosen_architecture = random.choice(self.architectures)

        # Sanitize the attribute value to ensure it's a valid identifier component
        sanitized_attribute = chosen_attribute_value.replace("-", "")

        # Generate a name for the new variant
        variant_name = f"{sanitized_attribute}{chosen_architecture}Agent"

        # Avoid direct duplicates if possible
        if existing_variants and variant_name in existing_variants:
            variant_name = f"{variant_name}V2"

        design_spec = {
            "name": variant_name,
            "description": (
                f"A new agent designed by the Agent Forge. It features "
                f"a '{chosen_attribute_value}' {chosen_attribute_type} system "
                f"built on a '{chosen_architecture}' architecture."
            ),
            "architecture": chosen_architecture,
            "attributes": {
                chosen_attribute_type: chosen_attribute_value,
            },
            "source_file": f"{variant_name.lower()}.py"
        }

        print(f"  - New design created: {design_spec['name']}")
        print(f"  - Specification: {design_spec}")
        return design_spec

# Example Usage
if __name__ == '__main__':
    designer = AgentDesigner()
    new_agent_spec = designer.design_new_variant(existing_variants=["StatefulModularAgent"])

    import json
    print("\n--- Generated Agent Specification ---")
    print(json.dumps(new_agent_spec, indent=2))
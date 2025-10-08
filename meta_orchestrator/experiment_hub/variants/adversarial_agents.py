import random
from typing import Dict, Any

from ...core.base_variant import AgentVariant
from ..registry import register

class AmbiguityInjectorVariant(AgentVariant):
    """
    An adversarial agent that generates intentionally ambiguous or difficult
    task descriptions to test the robustness of other agents.
    """

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a "poisoned" context with a challenging task description.
        """
        base_task = "Generate a summary of our project's progress."

        # Select an adversarial strategy at random
        strategy = random.choice([
            "add_vagueness",
            "add_contradiction",
            "add_excessive_detail"
        ])

        if strategy == "add_vagueness":
            task_id = f"{base_task} Make it 'good' and 'impactful'."
        elif strategy == "add_contradiction":
            task_id = f"{base_task} Keep it brief, under 10 words, but also ensure it is a comprehensive and detailed overview covering all aspects."
        elif strategy == "add_excessive_detail":
            filler = " ".join(["etc"] * 50) # 50 'etc's
            task_id = f"{base_task} Also, please consider the synergistic implications of our Q3 roadmap, {filler}, while bearing in mind the fiscal responsibilities outlined in the shareholder agreement."
        else:
            task_id = base_task

        print(f"  - AmbiguityInjector: Generated task with strategy '{strategy}'.")

        # The primary output is the modified context
        new_context = context.copy()
        new_context["task_id"] = task_id
        new_context["adversarial_strategy"] = strategy
        return new_context

# Register the adversarial agent so it can be selected in configurations
register("adversarial_ambiguity_injector")(AmbiguityInjectorVariant())
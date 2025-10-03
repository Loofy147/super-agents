from typing import Dict, Callable

# A centralized, singleton registry for all experiment variants.
REGISTRY: Dict[str, Callable] = {}

def register(name: str):
    """
    A decorator to register a new experiment variant into the central registry.
    """
    def _wrap(f: Callable) -> Callable:
        print(f"Registering variant: {name}")
        if name in REGISTRY:
            print(f"Warning: Overwriting existing variant '{name}' in registry.")
        REGISTRY[name] = f
        return f
    return _wrap
# This file makes 'variants' a Python sub-package.
# It can also be used to auto-discover variant modules.
import pkgutil
import importlib

# Discover and import all modules in this package to register the variants
__path__ = pkgutil.extend_path(__path__, __name__)
for _, module_name, _ in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{module_name}")
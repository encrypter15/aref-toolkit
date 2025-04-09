import os
import importlib

def load_plugins():
    plugins = {}
    for file in os.listdir(os.path.dirname(__file__)):
        if file.endswith(".py") and file != "__init__.py":
            module_name = file[:-3]
            module = importlib.import_module(f"plugins.{module_name}")
            plugins[module_name] = getattr(module, "run")
    return plugins

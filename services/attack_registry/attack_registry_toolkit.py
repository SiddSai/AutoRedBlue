import os
REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "attack_registry.JSON")

# call it like:
#
# from services.attack_registry.attack_registry_toolkit import REGISTRY_PATH
# resgistry = None
# with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
#     registry = json.load(f)
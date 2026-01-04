
import sys
import os

# Add src to path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))
sys.path.append(src_path)
print(f"Added {src_path} to sys.path")

try:
    import model
    print("Imported model:", model)
except ImportError as e:
    print("Failed to import model:", e)

try:
    import model.petri_net
    print("Imported model.petri_net:", model.petri_net)
except ImportError as e:
    print("Failed to import model.petri_net:", e)

try:
    from model.petri_net.wrapper import WrapperPetriNet
    print("Imported WrapperPetriNet")
except ImportError as e:
    print("Failed to import WrapperPetriNet:", e)

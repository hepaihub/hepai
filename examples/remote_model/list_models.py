

try:
    from hepai import __version__
except:
    import os, sys
    from pathlib import Path
    here = Path(__file__).parent
    sys.path.insert(1, str(here.parent.parent))
    from hepai import __version__

    
from hepai import HRModel

models = HRModel.list_models()  # List all models.
print(f"Models: {models}")


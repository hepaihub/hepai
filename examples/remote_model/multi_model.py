
try:
    from hepai import __version__
except:
    import os, sys
    from pathlib import Path
    here = Path(__file__).parent
    sys.path.insert(1, str(here.parent.parent))
    from hepai import __version__


from hepai import HRModel, HWorkerAPP


model1 = HRModel("hepai/hr-model1")
model2 = HRModel("hepai/hr-model2")
app = HWorkerAPP(models=[model1, model2])
app.run()  # Run the APP.



import os, sys
from pathlib import Path
import hepai as hai
from fastapi import FastAPI
import uvicorn

try:
    from haiddf.version import __version__
except:
    sys.path.insert(1, str(Path(__file__).parent.parent.parent.parent))
    from haiddf.version import __version__

from haiddf._types import HWorkerModel
from haiddf.modules.worker.worker_app import HWorkerAPP, HWorkerArgs


def main():
    model = HWorkerModel()
    worker_config = hai.parse_args(HWorkerArgs)
    app: FastAPI = HWorkerAPP(model, worker_config=worker_config)

    print(f'worker_id: `{app.worker.worker_id}`', flush=True)
    
    uvicorn.run(app, host=app.host, port=app.port)

if __name__ == "__main__":
    main()

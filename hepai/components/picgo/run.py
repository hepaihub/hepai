import sys
print(sys.path)

from pathlib import Path
here = Path(__file__).parent
try:
    from hepai import __version__
except:
    sys.path.insert(0, f'{here.parent.parent.parent}')
    from hepai import __version__

from hepai import Picgo

def run(img_path:str):
    picgo = Picgo()
    url = picgo.upload(img_path)
    return url

def main():
    
    # picgo = Picgo()
    print(run("/home/jzy/VSProjects/hai/demo.png"))

if __name__ == "__main__":
    main()


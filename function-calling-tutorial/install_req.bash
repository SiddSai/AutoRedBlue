python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 1) Make sure ipykernel is installed in the venv
python -m pip install ipykernel

# 2) Register this venv as a Jupyter kernel
python -m ipykernel install --user --name autoredblue-venv --display-name "Python (autoredblue-venv)"
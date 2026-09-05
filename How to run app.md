Open PowerShell in VoterApp and run:

python -m pip install -r requirements.txt
python scripts\generate_dataset.py
python -m uvicorn backend.main:app --reload


Then open:

http://127.0.0.1:8000

Demo login:

Username: officer01
Password: demo123
To stop the server, press Ctrl+C.
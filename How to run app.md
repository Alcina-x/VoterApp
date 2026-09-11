Open PowerShell in VoterApp and run:

python -m pip install -r requirements.txt
python scripts\generate_dataset.py

only run this in your terminal:
python -m uvicorn backend.main:app --reload

.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
Then open:

http://127.0.0.1:8000

Demo logins:

Username: Alcina, Akshaya, or Ajay
Password: demo123
To stop the server, press Ctrl+C.

How to put it to git hub
(run in terminal)
git add .
git commit -m "comment"
git push
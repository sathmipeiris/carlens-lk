# CAR PRICE PREDICTOR

This repository contains a minimal starter structure for the "CAR PRICE PREDICTOR" project.

Structure
- backend/: Flask-based backend that exposes a /predict endpoint and loads trained artifacts.
- frontend/: simple static frontend (HTML/JS) demonstrating how to call the backend.

Quick start (local)
1. Activate your virtualenv:
   ```powershell
   .\car_price_env\Scripts\Activate.ps1
   ```
2. Install dependencies (from project root):
   ```powershell
   pip install -r requirements.txt
   ```
3. Start the backend (development):
   ```powershell
   python backend/app.py
   ```
4. Open `frontend/index.html` in a browser or serve it with a static server.

Create a private GitHub repo and push
- Using GitHub CLI (recommended):
  ```powershell
  gh repo create "CAR-PRICE-PREDICTOR" --private --source=. --remote=origin --push
  ```
- Or manually create a private repo on github.com and then:
  ```powershell
  git remote add origin <your-repo-url>
  git branch -M main
  git push -u origin main
  ```

Notes
- Trained model artifacts (e.g., `final_best_model.pkl`, encoder files) should be kept out of source control; place them on a protected storage or add them to a release.
- `requirements.txt` was generated from the project venv and is included at the project root.

If you want, I can also create a GitHub repository and push this code for you — I will need access tokens or you can run the `gh repo create` command shown above.
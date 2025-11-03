# Lightweight Smart Cybersecurity Policy Generator (Prototype)

## Setup (local)
1. Clone repo.
2. Create virtualenv: python -m venv venv && source venv/bin/activate
3. pip install -r requirements.txt
4. Create a .env file in project root:
   GEMINI_API_KEY=your_api_key_here
   GEMINI_ENDPOINT=https://api.your-llm.com/v1/generate   # replace with actual
   FLASK_SECRET=some_secret_key
5. Add some lines to stories.txt
6. Run: python app.py
7. Visit http://localhost:5000

## Deployment (Render)
1. Push repo to GitHub.
2. Create new Web Service on Render:
   - Connect GitHub repo.
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
3. Set environment variables on Render: GEMINI_API_KEY, GEMINI_ENDPOINT, FLASK_SECRET
4. Deploy.

## Notes
- Replace call_gemini_api() body with your provider's SDK or endpoint.
- Keep GEMINI_API_KEY secret (do not commit to Git).

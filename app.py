# app.py
import os
import textwrap
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
import requests
from datetime import datetime
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "replace-me")  # change for production

# Config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_ENDPOINT = os.getenv(
    "GEMINI_ENDPOINT",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
)

STORIES_FILE = os.path.join(os.path.dirname(__file__), "stories.txt")

def load_local_context(n_lines=10):
    """Load some context lines from local stories file to include in prompt."""
    if not os.path.exists(STORIES_FILE):
        return ""
    with open(STORIES_FILE, "r", encoding="utf-8") as f:
        lines = f.read().strip()
    return "\n".join(lines.splitlines()[:n_lines])

def call_gemini_api(prompt: str, max_tokens: int = 800) -> str:
    """Calls Google Gemini API using proper authentication and payload format."""
    if not GEMINI_API_KEY:
        return ("[ERROR] Gemini API key not found. Please check your .env file.")

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        resp = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        j = resp.json()

        # Extract AI response safely
        return j.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "[No response text found]")
    except requests.exceptions.RequestException as e:
        return f"[Error calling AI service] {str(e)}"
    except Exception as e:
        return f"[Unexpected error] {str(e)}"

def construct_prompt(user_input: dict, local_context: str) -> str:
    business = user_input.get("business_type", "Informal vendor")
    tools = user_input.get("tools", "WhatsApp / Mobile money")
    concerns = user_input.get("concerns", "") or "general protection against scams and fraud"
    prompt = textwrap.dedent(f"""
    You are an AI assistant that writes short, clear, actionable cybersecurity policies for informal microbusinesses.
    Target user: {business}. Digital tools used: {tools}.
    Local context examples (do not reveal personally identifying info): 
    {local_context}

    User-stated concerns: {concerns}

    Produce:
    1) A short policy title (one line).
    2) A 6-12 point actionable policy list (each item one sentence; no jargon).
    3) A short 'Why this matters' paragraph (1-2 sentences).
    4) Simple implementation checklist (3 items).
    Keep language simple and concise for low-literacy users. Use imperative tone: 'Do this', 'Avoid that'.
    Format output as plain text with clear sections.
    """)
    return prompt

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    business_type = request.form.get("business_type", "").strip().lower()
    tools = request.form.get("tools", "").strip().lower()
    concerns = request.form.get("concerns", "").strip()

    #  Restrict business types
    allowed_types = ["whatsapp vendor", "street trader"]
    if business_type not in allowed_types:
        flash("⚠️ This tool only supports WhatsApp Vendors and Street Traders. No policy generated.", "danger")
        return redirect(url_for("index"))

    # Check if digital tools are valid
    valid_tools = ["whatsapp", "pos", "paystack", "bank transfer", "bank app", "mobile money"]
    tool_list = [t.strip() for t in tools.split(",") if t.strip()]
    unrecognized = [t for t in tool_list if t not in valid_tools]

    # Load local scam context
    local_context = load_local_context(n_lines=20)

    user_input = {
        "business_type": business_type.title(),
        "tools": tools,
        "concerns": concerns
    }

    prompt = construct_prompt(user_input, local_context)

    #  Add AI prompt note if tools are unrecognized
    if unrecognized:
        extra_note = (
            "\n\nNote: Some tools provided are not recognized as digital payment or communication tools. "
            "Based on your business type, consider using verified digital tools such as WhatsApp, POS systems, Paystack, or Bank Transfers for safer operations."
        )
        prompt += extra_note

    try:
        policy_text = call_gemini_api(prompt)
    except Exception as e:
        policy_text = f"[Error calling AI service] {str(e)}"

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"policy_{business_type.replace(' ', '_')}_{timestamp}.txt"

    return render_template(
        "result.html",
        policy=policy_text,
        filename=filename,
        business_type=business_type,
        tools=tools,
        concerns=concerns
    )


@app.route("/download", methods=["POST"])
def download():
    policy_text = request.form.get("policy_text", "")
    filename = request.form.get("filename", f"policy_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.txt")
    mem = BytesIO()
    mem.write(policy_text.encode("utf-8"))
    mem.seek(0)
    return send_file(mem, as_attachment=True, download_name=filename, mimetype="text/plain")

#  Test endpoint to check Gemini connectivity
@app.route("/test_api")
def test_api():
    test_prompt = "Say hello from Gemini API."
    response = call_gemini_api(test_prompt)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

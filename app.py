import os
import json
import requests
from flask import Flask, redirect, Response
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SITE = os.getenv("SITE", "").rstrip("/")
INTERNAL_URL = os.getenv("INTERNAL_URL", SITE).rstrip("/")
LOGIN_USER = os.getenv("LOGIN_USER")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD")
PORT = int(os.getenv("PORT", 3000))
LOCATION = os.getenv("LOCATION", "/auto-login")


def get_auth_token():
    """Login to the site and get the auth token."""
    login_url = f"{INTERNAL_URL}/api/auth/"
    payload = {"username": LOGIN_USER, "password": LOGIN_PASSWORD}
    headers = {"Content-Type": "application/json"}
    response = requests.post(login_url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def login_and_redirect():
    """
    Log into the site, store token in localStorage, and redirect.
    Works when hosted on the same domain as SITE (via reverse proxy).
    """
    try:
        data = get_auth_token()
        token = data.get("token")

        if not token:
            return "Login failed: No token in response", 500

        # Since we're on the same domain, we can set localStorage directly
        token_json = json.dumps(data)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Logging in...</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex; justify-content: center; align-items: center;
            height: 100vh; margin: 0; background: #1a1a2e; color: #eee;
        }}
        .spinner {{
            border: 3px solid #333; border-top: 3px solid #6366f1;
            border-radius: 50%; width: 32px; height: 32px;
            animation: spin 0.8s linear infinite; margin: 0 auto 16px;
        }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
    <div style="text-align:center">
        <div class="spinner"></div>
        <p>Logging in...</p>
    </div>
    <script>
        const data = {token_json};
        localStorage.setItem('token', data.token);
        window.location.href = '/';
    </script>
</body>
</html>"""
        return Response(html, mimetype='text/html')

    except requests.exceptions.RequestException as e:
        return f"Login request failed: {str(e)}", 500
    except Exception as e:
        return f"Error: {str(e)}", 500


# Register routes dynamically based on LOCATION env var
app.add_url_rule("/", view_func=login_and_redirect)
app.add_url_rule(LOCATION, view_func=login_and_redirect)


if __name__ == "__main__":
    print(f"Auth Redirect Server - Port {PORT}")
    print(f"Target: {SITE}")
    print(f"Location: {LOCATION}")
    print()
    app.run(host="0.0.0.0", port=PORT)

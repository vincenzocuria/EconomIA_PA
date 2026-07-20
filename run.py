"""Avvio locale: python run.py"""
import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app(os.getenv("FLASK_CONFIG") or "development")

if __name__ == "__main__":
    # Default 5050: evita conflitto con altre webapp sulla 5000
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5050")), debug=True)

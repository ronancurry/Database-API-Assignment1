"""Read configuration without printing credentials."""
import os
from pathlib import Path
from dotenv import load_dotenv

try:
    import streamlit as st
    from streamlit.errors import StreamlitSecretNotFoundError
except ImportError:
    st = None
    StreamlitSecretNotFoundError = RuntimeError


def _read_setting(name):
    value = os.getenv(name, "").strip()
    if value:
        return value
    if st is not None:
        try:
            return str(st.secrets.get(name, "")).strip()
        except StreamlitSecretNotFoundError:
            pass
    return ""


def get_settings():
    load_dotenv(Path(__file__).with_name(".env"))
    url = _read_setting("SUPABASE_URL").rstrip("/")
    key = _read_setting("SUPABASE_SECRET_KEY")
    if not url.startswith("https://"):
        raise ValueError("Set SUPABASE_URL to your project's HTTPS URL in .env or app secrets.")
    if not key:
        raise ValueError("Set SUPABASE_SECRET_KEY in .env or app secrets.")
    return url, key


def get_app_password():
    load_dotenv(Path(__file__).with_name(".env"))
    return _read_setting("APP_PASSWORD")

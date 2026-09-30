"""Shared connection helper for the scripts (reads .streamlit/secrets.toml or env vars)."""
import os
import tomllib
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parent.parent


def get_engine():
    if os.environ.get("DATABASE_URL"):
        return create_engine(os.environ["DATABASE_URL"])
    secrets_file = ROOT / ".streamlit" / "secrets.toml"
    if not secrets_file.exists():
        raise SystemExit("Missing .streamlit/secrets.toml (copy secrets.toml.example) or set DATABASE_URL.")
    with open(secrets_file, "rb") as f:
        s = tomllib.load(f)["mysql"]
    ca = Path(s.get("ssl_ca", ROOT / "certs" / "aiven-ca.pem"))
    if not ca.is_absolute():
        ca = ROOT / ca
    url = URL.create("mysql+pymysql", username=s["user"], password=s["password"],
                     host=s["host"], port=int(s["port"]), database=s["database"])
    return create_engine(url, connect_args={"ssl": {"ca": str(ca)}} if ca.exists() else {})

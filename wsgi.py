"""WSGI entry point for production deployment (gunicorn)."""
import os
from app import create_app

app = create_app('production')

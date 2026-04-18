#!/bin/bash
# Wrapper script for Railway - reads PORT env var and starts gunicorn
port=${PORT:-8080}
exec gunicorn app:app --bind "0.0.0.0:${port}"
#!/usr/bin/env python

from src.app import app

if __name__ == "__main__":
  if app.config['APP_ENVIRONMENT'] == "dev":
    app.run(host='127.0.0.1', port=5000, debug=True)
  else:
    app.run(host='0.0.0.0', port=5000)
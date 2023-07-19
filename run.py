#!/usr/bin/env python

from src.app import app
from alembic.config import Config
from alembic import command

if __name__ == "__main__":
  if app.config['APP_ENVIRONMENT'] != "test":
    # Run alembic migrations before starting the server
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option('sqlalchemy.url', app.config['SQLALCHEMY_DATABASE_URI'])
    command.upgrade(alembic_cfg, "head")

  if app.config['APP_ENVIRONMENT'] == "dev":
    app.run(host='127.0.0.1', port=5000, debug=True)
  else:
    app.run()
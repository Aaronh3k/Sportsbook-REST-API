"""create initial tables

Revision ID: fee927264e0a
Revises: 
Create Date: 2023-07-14 17:21:08.209354

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fee927264e0a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ENUM types
    op.execute("CREATE TYPE event_type AS ENUM ('preplay', 'inplay');")
    op.execute("CREATE TYPE event_status AS ENUM ('Pending', 'Started', 'Ended', 'Cancelled');")
    op.execute("CREATE TYPE selection_outcome AS ENUM ('Unsettled', 'Void', 'Lose', 'Win');")
    
    op.execute("""
    CREATE TABLE Sports (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        url_identifier VARCHAR(255),
        active BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    op.execute("""
    CREATE TABLE Events (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        url_identifier VARCHAR(255),
        active BOOLEAN,
        type event_type,
        sport_id INT,
        status event_status,
        scheduled_start TIMESTAMP,
        actual_start TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sport_id) REFERENCES Sports(id)
    )
    """)

    op.execute("""
    CREATE TABLE Selections (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        event_id INT,
        price DECIMAL(10, 2),
        active BOOLEAN,
        outcome selection_outcome,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES Events(id)
    )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE Selections")
    op.execute("DROP TABLE Events")
    op.execute("DROP TABLE Sports")
    
    # Remove ENUM types
    op.execute("DROP TYPE selection_outcome;")
    op.execute("DROP TYPE event_status;")
    op.execute("DROP TYPE event_type;")

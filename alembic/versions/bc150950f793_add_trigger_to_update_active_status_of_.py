"""add trigger to update active status of event and sport

Revision ID: bc150950f793
Revises: fee927264e0a
Create Date: 2023-07-18 11:06:13.293280

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bc150950f793'
down_revision = 'fee927264e0a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE OR REPLACE FUNCTION check_selection_active() RETURNS TRIGGER AS $$
    BEGIN
        -- Update the event active status
        UPDATE events
        SET active = EXISTS (SELECT 1 FROM selections WHERE event_id = events.id AND active);

        -- Update the sport active status
        UPDATE sports
        SET active = EXISTS (SELECT 1 FROM events WHERE sport_id = sports.id AND active);
        
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER check_selection_active_trigger
    AFTER INSERT OR UPDATE OR DELETE ON selections
    FOR EACH STATEMENT EXECUTE FUNCTION check_selection_active();
    """)

def downgrade() -> None:
    op.execute("""
    DROP TRIGGER check_selection_active_trigger ON selections;
    DROP FUNCTION check_selection_active;
    """)
"""
Add calling_time to queue_tokens table
"""
from alembic import op
import sqlalchemy as sa

revision = '20260507_0003'
down_revision = '6a025f451096'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        'queue_tokens',
        sa.Column('calling_time', sa.DateTime(timezone=True), nullable=True)
    )

def downgrade():
    op.drop_column('queue_tokens', 'calling_time')

from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'neos',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('neo_id', sa.String, unique=True, index=True),
        sa.Column('name', sa.String),
        sa.Column('close_approach_date', sa.Date, index=True),
        sa.Column('diameter_km', sa.Float),
        sa.Column('velocity_km_s', sa.Float),
        sa.Column('miss_distance_au', sa.Float),
        sa.Column('hazardous', sa.Boolean),
    )
    op.create_index('idx_close_date', 'neos', ['close_approach_date'])
    op.create_table(
        'subscribers',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('url', sa.String, unique=True),
    )

def downgrade():
    op.drop_table('subscribers')
    op.drop_index('idx_close_date', table_name='neos')
    op.drop_table('neos')

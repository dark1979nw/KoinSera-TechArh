"""add is_admin column

Revision ID: 004
Revises: 003
Create Date: 2024-03-20 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    # Add is_admin column
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True))
    # Copy data from Is_Admin to is_admin
    op.execute('UPDATE users SET is_admin = "Is_Admin"')
    # Make is_admin not nullable
    op.alter_column('users', 'is_admin', nullable=False)
    # Drop Is_Admin column
    op.drop_column('users', 'Is_Admin')

def downgrade():
    # Add Is_Admin column
    op.add_column('users', sa.Column('Is_Admin', sa.Boolean(), nullable=True))
    # Copy data from is_admin to Is_Admin
    op.execute('UPDATE users SET "Is_Admin" = is_admin')
    # Make Is_Admin not nullable
    op.alter_column('users', 'Is_Admin', nullable=False)
    # Drop is_admin column
    op.drop_column('users', 'is_admin') 
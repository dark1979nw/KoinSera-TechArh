"""rename is_admin column

Revision ID: 003
Revises: 002
Create Date: 2024-03-20 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    # Rename Is_Admin column to is_admin
    op.alter_column('users', 'Is_Admin', new_column_name='is_admin')

def downgrade():
    # Rename is_admin column back to Is_Admin
    op.alter_column('users', 'is_admin', new_column_name='Is_Admin') 
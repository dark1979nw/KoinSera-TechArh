"""initial migration

Revision ID: 001
Revises: 
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create languages table
    op.create_table(
        'languages',
        sa.Column('code', sa.String(2), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('login', sa.String(50), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(60), nullable=False),
        sa.Column('first_name', sa.String(50), nullable=False),
        sa.Column('last_name', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100), unique=True, nullable=False),
        sa.Column('company', sa.String(100)),
        sa.Column('language_code', sa.String(2), sa.ForeignKey('languages.code')),
        sa.Column('locked_until', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('last_login', sa.DateTime()),
        sa.Column('failed_login_attempts', sa.Integer(), default=0)
    )

    # Create indexes
    op.create_index('ix_users_login', 'users', ['login'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_language_code', 'users', ['language_code'])

    # Insert default languages
    op.execute("""
        INSERT INTO languages (code, name, is_default) VALUES
        ('en', 'English', true),
        ('ru', 'Русский', false)
    """)

def downgrade():
    # Drop users table
    op.drop_table('users')
    
    # Drop languages table
    op.drop_table('languages') 
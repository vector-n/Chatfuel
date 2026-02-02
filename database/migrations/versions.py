"""Add welcome_message to bots

Revision ID: add_welcome_message
Revises: 
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_welcome_message'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add welcome_message column to bots table
    op.add_column('bots', sa.Column('welcome_message', sa.Text(), nullable=True))


def downgrade():
    # Remove welcome_message column from bots table
    op.drop_column('bots', 'welcome_message')

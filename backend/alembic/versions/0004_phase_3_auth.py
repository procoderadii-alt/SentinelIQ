"""Phase 3 Auth Fields

Revision ID: 0004_phase_3_auth
Revises: 0003_dataset_upload
Create Date: 2026-06-19 23:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = '0004_phase_3_auth'
down_revision = '0003_dataset_upload'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add new fields to users table
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('mfa_secret', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('refresh_token', sa.String(length=255), nullable=True))

    # set defaults for existing rows
    op.execute("UPDATE users SET failed_login_attempts = 0, mfa_enabled = false")

def downgrade() -> None:
    op.drop_column('users', 'refresh_token')
    op.drop_column('users', 'mfa_secret')
    op.drop_column('users', 'mfa_enabled')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')

"""dataset upload

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-18 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # create table datasets
    op.create_table(
        'datasets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('uploaded_by_id', sa.UUID(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('record_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # add column source_dataset_id to crime_records
    with op.batch_alter_table('crime_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source_dataset_id', sa.UUID(), nullable=True))
        batch_op.create_foreign_key('fk_crime_records_datasets_id', 'datasets', ['source_dataset_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('crime_records', schema=None) as batch_op:
        batch_op.drop_constraint('fk_crime_records_datasets_id', type_='foreignkey')
        batch_op.drop_column('source_dataset_id')
    op.drop_table('datasets')

"""Add expert_items table

Revision ID: 7f769e0caa68
Revises: 9544f82e6b16
Create Date: 2025-10-26 07:21:29.101031

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f769e0caa68'
down_revision: Union[str, None] = '9544f82e6b16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('expert_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('author', sa.String(length=200), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=True),
        sa.Column('pick', sa.String(length=10), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('confidence', sa.String(length=50), nullable=True),
        sa.Column('scraped_at', sa.DateTime(), nullable=False),
        sa.Column('raw_data', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_expert_items_source', 'expert_items', ['source'], unique=False)
    op.create_index('ix_expert_items_published_at', 'expert_items', ['published_at'], unique=False)
    op.create_index('ix_expert_items_match_id', 'expert_items', ['match_id'], unique=False)
    op.create_index('ix_expert_items_source_published', 'expert_items', ['source', 'published_at'], unique=False)
    op.create_index('ix_expert_items_match_source', 'expert_items', ['match_id', 'source'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_expert_items_match_source', table_name='expert_items')
    op.drop_index('ix_expert_items_source_published', table_name='expert_items')
    op.drop_index('ix_expert_items_match_id', table_name='expert_items')
    op.drop_index('ix_expert_items_published_at', table_name='expert_items')
    op.drop_index('ix_expert_items_source', table_name='expert_items')
    op.drop_table('expert_items')

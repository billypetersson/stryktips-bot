"""Add title, summary, and match_tags to expert_items

Revision ID: f902bea8bb6c
Revises: 7f769e0caa68
Create Date: 2025-10-26 08:01:07.529049

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f902bea8bb6c'
down_revision: Union[str, None] = '7f769e0caa68'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add title column
    op.add_column('expert_items', sa.Column('title', sa.Text(), nullable=True))

    # Add summary column
    op.add_column('expert_items', sa.Column('summary', sa.Text(), nullable=True))

    # Add match_tags column (JSON for flexible matching)
    op.add_column('expert_items', sa.Column('match_tags', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove columns in reverse order
    op.drop_column('expert_items', 'match_tags')
    op.drop_column('expert_items', 'summary')
    op.drop_column('expert_items', 'title')

"""add score to job_offer and min_score to user_profile

Revision ID: a7c9e1f3b5d6
Revises: f6b8d0e2a4c5
Create Date: 2026-11-26 15:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c9e1f3b5d6'
down_revision: Union[str, Sequence[str], None] = 'f6b8d0e2a4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Offers already saved get no score; the existing profile gets the default threshold, 70."""
    op.add_column('job_offer', sa.Column('score', sa.Integer(), nullable=True))
    op.add_column('user_profile', sa.Column('min_score', sa.Integer(), server_default='70', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user_profile', 'min_score')
    op.drop_column('job_offer', 'score')

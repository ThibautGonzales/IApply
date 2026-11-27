"""create cover_letter table

Revision ID: a3b5d7f9c1e4
Revises: f2a4c6e8b0d3
Create Date: 2026-11-27 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3b5d7f9c1e4'
down_revision: Union[str, Sequence[str], None] = 'f2a4c6e8b0d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('cover_letter',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job_offer_id', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['job_offer_id'], ['job_offer.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('job_offer_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('cover_letter')

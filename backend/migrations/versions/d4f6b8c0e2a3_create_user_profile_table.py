"""create user_profile table

Revision ID: d4f6b8c0e2a3
Revises: c3e5a7b9d1f2
Create Date: 2026-11-26 14:50:00.000000

"""
from datetime import UTC, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4f6b8c0e2a3'
down_revision: Union[str, Sequence[str], None] = 'c3e5a7b9d1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the table and its only row: the profile always exists, empty until the user fills it."""
    profile = op.create_table('user_profile',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('looking_for', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.bulk_insert(profile, [{'id': 1, 'looking_for': '', 'updated_at': datetime.now(UTC)}])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('user_profile')

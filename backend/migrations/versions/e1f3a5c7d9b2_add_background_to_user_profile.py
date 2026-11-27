"""add the user's background (skills, career, experience) to the profile

Revision ID: e1f3a5c7d9b2
Revises: d0e2a4c6e8f1
Create Date: 2026-11-27 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f3a5c7d9b2'
down_revision: Union[str, Sequence[str], None] = 'd0e2a4c6e8f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: an empty background for the existing profile row."""
    with op.batch_alter_table('user_profile') as batch_op:
        batch_op.add_column(sa.Column('background', sa.Text(), server_default='', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('user_profile') as batch_op:
        batch_op.drop_column('background')

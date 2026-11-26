"""lower the default min_score to 50

Revision ID: b8d0f2a4c6e7
Revises: a7c9e1f3b5d6
Create Date: 2026-11-26 15:50:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b8d0f2a4c6e7'
down_revision: Union[str, Sequence[str], None] = 'a7c9e1f3b5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """A new migration rather than an edit of the previous one, which may already be applied.

    A profile still at 70 never chose it (no page could set it yet): it moves to 50 too.
    """
    with op.batch_alter_table('user_profile') as batch_op:
        batch_op.alter_column('min_score', server_default='50')
    op.execute("UPDATE user_profile SET min_score = 50 WHERE min_score = 70")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('user_profile') as batch_op:
        batch_op.alter_column('min_score', server_default='70')
    op.execute("UPDATE user_profile SET min_score = 70 WHERE min_score = 50")

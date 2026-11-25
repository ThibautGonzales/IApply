"""rename status_changed_at to last_news_at

Revision ID: b2d4f6a8c0e1
Revises: a187f14bf210
Create Date: 2026-11-25 16:20:00

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b2d4f6a8c0e1'
down_revision: Union[str, Sequence[str], None] = 'a187f14bf210'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Batch mode so the rename also works on SQLite (the test database).
def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('application') as batch_op:
        batch_op.alter_column('status_changed_at', new_column_name='last_news_at')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('application') as batch_op:
        batch_op.alter_column('last_news_at', new_column_name='status_changed_at')

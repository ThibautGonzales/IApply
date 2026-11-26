"""split min_score into an on-site and a remote threshold

Revision ID: d0e2a4c6e8f1
Revises: c9e1a3b5d7f8
Create Date: 2026-11-26 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0e2a4c6e8f1'
down_revision: Union[str, Sequence[str], None] = 'c9e1a3b5d7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """The old threshold becomes the on-site one, and the remote one starts with the same value,
    so the list does not change until the user sets them apart."""
    with op.batch_alter_table('user_profile') as batch_op:
        batch_op.alter_column('min_score', new_column_name='min_score_onsite')
        batch_op.add_column(sa.Column('min_score_remote', sa.Integer(), server_default='50', nullable=False))
    op.execute("UPDATE user_profile SET min_score_remote = min_score_onsite")


def downgrade() -> None:
    """Downgrade schema: the on-site threshold goes back to being the only one."""
    with op.batch_alter_table('user_profile') as batch_op:
        batch_op.drop_column('min_score_remote')
        batch_op.alter_column('min_score_onsite', new_column_name='min_score')

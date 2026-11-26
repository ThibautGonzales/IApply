"""insert the only user_profile row

Revision ID: e5a7c9d1f3b4
Revises: d4f6b8c0e2a3
Create Date: 2026-11-26 15:10:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e5a7c9d1f3b4'
down_revision: Union[str, Sequence[str], None] = 'd4f6b8c0e2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the profile, empty, unless a save already created it: the profile always exists."""
    op.execute(
        "INSERT INTO user_profile (id, looking_for, updated_at) "
        "SELECT 1, '', CURRENT_TIMESTAMP "
        "WHERE NOT EXISTS (SELECT 1 FROM user_profile WHERE id = 1)"
    )


def downgrade() -> None:
    """Nothing to do: the row goes away with the table in the previous migration."""

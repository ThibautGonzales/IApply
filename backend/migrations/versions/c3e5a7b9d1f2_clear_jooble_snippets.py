"""clear the Jooble snippets saved in job_offer.description

Revision ID: c3e5a7b9d1f2
Revises: b2d4f6a8c0e1
Create Date: 2026-11-25 17:15:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c3e5a7b9d1f2'
down_revision: Union[str, Sequence[str], None] = 'b2d4f6a8c0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Empty the snippets: from now on, description only holds the offer pasted by the user."""
    op.execute("UPDATE job_offer SET description = NULL WHERE source = 'jooble'")


def downgrade() -> None:
    """Nothing to do: the snippets are gone and the column itself did not change."""

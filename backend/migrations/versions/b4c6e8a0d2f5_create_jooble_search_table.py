"""create jooble_search table

Revision ID: b4c6e8a0d2f5
Revises: a3b5d7f9c1e4
Create Date: 2026-11-27 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b4c6e8a0d2f5'
down_revision: Union[str, Sequence[str], None] = 'a3b5d7f9c1e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('jooble_search',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('keywords', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
    sa.Column('remote', sa.Boolean(), nullable=False),
    sa.Column('location', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True),
    sa.Column('radius_km', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('jooble_search')

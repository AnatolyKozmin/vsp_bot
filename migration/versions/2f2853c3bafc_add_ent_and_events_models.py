"""Add Ent and Events models

Revision ID: 2f2853c3bafc
Revises: 644c81e411a9
Create Date: 2025-06-09 12:00:37.221886

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f2853c3bafc'
down_revision: Union[str, None] = '644c81e411a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('feature', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events', 'feature')
    # ### end Alembic commands ###

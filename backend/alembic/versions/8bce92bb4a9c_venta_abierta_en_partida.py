"""venta abierta en partida

Revision ID: 8bce92bb4a9c
Revises: 6ea4bcdea815
Create Date: 2026-08-12 13:39:04.566471

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bce92bb4a9c'
down_revision: Union[str, Sequence[str], None] = '6ea4bcdea815'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agrega el «bombillo» de venta, abierto por defecto en las partidas ya creadas."""
    with op.batch_alter_table('partida', schema=None) as batch_op:
        # server_default es imprescindible: la columna es NOT NULL y ya puede
        # haber partidas. Sin un valor por defecto, la migración falla en
        # cuanto exista una sola fila.
        batch_op.add_column(
            sa.Column('venta_abierta', sa.Boolean(), nullable=False, server_default=sa.true())
        )


def downgrade() -> None:
    """Quita el bombillo de venta."""
    with op.batch_alter_table('partida', schema=None) as batch_op:
        batch_op.drop_column('venta_abierta')

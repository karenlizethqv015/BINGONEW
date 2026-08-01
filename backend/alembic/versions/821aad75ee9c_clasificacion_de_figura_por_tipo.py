"""clasificacion de figura por tipo

Revision ID: 821aad75ee9c
Revises: 9433f6e50973
Create Date: 2026-07-31 15:39:34.379978

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '821aad75ee9c'
down_revision: Union[str, Sequence[str], None] = '9433f6e50973'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TIPO_FIGURA = sa.Enum(
    'sencillo', 'figura', 'pleno',
    name='tipofigura', native_enum=False, length=20,
)


def upgrade() -> None:
    """Mueve la clasificación sencillo/figura/pleno de partida_figura a figura."""
    with op.batch_alter_table('figura', schema=None) as batch_op:
        # server_default es imprescindible: la columna es NOT NULL y la tabla ya
        # puede tener figuras. Sin un valor por defecto, la migración falla en
        # cuanto exista una sola fila.
        batch_op.add_column(
            sa.Column('tipo', TIPO_FIGURA, nullable=False, server_default='figura')
        )
        batch_op.create_index(batch_op.f('ix_figura_tipo'), ['tipo'], unique=False)

    with op.batch_alter_table('partida_figura', schema=None) as batch_op:
        batch_op.drop_column('tipo_premio')


def downgrade() -> None:
    """Devuelve la clasificación a partida_figura."""
    with op.batch_alter_table('partida_figura', schema=None) as batch_op:
        # Mismo motivo que arriba: sin server_default, revertir rompe si hay
        # formas seleccionadas en alguna partida.
        batch_op.add_column(
            sa.Column(
                'tipo_premio', sa.VARCHAR(length=20),
                nullable=False, server_default='figura',
            )
        )

    with op.batch_alter_table('figura', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_figura_tipo'))
        batch_op.drop_column('tipo')

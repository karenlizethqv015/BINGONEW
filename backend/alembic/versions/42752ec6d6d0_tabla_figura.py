"""tabla figura — catálogo de formas de ganar

Revision ID: 42752ec6d6d0
Revises: 776a172f2bd0
Create Date: 2026-07-30 12:21:55.791506

Nota: los `server_default` usan `sa.func.now()` en vez del literal
`(CURRENT_TIMESTAMP)` que genera el autogenerador. `func.now()` lo traduce cada
motor a su sintaxis, así que esta migración sirve igual en SQLite y en
PostgreSQL (ver backend/README.md).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42752ec6d6d0'
down_revision: Union[str, Sequence[str], None] = '776a172f2bd0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea la tabla `figura` y el índice único de nombre."""
    op.create_table(
        'figura',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=60), nullable=False),
        # JSON genérico, nunca JSONB: la matriz 5x5 del patrón.
        sa.Column('patron', sa.JSON(), nullable=False),
        # Sin llave foránea: la tabla `usuario` es de la Fase 2.
        sa.Column('creado_por_id', sa.Integer(), nullable=True),
        sa.Column(
            'creado_en',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            'actualizado_en',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('figura', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_figura_nombre'), ['nombre'], unique=True)


def downgrade() -> None:
    """Elimina la tabla `figura`."""
    with op.batch_alter_table('figura', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_figura_nombre'))

    op.drop_table('figura')

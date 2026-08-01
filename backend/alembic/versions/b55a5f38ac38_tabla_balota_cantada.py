"""tabla balota_cantada

Revision ID: b55a5f38ac38
Revises: 821aad75ee9c
Create Date: 2026-07-31 16:27:36.680151

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b55a5f38ac38'
down_revision: Union[str, Sequence[str], None] = '821aad75ee9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea la tabla del historial de balotas cantadas."""
    op.create_table(
        'balota_cantada',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partida_id', sa.Integer(), nullable=False),
        sa.Column('numero', sa.Integer(), nullable=False),
        sa.Column('orden', sa.Integer(), nullable=False),
        # func.now() y no el literal (CURRENT_TIMESTAMP) que genera el
        # autogenerador: cada motor lo traduce a su sintaxis.
        sa.Column(
            'cantada_en',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint('numero >= 1 AND numero <= 75', name='ck_balota_rango'),
        sa.ForeignKeyConstraint(['partida_id'], ['partida.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        # El sorteo es sin reemplazo: una balota no puede salir dos veces.
        sa.UniqueConstraint('partida_id', 'numero', name='uq_balota_numero'),
        sa.UniqueConstraint('partida_id', 'orden', name='uq_balota_orden'),
    )
    with op.batch_alter_table('balota_cantada', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_balota_cantada_partida_id'), ['partida_id'], unique=False
        )

    # El autogenerador proponía además quitar el server_default de `figura.tipo`,
    # porque el modelo no lo declaraba. Se resolvió al revés: ahora el modelo sí
    # lo declara, así que la base se queda como está y las migraciones futuras
    # dejan de proponer este cambio una y otra vez.

    # ### end Alembic commands ###


def downgrade() -> None:
    """Elimina la tabla del historial de balotas."""
    with op.batch_alter_table('balota_cantada', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_balota_cantada_partida_id'))

    op.drop_table('balota_cantada')
    # ### end Alembic commands ###

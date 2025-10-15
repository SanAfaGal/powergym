"""add vectorial indexes

Revision ID: 8c27a8605343
Revises: 7b0bbe68686d
Create Date: 2025-10-14 09:13:58.652457

"""
from alembic import op
import sqlalchemy as sa


revision = '8c27a8605343'
down_revision = '7b0bbe68686d'
branch_labels = None
depends_on = None


def upgrade():
    # Índice para búsqueda por tipo de biométrico (FACE)
    op.create_index(
        'idx_biometrics_type_active',
        'client_biometrics',
        ['type', 'is_active'],
        postgresql_where=sa.text("type = 'FACE' AND is_active = true")
    )

    # Índice compuesto para búsquedas de biométricos activos por cliente
    op.create_index(
        'idx_biometrics_client_type_active',
        'client_biometrics',
        ['client_id', 'type', 'is_active']
    )

    # Índice HNSW para búsqueda de similitud vectorial (RÁPIDO para consultas)
    # Usa cosine distance para comparación de embeddings faciales
    op.execute("""
        CREATE INDEX idx_biometrics_embedding_hnsw 
        ON client_biometrics 
        USING hnsw (embedding_vector vector_cosine_ops)
        WHERE embedding_vector IS NOT NULL AND is_active = true;
    """)

    # Índice IVFFlat alternativo (usa menos memoria, bueno para datasets grandes)
    # Descomenta si prefieres este método:
    # op.execute("""
    #     CREATE INDEX idx_biometrics_embedding_ivfflat
    #     ON client_biometrics
    #     USING ivfflat (embedding_vector vector_cosine_ops)
    #     WITH (lists = 100)
    #     WHERE embedding_vector IS NOT NULL AND is_active = true;
    # """)

    # Índice para consultas de clientes activos (usado en JOIN con biométricos)
    op.create_index(
        'idx_clients_active',
        'clients',
        ['is_active'],
        postgresql_where=sa.text("is_active = true")
    )

    # Índice para búsqueda de clientes por DNI (ya existe unique, pero esto acelera lookups)
    op.create_index(
        'idx_clients_dni_type_number',
        'clients',
        ['dni_type', 'dni_number']
    )

    # Índice para attendances por fecha (útil para verificar última asistencia)
    op.create_index(
        'idx_attendances_client_checkin',
        'attendances',
        ['client_id', 'check_in'],
        postgresql_using='btree'
    )

    # Índice para búsqueda de attendances recientes
    op.create_index(
        'idx_attendances_checkin_desc',
        'attendances',
        [sa.text('check_in DESC')]
    )


def downgrade():
    # Eliminar índices en orden inverso
    op.drop_index('idx_attendances_checkin_desc', table_name='attendances')
    op.drop_index('idx_attendances_client_checkin', table_name='attendances')
    op.drop_index('idx_clients_dni_type_number', table_name='clients')
    op.drop_index('idx_clients_active', table_name='clients')
    op.execute("DROP INDEX IF EXISTS idx_biometrics_embedding_hnsw;")
    # op.execute("DROP INDEX IF EXISTS idx_biometrics_embedding_ivfflat;")
    op.drop_index('idx_biometrics_client_type_active', table_name='client_biometrics')
    op.drop_index('idx_biometrics_type_active', table_name='client_biometrics')
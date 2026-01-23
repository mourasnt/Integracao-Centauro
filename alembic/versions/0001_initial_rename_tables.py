"""Initial migration - rename tables to English

Revision ID: 0001
Revises: 
Create Date: 2026-01-23

This migration renames all tables from Portuguese to English names
and updates foreign key references accordingly.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if old tables exist (migration from existing database)
    # If they don't exist, create new tables with English names
    
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # If 'cargas' exists, we need to rename tables
    if 'cargas' in existing_tables:
        # Rename tables from Portuguese to English
        op.rename_table('cargas', 'shipments')
        op.rename_table('cte_cliente', 'client_ctes')
        op.rename_table('cte_subcontratacao', 'subcontracted_ctes')
        op.rename_table('agendamentos', 'schedules')
        op.rename_table('tracking', 'tracking_events')
        op.rename_table('estados', 'states')
        op.rename_table('municipios', 'municipalities')
        
        # Rename columns in shipments (formerly cargas)
        with op.batch_alter_table('shipments') as batch_op:
            batch_op.alter_column('id_3zx', new_column_name='external_id')
            batch_op.alter_column('id_cliente', new_column_name='client_id')
            batch_op.alter_column('origem_uf', new_column_name='origin_state')
            batch_op.alter_column('origem_municipio', new_column_name='origin_city')
            batch_op.alter_column('destino_uf', new_column_name='destination_state')
            batch_op.alter_column('destino_municipio', new_column_name='destination_city')
        
        # Rename columns in client_ctes (formerly cte_cliente)
        with op.batch_alter_table('client_ctes') as batch_op:
            batch_op.alter_column('chave', new_column_name='access_key')
            batch_op.alter_column('carga_id', new_column_name='shipment_id')
            batch_op.alter_column('nfs_json', new_column_name='invoices_json')
            # Update foreign key reference
            batch_op.drop_constraint('cte_cliente_carga_id_fkey', type_='foreignkey')
            batch_op.create_foreign_key(
                'client_ctes_shipment_id_fkey',
                'shipments',
                ['shipment_id'],
                ['id'],
                ondelete='CASCADE'
            )
        
        # Rename columns in subcontracted_ctes (formerly cte_subcontratacao)
        with op.batch_alter_table('subcontracted_ctes') as batch_op:
            batch_op.alter_column('chave', new_column_name='access_key')
            batch_op.alter_column('carga_id', new_column_name='shipment_id')
            batch_op.alter_column('vblog_status_desc', new_column_name='vblog_status_description')
            # Update foreign key reference
            batch_op.drop_constraint('cte_subcontratacao_carga_id_fkey', type_='foreignkey')
            batch_op.create_foreign_key(
                'subcontracted_ctes_shipment_id_fkey',
                'shipments',
                ['shipment_id'],
                ['id'],
                ondelete='CASCADE'
            )
        
        # Rename columns in schedules (formerly agendamentos)
        with op.batch_alter_table('schedules') as batch_op:
            batch_op.alter_column('carga_id', new_column_name='shipment_id')
            batch_op.alter_column('eta_programado', new_column_name='eta_scheduled')
            batch_op.alter_column('eta_realizado', new_column_name='eta_actual')
            batch_op.alter_column('eta_saida', new_column_name='eta_departure')
            batch_op.alter_column('etd_programado', new_column_name='etd_scheduled')
            batch_op.alter_column('etd_realizado', new_column_name='etd_actual')
            batch_op.alter_column('etd_finalizado', new_column_name='etd_completed')
            # Update foreign key reference
            batch_op.drop_constraint('agendamentos_carga_id_fkey', type_='foreignkey')
            batch_op.create_foreign_key(
                'schedules_shipment_id_fkey',
                'shipments',
                ['shipment_id'],
                ['id'],
                ondelete='CASCADE'
            )
        
        # Rename columns in tracking_events (formerly tracking)
        with op.batch_alter_table('tracking_events') as batch_op:
            batch_op.alter_column('cte_cliente_id', new_column_name='client_cte_id')
            batch_op.alter_column('codigo_evento', new_column_name='event_code')
            batch_op.alter_column('descricao', new_column_name='description')
            batch_op.alter_column('data_evento', new_column_name='event_date')
            # Update foreign key reference
            batch_op.drop_constraint('tracking_cte_cliente_id_fkey', type_='foreignkey')
            batch_op.create_foreign_key(
                'tracking_events_client_cte_id_fkey',
                'client_ctes',
                ['client_cte_id'],
                ['id'],
                ondelete='CASCADE'
            )
        
        # Rename columns in states (formerly estados)
        with op.batch_alter_table('states') as batch_op:
            batch_op.alter_column('nome', new_column_name='name')
            batch_op.alter_column('sigla', new_column_name='abbreviation')
            batch_op.alter_column('codigo_ibge', new_column_name='ibge_code')
        
        # Rename columns in municipalities (formerly municipios)
        with op.batch_alter_table('municipalities') as batch_op:
            batch_op.alter_column('nome', new_column_name='name')
            batch_op.alter_column('codigo_ibge', new_column_name='ibge_code')
            batch_op.alter_column('estado_id', new_column_name='state_id')
            # Update foreign key reference
            batch_op.drop_constraint('municipios_estado_id_fkey', type_='foreignkey')
            batch_op.create_foreign_key(
                'municipalities_state_id_fkey',
                'states',
                ['state_id'],
                ['id'],
                ondelete='CASCADE'
            )
    
    else:
        # Fresh install - create tables with English names
        # Users table
        op.create_table(
            'users',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('username', sa.String(), nullable=False),
            sa.Column('hashed_password', sa.String(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('username')
        )
        
        # States table
        op.create_table(
            'states',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('abbreviation', sa.String(2), nullable=False),
            sa.Column('ibge_code', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('abbreviation'),
            sa.UniqueConstraint('ibge_code')
        )
        
        # Municipalities table
        op.create_table(
            'municipalities',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('ibge_code', sa.Integer(), nullable=False),
            sa.Column('state_id', sa.UUID(), nullable=False),
            sa.ForeignKeyConstraint(['state_id'], ['states.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('ibge_code')
        )
        
        # Shipments table
        op.create_table(
            'shipments',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('external_id', sa.String(), nullable=True),
            sa.Column('client_id', sa.String(), nullable=True),
            sa.Column('origin_state', sa.JSON(), nullable=True),
            sa.Column('origin_city', sa.JSON(), nullable=True),
            sa.Column('destination_state', sa.JSON(), nullable=True),
            sa.Column('destination_city', sa.JSON(), nullable=True),
            sa.Column('status', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('external_id')
        )
        op.create_index('ix_shipments_external_id', 'shipments', ['external_id'])
        
        # Client CTes table
        op.create_table(
            'client_ctes',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('shipment_id', sa.UUID(), nullable=False),
            sa.Column('access_key', sa.String(60), nullable=False),
            sa.Column('xml_encrypted', sa.Text(), nullable=True),
            sa.Column('invoices_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_client_ctes_shipment_id', 'client_ctes', ['shipment_id'])
        op.create_index('ix_client_ctes_access_key', 'client_ctes', ['access_key'])
        
        # Subcontracted CTes table
        op.create_table(
            'subcontracted_ctes',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('shipment_id', sa.UUID(), nullable=False),
            sa.Column('access_key', sa.String(60), nullable=False),
            sa.Column('xml_encrypted', sa.Text(), nullable=True),
            sa.Column('vblog_status_code', sa.String(20), nullable=True),
            sa.Column('vblog_status_description', sa.Text(), nullable=True),
            sa.Column('vblog_raw_response', sa.Text(), nullable=True),
            sa.Column('vblog_attempts', sa.Integer(), nullable=False, default=0),
            sa.Column('vblog_received_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_subcontracted_ctes_shipment_id', 'subcontracted_ctes', ['shipment_id'])
        op.create_index('ix_subcontracted_ctes_access_key', 'subcontracted_ctes', ['access_key'])
        
        # Schedules table
        op.create_table(
            'schedules',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('shipment_id', sa.UUID(), nullable=False),
            sa.Column('eta_scheduled', sa.DateTime(timezone=True), nullable=True),
            sa.Column('eta_actual', sa.DateTime(timezone=True), nullable=True),
            sa.Column('eta_departure', sa.DateTime(timezone=True), nullable=True),
            sa.Column('etd_scheduled', sa.DateTime(timezone=True), nullable=True),
            sa.Column('etd_actual', sa.DateTime(timezone=True), nullable=True),
            sa.Column('etd_completed', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('shipment_id')
        )
        
        # Tracking events table
        op.create_table(
            'tracking_events',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('client_cte_id', sa.UUID(), nullable=False),
            sa.Column('event_code', sa.String(10), nullable=False),
            sa.Column('description', sa.String(255), nullable=False),
            sa.Column('event_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['client_cte_id'], ['client_ctes.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_tracking_events_client_cte_id', 'tracking_events', ['client_cte_id'])


def downgrade() -> None:
    # Check which tables exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'shipments' in existing_tables:
        # Check if this was a rename or fresh install by looking for old-style data
        # For safety, we'll just rename back to Portuguese names
        
        # Rename columns back in municipalities
        with op.batch_alter_table('municipalities') as batch_op:
            batch_op.alter_column('name', new_column_name='nome')
            batch_op.alter_column('ibge_code', new_column_name='codigo_ibge')
            batch_op.alter_column('state_id', new_column_name='estado_id')
        
        # Rename columns back in states
        with op.batch_alter_table('states') as batch_op:
            batch_op.alter_column('name', new_column_name='nome')
            batch_op.alter_column('abbreviation', new_column_name='sigla')
            batch_op.alter_column('ibge_code', new_column_name='codigo_ibge')
        
        # Rename columns back in tracking_events
        with op.batch_alter_table('tracking_events') as batch_op:
            batch_op.alter_column('client_cte_id', new_column_name='cte_cliente_id')
            batch_op.alter_column('event_code', new_column_name='codigo_evento')
            batch_op.alter_column('description', new_column_name='descricao')
            batch_op.alter_column('event_date', new_column_name='data_evento')
        
        # Rename columns back in schedules
        with op.batch_alter_table('schedules') as batch_op:
            batch_op.alter_column('shipment_id', new_column_name='carga_id')
            batch_op.alter_column('eta_scheduled', new_column_name='eta_programado')
            batch_op.alter_column('eta_actual', new_column_name='eta_realizado')
            batch_op.alter_column('eta_departure', new_column_name='eta_saida')
            batch_op.alter_column('etd_scheduled', new_column_name='etd_programado')
            batch_op.alter_column('etd_actual', new_column_name='etd_realizado')
            batch_op.alter_column('etd_completed', new_column_name='etd_finalizado')
        
        # Rename columns back in subcontracted_ctes
        with op.batch_alter_table('subcontracted_ctes') as batch_op:
            batch_op.alter_column('access_key', new_column_name='chave')
            batch_op.alter_column('shipment_id', new_column_name='carga_id')
            batch_op.alter_column('vblog_status_description', new_column_name='vblog_status_desc')
        
        # Rename columns back in client_ctes
        with op.batch_alter_table('client_ctes') as batch_op:
            batch_op.alter_column('access_key', new_column_name='chave')
            batch_op.alter_column('shipment_id', new_column_name='carga_id')
            batch_op.alter_column('invoices_json', new_column_name='nfs_json')
        
        # Rename columns back in shipments
        with op.batch_alter_table('shipments') as batch_op:
            batch_op.alter_column('external_id', new_column_name='id_3zx')
            batch_op.alter_column('client_id', new_column_name='id_cliente')
            batch_op.alter_column('origin_state', new_column_name='origem_uf')
            batch_op.alter_column('origin_city', new_column_name='origem_municipio')
            batch_op.alter_column('destination_state', new_column_name='destino_uf')
            batch_op.alter_column('destination_city', new_column_name='destino_municipio')
        
        # Rename tables back to Portuguese
        op.rename_table('municipalities', 'municipios')
        op.rename_table('states', 'estados')
        op.rename_table('tracking_events', 'tracking')
        op.rename_table('schedules', 'agendamentos')
        op.rename_table('subcontracted_ctes', 'cte_subcontratacao')
        op.rename_table('client_ctes', 'cte_cliente')
        op.rename_table('shipments', 'cargas')

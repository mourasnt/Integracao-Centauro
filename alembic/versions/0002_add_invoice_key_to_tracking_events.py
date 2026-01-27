"""Add invoice_key column to tracking_events table.

This migration adds a nullable invoice_key column to track events per NF-e
instead of per CTe, enabling individual invoice status tracking.

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add invoice_key column to tracking_events table."""
    op.add_column(
        'tracking_events',
        sa.Column(
            'invoice_key',
            sa.String(60),
            nullable=True,
            comment='NF-e key this event applies to (null = all invoices in CTe)',
        )
    )
    # Create index for faster lookups by invoice key
    op.create_index(
        'ix_tracking_events_invoice_key',
        'tracking_events',
        ['invoice_key'],
        unique=False,
    )


def downgrade() -> None:
    """Remove invoice_key column from tracking_events table."""
    op.drop_index('ix_tracking_events_invoice_key', table_name='tracking_events')
    op.drop_column('tracking_events', 'invoice_key')

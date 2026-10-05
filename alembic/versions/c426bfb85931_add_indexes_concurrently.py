"""add indexes concurrently

Revision ID: c426bfb85931
Revises: 7354b7ac0c59
Create Date: 2026-10-04 03:10:21.782454

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c426bfb85931"
down_revision: str | Sequence[str] | None = "7354b7ac0c59"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # CREATE INDEX CONCURRENTLY не можна виконувати всередині транзакції,
    # тому виходимо з транзакції Alembic на час створення індексів
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_notifications_idempotency_key",
            "notifications",
            ["idempotency_key"],
            unique=True,
            postgresql_concurrently=True,
        )
        op.create_index(
            "ix_notifications_status",
            "notifications",
            ["status"],
            postgresql_concurrently=True,
        )
        op.create_index(
            "ix_delivery_logs_notification_id",
            "delivery_logs",
            ["notification_id"],
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.get_context().autocommit_block():
        op.drop_index(
            "ix_delivery_logs_notification_id",
            table_name="delivery_logs",
            postgresql_concurrently=True,
        )
        op.drop_index(
            "ix_notifications_status",
            table_name="notifications",
            postgresql_concurrently=True,
        )
        op.drop_index(
            "ix_notifications_idempotency_key",
            table_name="notifications",
            postgresql_concurrently=True,
        )

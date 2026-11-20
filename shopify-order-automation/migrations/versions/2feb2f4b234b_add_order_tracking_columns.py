
"""Add order tracking and notification columns.

Revision ID: 2feb2f4b234b
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "2feb2f4b234b"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    # 1. Add notification columns as nullable first.
    op.add_column(
        "notification_jobs",
        sa.Column("notification_type", sa.String(40), nullable=True)
    )

    op.add_column(
        "notification_jobs",
        sa.Column("dedupe_key", sa.String(255), nullable=True)
    )

    op.add_column(
        "notification_jobs",
        sa.Column("payload", sa.JSON(), nullable=True)
    )

    # 2. Backfill existing notification jobs.
    # These legacy rows were created by the old order-creation webhook.
    op.execute("""
        UPDATE notification_jobs
        SET
            notification_type = 'confirmation',
            dedupe_key = 'legacy:' || id::text,
            payload = '{}'::json
        WHERE notification_type IS NULL
           OR dedupe_key IS NULL
           OR payload IS NULL
    """)

    # 3. Enforce NOT NULL after backfilling.
    op.alter_column(
        "notification_jobs",
        "notification_type",
        existing_type=sa.String(40),
        nullable=False
    )

    op.alter_column(
        "notification_jobs",
        "dedupe_key",
        existing_type=sa.String(255),
        nullable=False
    )

    op.alter_column(
        "notification_jobs",
        "payload",
        existing_type=sa.JSON(),
        nullable=False
    )

    # 4. Replace old unique constraint.
    op.drop_constraint(
        "uq_order_channel",
        "notification_jobs",
        type_="unique"
    )

    op.create_unique_constraint(
        "uq_notification_dedupe",
        "notification_jobs",
        ["dedupe_key"]
    )

    # 5. Add order tracking columns as nullable.
    op.add_column(
        "orders",
        sa.Column("status", sa.String(30), nullable=True)
    )

    op.add_column(
        "orders",
        sa.Column(
            "cancelled_at",
            sa.DateTime(timezone=True),
            nullable=True
        )
    )

    op.add_column(
        "orders",
        sa.Column("fulfillment_status", sa.String(30), nullable=True)
    )

    op.add_column(
        "orders",
        sa.Column("tracking_company", sa.String(100), nullable=True)
    )

    op.add_column(
        "orders",
        sa.Column("tracking_number", sa.String(150), nullable=True)
    )

    op.add_column(
        "orders",
        sa.Column("tracking_url", sa.String(1000), nullable=True)
    )

    op.add_column(
        "orders",
        sa.Column(
            "delivered_at",
            sa.DateTime(timezone=True),
            nullable=True
        )
    )

    op.add_column(
        "orders",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True
        )
    )

    # 6. Backfill existing orders.
    op.execute("""
        UPDATE orders
        SET
            status = 'received',
            fulfillment_status = 'unfulfilled',
            updated_at = COALESCE(created_at, CURRENT_TIMESTAMP)
        WHERE status IS NULL
           OR fulfillment_status IS NULL
           OR updated_at IS NULL
    """)

    # 7. Enforce NOT NULL.
    op.alter_column(
        "orders",
        "status",
        existing_type=sa.String(30),
        nullable=False
    )

    op.alter_column(
        "orders",
        "fulfillment_status",
        existing_type=sa.String(30),
        nullable=False
    )

    op.alter_column(
        "orders",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False
    )

    # 8. Add status index.
    op.create_index(
        "ix_orders_status",
        "orders",
        ["status"],
        unique=False
    )


def downgrade():

    # Remove the order tracking index and columns.
    op.drop_index("ix_orders_status", table_name="orders")

    op.drop_column("orders", "updated_at")
    op.drop_column("orders", "delivered_at")
    op.drop_column("orders", "tracking_url")
    op.drop_column("orders", "tracking_number")
    op.drop_column("orders", "tracking_company")
    op.drop_column("orders", "fulfillment_status")
    op.drop_column("orders", "cancelled_at")
    op.drop_column("orders", "status")

    # Restore the old constraint only if existing data permits it.
    op.drop_constraint(
        "uq_notification_dedupe",
        "notification_jobs",
        type_="unique"
    )

    op.create_unique_constraint(
        "uq_order_channel",
        "notification_jobs",
        ["order_id", "channel"]
    )

    op.drop_column("notification_jobs", "payload")
    op.drop_column("notification_jobs", "dedupe_key")
    op.drop_column("notification_jobs", "notification_type")

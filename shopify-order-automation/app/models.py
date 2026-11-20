
from datetime import datetime, timezone
from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)

    shopify_order_id = db.Column(
        db.String(80), unique=True, nullable=False, index=True
    )

    order_number = db.Column(db.String(80), nullable=False)
    customer_name = db.Column(db.String(200), nullable=False, default="there")
    phone = db.Column(db.String(40), nullable=False)
    currency = db.Column(db.String(8), nullable=False)
    total_price = db.Column(db.String(40), nullable=False)
    line_items = db.Column(db.JSON, nullable=False)

    # Order lifecycle
    status = db.Column(
        db.String(30), nullable=False, default="received", index=True
    )

    cancelled_at = db.Column(db.DateTime(timezone=True))

    # Fulfillment and delivery tracking
    fulfillment_status = db.Column(
        db.String(30), nullable=False, default="unfulfilled"
    )

    tracking_company = db.Column(db.String(100))
    tracking_number = db.Column(db.String(150))
    tracking_url = db.Column(db.String(1000))

    delivered_at = db.Column(db.DateTime(timezone=True))

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False
    )


class NotificationJob(db.Model):
    __tablename__ = "notification_jobs"

    __table_args__ = (
        db.UniqueConstraint(
            "dedupe_key",
            name="uq_notification_dedupe"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id"),
        nullable=False,
        index=True
    )

    # confirmation, cancelled, shipped, delivered, etc.
    notification_type = db.Column(
        db.String(40), nullable=False
    )

    # Prevent duplicate notification jobs
    dedupe_key = db.Column(
        db.String(255), nullable=False
    )

    payload = db.Column(
        db.JSON, nullable=False, default=dict
    )

    channel = db.Column(
        db.String(30), nullable=False, default="whatsapp"
    )

    status = db.Column(
        db.String(20), nullable=False, default="pending", index=True
    )

    attempts = db.Column(
        db.Integer, nullable=False, default=0
    )

    next_attempt_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        nullable=False,
        index=True
    )

    last_error = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        nullable=False
    )

    sent_at = db.Column(db.DateTime(timezone=True))

    order = db.relationship("Order")

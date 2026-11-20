from app.extensions import db
from app.models import NotificationJob


def queue_notification(order, notification_type, dedupe_key, payload=None):
    existing = NotificationJob.query.filter_by(
        dedupe_key=dedupe_key
    ).first()

    if existing:
        return existing

    job = NotificationJob(
        order_id=order.id,
        notification_type=notification_type,
        dedupe_key=dedupe_key,
        payload=payload or {},
        channel="whatsapp",
        status="pending"
    )

    db.session.add(job)
    return job
import time
from datetime import datetime, timezone, timedelta
from flask import current_app
from sqlalchemy import select
from app import create_app
from app.extensions import db
from app.models import Order, NotificationJob
from app.services.ai_service import create_personalised_message
from app.services.whatsapp_service import send_order_template

def claim_job():
    # PostgreSQL row lock prevents two workers claiming the same pending job.
    job = db.session.execute(
        select(NotificationJob)
        .where(NotificationJob.status == "pending",
               NotificationJob.next_attempt_at <= datetime.now(timezone.utc))
        .order_by(NotificationJob.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    ).scalar_one_or_none()

    if not job:
        return None

    job.status = "processing"
    job.attempts += 1
    order = db.session.get(Order, job.order_id)
    data = {
        "job_id": job.id,
        "phone": order.phone,
        "customer_name": order.customer_name,
        "order_number": order.order_number,
        "currency": order.currency,
        "total_price": order.total_price,
        "line_items": order.line_items,
        "attempts": job.attempts,
    }
    db.session.commit()
    return data

def update_job(job_id: int, error: str | None = None):
    job = db.session.get(NotificationJob, job_id)
    if not job:
        return
    if error is None:
        job.status = "sent"
        job.sent_at = datetime.now(timezone.utc)
        job.last_error = None
    else:
        job.last_error = error[:4000]
        if job.attempts >= current_app.config["MAX_JOB_ATTEMPTS"]:
            job.status = "failed"
        else:
            job.status = "pending"
            seconds = min(3600, 2 ** min(job.attempts, 10))
            job.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    db.session.commit()

def run_worker():
    app = create_app()
    with app.app_context():
        while True:
            try:
                job = claim_job()
                if not job:
                    time.sleep(current_app.config["WORKER_POLL_SECONDS"])
                    continue
                try:
                    message = create_personalised_message(job)
                    send_order_template(
                        job["phone"], job["customer_name"], job["order_number"], message
                    )
                    update_job(job["job_id"])
                except Exception as exc:
                    current_app.logger.exception("Notification job failed: %s", job["job_id"])
                    db.session.rollback()
                    update_job(job["job_id"], str(exc))
            except Exception:
                current_app.logger.exception("Worker loop error")
                db.session.rollback()
                time.sleep(current_app.config["WORKER_POLL_SECONDS"])
def build_notification_message(job, order):
    notification_type = job.notification_type
    data = job.payload or {}

    if notification_type == "cancelled":
        return (
            f"Your order {order.order_number} has been cancelled."
        )

    if notification_type == "shipped":
        return (
            f"Your order {order.order_number} has been shipped. "
            f"Tracking number: {data.get('tracking_number') or 'Not available'}. "
            f"Track here: {data.get('tracking_url') or 'Check with the carrier'}"
        )

    if notification_type == "in_transit":
        return f"Your order {order.order_number} is in transit."

    if notification_type == "out_for_delivery":
        return f"Your order {order.order_number} is out for delivery."

    if notification_type == "delivered":
        return f"Your order {order.order_number} has been delivered."

    if notification_type == "confirmation":
        return create_personalised_message({
            "customer_name": order.customer_name,
            "order_number": order.order_number,
            "currency": order.currency,
            "total_price": str(order.total_price),
            "line_items": order.line_items
        })

    raise ValueError(f"Unknown notification type: {notification_type}")                

if __name__ == "__main__":
    run_worker()

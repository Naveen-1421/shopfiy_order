import base64
from datetime import datetime
import datetime
import hashlib
import hmac
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import Order, NotificationJob
from datetime import datetime, timezone
from app.services.notification_queue import queue_notification

shopify_bp = Blueprint("shopify", __name__)

def valid_shopify_hmac(raw_body: bytes, supplied: str | None) -> bool:
    if not supplied:
        return False
    digest = hmac.new(
        current_app.config["SHOPIFY_WEBHOOK_SECRET"].encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected, supplied)

@shopify_bp.post("/webhooks/shopify/orders-create")
def orders_create():
    raw = request.get_data(cache=True)
    if not valid_shopify_hmac(raw, request.headers.get("X-Shopify-Hmac-Sha256")):
        return jsonify(error="Invalid Shopify signature"), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Invalid JSON payload"), 400

    try:
        shopify_id = str(payload["id"])
        customer = payload.get("customer") or {}
        shipping = payload.get("shipping_address") or {}
        billing = payload.get("billing_address") or {}
        phone = (shipping.get("phone") or billing.get("phone") or
                 payload.get("phone") or customer.get("phone") or "")
        phone = "".join(ch for ch in phone if ch.isdigit())
        if not phone:
            return jsonify(error="Order has no customer phone number"), 422

        first = customer.get("first_name") or shipping.get("first_name") or ""
        last = customer.get("last_name") or shipping.get("last_name") or ""
        name = (f"{first} {last}".strip() or "there")[:200]
        line_items = [{
            "title": str(item.get("title") or "Item")[:200],
            "quantity": int(item.get("quantity") or 1),
        } for item in payload.get("line_items", [])]

        existing = Order.query.filter_by(shopify_order_id=shopify_id).first()
        if existing:
            return jsonify(accepted=True, duplicate=True), 202

        order = Order(
            shopify_order_id=shopify_id,
            order_number=str(payload.get("name") or payload.get("order_number") or shopify_id),
            customer_name=name,
            phone=phone,
            currency=str(payload.get("currency") or "USD")[:8],
            total_price=str(payload.get("total_price") or "0")[:40],
            line_items=line_items,
        )
        db.session.add(order)
        db.session.flush()
        queue_notification(
            order,
            "confirmation",
            f"{order.id}:confirmation",
            {}
        )

        db.session.commit()
        return jsonify(accepted=True, duplicate=False), 202
    except (KeyError, TypeError, ValueError):
        db.session.rollback()
        return jsonify(error="Invalid Shopify order payload"), 400
    except IntegrityError:
        db.session.rollback()
        # Unique constraint protects against concurrent duplicate webhook deliveries.
        return jsonify(accepted=True, duplicate=True), 202
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to persist Shopify order webhook")
        return jsonify(error="Temporary server error"), 500
@shopify_bp.post("/webhooks/shopify/orders-cancelled")
def orders_cancelled():

    raw = request.get_data(cache=True)

    if not valid_shopify_hmac(
        raw,
        request.headers.get("X-Shopify-Hmac-Sha256")
    ):
        return jsonify(error="Invalid Shopify signature"), 401

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict) or not payload.get("id"):
        return jsonify(error="Invalid payload"), 400

    try:
        shopify_id = str(payload["id"])

        order = Order.query.filter_by(
            shopify_order_id=shopify_id
        ).with_for_update().first()

        if not order:
            # In the complete implementation, persist this event
            # in webhook_events and reconcile when orders/create arrives.
            return jsonify(
                accepted=True,
                pending_order=True
            ), 202

        if order.status in ("cancelled", "refunded"):
            return jsonify(accepted=True, duplicate=True), 202

        order.status = "cancelled"
        order.cancelled_at = datetime.now(timezone.utc)

        # Cancel unsent confirmation/tracking jobs.
        NotificationJob.query.filter(
            NotificationJob.order_id == order.id,
            NotificationJob.status.in_(["pending", "retry"])
        ).update(
            {"status": "cancelled"},
            synchronize_session=False
        )

        queue_notification(
            order,
            "cancelled",
            f"{order.id}:cancelled",
            {"reason": payload.get("cancel_reason")}
        )

        db.session.commit()

        return jsonify(
            accepted=True,
            status="cancelled"
        ), 202

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Order cancellation webhook failed")
        return jsonify(error="Temporary server error"), 500
@shopify_bp.post("/webhooks/shopify/fulfillments")
def fulfillment_update():

    raw = request.get_data(cache=True)

    if not valid_shopify_hmac(
        raw,
        request.headers.get("X-Shopify-Hmac-Sha256")
    ):
        return jsonify(error="Invalid Shopify signature"), 401

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify(error="Invalid payload"), 400

    try:
        shopify_order_id = str(payload["order_id"])

        order = Order.query.filter_by(
            shopify_order_id=shopify_order_id
        ).with_for_update().first()

        if not order:
            return jsonify(
                accepted=True,
                pending_order=True
            ), 202

        if order.status in ("cancelled", "refunded"):
            return jsonify(accepted=True, skipped=True), 202

        tracking_numbers = payload.get("tracking_numbers") or []
        tracking_urls = payload.get("tracking_urls") or []

        tracking_number = (
            str(tracking_numbers[0])
            if tracking_numbers else None
        )

        tracking_url = (
            str(tracking_urls[0])
            if tracking_urls else None
        )

        order.tracking_company = payload.get("tracking_company")
        order.tracking_number = tracking_number
        order.tracking_url = tracking_url
        order.fulfillment_status = "shipped"

        fulfillment_id = str(payload.get("id", "unknown"))

        queue_notification(
            order,
            "shipped",
            f"{order.id}:fulfillment:{fulfillment_id}:shipped",
            {
                "tracking_company": order.tracking_company,
                "tracking_number": tracking_number,
                "tracking_url": tracking_url
            }
        )

        db.session.commit()

        return jsonify(
            accepted=True,
            status="shipped"
        ), 202

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Fulfillment webhook failed")
        return jsonify(error="Temporary server error"), 500
    
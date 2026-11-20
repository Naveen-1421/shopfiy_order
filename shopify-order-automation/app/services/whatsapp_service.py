
import requests
from flask import current_app


def send_order_template(
    phone: str,
    customer_name: str,
    order_number: str,
    message: str
):
    api_version = current_app.config["WHATSAPP_API_VERSION"]
    phone_number_id = current_app.config["WHATSAPP_PHONE_NUMBER_ID"]
    access_token = current_app.config["WHATSAPP_ACCESS_TOKEN"]

    url = (
        f"https://graph.facebook.com/{api_version}/"
        f"{phone_number_id}/messages"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": {
            "name": current_app.config["WHATSAPP_TEMPLATE_NAME"],
            "language": {
                "code": current_app.config["WHATSAPP_TEMPLATE_LANGUAGE"]
            },
            "components": [{
                "type": "body",
                "parameters": [
                    {"type": "text", "text": customer_name[:60]},
                    {"type": "text", "text": order_number[:60]},
                    {"type": "text", "text": message[:500]},
                ],
            }],
        },
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=(5, 20)
    )

    if not response.ok:
        current_app.logger.error(
            "WhatsApp API error. Status: %s | Response: %s",
            response.status_code,
            response.text
        )
        raise Exception(
            f"WhatsApp API failed: {response.status_code} - {response.text}"
        )

    result = response.json()
    current_app.logger.info("WhatsApp message response: %s", result)

    return result

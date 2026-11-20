import json
from flask import current_app
from openai import OpenAI

def create_personalised_message(order: dict) -> str:
    client = OpenAI(api_key=current_app.config["OPENAI_API_KEY"])
    safe_order = {
        "customer_first_name": order["customer_name"].split()[0],
        "order_number": order["order_number"],
        "products": [
            {"title": item.get("title", "Item"), "quantity": item.get("quantity", 1)}
            for item in order["line_items"][:10]
        ],
        "total": f'{order["currency"]} {order["total_price"]}',
    }
    result = client.chat.completions.create(
        model=current_app.config["OPENAI_MODEL"],
        temperature=0.4,
        max_tokens=100,
        messages=[
            {"role": "system", "content":
             "Write a friendly, concise WhatsApp order confirmation. Use only supplied facts. "
             "Do not invent delivery dates, tracking links, discounts, or payment status. "
             "Maximum 240 characters."},
            {"role": "user", "content": json.dumps(safe_order, ensure_ascii=False)},
        ],
    )
    message = (result.choices[0].message.content or "").strip()
    if not message:
        raise RuntimeError("AI returned an empty confirmation")
    return message[:500]

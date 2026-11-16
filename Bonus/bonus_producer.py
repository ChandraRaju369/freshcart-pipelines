
import json
import time
from datetime import datetime, timezone

import pika

EXCHANGE = "freshcart-bonus"
ROUTING_KEY = "freshcart.orders.web"

# Use a fixed batch ID so we can test idempotency later.
BATCH_ID = "BONUS-001"

CUSTOMERS = [
    ("priya.r@gmail.com", "Priya R", "600041"),
    ("arjun.k@yahoo.in", "Arjun K", "560034"),
    ("meera@outlook.com", "Meera S", "400050"),
]


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost")
    )
    channel = connection.channel()

    channel.exchange_declare(
        exchange=EXCHANGE,
        exchange_type="topic",
        durable=True,
    )

    print("FreshCart bonus producer started.")
    print("Publishing one order every 2 seconds.")

    try:
        for number in range(1, 36):
            email, name, pincode = CUSTOMERS[
                (number - 1) % len(CUSTOMERS)
            ]

            order = {
                "order_id": f"BONUS-ORDER-{number:03d}",
                "cust_email": email,
                "cust_name": name,
                "order_date": "2026-09-03",
                "amount": str(500 + number * 25),
                "currency": "INR",
                "pincode": pincode,
                "updated_at": "2026-09-03 12:00:00",
            }

            message = {
                "batch_id": BATCH_ID,
                "source": "web",
                "published_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "data": order,
            }

            channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=ROUTING_KEY,
                body=json.dumps(message).encode("utf-8"),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                ),
            )

            print(f"Published: {order['order_id']}")
            time.sleep(2)

    except KeyboardInterrupt:
        print("Producer stopped.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()

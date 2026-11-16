
import json
import time
from pathlib import Path

import pika

EXCHANGE = "freshcart-bonus"
QUEUE = "freshcart-bonus-orders"
ROUTING_KEY = "freshcart.orders.#"

OUTPUT_FILE = Path(__file__).resolve().parent / "bonus_orders.jsonl"
COLLECTION_SECONDS = 60


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

    channel.queue_declare(
        queue=QUEUE,
        durable=True,
    )

    channel.queue_bind(
        exchange=EXCHANGE,
        queue=QUEUE,
        routing_key=ROUTING_KEY,
    )

    channel.basic_qos(prefetch_count=1)

    received = 0
    start_time = time.monotonic()

    print("FreshCart bonus consumer started.")
    print("Collecting orders for 60 seconds...")

    with open(OUTPUT_FILE, "a", encoding="utf-8") as file:

        while time.monotonic() - start_time < COLLECTION_SECONDS:

            method, properties, body = channel.basic_get(
                queue=QUEUE,
                auto_ack=False,
            )

            if method is None:
                time.sleep(0.2)
                continue

            try:
                message = json.loads(body)

                if not isinstance(message.get("data"), dict):
                    raise ValueError("Missing order data")

                order = message["data"]

                if not order.get("order_id"):
                    raise ValueError("Missing order_id")

                file.write(
                    json.dumps(order, ensure_ascii=False) + "\n"
                )
                file.flush()

                channel.basic_ack(
                    delivery_tag=method.delivery_tag
                )

                received += 1
                print(
                    f"Received: {order['order_id']}"
                )

            except (ValueError, json.JSONDecodeError) as error:
                print(f"Rejected invalid message: {error}")
                channel.basic_nack(
                    delivery_tag=method.delivery_tag,
                    requeue=False,
                )

    connection.close()

    print("\nCollection completed.")
    print(f"Total orders received: {received}")
    print(f"Orders saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

"""Create and verify customer orders through the Supabase Data API."""
from datetime import date
from decimal import Decimal

from database import get_client, get_customers, get_products


def print_table(headers, rows):
    """Print rows of strings as a table with aligned columns."""
    # Each column is as wide as its longest value or heading.
    widths = [max(len(header), *(len(row[index]) for row in rows)) for index, header in enumerate(headers)]
    print(" | ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def display_customers_and_products(customers, products):
    """Show the customers and products that were loaded from Supabase."""
    print("\nCustomers")
    print_table(
        ["Customer ID", "Customer Name"],
        [[str(row["customer_id"]), str(row["name"])] for row in customers],
    )
    print("\nProducts")
    print_table(
        ["Product ID", "Product Name", "Current Price"],
        [[str(row["product_id"]), str(row["product_name"]), f"${Decimal(str(row['price'])):.2f}"]
         for row in products],
    )


def prompt_for_existing_id(label, valid_ids):
    """Ask until the user enters an integer ID that exists in valid_ids."""
    while True:
        raw_value = input(f"Enter {label} ID: ").strip()
        try:
            value = int(raw_value)
        except ValueError:
            # int() rejects text and decimals such as "hello" or "1.5".
            print("Please enter a whole-number ID.")
            continue
        if value not in valid_ids:
            print(f"That {label.lower()} ID is not in the list. Please try again.")
            continue
        return value


def prompt_for_quantity():
    """Ask until the user enters a positive whole number."""
    while True:
        raw_value = input("Enter quantity: ").strip()
        try:
            quantity = int(raw_value)
        except ValueError:
            print("Please enter a positive whole number, such as 1 or 2.")
            continue
        if quantity <= 0:
            print("Quantity must be greater than zero.")
            continue
        return quantity


def prompt_yes_no(question):
    """Ask a Y/N question until the user answers Y or N (any case)."""
    while True:
        answer = input(f"{question} (Y/N): ").strip().lower()
        if answer in ("y", "n"):
            return answer == "y"
        print("Please enter Y or N.")


def prompt_for_confirmation():
    return prompt_yes_no("Confirm this purchase?")


def display_order_summary(customer, product, quantity, unit_price):
    """Show the order details before the user confirms it."""
    print("\nOrder summary")
    print(f"Customer: {customer['name']}")
    print(f"Product: {product['product_name']}")
    print(f"Quantity: {quantity}")
    print(f"Current unit price: ${unit_price:.2f}")
    print(f"Order total: ${unit_price * quantity:.2f}")


def insert_order(client, customer_id, product_id, quantity, unit_price):
    """Insert one order and return the order ID that the database generated."""
    payload = {
        "customer_id": customer_id,
        "product_id": product_id,
        "quantity": quantity,
        "order_date": date.today().isoformat(),
        "unit_price": str(unit_price),
    }
    # order_id is not sent; the database creates it and returns it here.
    inserted = client.table("orders").insert(payload).select("order_id").execute().data
    if not inserted or inserted[0].get("order_id") is None:
        raise RuntimeError("The API did not return a generated order ID.")
    return inserted[0]["order_id"]


def fetch_order(client, order_id):
    """Query Supabase again for the saved order, including customer and product names."""
    # The embedded customers(...) and products(...) use the foreign keys on orders.
    verified = (
        client.table("orders")
        .select("order_id, quantity, unit_price, order_date, customers(name), products(product_name)")
        .eq("order_id", order_id)
        .execute()
        .data
    )
    if not verified:
        raise LookupError("The inserted order was not returned by the verification query.")
    return verified[0]


def relation_value(record, key):
    """Return an embedded related record as a dict, whether the API sent a dict or a list."""
    relation = record.get(key) or {}
    if isinstance(relation, list):
        relation = relation[0] if relation else {}
    return relation


def display_verified_order(order):
    """Print the order retrieved from the database, using its stored unit_price for the total."""
    unit_price = Decimal(str(order["unit_price"]))
    total = unit_price * int(order["quantity"])
    customer = relation_value(order, "customers").get("name", "(unavailable)")
    product = relation_value(order, "products").get("product_name", "(unavailable)")
    print_table(
        ["Order ID", "Customer", "Product", "Quantity", "Unit Price", "Total", "Order Date"],
        [[
            str(order["order_id"]), customer, product, str(order["quantity"]),
            f"${unit_price:.2f}", f"${total:.2f}", str(order["order_date"]),
        ]],
    )


def save_and_verify(customer_id, product_id, quantity, unit_price):
    """Insert the order, then verify it with a separate query. Never retries the insert."""
    try:
        client = get_client()
        order_id = insert_order(client, customer_id, product_id, quantity, unit_price)
    except Exception:
        # Do not print the exception itself; it could include connection details.
        print("The order could not be saved. Check your Supabase settings and connection, then try again.")
        return

    print(f"\nOrder saved. Supabase assigned order ID {order_id}.")

    try:
        saved_order = fetch_order(client, order_id)
    except Exception:
        print(f"Verification could not be completed for order ID {order_id}. "
              "The order was not inserted again.")
        return

    print("\nSaved order retrieved from Supabase:")
    display_verified_order(saved_order)


def enter_one_order(customer_by_id, product_by_id):
    """Collect, confirm, and save a single order. All values are local to this call."""
    customer_id = prompt_for_existing_id("customer", customer_by_id.keys())
    product_id = prompt_for_existing_id("product", product_by_id.keys())
    quantity = prompt_for_quantity()
    customer = customer_by_id[customer_id]
    product = product_by_id[product_id]
    # The price comes from the database, not from the user.
    unit_price = Decimal(str(product["price"]))

    display_order_summary(customer, product, quantity, unit_price)

    if not prompt_for_confirmation():
        print("Order cancelled; nothing was inserted.")
        return
    save_and_verify(customer_id, product_id, quantity, unit_price)


def run():
    """Load data from Supabase, then take orders until the user chooses to exit."""
    try:
        customers = get_customers()
        products = get_products()
    except Exception:
        print("Could not load customers and products from Supabase. Check your .env settings and connection.")
        return

    if not customers:
        print("No customers were found. Load customer records before entering an order.")
        return
    if not products:
        print("No products were found. Load product records before entering an order.")
        return

    display_customers_and_products(customers, products)

    # Look up records by ID for validation and for the order summary.
    customer_by_id = {int(row["customer_id"]): row for row in customers}
    product_by_id = {int(row["product_id"]): row for row in products}

    while True:
        enter_one_order(customer_by_id, product_by_id)
        if not prompt_yes_no("\nEnter another order?"):
            print("Goodbye.")
            return


if __name__ == "__main__":
    try:
        run()
    except (EOFError, KeyboardInterrupt):
        print("\nOrder entry stopped.")

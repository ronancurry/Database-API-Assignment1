"""Reusable API functions for local classroom scripts and a future backend.
Every .execute() sends an HTTP request; this is not a direct PostgreSQL connection.
"""
from datetime import date
from decimal import Decimal
from functools import lru_cache
from supabase import create_client
from config import get_settings


@lru_cache(maxsize=1)
def get_client():
    url, key = get_settings()
    return create_client(url, key)


def get_products(max_price=None):
    query = get_client().table("products").select("*")
    if max_price is not None:
        query = query.lte("price", float(max_price))
    return query.order("product_id").execute().data


def get_customers(city=None):
    query = get_client().table("customers").select("*")
    if city:
        query = query.eq("city", city)
    return query.order("customer_id").execute().data


def add_customer(name, email, city):
    if not all(value.strip() for value in (name, email, city)):
        raise ValueError("Name, email, and city are required.")
    response = get_client().table("customers").insert({
        "name": name.strip(), "email": email.strip().lower(), "city": city.strip()
    }).execute()
    return response.data[0]


def update_product_price(product_id, price):
    price = Decimal(str(price))
    if not price.is_finite() or price < 0 or price != price.quantize(Decimal("0.01")):
        raise ValueError("Use a nonnegative price with at most two decimal places.")
    response = (get_client().table("products").update({"price": str(price)})
                .eq("product_id", int(product_id)).execute())
    if not response.data:
        raise ValueError("Product not found.")
    return response.data[0]


def create_order(customer_id, product_id, quantity):
    if type(quantity) is not int or quantity <= 0:
        raise ValueError("Quantity must be a positive integer.")
    # Snapshot the price so later catalog changes do not rewrite past revenue.
    products = (get_client().table("products").select("price")
                .eq("product_id", int(product_id)).execute().data)
    if not products:
        raise ValueError("Product not found.")
    response = get_client().table("orders").insert({
        "customer_id": int(customer_id), "product_id": int(product_id),
        "quantity": quantity, "order_date": date.today().isoformat(),
        "unit_price": products[0]["price"]
    }).execute()
    return response.data[0]


def get_product(product_id):
    products = (get_client().table("products").select("*")
                .eq("product_id", int(product_id)).execute().data)
    if not products:
        raise ValueError("Product not found.")
    return products[0]


def insert_order_at_price(customer_id, product_id, quantity, unit_price):
    if type(quantity) is not int or quantity <= 0:
        raise ValueError("Quantity must be a positive integer.")
    price = Decimal(str(unit_price))
    if not price.is_finite() or price < 0:
        raise ValueError("Product price is invalid.")
    response = get_client().table("orders").insert({
        "customer_id": int(customer_id), "product_id": int(product_id),
        "quantity": quantity, "order_date": date.today().isoformat(),
        "unit_price": str(price),
    }).select("order_id").execute()
    if not response.data or response.data[0].get("order_id") is None:
        raise RuntimeError("The API did not return the generated order ID.")
    return response.data[0]["order_id"]


def get_orders():
    # Foreign keys let the API embed the related records in one response.
    return (get_client().table("orders")
            .select("*, customers(name, city), products(product_name)")
            .order("order_id").execute().data)


def get_order(order_id):
    orders = (get_client().table("orders")
              .select("order_id, customer_id, product_id, quantity, unit_price, order_date, "
                      "customers(name), products(product_name)")
              .eq("order_id", int(order_id)).execute().data)
    if not orders:
        raise LookupError("The saved order was not returned by the verification query.")
    return orders[0]


def delete_order(order_id):
    return (get_client().table("orders").delete()
            .eq("order_id", int(order_id)).execute().data)

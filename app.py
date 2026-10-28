"""Streamlit order-entry app for the fictional classroom Supabase database."""
import hmac
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

from config import get_app_password
from database import get_customers, get_order, get_orders, get_product, get_products, insert_order_at_price


st.set_page_config(page_title="Order Desk", page_icon="📦", layout="wide")
st.markdown(
    """
    <style>
    .stApp { background: #f4f6f2; }
    [data-testid="stHeader"] { background: rgba(244, 246, 242, 0.9); }
    .block-container { max-width: 1180px; padding-top: 2rem; padding-bottom: 4rem; }
    h1, h2, h3 { color: #152b25; }
    h1 { font-family: Georgia, 'Times New Roman', serif; font-weight: 500; }
    [data-testid="stMetric"] { background: #fff; padding: 1rem 1.1rem; border-left: 3px solid #d47945; }
    div[data-testid="stForm"] { background: #fff; border: 1px solid #dce3dc; padding: 1.2rem; }
    div.stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
        background: #176957; border-color: #176957; color: white;
    }
    div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        border-color: #d47945; color: #152b25;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def require_access():
    """Require the classroom password before touching the database."""
    password = get_app_password()
    if not password:
        st.error("App access is not configured. Set APP_PASSWORD in local .env or Streamlit secrets.")
        st.stop()

    if st.session_state.get("authorized"):
        return

    st.title("Order Desk")
    st.write("Enter the classroom access password to continue.")
    with st.form("access_form"):
        entered_password = st.text_input("Access password", type="password")
        submitted = st.form_submit_button("Unlock", type="primary")
    if submitted:
        if hmac.compare_digest(entered_password, password):
            st.session_state["authorized"] = True
            st.rerun()
        st.error("That password was not accepted.")
    st.stop()


@st.cache_data(ttl=60, show_spinner=False)
def load_app_data():
    return get_customers(), get_products(), get_orders()


def relation_name(record, relation, field):
    value = record.get(relation) or {}
    if isinstance(value, list):
        value = value[0] if value else {}
    return value.get(field, "(unavailable)")


def display_order_table(order):
    unit_price = Decimal(str(order["unit_price"]))
    quantity = int(order["quantity"])
    frame = pd.DataFrame([{
        "Order ID": order["order_id"],
        "Customer": relation_name(order, "customers", "name"),
        "Product": relation_name(order, "products", "product_name"),
        "Quantity": quantity,
        "Unit Price": float(unit_price),
        "Total": float(unit_price * quantity),
        "Order Date": str(order["order_date"]),
    }])
    st.dataframe(
        frame,
        hide_index=True,
        width="stretch",
        column_config={
            "Unit Price": st.column_config.NumberColumn(format="$%.2f"),
            "Total": st.column_config.NumberColumn(format="$%.2f"),
        },
    )


def show_catalog(customers, products):
    customer_frame = pd.DataFrame([
        {"Customer ID": row["customer_id"], "Customer Name": row["name"]}
        for row in customers
    ])
    product_frame = pd.DataFrame([
        {
            "Product ID": row["product_id"],
            "Product Name": row["product_name"],
            "Category": row.get("category", "Uncategorized"),
            "Price": float(Decimal(str(row["price"]))),
        }
        for row in products
    ])
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Customers")
        st.dataframe(customer_frame, hide_index=True, width="stretch")
    with right:
        st.subheader("Products")
        st.dataframe(
            product_frame,
            hide_index=True,
            width="stretch",
            column_config={"Price": st.column_config.NumberColumn(format="$%.2f")},
        )


def product_label(product_by_id, product_id):
    product = product_by_id[product_id]
    price = Decimal(str(product["price"]))
    return f"{product['product_name']} · ${price:.2f} · ID {product_id}"


def customer_label(customer_by_id, customer_id):
    return f"{customer_by_id[customer_id]['name']} · ID {customer_id}"


def show_history(orders, customers):
    st.subheader("Order History")
    customer_by_id = {int(row["customer_id"]): row for row in customers}
    customer_ids = [None, *customer_by_id.keys()]
    selected_customer = st.selectbox(
        "Filter by customer",
        customer_ids,
        format_func=lambda value: "All customers" if value is None else customer_label(customer_by_id, value),
        key="history_customer_filter",
    )
    filtered = [
        order for order in orders
        if selected_customer is None or int(order["customer_id"]) == selected_customer
    ]
    total_value = sum(
        (Decimal(str(order["unit_price"])) * int(order["quantity"]) for order in filtered),
        Decimal("0"),
    )
    st.metric("Value of displayed orders", f"${total_value:.2f}")
    history_frame = pd.DataFrame([
        {
            "Order ID": order["order_id"],
            "Customer": relation_name(order, "customers", "name"),
            "Product": relation_name(order, "products", "product_name"),
            "Quantity": int(order["quantity"]),
            "Unit Price": float(Decimal(str(order["unit_price"]))),
            "Total": float(Decimal(str(order["unit_price"])) * int(order["quantity"])),
            "Order Date": str(order["order_date"]),
        }
        for order in filtered
    ])
    st.dataframe(
        history_frame,
        hide_index=True,
        width="stretch",
        column_config={
            "Unit Price": st.column_config.NumberColumn(format="$%.2f"),
            "Total": st.column_config.NumberColumn(format="$%.2f"),
        },
    )


def show_order_entry(customers, products):
    st.subheader("Create an order")
    if not customers or not products:
        st.warning("A customer and product are required before an order can be created.")
        return

    customer_by_id = {int(row["customer_id"]): row for row in customers}
    product_by_id = {int(row["product_id"]): row for row in products}
    with st.form("order_details"):
        customer_id = st.selectbox(
            "Customer",
            list(customer_by_id),
            format_func=lambda value: customer_label(customer_by_id, value),
        )
        product_id = st.selectbox(
            "Product",
            list(product_by_id),
            format_func=lambda value: product_label(product_by_id, value),
        )
        quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
        review_clicked = st.form_submit_button("Review order", type="primary")

    if review_clicked:
        selected_product = product_by_id[product_id]
        st.session_state["pending_review"] = {
            "customer_id": customer_id,
            "customer_name": customer_by_id[customer_id]["name"],
            "product_id": product_id,
            "product_name": selected_product["product_name"],
            "quantity": int(quantity),
            "unit_price": str(Decimal(str(selected_product["price"]))),
            "revision": st.session_state.get("review_revision", 0) + 1,
        }
        st.session_state["review_revision"] = st.session_state["pending_review"]["revision"]
        st.session_state.pop("save_error", None)

    pending = st.session_state.get("pending_review")
    if not pending:
        return

    st.markdown("#### Review before saving")
    st.write(f"**Customer:** {pending['customer_name']}")
    st.write(f"**Product:** {pending['product_name']}")
    st.write(f"**Quantity:** {pending['quantity']}")
    unit_price = Decimal(pending["unit_price"])
    st.write(f"**Unit price:** ${unit_price:.2f}")
    st.write(f"**Total:** ${unit_price * pending['quantity']:.2f}")

    confirmation_key = f"confirm_order_{pending['revision']}"
    with st.form(f"confirm_form_{pending['revision']}"):
        confirmed = st.checkbox("I have reviewed these details and confirm this order.", key=confirmation_key)
        save_clicked = st.form_submit_button("Confirm and save order", type="primary")

    cancel_clicked = st.button("Cancel review", key=f"cancel_review_{pending['revision']}")
    if cancel_clicked:
        st.session_state.pop("pending_review", None)
        st.rerun()

    if not save_clicked:
        return
    if not confirmed:
        st.warning("Check the confirmation box before saving the order.")
        return

    try:
        current_product = get_product(pending["product_id"])
        current_price = Decimal(str(current_product["price"]))
    except Exception:
        st.error("The current product price could not be checked. Nothing was submitted.")
        return

    if current_price != unit_price:
        pending["unit_price"] = str(current_price)
        pending["revision"] += 1
        st.session_state["pending_review"] = pending
        st.session_state["review_revision"] = pending["revision"]
        st.warning("The price changed. Review the updated total and confirm again before saving.")
        st.rerun()

    try:
        order_id = insert_order_at_price(
            pending["customer_id"], pending["product_id"], pending["quantity"], current_price
        )
    except Exception:
        st.session_state.pop("pending_review", None)
        st.session_state["save_error"] = (
            "The save result could not be confirmed. Check Order History before trying again; "
            "the app will not automatically resubmit this order."
        )
        st.rerun()

    st.session_state.pop("pending_review", None)
    st.session_state.pop("save_error", None)
    st.session_state["last_order_id"] = order_id
    try:
        st.session_state["verified_order"] = get_order(order_id)
        st.session_state["verification_error"] = False
    except Exception:
        st.session_state["verified_order"] = None
        st.session_state["verification_error"] = True
    load_app_data.clear()
    st.rerun()


def main():
    require_access()
    st.title("Customer Order Desk")
    st.write("Browse the live classroom catalog, place a confirmed order, and verify it against Supabase.")

    if st.button("Refresh Data", icon=":material/refresh:"):
        load_app_data.clear()

    try:
        customers, products, orders = load_app_data()
    except Exception:
        st.error("Supabase could not be reached. Check the app's connection settings and try Refresh Data.")
        st.stop()

    if not customers:
        st.warning("No customers were returned from Supabase.")
    if not products:
        st.warning("No products were returned from Supabase.")

    show_catalog(customers, products)
    st.divider()
    show_order_entry(customers, products)

    if st.session_state.get("save_error"):
        st.error(st.session_state["save_error"])
    if "last_order_id" in st.session_state:
        order_id = st.session_state["last_order_id"]
        st.success(f"Order {order_id} was saved to Supabase.")
        if st.session_state.get("verification_error"):
            st.warning("The order was saved, but it could not be retrieved for verification. It was not submitted again.")
        elif st.session_state.get("verified_order"):
            st.subheader("Verified saved order")
            display_order_table(st.session_state["verified_order"])

    st.divider()
    show_history(orders, customers)


main()
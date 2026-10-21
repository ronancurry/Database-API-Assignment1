import unittest
from datetime import date
from decimal import Decimal
from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

import order_entry


class OrderEntryTests(unittest.TestCase):
    def test_customer_id_reprompts_for_text_and_unknown_id(self):
        output = StringIO()
        with patch("builtins.input", side_effect=["hello", "999", "1"]), redirect_stdout(output):
            result = order_entry.prompt_for_existing_id("customer", {1, 2})

        self.assertEqual(result, 1)
        self.assertIn("whole-number ID", output.getvalue())
        self.assertIn("not in the list", output.getvalue())

    def test_unknown_product_id_reprompts(self):
        output = StringIO()
        with patch("builtins.input", side_effect=["999", "2"]), redirect_stdout(output):
            result = order_entry.prompt_for_existing_id("product", {1, 2})

        self.assertEqual(result, 2)
        self.assertIn("not in the list", output.getvalue())

    def test_quantity_reprompts_until_positive_whole_number(self):
        output = StringIO()
        inputs = ["0", "-2", "1.5", "hello", "3"]
        with patch("builtins.input", side_effect=inputs), redirect_stdout(output):
            result = order_entry.prompt_for_quantity()

        self.assertEqual(result, 3)
        self.assertGreaterEqual(output.getvalue().count("Quantity must be greater"), 2)
        self.assertGreaterEqual(output.getvalue().count("positive whole number"), 2)

    def test_confirmation_reprompts_and_accepts_lowercase_no(self):
        output = StringIO()
        with patch("builtins.input", side_effect=["maybe", "n"]), redirect_stdout(output):
            result = order_entry.prompt_for_confirmation()

        self.assertFalse(result)
        self.assertIn("Please enter Y or N", output.getvalue())

    def test_cancel_does_not_call_order_api(self):
        customers = [{"customer_id": 1, "name": "Casey Example"}]
        products = [{"product_id": 2, "product_name": "Notebook", "price": "4.25"}]
        inputs = ["1", "2", "1", "N", "n"]
        output = StringIO()
        with (
            patch.object(order_entry, "get_customers", return_value=customers),
            patch.object(order_entry, "get_products", return_value=products),
            patch.object(order_entry, "get_client") as get_client,
            patch("builtins.input", side_effect=inputs),
            redirect_stdout(output),
        ):
            order_entry.run()

        get_client.assert_not_called()
        self.assertIn("nothing was inserted", output.getvalue())

    def make_client(self, inserted, verified):
        client = Mock()
        table = client.table.return_value
        table.insert.return_value.select.return_value.execute.return_value = SimpleNamespace(data=inserted)
        table.select.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=verified)
        return client, table

    def test_insert_sends_validated_values_and_returns_generated_id(self):
        client, table = self.make_client([{"order_id": 1042}], [])

        order_id = order_entry.insert_order(client, 1, 2, 2, "4.25")

        self.assertEqual(order_id, 1042)
        table.insert.assert_called_once_with({
            "customer_id": 1,
            "product_id": 2,
            "quantity": 2,
            "order_date": date.today().isoformat(),
            "unit_price": "4.25",
        })

    def test_fetch_order_queries_by_generated_id(self):
        expected_order = {
            "order_id": 1042,
            "quantity": 2,
            "unit_price": "4.25",
            "order_date": "2026-10-21",
            "customers": {"name": "Casey Example"},
            "products": {"product_name": "Notebook"},
        }
        client, table = self.make_client([], [expected_order])

        result = order_entry.fetch_order(client, 1042)

        self.assertEqual(result, expected_order)
        table.select.return_value.eq.assert_called_once_with("order_id", 1042)

    def test_save_and_verify_inserts_once_then_shows_retrieved_order(self):
        saved = {
            "order_id": 1042, "quantity": 2, "unit_price": "4.25", "order_date": "2026-10-21",
            "customers": {"name": "Casey Example"}, "products": {"product_name": "Notebook"},
        }
        client, table = self.make_client([{"order_id": 1042}], [saved])
        output = StringIO()
        with patch.object(order_entry, "get_client", return_value=client), redirect_stdout(output):
            order_entry.save_and_verify(1, 2, 2, Decimal("4.25"))

        table.insert.assert_called_once()
        self.assertIn("Order saved", output.getvalue())
        self.assertIn("Casey Example", output.getvalue())
        self.assertIn("$8.50", output.getvalue())

    def test_failed_verification_is_reported_without_reinserting(self):
        client, table = self.make_client([{"order_id": 1042}], [])
        output = StringIO()
        with patch.object(order_entry, "get_client", return_value=client), redirect_stdout(output):
            order_entry.save_and_verify(1, 2, 1, Decimal("4.25"))

        table.insert.assert_called_once()
        self.assertIn("Verification could not be completed", output.getvalue())

    def test_failed_insert_does_not_claim_success(self):
        client = Mock()
        client.table.return_value.insert.return_value.select.return_value.execute.side_effect = Exception("boom")
        output = StringIO()
        with patch.object(order_entry, "get_client", return_value=client), redirect_stdout(output):
            order_entry.save_and_verify(1, 2, 1, Decimal("4.25"))

        self.assertIn("could not be saved", output.getvalue())
        self.assertNotIn("Order saved", output.getvalue())


if __name__ == "__main__":
    unittest.main()
import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

import database


class DatabaseOrderTests(unittest.TestCase):
    def test_insert_order_uses_confirmed_price_and_returns_database_id(self):
        client = Mock()
        client.table.return_value.insert.return_value.select.return_value.execute.return_value = (
            SimpleNamespace(data=[{"order_id": 205}])
        )

        with patch.object(database, "get_client", return_value=client):
            order_id = database.insert_order_at_price(1, 3, 2, "19.50")

        self.assertEqual(order_id, 205)
        client.table.assert_called_once_with("orders")
        client.table.return_value.insert.assert_called_once_with({
            "customer_id": 1,
            "product_id": 3,
            "quantity": 2,
            "order_date": date.today().isoformat(),
            "unit_price": "19.50",
        })

    def test_insert_order_rejects_nonpositive_quantity_before_api_call(self):
        client = Mock()

        with patch.object(database, "get_client", return_value=client):
            with self.assertRaises(ValueError):
                database.insert_order_at_price(1, 3, 0, "19.50")

        client.table.assert_not_called()

    def test_get_order_retrieves_the_requested_id(self):
        expected = {"order_id": 205, "quantity": 2, "unit_price": "19.50"}
        client = Mock()
        client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            SimpleNamespace(data=[expected])
        )

        with patch.object(database, "get_client", return_value=client):
            result = database.get_order(205)

        self.assertEqual(result, expected)
        client.table.return_value.select.return_value.eq.assert_called_once_with("order_id", 205)


if __name__ == "__main__":
    unittest.main()
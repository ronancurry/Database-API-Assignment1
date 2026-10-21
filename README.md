# Customer Order Entry

A terminal program that creates customer orders in Supabase and then queries the database again to verify each order was saved.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then put your own Supabase URL and secret key in `.env`.

## Run

```bash
python order_entry.py
```

## Testing results

| Test | Result |
|---|---|
| Text instead of a customer ID | Passed. Shows a message and asks again |
| Customer ID that doesn't exist | Passed. Rejected and asks again |
| Product ID that doesn't exist | Passed. Rejected and asks again |
| Quantity `0`, `-2`, `1.5`, `hello` | Passed. Each one rejected and asks again |
| Cancel at confirmation | Passed. No order inserted |
| Confirm a valid order | Passed. Exactly one order inserted (ID 1001) |
| Retrieve the new order | Passed. Order 1001 shown in the verification table |

Output from a live run:

```text

Customers
Customer ID | Customer Name
------------+--------------
1           | Avery Morgan 
2           | Jordan Patel 
3           | Taylor Chen  
4           | Casey Rivera 
5           | Riley Brooks 
6           | Morgan Lee   
7           | Jamie Wilson 
8           | Alex Kim     
9           | Cameron Davis
10          | Quinn Garcia 
11          | Sam Parker   
12          | Drew Johnson 
13          | Skyler Reed  
14          | Reese Martin 
15          | Rowan Lewis  
16          | Peyton Clark 
17          | Finley Hall  
18          | Emerson Young
19          | Dakota Allen 
20          | Harper Scott 

Products
Product ID | Product Name   | Current Price
-----------+----------------+--------------
1          | Notebook       | $4.50        
2          | Pen Set        | $6.00        
3          | Backpack       | $45.00       
4          | Water Bottle   | $18.00       
5          | Hoodie         | $39.00       
6          | T-Shirt        | $19.00       
7          | USB Drive      | $12.50       
8          | Wireless Mouse | $24.00       
9          | Desk Lamp      | $29.00       
10         | Coffee Mug     | $10.00       
11         | Planner        | $15.00       
12         | Laptop Stand   | $35.00       
Enter customer ID: hello
Please enter a whole-number ID.
Enter customer ID: 999
That customer ID is not in the list. Please try again.
Enter customer ID: 1
Enter product ID: 999
That product ID is not in the list. Please try again.
Enter product ID: 3
Enter quantity: 0
Quantity must be greater than zero.
Enter quantity: -2
Quantity must be greater than zero.
Enter quantity: 1.5
Please enter a positive whole number, such as 1 or 2.
Enter quantity: hello
Please enter a positive whole number, such as 1 or 2.
Enter quantity: 2

Order summary
Customer: Avery Morgan
Product: Backpack
Quantity: 2
Current unit price: $45.00
Order total: $90.00
Confirm this purchase? (Y/N): maybe
Please enter Y or N.
Confirm this purchase? (Y/N): n
Order cancelled; nothing was inserted.

Enter another order? (Y/N): y
Enter customer ID: 2
Enter product ID: 7
Enter quantity: 3

Order summary
Customer: Jordan Patel
Product: USB Drive
Quantity: 3
Current unit price: $12.50
Order total: $37.50
Confirm this purchase? (Y/N): y

Order saved. Supabase assigned order ID 1001.

Saved order retrieved from Supabase:
Order ID | Customer     | Product   | Quantity | Unit Price | Total  | Order Date
---------+--------------+-----------+----------+------------+--------+-----------
1001     | Jordan Patel | USB Drive | 3        | $12.50     | $37.50 | 2026-10-21

Enter another order? (Y/N): n
Goodbye.
```

## References

- `decimal.Decimal`: https://docs.python.org/3/library/decimal.html
- `unittest.mock` (used in `tests/`): https://docs.python.org/3/library/unittest.mock.html

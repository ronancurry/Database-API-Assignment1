# Customer Order Entry

This is my DATA 4000 Database API assignment. It's a Python program that runs in the terminal and lets you create orders for existing customers in our Supabase database. After it saves an order, it queries Supabase again to make sure the order was actually saved.

## What the program does

When you run `order_entry.py`, this is what happens:

1. It pulls the customers and products from Supabase and prints them as two tables, with prices shown to two decimal places.
2. It asks for a customer ID, a product ID, and a quantity. If something isn't valid, it explains what's wrong and asks again.
3. It shows an order summary (customer, product, quantity, current unit price, and total) and asks you to confirm with Y or N.
4. If you type **N**, the order is cancelled and nothing gets inserted. If you type **Y**, the order is inserted through the Supabase API using today's date and the product's current price from the database. The database creates the order ID.
5. It takes the order ID that came back from the insert and sends a **new query** to Supabase to look up that order, then prints it in a table. If that lookup fails or comes back empty, it says verification couldn't be completed, and it doesn't try to insert the order again.
6. It asks if you want to enter another order and keeps going until you say N (this is the extra credit).

You never have to type in a price or an order ID. Those come from the database.

## Setup

I used Python 3.11 or newer. In the project folder, make a virtual environment, activate it, install the packages, and copy the environment template:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell it's `py -m venv .venv`, then `.\.venv\Scripts\Activate.ps1` to activate, and `Copy-Item .env.example .env` to copy the template.

Next, open `.env` and put in your own Supabase project URL and secret key:

```dotenv
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=sb_secret_your_own_key
```

Your Supabase project needs the `customers`, `products`, and `orders` tables, and the Data API has to be turned on. The `.env` file is in `.gitignore`, so my real keys never get uploaded. Only `.env.example` is in the repo, and it just has placeholders.

## How to run it

With the virtual environment activated, run this from the project folder:

```bash
python order_entry.py
```

I also wrote some automated tests. They use a fake API client, so they don't change anything in Supabase. To run them:

```bash
python -m unittest discover -s tests -v
```

## Testing results

| Test | Expected behavior | Result |
|---|---|---|
| Enter text (`hello`) instead of a customer ID | Helpful message; asks again | Passed. Printed "Please enter a whole-number ID." and asked again |
| Enter a customer ID that does not exist | Rejects the ID; asks again | Passed. Printed "That customer ID is not in the list. Please try again." |
| Enter a product ID that does not exist | Rejects the ID; asks again | Passed. Printed "That product ID is not in the list. Please try again." |
| Enter quantity `0`, `-2`, `1.5`, `hello` | Rejects each value; asks again | Passed. `0` and `-2` printed "Quantity must be greater than zero."; `1.5` and `hello` printed "Please enter a positive whole number…" |
| Cancel at the confirmation prompt | No order is inserted | Passed. Printed "Order cancelled; nothing was inserted." and no insert request was sent |
| Confirm a valid order | Exactly one order is inserted | Passed. One insert request, then "Order saved. Supabase assigned order ID …" |
| Retrieve the newly created order | Saved order appears in the verification table | Passed. A separate query by order ID found the saved order and showed it in the table |

All 10 automated tests in `tests/test_order_entry.py` pass. They cover every case above, plus two failure cases: when the insert fails (no success message is shown), and when the verification lookup fails (the program reports it and doesn't insert the order again).

### Live run (successful insertion and verification)

This is the output from one real run of `python order_entry.py` on 2026-10-21. In it I try each kind of bad input, cancel one order, and then confirm a second order that gets inserted and looked up again with a separate query. No credentials show up anywhere in the output.

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

Afterwards I checked the `orders` table. Order 1001 was the only new row, and the Backpack order I cancelled was never inserted.

## Files

- `order_entry.py`: the main order entry program
- `database.py`: Supabase client and helper functions for customers and products (given in class)
- `config.py`: loads the URL and key from `.env` (given in class)
- `requirements.txt`: the Python packages you need
- `.env.example`: a template with placeholder credentials
- `.gitignore`: keeps `.env` and other local files out of Git
- `tests/`: automated tests for input checks, saving, and verification

## References

A few things I used that weren't covered in class:

- `decimal.Decimal`, so money math is exact instead of using floats: https://docs.python.org/3/library/decimal.html
- `unittest` and `unittest.mock`, for testing with a fake API client: https://docs.python.org/3/library/unittest.html and https://docs.python.org/3/library/unittest.mock.html
- Getting the new order ID back from the insert with `.insert(...).select("order_id")`, and pulling in related tables with `customers(name)`: https://supabase.com/docs/reference/python/insert and https://supabase.com/docs/reference/python/select

# Customer Order Desk

A password-gated Streamlit order-entry app for the fictional classroom Supabase database. It displays the live customer and product catalogs, saves confirmed orders, retrieves each saved order in a separate verification query, and shows order history with an optional customer filter.

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, and a private `APP_PASSWORD` in `.env`, then run:

```bash
streamlit run app.py
```

The local `.env` file is ignored by Git. Never put a real key or app password in `.env.example`, source code, screenshots, or a commit.

## Streamlit Community Cloud

1. Push the required source files to your GitHub repository.
2. In Streamlit Community Cloud, create an app from that repository and select the `main` branch and `app.py` entry point.
3. Add these values in the app's secrets settings, using a newly rotated Supabase secret if the previous key was exposed:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_SECRET_KEY = "your-supabase-secret-key"
APP_PASSWORD = "a-private-classroom-password"
```

4. Deploy the app, open the hosted URL, and test it while signed in with the app password. Give the instructor the app password privately through the course submission system.
5. Update the links and testing results below after the hosted app is deployed and verified.

Do not commit `.env`, `.streamlit/secrets.toml`, or real credentials. The app checks its password before making any database request; this shared classroom password is not a production login system.

## Submission Links

- Streamlit app: https://database-api-assignment1-jexeeqhzefmdvsbu4jx96y.streamlit.app/

- GitHub repository: https://github.com/ronancurry/Database-API-Assignment1


## Tests

Run the local unit tests with:

```bash
python -m unittest discover -v
```

The automated tests exercise local validation and mocked API calls. They do not replace the required deployed-app tests. After deployment, verify authorized access, live catalog data, invalid quantity handling, refusal to save without confirmation, one successful confirmed order, fresh verification, no duplicate on rerun, refreshed order history, and the customer filter. Record the actual results here and include screenshots of the hosted order form and a genuinely verified order; do not use fabricated test data or screenshots.

## How It Works

- `app.py` collects a customer, product, and positive whole-number quantity. It shows a review, then asks for a separate explicit confirmation.
- At confirmation, it fetches the selected product again. A changed price updates the review and requires a fresh confirmation.
- `database.py` sends requests through the Supabase Python client. It stores the current price and date, lets the database generate the order ID, then retrieves that ID in a new API query.
- `config.py` reads local `.env` values or Streamlit secrets. Credentials are not hard-coded in the repository.

The app depends on Streamlit, pandas, python-dotenv, and the Supabase Python client. Streamlit reruns the script on interaction; inserts occur only on the explicit confirmation form submission, and the pending order is cleared after an insert attempt to avoid an automatic retry.

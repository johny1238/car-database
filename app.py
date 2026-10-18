import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Car Inventory Management", layout="wide")


# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("car_inventory.db")
    c = conn.cursor()

    # Create table if it doesn't exist
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_name TEXT,
            year TEXT,
            colour TEXT,
            car_number TEXT,
            vin_number TEXT,
            buying_date TEXT,
            date_of_malso TEXT,
            dealer_name TEXT,
            dealer_contact TEXT,
            city_of_buying TEXT,
            amount REAL,
            deposit REAL,
            pickup_deadline TEXT,
            car_location TEXT,
            status TEXT
        )
    """
    )
    conn.commit()

    # Automatically add missing columns if upgrading from old database structure
    columns = [row[1] for row in c.execute("PRAGMA table_info(cars)").fetchall()]
    new_cols = {
        "year": "TEXT",
        "colour": "TEXT",
        "car_number": "TEXT",
        "vin_number": "TEXT",
        "date_of_malso": "TEXT",
    }
    for col_name, col_type in new_cols.items():
        if col_name not in columns:
            c.execute(f"ALTER TABLE cars ADD COLUMN {col_name} {col_type}")
            conn.commit()

    conn.close()


init_db()


def get_connection():
    return sqlite3.connect("car_inventory.db")


# --- NAVIGATION ---
st.sidebar.title("Business Portal")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard & Notifications", "Add New Car", "View & Update Cars"],
)

# --- PAGE 1: DASHBOARD ---
if page == "Dashboard & Notifications":
    st.title("📊 Dashboard & Pickup Notifications")

    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM cars", conn)
    conn.close()

    if not df.empty:
        # Warning Alerts for Pickups within 2 days
        today = datetime.now().date()
        df["pickup_date_obj"] = pd.to_datetime(
            df["pickup_deadline"]
        ).dt.date
        urgent_pickups = df[
            (df["status"] != "Delivered")
            & (df["pickup_date_obj"] - today <= timedelta(days=2))
        ]

        if not urgent_pickups.empty:
            st.error(
                f"🚨 WARNING: {len(urgent_pickups)} vehicle(s) approaching or past 7-day pickup deadline!"
            )
            for _, row in urgent_pickups.iterrows():
                st.write(
                    f"⚠️ *{row['car_name']}* ({row['car_number'] if row['car_number'] else 'N/A'}) - Deadline: *{row['pickup_deadline']}* | Location: {row['car_location']}"
                )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Vehicles", len(df))
        col2.metric("In Yard", len(df[df["car_location"] == "Yard"]))
        col3.metric("In Showroom", len(df[df["car_location"] == "Showroom"]))
        col4.metric("Delivered", len(df[df["status"] == "Delivered"]))

        st.subheader("All Active Cars")
        st.dataframe(df.drop(columns=["pickup_date_obj"]), use_container_width=True)
    else:
        st.info("No cars added to the database yet.")

# --- PAGE 2: ADD NEW CAR ---
elif page == "Add New Car":
    st.title("🚘 Add New Car to Inventory")

    with st.form("add_car_form"):
        col1, col2 = st.columns(2)

        with col1:
            car_name = st.text_input("Car Name")
            year = st.text_input("Year (e.g. 2022)")
            colour = st.text_input("Colour")
            car_number = st.text_input("Car Number (License Plate)")
            vin_number = st.text_input("VIN Number")
            buying_date = st.date_input("Buying Date", datetime.now())
            date_of_malso = st.date_input(
                "Date of Malso (Optional)", value=None
            )

        with col2:
            dealer_name = st.text_input("Dealer Name")
            dealer_contact = st.text_input("Dealer Contact Number")
            city_of_buying = st.text_input("City of Buying")
            amount = st.number_input(
                "Total Amount (₩)", min_value=0.0, step=100000.0
            )
            deposit = st.number_input(
                "Deposit Paid (₩)", min_value=0.0, step=50000.0
            )
            car_location = st.selectbox("Location", ["Yard", "Showroom"])
            status = st.selectbox("Status", ["Pending", "In Transit", "Delivered"])

        submit = st.form_submit_button("Save Car Record")

        if submit:
            if car_name:
                pickup_deadline = buying_date + timedelta(days=7)
                malso_str = (
                    str(date_of_malso) if date_of_malso is not None else ""
                )

                conn = get_connection()
                c = conn.cursor()
                c.execute(
                    """
                    INSERT INTO cars (car_name, year, colour, car_number, vin_number, buying_date, date_of_malso, dealer_name, dealer_contact, city_of_buying, amount, deposit, pickup_deadline, car_location, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        car_name,
                        year,
                        colour,
                        car_number,
                        vin_number,
                        str(buying_date),
                        malso_str,
                        dealer_name,
                        dealer_contact,
                        city_of_buying,
                        amount,
                        deposit,
                        str(pickup_deadline),
                        car_location,
                        status,
                    ),
                )
                conn.commit()
                conn.close()
                st.success(
                    f"Successfully added {car_name}! 7-Day Pickup Deadline set for {pickup_deadline}."
                )
            else:
                st.error("Please enter a Car Name.")

# --- PAGE 3: VIEW & UPDATE CARS ---
elif page == "View & Update Cars":
    st.title("✏️ Manage Inventory Records")

    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM cars", conn)
    conn.close()

    if not df.empty:
        car_options = {
            f"ID {row['id']} - {row['car_name']} ({row['car_number']})": row[
                "id"
            ]
            for _, row in df.iterrows()
        }
        selected_car_str = st.selectbox("Select Car to Update", list(car_options.keys()))
        selected_id = car_options[selected_car_str]

        car_data = df[df["id"] == selected_id].iloc[0]

        with st.form("update_car_form"):
            col1, col2 = st.columns(2)

            with col1:
                u_car_name = st.text_input("Car Name", value=car_data["car_name"])
                u_year = st.text_input("Year", value=str(car_data["year"] or ""))
                u_colour = st.text_input("Colour", value=str(car_data["colour"] or ""))
                u_car_number = st.text_input(
                    "Car Number", value=str(car_data["car_number"] or "")
                )
                u_vin_number = st.text_input(
                    "VIN Number", value=str(car_data["vin_number"] or "")
                )
                u_buying_date = st.text_input(
                    "Buying Date (YYYY-MM-DD)", value=str(car_data["buying_date"])
                )
                u_date_of_malso = st.text_input(
                    "Date of Malso (YYYY-MM-DD)",
                    value=str(car_data["date_of_malso"] or ""),
                )

            with col2:
                u_dealer_name = st.text_input(
                    "Dealer Name", value=str(car_data["dealer_name"] or "")
                )
                u_dealer_contact = st.text_input(
                    "Dealer Contact", value=str(car_data["dealer_contact"] or "")
                )
                u_city_of_buying = st.text_input(
                    "City of Buying", value=str(car_data["city_of_buying"] or "")
                )
                u_amount = st.number_input(
                    "Amount (₩)",
                    value=float(
                        car_data["amount"] if car_data["amount"] else 0.0
                    ),
                )
                u_deposit = st.number_input(
                    "Deposit (₩)",
                    value=float(
                        car_data["deposit"] if car_data["deposit"] else 0.0
                    ),
                )
                u_car_location = st.selectbox(
                    "Location",
                    ["Yard", "Showroom"],
                    index=0 if car_data["car_location"] == "Yard" else 1,
                )
                u_status = st.selectbox(
                    "Status",
                    ["Pending", "In Transit", "Delivered"],
                    index=["Pending", "In Transit", "Delivered"].index(
                        car_data["status"]
                    )
                    if car_data["status"] in ["Pending", "In Transit", "Delivered"]
                    else 0,
                )

            update_btn = st.form_submit_button("Update Record")

            if update_btn:
                conn = get_connection()
                c = conn.cursor()
                c.execute(
                    """
                    UPDATE cars
                    SET car_name=?, year=?, colour=?, car_number=?, vin_number=?, buying_date=?, date_of_malso=?, dealer_name=?, dealer_contact=?, city_of_buying=?, amount=?, deposit=?, car_location=?, status=?
                    WHERE id=?
                """,
                    (
                        u_car_name,
                        u_year,
                        u_colour,
                        u_car_number,
                        u_vin_number,
                        u_buying_date,
                        u_date_of_malso,
                        u_dealer_name,
                        u_dealer_contact,
                        u_city_of_buying,
                        u_amount,
                        u_deposit,
                        u_car_location,
                        u_status,
                        selected_id,
                    ),
                )
                conn.commit()
                conn.close()
                st.success("Record updated successfully!")
                st.rerun()
    else:
        st.info("No cars available to update.")
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# Set Page Config
st.set_page_config(
    page_title="Car Inventory & Pickup Tracking",
    page_icon="🚗",
    layout="wide",
)


# Initialize Database
def init_db():
    conn = sqlite3.connect("car_inventory.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_name TEXT NOT NULL,
            buying_date DATE NOT NULL,
            dealer_name TEXT,
            dealer_contact TEXT,
            city_of_buying TEXT,
            amount REAL,
            deposit REAL,
            pickup_deadline DATE,
            car_location TEXT,
            export_date DATE,
            delivered_status TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


def get_db_connection():
    return sqlite3.connect("car_inventory.db")


# Sidebar Navigation
st.sidebar.title("🚗 Car Business Portal")
menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard & Notifications", "Add New Car", "View & Update Cars"],
)

# -------------------------------------------------------------
# 1. DASHBOARD & NOTIFICATIONS
# -------------------------------------------------------------
if menu == "Dashboard & Notifications":
    st.title("📊 Dashboard & Pickup Notifications")

    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM cars", conn)
    conn.close()

    if not df.empty:
        df["buying_date"] = pd.to_datetime(df["buying_date"]).dt.date
        df["pickup_deadline"] = pd.to_datetime(df["pickup_deadline"]).dt.date
        today = datetime.now().date()

        # Pickup Notifications (2 days prior to 7-day week limit)
        # Pickup deadline = buying_date + 7 days
        # Alert period = when today is >= (pickup_deadline - 2 days) AND car is not delivered
        df["days_left"] = (df["pickup_deadline"] - today).apply(lambda x: x.days)

        alert_cars = df[
            (df["days_left"] <= 2) & (df["delivered_status"] != "Delivered")
        ]

        if not alert_cars.empty:
            st.error(
                "🚨 *ATTENTION REQUIRED: Upcoming Pickup Deadlines within 2 Days / Overdue!*"
            )
            for _, row in alert_cars.iterrows():
                days_txt = (
                    f"Overdue by {abs(row['days_left'])} days!"
                    if row["days_left"] < 0
                    else f"Due in {row['days_left']} day(s)!"
                )
                st.warning(
                    f"⚠️ *{row['car_name']}* | Dealer: {row['dealer_name']} ({row['dealer_contact']}) | "
                    f"City: {row['city_of_buying']} | Deadline: *{row['pickup_deadline']}* ({days_txt})"
                )

        st.markdown("---")

        # Key Business Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Vehicles", len(df))
        col2.metric("In Yard", len(df[df["car_location"] == "Yard"]))
        col3.metric("In Showroom", len(df[df["car_location"] == "Showroom"]))
        col4.metric(
            "Delivered", len(df[df["delivered_status"] == "Delivered"])
        )

        st.markdown("---")
        st.subheader("All Active Cars")
        st.dataframe(df, use_container_width=True)

    else:
        st.info("No cars currently in the database. Add your first vehicle!")

# -------------------------------------------------------------
# 2. ADD NEW CAR
# -------------------------------------------------------------
elif menu == "Add New Car":
    st.title("➕ Add New Vehicle to Inventory")

    with st.form("add_car_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            car_name = st.text_input("Car Name (Year, Make, Model)*")
            buying_date = st.date_input("Buying Date", datetime.now())
            dealer_name = st.text_input("Dealer Name")
            dealer_contact = st.text_input("Dealer Contact Info")
            city_of_buying = st.text_input("City of Buying")

        with col2:
            amount = st.number_input(
                "Total Amount (₩)", min_value=0.0, step=500.0
            )
            deposit = st.number_input(
                "Deposit Paid (₩)", min_value=0.0, step=100.0
            )
            car_location = st.selectbox("Car Location", ["Yard", "Showroom"])
            delivered_status = st.selectbox(
                "Delivery Status", ["Pending", "In Transit", "Delivered"]
            )
            export_date = st.date_input("Export Date (Optional)", value=None)

        # Calculate deadline (Buying Date + 7 Days)
        pickup_deadline = buying_date + timedelta(days=7)
        st.info(
            f"📅 *Automated Delivery Pickup Deadline:* {pickup_deadline.strftime('%Y-%m-%d')} (7 days after buying date)"
        )

        submit = st.form_submit_button("Save Car Record")

        if submit:
            if not car_name:
                st.error("Please provide the Car Name.")
            else:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute(
                    """
                    INSERT INTO cars (
                        car_name, buying_date, dealer_name, dealer_contact, city_of_buying,
                        amount, deposit, pickup_deadline, car_location, export_date, delivered_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        car_name,
                        buying_date,
                        dealer_name,
                        dealer_contact,
                        city_of_buying,
                        amount,
                        deposit,
                        pickup_deadline,
                        car_location,
                        export_date if export_date else None,
                        delivered_status,
                    ),
                )
                conn.commit()
                conn.close()
                st.success(
                    f"Successfully added *{car_name}* to the database!"
                )

# -------------------------------------------------------------
# 3. VIEW & UPDATE CARS
# -------------------------------------------------------------
elif menu == "View & Update Cars":
    st.title("✏️ Manage & Update Records")

    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM cars", conn)

    if not df.empty:
        car_list = df["id"].astype(str) + " - " + df["car_name"]
        selected_car = st.selectbox("Select Vehicle to Update", car_list)

        if selected_car:
            car_id = int(selected_car.split(" - ")[0])
            car_data = df[df["id"] == car_id].iloc[0]

            with st.form("update_form"):
                col1, col2 = st.columns(2)

                with col1:
                    u_car_name = st.text_input(
                        "Car Name", value=car_data["car_name"]
                    )
                    u_dealer_name = st.text_input(
                        "Dealer Name", value=car_data["dealer_name"]
                    )
                    u_dealer_contact = st.text_input(
                        "Dealer Contact", value=car_data["dealer_contact"]
                    )
                    u_city = st.text_input(
                        "City of Buying", value=car_data["city_of_buying"]
                    )
                    u_location = st.selectbox(
                        "Car Location",
                        ["Yard", "Showroom"],
                        index=["Yard", "Showroom"].index(
                            car_data["car_location"]
                        )
                        if car_data["car_location"] in ["Yard", "Showroom"]
                        else 0,
                    )

                with col2:
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
                    u_delivered = st.selectbox(
                        "Delivery Status",
                        ["Pending", "In Transit", "Delivered"],
                        index=[
                            "Pending",
                            "In Transit",
                            "Delivered",
                        ].index(car_data["delivered_status"])
                        if car_data["delivered_status"]
                        in ["Pending", "In Transit", "Delivered"]
                        else 0,
                    )

                update_btn = st.form_submit_button("Update Details")

                if update_btn:
                    c = conn.cursor()
                    c.execute(
                        """
                        UPDATE cars 
                        SET car_name=?, dealer_name=?, dealer_contact=?, city_of_buying=?, 
                            amount=?, deposit=?, car_location=?, delivered_status=?
                        WHERE id=?
                    """,
                        (
                            u_car_name,
                            u_dealer_name,
                            u_dealer_contact,
                            u_city,
                            u_amount,
                            u_deposit,
                            u_location,
                            u_delivered,
                            car_id,
                        ),
                    )
                    conn.commit()
                    st.success("Record updated successfully!")
                    st.rerun()
    else:
        st.info("No records found.")

    conn.close()
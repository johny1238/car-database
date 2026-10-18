from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import requests

st.set_page_config(page_title="Car Inventory Management", layout="wide")

# --- GOOGLE SHEET CONFIGURATION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1xHoMFFghP0DXccDHqdfqZaBWkLkpJKVPrR-r4262wjE/edit?usp=drivesdk"

# Paste your Apps Script deployment URL here if you set one up, otherwise leave as is
APPS_SCRIPT_URL = "PASTE_YOUR_APPS_SCRIPT_DEPLOYMENT_URL_HERE"


def get_csv_url(url):
    if "/edit" in url:
        return url.split("/edit")[0] + "/export?format=csv&gid=0"
    return url


def load_data():
    try:
        csv_url = get_csv_url(SHEET_URL)
        df = pd.read_csv(csv_url)
        df = df.dropna(how="all")
        expected_cols = [
            "car_name",
            "car_number",
            "car_location",
            "amount",
            "deposit",
            "status",
            "pickup_deadline",
        ]
        display_df = df[[col for col in expected_cols if col in df.columns]]
        return display_df
    except Exception as e:
        st.error(
            f"Could not load data from Google Sheet. Make sure the URL is correct and shared as 'Anyone with the link'. Error: {e}"
        )
        return pd.DataFrame()


# --- NAVIGATION ---
st.sidebar.title("Business Portal")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard & Notifications", "Add New Car", "View & Update Cars"],
)

# --- PAGE 1: DASHBOARD ---
if page == "Dashboard & Notifications":
    st.title("📊 Dashboard & Pickup Notifications")

    df = load_data()

    if not df.empty and "car_name" in df.columns:
        for col in ["amount", "deposit"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        today = datetime.now().date()
        if "pickup_deadline" in df.columns:
            df["pickup_date_obj"] = pd.to_datetime(
                df["pickup_deadline"], errors="coerce"
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
                        f"⚠️ *{row['car_name']}* ({row['car_number'] if pd.notna(row['car_number']) else 'N/A'}) - Deadline: *{row['pickup_deadline']}* | Location: {row['car_location']}"
                    )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Vehicles", len(df))
        if "car_location" in df.columns:
            col2.metric("In Yard", len(df[df["car_location"] == "Yard"]))
            col3.metric("In Showroom", len(df[df["car_location"] == "Showroom"]))
        if "status" in df.columns:
            col4.metric("Delivered", len(df[df["status"] == "Delivered"]))

        st.subheader("All Active Cars")
        st.dataframe(
            df.drop(columns=["pickup_date_obj"], errors="ignore"),
            use_container_width=True,
        )
    else:
        st.info("No cars found or sheet is empty.")

# --- PAGE 2: ADD NEW CAR ---
elif page == "Add New Car":
    st.title("🚘 Add New Car to Inventory")

    if APPS_SCRIPT_URL == "PASTE_YOUR_APPS_SCRIPT_DEPLOYMENT_URL_HERE":
        st.info(
            "Note: To add new records directly through this app, you can connect a Google Apps Script. Otherwise, you can manage and add new rows directly in your Google Sheet!"
        )
    else:
        with st.form("add_car_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                car_name = st.text_input("Car Name*", placeholder="Toyota Corolla")
                car_number = st.text_input("Car Number", placeholder="ABC 123")
                amount = st.number_input("Amount (Total)*", min_value=0, step=100)
                deposit = st.number_input("Deposit Paid*", min_value=0, step=100)
            with col2:
                car_location = st.selectbox("Car Location*", ["Yard", "Showroom"])
                status = st.selectbox(
                    "Current Status*",
                    ["Available", "Booked", "Sold", "Delivered"],
                )
                default_deadline = (datetime.now() + timedelta(days=7)).date()
                pickup_deadline = st.date_input(
                    "Pickup Deadline*", value=default_deadline
                )

            submit_button = st.form_submit_button("Submit Car to Inventory")

        if submit_button:
            if not car_name:
                st.warning("Please enter a Car Name.")
            else:
                data_payload = {
                    "car_name": car_name,
                    "car_number": car_number,
                    "car_location": car_location,
                    "amount": str(amount),
                    "deposit": str(deposit),
                    "status": status,
                    "pickup_deadline": pickup_deadline.strftime("%Y-%m-%d"),
                }
                try:
                    response = requests.post(
                        APPS_SCRIPT_URL, data=data_payload, timeout=10
                    )
                    if response.status_code == 200:
                        st.success(
                            f"Successfully added *{car_name}* to the inventory!"
                        )
                    else:
                        st.error(
                            f"Could not connect to Google Sheet. Error: {response.text}"
                        )
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")

# --- PAGE 3: VIEW & UPDATE CARS ---
elif page == "View & Update Cars":
    st.title("✏️ Manage Inventory Records")
    st.info(
        "You can view and edit your vehicle records directly inside your Google Sheet for instant updates!"
    )
    df = load_data()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No records to display.")
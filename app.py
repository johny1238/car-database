from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Car Inventory Management", layout="wide")

# --- GOOGLE SHEET CSV LINK ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1xHoMFFghP0DXccDHqdfqZaBWkLkpJKVPrR-r4262wjE/edit?usp=drivesdk"


def get_csv_url(url):
    if "/edit" in url:
        return url.split("/edit")[0] + "/export?format=csv&gid=0"
    return url


def load_data():
    try:
        csv_url = get_csv_url(SHEET_URL)
        df = pd.read_csv(csv_url)
        df = df.dropna(how="all")
        return df
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
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        df["deposit"] = pd.to_numeric(df["deposit"], errors="coerce").fillna(0)

        today = datetime.now().date()
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
        col2.metric("In Yard", len(df[df["car_location"] == "Yard"]))
        col3.metric("In Showroom", len(df[df["car_location"] == "Showroom"]))
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
    st.info(
        "Note: With direct Google Sheets viewing, adding new records requires connecting via Google Apps Script or viewing directly in your sheet. Use your Google Sheet to add new rows directly!"
    )

# --- PAGE 3: VIEW & UPDATE CARS ---
elif page == "View & Update Cars":
    st.title("✏️ Manage Inventory Records")
    st.info(
        "You can view and edit your vehicle records directly inside your Google Sheet for instant updates!"
    )
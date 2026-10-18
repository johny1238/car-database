from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Car Inventory Management", layout="wide")

# --- ESTABLISH GOOGLE SHEETS CONNECTION ---
# This connects straight to your Google Sheet database
conn = st.connection("gsheets", type=GSheetsConnection)


def load_data():
    # Reads the Google Sheet data into a Pandas DataFrame
    data = conn.read(worksheet="Sheet1", ttl=0)
    # Drop empty rows if any
    data = data.dropna(how="all")
    return data


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
        # Convert numeric columns safely
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        df["deposit"] = pd.to_numeric(df["deposit"], errors="coerce").fillna(0)

        # Warning Alerts for Pickups within 2 days
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
        st.dataframe(df.drop(columns=["pickup_date_obj"], errors="ignore"), use_container_width=True)
    else:
        st.info("No cars added to the database yet or sheet is empty.")

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

                df = load_data()
                new_id = int(df["id"].max() + 1) if not df.empty and "id" in df.columns and pd.notna(df["id"].max()) else 1

                new_row = pd.DataFrame([{
                    "id": new_id,
                    "car_name": car_name,
                    "year": year,
                    "colour": colour,
                    "car_number": car_number,
                    "vin_number": vin_number,
                    "buying_date": str(buying_date),
                    "date_of_malso": malso_str,
                    "dealer_name": dealer_name,
                    "dealer_contact": dealer_contact,
                    "city_of_buying": city_of_buying,
                    "amount": amount,
                    "deposit": deposit,
                    "pickup_deadline": str(pickup_deadline),
                    "car_location": car_location,
                    "status": status
                }] )

                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)

                st.success(
                    f"Successfully added {car_name} to Google Sheets! 7-Day Deadline: {pickup_deadline}."
                )
            else:
                st.error("Please enter a Car Name.")

# --- PAGE 3: VIEW & UPDATE CARS ---
elif page == "View & Update Cars":
    st.title("✏️ Manage Inventory Records")

    df = load_data()

    if not df.empty and "car_name" in df.columns:
        df["id"] = pd.to_numeric(df["id"], errors="coerce")
        car_options = {
            f"ID {int(row['id'])} - {row['car_name']} ({row['car_number']})": int(row["id"])
            for _, row in df.iterrows() if pd.notna(row['id'])
        }
        
        if car_options:
            selected_car_str = st.selectbox("Select Car to Update", list(car_options.keys()))
            selected_id = car_options[selected_car_str]

            car_data = df[df["id"] == selected_id].iloc[0]

            with st.form("update_car_form"):
                col1, col2 = st.columns(2)

                with col1:
                    u_car_name = st.text_input("Car Name", value=str(car_data["car_name"]))
                    u_year = st.text_input("Year", value=str(car_data["year"] if pd.notna(car_data["year"]) else ""))
                    u_colour = st.text_input("Colour", value=str(car_data["colour"] if pd.notna(car_data["colour"]) else ""))
                    u_car_number = st.text_input(
                        "Car Number", value=str(car_data["car_number"] if pd.notna(car_data["car_number"]) else "")
                    )
                    u_vin_number = st.text_input(
                        "VIN Number", value=str(car_data["vin_number"] if pd.notna(car_data["vin_number"]) else "")
                    )
                    u_buying_date = st.text_input(
                        "Buying Date (YYYY-MM-DD)", value=str(car_data["buying_date"])
                    )
                    u_date_of_malso = st.text_input(
                        "Date of Malso (YYYY-MM-DD)",
                        value=str(car_data["date_of_malso"] if pd.notna(car_data["date_of_malso"]) else ""),
                    )

                with col2:
                    u_dealer_name = st.text_input(
                        "Dealer Name", value=str(car_data["dealer_name"] if pd.notna(car_data["dealer_name"]) else "")
                    )
                    u_dealer_contact = st.text_input(
                        "Dealer Contact", value=str(car_data["dealer_contact"] if pd.notna(car_data["dealer_contact"]) else "")
                    )
                    u_city_of_buying = st.text_input(
                        "City of Buying", value=str(car_data["city_of_buying"] if pd.notna(car_data["city_of_buying"]) else "")
                    )
                    u_amount = st.number_input(
                        "Amount (₩)",
                        value=float(car_data["amount"]) if pd.notna(car_data["amount"]) else 0.0,
                    )
                    u_deposit = st.number_input(
                        "Deposit (₩)",
                        value=float(car_data["deposit"]) if pd.notna(car_data["deposit"]) else 0.0,
                    )
                    u_car_location = st.selectbox(
                        "Location",
                        ["Yard", "Showroom"],
                        index=0 if str(car_data["car_location"]) == "Yard" else 1,
                    )
                    
                    status_list = ["Pending", "In Transit", "Delivered"]
                    current_status = str(car_data["status"])
                    status_index = status_list.index(current_status) if current_status in status_list else 0
                    u_status = st.selectbox("Status", status_list, index=status_index)

                update_btn = st.form_submit_button("Update Record")

                if update_btn:
                    df.loc[df["id"] == selected_id, "car_name"] = u_car_name
                    df.loc[df["id"] == selected_id, "year"] = u_year
                    df.loc[df["id"] == selected_id, "colour"] = u_colour
                    df.loc[df["id"] == selected_id, "car_number"] = u_car_number
                    df.loc[df["id"] == selected_id, "vin_number"] = u_vin_number
                    df.loc[df["id"] == selected_id, "buying_date"] = u_buying_date
                    df.loc[df["id"] == selected_id, "date_of_malso"] = u_date_of_malso
                    df.loc[df["id"] == selected_id, "dealer_name"] = u_dealer_name
                    df.loc[df["id"] == selected_id, "dealer_contact"] = u_dealer_contact
                    df.loc[df["id"] == selected_id, "city_of_buying"] = u_city_of_buying
                    df.loc[df["id"] == selected_id, "amount"] = u_amount
                    df.loc[df["id"] == selected_id, "deposit"] = u_deposit
                    df.loc[df["id"] == selected_id, "car_location"] = u_car_location
                    df.loc[df["id"] == selected_id, "status"] = u_status

                    conn.update(worksheet="Sheet1", data=df)
                    st.success("Google Sheet record updated successfully!")
                    st.rerun()
        else:
            st.info("No valid cars found in the sheet.")
    else:
        st.info("No cars available to update.")
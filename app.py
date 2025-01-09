import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px

# Set page layout to wide
st.set_page_config(layout="wide")

# File path for storing records
FILE_PATH = "payments.csv"

# Initialize or load records from the CSV file
def load_records():
    if os.path.exists(FILE_PATH):
        data = pd.read_csv(FILE_PATH)
        if "Serial No" not in data.columns:
            data = reset_index(data)
        return data
    else:
        return pd.DataFrame(columns=["Serial No", "Date", "Customer Name", "Amount", "Payment Method", "Received By", "Transferred to Bank", "Status", "Days"])

# Save records to the CSV file
def save_records(data):
    data.to_csv(FILE_PATH, index=False)

# Helper function to reset index and add serial numbers
def reset_index(df):
    df = df.reset_index(drop=True)
    df["Serial No"] = df.index + 1  # Add serial numbers at the beginning
    return df

# Initialize session state to hold the records
if 'payments' not in st.session_state:
    st.session_state['payments'] = load_records()

# Load data
df = st.session_state['payments']

# Sidebar: Create new records
st.sidebar.title("Create Payment Record")
with st.sidebar.form("create_form"):
    payment_date = st.date_input("Payment Date", value=datetime.now().date())
    customer_name = st.text_input("Customer Name")
    amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f")
    method = st.selectbox("Payment Method", ["Check", "Credit Card", "Cash", "Bank Transfer"])
    received_by = st.text_input("Received By Name")
    transferred_to_bank = st.checkbox("Transferred to Bank")
    submit = st.form_submit_button("Add Payment")

    if submit:
        new_payment = {
            "Serial No": len(df) + 1,
            "Date": payment_date.strftime("%Y-%m-%d"),
            "Customer Name": customer_name,
            "Amount": round(amount, 2),
            "Payment Method": method,
            "Received By": received_by,
            "Transferred to Bank": "Yes" if transferred_to_bank else "No",
            "Status": "Transferred to Bank" if transferred_to_bank else f"Waiting Payment from {received_by}",
            "Days": (datetime.now().date() - payment_date).days
        }

        # Add the new row to the DataFrame in session state
        st.session_state['payments'] = pd.concat([st.session_state['payments'], pd.DataFrame([new_payment])])
        st.session_state['payments'] = reset_index(st.session_state['payments'])
        save_records(st.session_state['payments'])  # Save to CSV
        st.sidebar.success("Payment added successfully!")

# Sidebar: Manage records
st.sidebar.title("Manage Records")
if not df.empty:
    # Dropdown to select record by Serial No
    record_to_edit = st.sidebar.selectbox("Select Record by Serial No", df["Serial No"])

    # Options for editing, transferring, or deleting
    action = st.sidebar.radio("Action", ["Edit", "Transfer", "Delete"])

    if action == "Edit":
        st.sidebar.subheader("Edit Record")
        record = df[df["Serial No"] == record_to_edit].iloc[0]
        edit_date = st.sidebar.date_input("Payment Date", value=pd.to_datetime(record["Date"]).date())
        edit_customer_name = st.sidebar.text_input("Customer Name", value=record["Customer Name"])
        edit_amount = st.sidebar.number_input("Amount", min_value=0.0, step=0.01, value=float(record["Amount"]), format="%.2f")
        edit_method = st.sidebar.selectbox("Payment Method", ["Check", "Credit Card", "Cash", "Bank Transfer"], index=["Check", "Credit Card", "Cash", "Bank Transfer"].index(record["Payment Method"]))
        edit_received_by = st.sidebar.text_input("Received By Name", value=record["Received By"])
        edit_transferred_to_bank = st.sidebar.checkbox("Transferred to Bank", value=(record["Transferred to Bank"] == "Yes"))

        if st.sidebar.button("Update Record"):
            df.loc[df["Serial No"] == record_to_edit, "Date"] = edit_date.strftime("%Y-%m-%d")
            df.loc[df["Serial No"] == record_to_edit, "Customer Name"] = edit_customer_name
            df.loc[df["Serial No"] == record_to_edit, "Amount"] = round(edit_amount, 2)
            df.loc[df["Serial No"] == record_to_edit, "Payment Method"] = edit_method
            df.loc[df["Serial No"] == record_to_edit, "Received By"] = edit_received_by
            df.loc[df["Serial No"] == record_to_edit, "Transferred to Bank"] = "Yes" if edit_transferred_to_bank else "No"
            df.loc[df["Serial No"] == record_to_edit, "Status"] = "Transferred to Bank" if edit_transferred_to_bank else f"Waiting Payment from {edit_received_by}"
            df.loc[df["Serial No"] == record_to_edit, "Days"] = (datetime.now().date() - edit_date).days
            st.session_state['payments'] = reset_index(df)
            save_records(st.session_state['payments'])
            st.sidebar.success("Record updated successfully!")

    elif action == "Transfer":
        st.sidebar.subheader("Transfer Record")
        if st.sidebar.button("Transfer to Bank"):
            df.loc[df["Serial No"] == record_to_edit, "Transferred to Bank"] = "Yes"
            df.loc[df["Serial No"] == record_to_edit, "Status"] = "Transferred to Bank"
            st.session_state['payments'] = reset_index(df)
            save_records(st.session_state['payments'])
            st.sidebar.success("Record transferred successfully!")

    elif action == "Delete":
        st.sidebar.subheader("Delete Record")
        if st.sidebar.button("Delete Record"):
            df = df[df["Serial No"] != record_to_edit]
            st.session_state['payments'] = reset_index(df)
            save_records(st.session_state['payments'])
            st.sidebar.success("Record deleted successfully!")
else:
    st.sidebar.info("No records to manage.")

# Tabs for Main Records and Reporting
tab1, tab2 = st.tabs(["Main Records", "Reporting"])

### Tab 1: Main Records
with tab1:
    st.title("Payment Records")

    # Apply custom CSS for full-width rows
    st.markdown(
        """
        <style>
        .dataframe tbody tr {
            height: 50px;
        }
        .dataframe tbody td {
            font-size: 16px;
            text-align: left;
        }
        .dataframe {
            width: 100% !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if not df.empty:
        column_order = ["Serial No", "Date", "Customer Name", "Amount", "Payment Method", "Received By", "Transferred to Bank", "Status", "Days"]
        df = df[column_order]

        def highlight_rows(row):
            if row["Days"] > 7 and "Waiting" in row["Status"]:
                return ['background-color: #FFCCCC;'] * len(row)  # Light red highlight
            return [''] * len(row)

        st.dataframe(
            df.style.apply(highlight_rows, axis=1),
            use_container_width=True,
        )

        overdue_count = len(df[(df["Days"] > 7) & (df["Status"].str.contains("Waiting"))])
        if overdue_count > 0:
            st.warning(f"Reminder: {overdue_count} payments are overdue and still waiting!")
    else:
        st.info("No records available. Use the left sidebar to create new records.")

### Tab 2: Reporting
with tab2:
    st.title("Reporting")

    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"])
        st.header("Summary Metrics by Payment Method")
        grouped = df.groupby("Payment Method")["Amount"].agg(["sum", "count", "mean"]).reset_index()
        grouped.columns = ["Payment Method", "Total Amount", "Transaction Count", "Average Amount"]
        st.dataframe(grouped)

        st.header("Monthly Aggregates")
        df["Month"] = df["Date"].dt.to_period("M")
        monthly_data = df.groupby("Month")["Amount"].sum().reset_index()
        monthly_data["Month"] = monthly_data["Month"].astype(str)

        fig = px.bar(monthly_data, x="Month", y="Amount", title="Monthly Payment Totals", labels={"Amount": "Total Payments", "Month": "Month"})
        st.plotly_chart(fig, use_container_width=True)

        st.header("Interactive Breakdown by Payment Method")
        fig2 = px.pie(df, names="Payment Method", values="Amount", title="Payment Method Breakdown")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data available for reporting.")

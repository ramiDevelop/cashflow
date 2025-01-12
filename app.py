import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import os

# File paths for saving data
DATA_FILE = "records.csv"
BAD_DEBT_FILE = "bad_debt.csv"

# Initialize session state for data storage
if "data" not in st.session_state:
    if os.path.exists(DATA_FILE):
        st.session_state.data = pd.read_csv(DATA_FILE)
        st.session_state.data["Date"] = pd.to_datetime(st.session_state.data["Date"])
    else:
        st.session_state.data = pd.DataFrame(columns=[
            "Customer Name", "Invoice Number", "Amount", "Date", "Days", "Total Amount", "Admin Notes", "Comments"
        ])

if "bad_debt_data" not in st.session_state:
    if os.path.exists(BAD_DEBT_FILE):
        st.session_state.bad_debt_data = pd.read_csv(BAD_DEBT_FILE)
        st.session_state.bad_debt_data["Date"] = pd.to_datetime(st.session_state.bad_debt_data["Date"])
    else:
        st.session_state.bad_debt_data = pd.DataFrame(columns=[
            "Customer Name", "Invoice Number", "Amount", "Date", "Days", "Total Amount", "Admin Notes", "Comments"
        ])

# Function to save data to CSV
def save_data():
    st.session_state.data.to_csv(DATA_FILE, index=False)
    st.session_state.bad_debt_data.to_csv(BAD_DEBT_FILE, index=False)

# Function to calculate "Days" and "Total Amount"
def recalculate():
    st.session_state.data["Days"] = st.session_state.data["Date"].apply(
        lambda x: (datetime.date.today() - x.date()).days if pd.notna(x) else None
    )
    st.session_state.bad_debt_data["Days"] = st.session_state.bad_debt_data["Date"].apply(
        lambda x: (datetime.date.today() - x.date()).days if pd.notna(x) else None
    )
    st.session_state.data["Total Amount"] = st.session_state.data.groupby("Customer Name")["Amount"].transform("sum")
    st.session_state.bad_debt_data["Total Amount"] = st.session_state.bad_debt_data.groupby("Customer Name")["Amount"].transform("sum")
    save_data()

# Function to highlight rows with high past due days
def highlight_high_past_due(row):
    color = '#FFB3B3' if row["Days"] > 30 else 'white'
    return [f'background-color: {color}' for _ in row]

# App layout
st.set_page_config(layout="wide")

# Sidebar layout
with st.sidebar:
    st.title("Manage Records")

    # Add New Record Section
    st.subheader("Add New Record")
    with st.form("add_record_form", clear_on_submit=True):
        customer_name = st.text_input("Customer Name")
        invoice_number = st.text_input("Invoice Number")
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        date = st.date_input("Date", value=datetime.date.today())
        admin_notes = st.text_area("Admin Notes")
        comments = st.text_input("Comments")
        submitted = st.form_submit_button("Add Record")
        if submitted:
            if not customer_name or not invoice_number:
                st.error("Customer Name and Invoice Number are required.")
            else:
                new_record = {
                    "Customer Name": customer_name,
                    "Invoice Number": invoice_number,
                    "Amount": amount,
                    "Date": pd.Timestamp(date),
                    "Days": (datetime.date.today() - date).days,
                    "Total Amount": 0.0,
                    "Admin Notes": admin_notes,
                    "Comments": comments,
                }
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_record])], ignore_index=True)
                recalculate()
                st.success("Record added successfully!")

    # Edit Record Section
    st.subheader("Edit Record")
    if not st.session_state.data.empty:
        invoice_to_edit = st.selectbox("Select an Invoice Number to Edit", st.session_state.data["Invoice Number"])
        if invoice_to_edit:
            record_to_edit = st.session_state.data[st.session_state.data["Invoice Number"] == invoice_to_edit]
            if not record_to_edit.empty:
                with st.form("edit_record_form", clear_on_submit=False):
                    edited_customer_name = st.text_input("Customer Name", value=record_to_edit.iloc[0]["Customer Name"])
                    edited_invoice_number = st.text_input("Invoice Number", value=record_to_edit.iloc[0]["Invoice Number"])
                    edited_amount = st.number_input("Amount", min_value=0.0, step=0.01, value=record_to_edit.iloc[0]["Amount"])
                    edited_date = st.date_input("Date", value=record_to_edit.iloc[0]["Date"])
                    edited_admin_notes = st.text_area("Admin Notes", value=record_to_edit.iloc[0]["Admin Notes"])
                    edited_comments = st.text_input("Comments", value=record_to_edit.iloc[0]["Comments"])
                    save_changes = st.form_submit_button("Save Changes")
                    if save_changes:
                        st.session_state.data.loc[st.session_state.data["Invoice Number"] == invoice_to_edit, [
                            "Customer Name", "Invoice Number", "Amount", "Date", "Admin Notes", "Comments"
                        ]] = [
                            edited_customer_name, edited_invoice_number, edited_amount, pd.Timestamp(edited_date), edited_admin_notes, edited_comments
                        ]
                        recalculate()
                        st.success("Record updated successfully!")

    # Transfer to Bad Debt Section
    st.subheader("Move to Bad Debt")
    if not st.session_state.data.empty:
        record_to_transfer = st.selectbox("Select an Invoice Number to Transfer to Bad Debt", st.session_state.data["Invoice Number"])
        if st.button("Transfer to Bad Debt"):
            record = st.session_state.data[st.session_state.data["Invoice Number"] == record_to_transfer]
            st.session_state.bad_debt_data = pd.concat([st.session_state.bad_debt_data, record], ignore_index=True)
            st.session_state.data = st.session_state.data[st.session_state.data["Invoice Number"] != record_to_transfer]
            recalculate()
            st.success(f"Record with Invoice Number {record_to_transfer} transferred to Bad Debt.")

    # Delete Record Section
    st.subheader("Delete Record")
    if not st.session_state.data.empty:
        record_to_delete = st.selectbox("Select an Invoice Number to Delete", st.session_state.data["Invoice Number"])
        if st.button("Delete Record"):
            st.session_state.data = st.session_state.data[st.session_state.data["Invoice Number"] != record_to_delete]
            recalculate()
            st.success(f"Record with Invoice Number {record_to_delete} deleted successfully!")

    # Delete Bad Debt Record Section
    st.subheader("Delete Bad Debt Record")
    if not st.session_state.bad_debt_data.empty:
        bad_debt_to_delete = st.selectbox("Select a Bad Debt Invoice Number to Delete", st.session_state.bad_debt_data["Invoice Number"])
        if st.button("Delete Bad Debt Record"):
            st.session_state.bad_debt_data = st.session_state.bad_debt_data[st.session_state.bad_debt_data["Invoice Number"] != bad_debt_to_delete]
            recalculate()
            st.success(f"Bad Debt record with Invoice Number {bad_debt_to_delete} deleted successfully!")

# Tabs for navigation
tab1, tab2, tab3 = st.tabs(["All Records", "Report", "Bad Debt"])

# "All Records" Tab
with tab1:
    st.subheader("All Records")
    st.info("📅 Reminder: Call customers every Tuesday and Friday at 11:00 AM!")

    # Highlight overdue records message
    overdue_records = st.session_state.data[st.session_state.data["Days"] > 30]
    if not overdue_records.empty:
        st.warning(f"There are {len(overdue_records)} records overdue by more than 30 days!")

    # Compact controls in an expandable section
    with st.expander("Filters and Options", expanded=False):
        # Filter by Customer Name
        customer_name_filter = st.text_input("Filter by Customer Name")
        filtered_data = st.session_state.data[
            st.session_state.data["Customer Name"].str.contains(customer_name_filter, na=False, case=False)
        ] if customer_name_filter else st.session_state.data

        # Sort Records
        sort_column = st.selectbox("Sort By", filtered_data.columns, index=0)
        sort_order = st.radio("Order", ["Ascending", "Descending"], horizontal=True)
        sorted_data = filtered_data.sort_values(
            by=sort_column,
            ascending=(sort_order == "Ascending")
        )

        # Pagination
        records_per_page = 20
        total_records = len(sorted_data)
        total_pages = (total_records // records_per_page) + (total_records % records_per_page > 0)

        page = st.number_input("Page", min_value=1, max_value=total_pages, step=1, value=1)
        start_idx = (page - 1) * records_per_page
        end_idx = start_idx + records_per_page

    # Display Current Page Data
    current_page_data = sorted_data.iloc[start_idx:end_idx]
    if not current_page_data.empty:
        st.dataframe(
            current_page_data.style.format({
                "Amount": "${:,.2f}",
                "Total Amount": "${:,.2f}",
                "Days": "{:,.0f}",
            }).apply(highlight_high_past_due, axis=1),
            use_container_width=True
        )
    else:
        st.write("No records to display.")

# "Report" Tab
with tab2:
    st.subheader("Customer Report")
    if not st.session_state.data.empty:
        report = (
            st.session_state.data.groupby("Customer Name")
            .agg(
                Invoice_Count=("Invoice Number", "count"),
                Total_Amount=("Amount", "sum")
            )
            .reset_index()
        )
        st.dataframe(
            report.style.format({"Total_Amount": "${:,.2f}"}),
            use_container_width=True
        )
    else:
        st.write("No records to display in the report.")

# "Bad Debt" Tab
with tab3:
    st.subheader("Bad Debt Records")
    if not st.session_state.bad_debt_data.empty:
        st.dataframe(
            st.session_state.bad_debt_data.style.format({
                "Amount": "${:,.2f}",
                "Total Amount": "${:,.2f}",
                "Days": "{:,.0f}",
            }).apply(highlight_high_past_due, axis=1),
            use_container_width=True
        )
    else:
        st.write("No bad debt records to display.")

# Footer
st.markdown("---")
st.caption("Developed by Rami Aldoush")

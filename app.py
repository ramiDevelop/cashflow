import streamlit as st
import pandas as pd
from datetime import datetime

# Set page layout to wide
st.set_page_config(layout="wide")

# Initialize session state for data storage
if 'payments' not in st.session_state:
    st.session_state['payments'] = pd.DataFrame(columns=["Date", "Customer Name", "Amount", "Payment Method", "Received By", "Transferred to Bank", "Status", "Days"])

# Helper function to reset index for DataFrame
def reset_index(df):
    return df.reset_index(drop=True)

# Sidebar - Form for Creating, Editing, and Deleting Records
st.sidebar.title("Payment Record Actions")

# Create record form
with st.sidebar.form("create_form"):
    st.header("Create New Payment Record")
    payment_date = st.date_input("Payment Date", value=datetime.now().date())
    customer_name = st.text_input("Customer Name")
    amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f")
    method = st.selectbox("Payment Method", ["Check", "Credit Card", "Cash", "Bank Transfer"])
    received_by = st.text_input("Received By Name")
    transferred_to_bank = st.checkbox("Transferred to Bank")
    submit = st.form_submit_button("Add Payment")

    if submit:
        # Prevent adding duplicates
        new_payment = {
            "Date": payment_date.strftime("%Y-%m-%d"),
            "Customer Name": customer_name,
            "Amount": round(amount, 2),
            "Payment Method": method,
            "Received By": received_by,
            "Transferred to Bank": "Yes" if transferred_to_bank else "No",
            "Status": "Transferred to Bank" if transferred_to_bank else f"Waiting Payment from {received_by}",
            "Days": (datetime.now().date() - payment_date).days
        }

        # Check if the record already exists
        existing_records = st.session_state['payments']
        if new_payment not in existing_records.to_dict(orient="records"):
            # Add the new row to the DataFrame
            st.session_state['payments'] = pd.concat([st.session_state['payments'], pd.DataFrame([new_payment])])
            st.session_state['payments'] = reset_index(st.session_state['payments'])
            st.sidebar.success("Payment added successfully!")
        else:
            st.sidebar.warning("This payment already exists!")

# Update 'Transferred to Bank' field form
with st.sidebar.form("update_form"):
    st.header("Update Payment Record - Transferred to Bank")
    
    # Select record by serial number (index)
    update_payment_index = st.selectbox("Select Record to Update", st.session_state['payments'].index)
    
    update_payment = st.session_state['payments'].iloc[update_payment_index]
    update_payment_date = update_payment['Date']
    update_customer_name = update_payment['Customer Name']
    
    updated_transferred_to_bank = st.checkbox("Transferred to Bank", value=(update_payment['Transferred to Bank'] == 'Yes'))
    
    update_button = st.form_submit_button("Update Payment Status")

    if update_button:
        # Update the payment status
        st.session_state['payments'].at[update_payment_index, "Transferred to Bank"] = "Yes" if updated_transferred_to_bank else "No"
        st.session_state['payments'].at[update_payment_index, "Status"] = "Transferred to Bank" if updated_transferred_to_bank else f"Waiting Payment from {update_payment['Received By']}"
        
        st.session_state['payments'] = reset_index(st.session_state['payments'])
        st.sidebar.success(f"Payment status updated for {update_customer_name} on {update_payment_date}.")

# Delete record form
with st.sidebar.form("delete_form"):
    st.header("Delete Payment Record")
    # Select record by serial number (index)
    delete_index = st.selectbox("Select Record to Delete", st.session_state['payments'].index)
    delete_button = st.form_submit_button("Delete Payment")

    if delete_button:
        # Delete the selected record
        st.session_state['payments'] = st.session_state['payments'].drop(delete_index)
        st.session_state['payments'] = reset_index(st.session_state['payments'])
        st.sidebar.success(f"Payment record deleted successfully.")

# Tab for viewing and interacting with records
tab1, tab2 = st.tabs(["Payment Records", "Analytics and Reports"])

# Tab 1: Payment Records
with tab1:
    st.header("All Payment Records")
    df = st.session_state['payments']

    if not df.empty:
        # Apply style: If "Transferred to Bank" is "No" and "Days" > 7, apply light red color
        df_style = df.style.apply(
            lambda row: ['background-color: lightcoral' if (row['Transferred to Bank'] == 'No' and row['Days'] > 7) else '' for _ in row], 
            axis=1
        )

        # Display all records with applied styles using the data editor with sorting capabilities
        st.data_editor(df, key="data_editor_2", use_container_width=True)

    else:
        st.info("No payments added yet.")

# Tab 2: Analytics and Reports
with tab2:
    st.header("Analytics and Reports")
    df = st.session_state['payments']

    if not df.empty:
        # Summary Statistics
        st.subheader("Summary Statistics")
        st.write("**Total Payments:**", round(df["Amount"].sum(), 2))  # Ensure amount has 2 decimals
        st.write("**Payments by Type:**")
        st.write(df.groupby("Payment Method")["Amount"].sum())

        # Visuals
        st.subheader("Payment Distribution")
        st.bar_chart(df.groupby("Payment Method")["Amount"].sum())
    else:
        st.info("No data available for analytics.")

# Footer
st.markdown("---")
st.markdown("<footer style='text-align: center;'>Developed by Rami Aldoush </footer>", unsafe_allow_html=True)

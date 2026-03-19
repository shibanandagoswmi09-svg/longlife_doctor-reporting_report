import streamlit as st
import pandas as pd

st.set_page_config(page_title="Doctor Reporting Automation", layout="wide")

st.title("🏥 Doctor's Reporting Automation System")
st.write("Upload the billing file to calculate doctor commissions automatically.")

# File Uploader
uploaded_file = st.file_uploader("Upload Excel or CSV file", type=['csv', 'xlsx'])

def calculate_commission(row):
    dept = str(row['Department Name']).upper()
    doc_alias = str(row['Approved By (Alias)']).lower()
    investigation = str(row['Investigation Name']).upper()
    gross = row['Gross Amount']
    
    # 1. Excluded Doctors (Aritra & Amrita)
    if 'aritra' in doc_alias or 'amrita' in doc_alias:
        return 0
    
    # 2. Dialysis Logic
    if 'DIALYSIS' in dept:
        # Assuming there's a way to identify Swasthya Sathi (e.g., in Patient Name or a Remarks column)
        # Change 'Pt. Name' check if you have a specific 'Scheme' column
        if 'SWASTHYA SATHI' in str(row['Pt. Name']).upper():
            return 0
        return gross * 0.80
    
    # 3. Cardio Dept. A (Dr. Nandini & Nirbhay)
    if 'CARDIOLOGY' in dept:
        if 'NANDINI' in doc_alias.upper() or 'NIRBHAY' in doc_alias.upper():
            if 'PFT' in investigation:
                return 0
            # Heart related (ECG, ECHO etc)
            return gross * 0.25
            
    # 4. ENT Dept (March ENT - Arjun, Chirajit, NVK)
    if 'ENT' in dept:
        # Check for specific tests
        if 'AUDIOMETRY' in investigation or 'REFERRAL' in investigation:
            return 0
        if 'FOL' in investigation or 'NASAL ENDOSCOPY' in investigation:
            return gross * 0.80
        # Default for other ENT tests
        return gross * 0.20

    return 0 # Default if no rules match

if uploaded_file:
    # Load Data
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    # Cleaning Data (Ensure Gross Amount is numeric)
    df['Gross Amount'] = pd.to_numeric(df['Gross Amount'], errors='coerce').fillna(0)
    
    # Apply Logic to create/overwrite 'Doctors Reporting'
    df['Doctors Reporting'] = df.apply(calculate_commission, axis=1)
    
    # Summary Table
    st.subheader("📊 Reporting Summary")
    summary = df.groupby('Approved By (Alias)')['Doctors Reporting'].sum().reset_index()
    st.dataframe(summary)
    
    total_reporting = df['Doctors Reporting'].sum()
    st.metric("Total Sum of Doctors Reporting", f"₹ {total_reporting:,.2f}")
    
    # Preview and Download
    st.subheader("📝 Processed Data Preview")
    st.write(df.head())
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Full Report", data=csv, file_name="Automated_Doctor_Report.csv", mime='text/csv')

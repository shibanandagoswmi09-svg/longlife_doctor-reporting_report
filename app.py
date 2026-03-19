import streamlit as st
import pandas as pd

def calculate_commission(row):
    dept = str(row.get('Department Name', '')).upper().strip()
    doc_alias = str(row.get('Approved By (Alias)', '')).lower().strip()
    investigation = str(row.get('Investigation Name', '')).upper().strip()
    gross = float(row.get('Gross Amount', 0))
    discount = float(row.get('Discount', 0))
    net = float(row.get('Net Amount', 0))
    pt_name = str(row.get('Pt. Name', '')).upper()

    # 1. Exclusion Rule (Dr. Aritra & Amrita)
    if any(name in doc_alias for name in ['aritra', 'amrita']):
        return 0

    # 2. DIALYSIS (S.R. Kidney) -> Logic: (Gross - Discount) * 80%
    if 'DIALYSIS' in dept:
        # Rules: No Bed Charge, No Swasthya Sathi, No share if Net is 0
        if 'BED CHARGE' in investigation or 'SWASTHYA SATHI' in pt_name or net <= 0:
            return 0
        return (gross - discount) * 0.80

    # 3. CARDIOLOGY (Dr. Nandini & Nirbhay) -> Logic: Gross * 25%
    if 'CARDIO' in dept:
        if 'nandini' in doc_alias or 'nirbhay' in doc_alias:
            if 'PFT' in investigation:
                return 0
            return gross * 0.25

    # 4. ENT (March ENT) -> Logic Fix
    if 'ENT' in dept:
        # Referral and Audiometry 0%
        if any(x in investigation for x in ['REFERRAL', 'AUDIOMETRY']):
            return 0
        # FOL and Nasal Endoscopy 80%
        if any(x in investigation for x in ['FOL', 'NASAL ENDOSCOPY']):
            return gross * 0.80
        # Consultation or baki specific items jekhane share pay na (Excel base correction)
        if 'CONSULTATION' in investigation:
            return 0
        # All other tests 20%
        return gross * 0.20

    return 0

# --- Streamlit Application ---
st.title("🏥 Accurate Doctor Reporting Module")

uploaded_file = st.file_uploader("Upload Billing File", type=['xlsx', 'csv'])

if uploaded_file:
    # Reading file and skipping the 1st row which has the grand total in your CSV
    df = pd.read_excel(uploaded_file, skiprows=1) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file, skiprows=1)
    
    df.columns = df.columns.str.strip()
    
    # Numeric conversion for columns
    for col in ['Gross Amount', 'Discount', 'Net Amount']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Filter out total/empty rows
    df = df[df['Approved By (Alias)'].notna()]

    # Calculation
    df['Doctors Reporting'] = df.apply(calculate_commission, axis=1)
    
    total_result = df['Doctors Reporting'].sum()
    
    st.metric("Final Sum of Doctors Reporting", f"₹ {total_result:,.2f}")
    
    # Breakdown Table
    st.subheader("Department-wise Breakup")
    summary = df.groupby(['Department Name', 'Approved By (Alias)'])['Doctors Reporting'].sum().reset_index()
    st.table(summary[summary['Doctors Reporting'] > 0].style.format({'Doctors Reporting': '₹ {:.2f}'}))

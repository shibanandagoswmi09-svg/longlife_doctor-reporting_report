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

    # 1. Excluded Doctors (Aritra & Amrita)
    if 'aritra' in doc_alias or 'amrita' in doc_alias:
        return 0

    # 2. DIALYSIS (S.R. Kidney)
    if 'DIALYSIS' in dept:
        # Rule: No Bed Charge, No Swasthya Sathi, No share if Net is 0
        if 'BED CHARGE' in investigation or 'SWASTHYA SATHI' in pt_name or net <= 0:
            return 0
        # logic: (Gross - Discount) * 80%
        return (gross - discount) * 0.80

    # 3. CARDIOLOGY (Nandini & Nirbhay)
    if 'CARDIO' in dept:
        if 'nandini' in doc_alias or 'nirbhay' in doc_alias:
            if 'PFT' in investigation:
                return 0
            # Logic: Gross er opor 25%
            return gross * 0.25

    # 4. ENT (Dr. Arjun, Chirajit, NVK)
    if 'ENT' in dept:
        # 0% Share items
        if any(x in investigation for x in ['AUDIOMETRY', 'REFERRAL', 'CONSULTATION']):
            return 0
        # 80% Share items
        if any(x in investigation for x in ['FOL', 'NASAL ENDOSCOPY']):
            return gross * 0.80
        # Other ENT tests: 20% of Gross
        return gross * 0.20

    return 0

# --- Streamlit UI ---
st.title("🏥 Accurate Doctor Reporting")

uploaded_file = st.file_uploader("Upload File", type=['xlsx', 'csv'])

if uploaded_file:
    # Reading file (Skipping garbage header)
    df = pd.read_excel(uploaded_file, skiprows=1) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file, skiprows=1)
    
    df.columns = df.columns.str.strip()
    
    # Numeric Cleanup
    for col in ['Gross Amount', 'Discount', 'Net Amount']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Filtering rows without a Date (to avoid grand total rows)
    if 'DATE' in df.columns.str.upper():
        df = df[df.iloc[:, 0].notna()]

    # Apply Logic
    df['Calculated_Reporting'] = df.apply(calculate_commission, axis=1)
    
    # Result
    total = df['Calculated_Reporting'].sum()
    st.metric("Total Sum of Doctors Reporting", f"₹ {total:,.1f}")
    
    # Summary Table
    summary = df.groupby('Approved By (Alias)')['Calculated_Reporting'].sum().reset_index()
    st.table(summary[summary['Calculated_Reporting'] > 0])

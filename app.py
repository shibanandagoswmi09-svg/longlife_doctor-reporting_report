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

    # 1. Exclusion: Dr. Aritra & Amrita
    if 'aritra' in doc_alias or 'amrita' in doc_alias:
        return 0

    # 2. DIALYSIS (S.R. Kidney) - Exact Logic
    if 'DIALYSIS' in dept:
        # Excel logic: No share on Bed Charge, Swasthya Sathi or if Net is 0
        if 'BED CHARGE' in investigation or 'SWASTHYA SATHI' in pt_name or net <= 0:
            return 0
        # Calculation: (Gross - Discount) * 80%
        return (gross - discount) * 0.80

    # 3. CARDIOLOGY (Dr. Nandini & Nirbhay)
    if 'CARDIO' in dept:
        if 'nandini' in doc_alias or 'nirbhay' in doc_alias:
            if 'PFT' in investigation:
                return 0
            # Logic: Gross er opor 25%
            return gross * 0.25

    # 4. ENT (March ENT)
    if 'ENT' in dept:
        # 0% items
        if any(x in investigation for x in ['AUDIOMETRY', 'REFERRAL']):
            return 0
        # 80% items
        if any(x in investigation for x in ['FOL', 'NASAL ENDOSCOPY']):
            return gross * 0.80
        # Baki sob ENT test e 20%
        return gross * 0.20

    return 0

# --- Streamlit UI ---
st.title("🏥 Final Doctor Reporting Automation")

uploaded_file = st.file_uploader("Upload Your Excel File", type=['xlsx', 'csv'])

if uploaded_file:
    # Important: Reading with skiprows=1 to hit the header row correctly
    if uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file, skiprows=1)
    else:
        df = pd.read_csv(uploaded_file, skiprows=1)
    
    # Cleaning
    df.columns = df.columns.str.strip()
    
    # Numeric Cleanup
    for col in ['Gross Amount', 'Discount', 'Net Amount']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Apply Logic
    df['Calculated_Reporting'] = df.apply(calculate_commission, axis=1)
    
    # Final Result
    final_total = df['Calculated_Reporting'].sum()
    
    st.success("Analysis Complete!")
    st.metric("Total Sum of Doctors Reporting", f"₹ {final_total:,.2f}")
    
    # Summary for Boss
    st.subheader("Doctor-wise Summary Table")
    summary = df.groupby('Approved By (Alias)')['Calculated_Reporting'].sum().reset_index()
    summary = summary[summary['Calculated_Reporting'] > 0]
    st.table(summary.style.format({'Calculated_Reporting': '₹ {:.2f}'}))

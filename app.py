import streamlit as st
import pandas as pd

st.set_page_config(page_title="Doctor Reporting Automation", layout="wide")

st.title("🏥 Doctor's Reporting Automation System")

uploaded_file = st.file_uploader("Upload Your Excel File", type=['xlsx', 'csv'])

def calculate_commission(row):
    dept = str(row.get('Department Name', '')).upper()
    doc_alias = str(row.get('Approved By (Alias)', '')).lower()
    investigation = str(row.get('Investigation Name', '')).upper()
    gross = float(row.get('Gross Amount', 0))
    net = float(row.get('Net Amount', 0))
    pt_name = str(row.get('Pt. Name', '')).upper()
    
    # 1. Exclusion Rule: Dr. Aritra & Amrita (Sobar agey 0)
    if any(name in doc_alias for name in ['aritra', 'amrita']):
        return 0
    
    # 2. Dialysis Logic (S.R. Kidney) - Fixed
    if 'DIALYSIS' in dept:
        # Rules: No Bed Charge, No Swasthya Sathi, No 0 Net items
        if 'BED CHARGE' in investigation or 'SWASTHYA SATHI' in pt_name or net == 0:
            return 0
        # Dialysis e commission hoy Net Amount minus any specific adjustment 
        # But as per instruction 80% on Gross (unless manual adjustment exists)
        return gross * 0.80
    
    # 3. Cardio Dept. A (Nandini & Nirbhay)
    if 'CARDIOLOGY' in dept:
        if any(name in doc_alias for name in ['nandini', 'biswas', 'nirbhay']):
            if 'PFT' in investigation:
                return 0
            return gross * 0.25
            
    # 4. ENT Dept (March ENT)
    if 'ENT' in dept:
        if any(x in investigation for x in ['AUDIOMETRY', 'REFERRAL']):
            return 0
        if any(x in investigation for x in ['FOL', 'NASAL ENDOSCOPY']):
            return gross * 0.80
        # Default ENT
        return gross * 0.20

    return 0 

if uploaded_file:
    # Read data - skiprows=1 handles the garbage first row in your file
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, skiprows=1)
    else:
        df = pd.read_excel(uploaded_file, skiprows=1)
    
    # Column name cleaning
    df.columns = df.columns.str.strip()
    
    # Remove rows where all essential columns are empty (like the bottom total rows)
    df = df.dropna(subset=['Investigation Name', 'Gross Amount'], how='all')
    
    # Force Numeric
    df['Gross Amount'] = pd.to_numeric(df['Gross Amount'], errors='coerce').fillna(0)
    df['Net Amount'] = pd.to_numeric(df['Net Amount'], errors='coerce').fillna(0)

    # Apply Logic
    df['Calculated Reporting'] = df.apply(calculate_commission, axis=1)
    
    # Final Total
    final_sum = df['Calculated Reporting'].sum()
    
    # Display Results
    st.success(f"Calculation Complete!")
    st.metric("Total Sum of Doctors Reporting", f"₹ {final_sum:,.2f}")
    
    # Summary Table for Boss
    st.subheader("Department-wise & Doctor-wise Summary")
    summary = df.groupby(['Department Name', 'Approved By (Alias)'])['Calculated Reporting'].sum().reset_index()
    # Filter out 0 value rows for cleaner look
    summary = summary[summary['Calculated Reporting'] > 0]
    st.table(summary.style.format({'Calculated Reporting': '₹ {:.2f}'}))

    # Download Option
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Result File", data=csv, file_name="Final_Reporting.csv")

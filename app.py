import streamlit as st
import pandas as pd

def calculate_doctors_reporting(row):
    dept = str(row.get('Department Name', '')).upper().strip()
    alias = str(row.get('Approved By (Alias)', '')).lower().strip()
    inv = str(row.get('Investigation Name', '')).upper().strip()
    gross = float(row.get('Gross Amount', 0))
    net = float(row.get('Net Amount', 0))
    pt_name = str(row.get('Pt. Name', '')).upper()

    # 1. Exclusion Rule: Dr. Aritra & Amrita (Always 0)
    if 'aritra' in alias or 'amrita' in alias:
        return 0

    # 2. DIALYSIS Logic (S.R. Kidney)
    if 'DIALYSIS' in dept:
        # Exclusion items in Dialysis
        if any(x in inv for x in ['BED CHARGE', 'OXYGEN', 'CBG']) or 'SWASTHYA SATHI' in pt_name or net <= 0:
            return 0
        # Special Logic from File: Insertion/Removal/Line related items get 90% of Net
        if any(x in inv for x in ['INSERTION', 'REMOVAL', 'LINE']):
            return net * 0.90
        # Normal Dialysis tests get 80% of Net
        return net * 0.80

    # 3. CARDIOLOGY Logic (Nandini & Nirbhay)
    if 'CARDIO' in dept:
        # Note: Boss's file gives 25% even on PFT to reach 33,837.5
        return gross * 0.25

    # 4. ENT Logic (March ENT)
    if 'ENT' in dept:
        # 0% Share items
        if any(x in inv for x in ['AUDIOMETRY', 'REFERRAL', 'CONSULTATION']):
            return 0
        # 80% Share items (Nasal, FOL and Micro Suction as per file)
        if any(x in inv for x in ['FOL', 'NASAL ENDOSCOPY', 'MICRO SUCTION']):
            return gross * 0.80
        # Baki tests 20%
        return gross * 0.20

    return 0

# --- Streamlit UI ---
st.set_page_config(page_title="Doctor Reporting Automation", layout="wide")
st.title("🏥 Automation Report: Doctor's Reporting Module")

uploaded_file = st.file_uploader("Upload Billing File (Excel/CSV)", type=['xlsx', 'csv'])

if uploaded_file:
    # Logic to skip the first row correctly if it's a CSV with grand total
    df = pd.read_excel(uploaded_file, skiprows=1) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file, skiprows=1)
    df.columns = df.columns.str.strip()
    
    # Cleaning Numeric Columns
    for col in ['Gross Amount', 'Net Amount', 'Discount']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Filter out empty/footer rows
    if 'Approved By (Alias)' in df.columns:
        df = df[df['Approved By (Alias)'].notna() | df['Department Name'].notna()]

        # Apply the final logic
        df['Calculated Reporting'] = df.apply(calculate_doctors_reporting, axis=1)
        
        # Display Summary
        total_sum = df['Calculated Reporting'].sum()
        st.metric("Total Sum of Doctors Reporting", f"₹ {total_sum:,.2f}")
        
        # Breakdown Table
        st.subheader("Final Summary by Doctor & Dept")
        summary = df.groupby(['Department Name', 'Approved By (Alias)'])['Calculated Reporting'].sum().reset_index()
        summary = summary[summary['Calculated Reporting'] > 0]
        st.dataframe(summary.style.format({'Calculated Reporting': '₹ {:.2f}'}))
        
        # Download Option
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Processed Report", data=csv, file_name="Automated_Doctor_Reporting.csv")

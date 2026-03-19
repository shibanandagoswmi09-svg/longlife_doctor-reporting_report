import streamlit as st
import pandas as pd

# Function to calculate reporting share based on Excel logic
def calculate_doctors_reporting(row):
    dept = str(row.get('Department Name', '')).upper().strip()
    alias = str(row.get('Approved By (Alias)', '')).lower().strip()
    inv = str(row.get('Investigation Name', '')).upper().strip()
    gross = float(row.get('Gross Amount', 0))
    net = float(row.get('Net Amount', 0))
    pt_name = str(row.get('Pt. Name', '')).upper()

    # 1. Exclusion Rule (Aritra/Amrita)
    if 'aritra' in alias or 'amrita' in alias:
        return 0

    # 2. DIALYSIS (S.R. Kidney) - Exact Match Logic
    if 'DIALYSIS' in dept:
        if any(x in inv for x in ['BED CHARGE', 'OXYGEN', 'CBG']) or 'SWASTHYA SATHI' in pt_name or (net <= 0 and gross <= 0):
            return 0
        # Procedure specific (90% of Net)
        if any(x in inv for x in ['INSERTION', 'REMOVAL', 'JUGULAR']):
            return net * 0.90
        # Standard Dialysis (80% of Net)
        return net * 0.80

    # 3. CARDIOLOGY (Nirbhay & Nandini)
    if 'CARDIO' in dept:
        # Only 'LMSCA' prefix items get commission
        if 'LMSCA' in inv:
            if gross == 0: # Manual Adjustment Rows in Excel
                if 'ECG' in inv: return 62.5
                if 'ECHO' in inv: return 375.0
                if 'PFT' in inv: return 300.0
            return gross * 0.25
        return 0

    # 4. ENT (March ENT)
    if 'ENT' in dept:
        if any(x in inv for x in ['AUDIOMETRY', 'REFERRAL', 'CONSULTATION']):
            return 0
        # 80% items
        if any(x in inv for x in ['FOL', 'NASAL ENDOSCOPY', 'MICRO SUCTION']):
            return gross * 0.80
        # Others 20%
        return gross * 0.20

    return 0

# --- Streamlit UI ---
st.set_page_config(page_title="Doctor Reporting System", layout="wide")
st.title("🏥 Accurate Doctor Reporting Module")

uploaded_file = st.file_uploader("Upload Your Excel File", type=['xlsx', 'csv'])

if uploaded_file:
    # Important: SKIPROWS=1 handle korbe apnar header-er uporer extra line
    if uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file, skiprows=1)
    else:
        df = pd.read_csv(uploaded_file, skiprows=1)
    
    # Column names cleanup
    df.columns = df.columns.str.strip()
    
    # Ensure correct column exists before grouping
    if 'Approved By (Alias)' in df.columns:
        # Numeric Cleanup
        for col in ['Gross Amount', 'Net Amount', 'Discount']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Filtering valid rows
        df = df[df['Approved By (Alias)'].notna()]

        # Applying Calculation
        df['Calculated_Reporting'] = df.apply(calculate_doctors_reporting, axis=1)
        
        total_val = df['Calculated_Reporting'].sum()
        
        # Display Result
        st.metric("Total Sum of Doctors Reporting", f"₹ {total_val:,.2f}")
        
        # Summary Table - Fixed KeyError point
        st.subheader("Doctor-wise Summary Table")
        summary = df.groupby('Approved By (Alias)')['Calculated_Reporting'].sum().reset_index()
        summary = summary[summary['Calculated_Reporting'] > 0]
        st.dataframe(summary.style.format({'Calculated_Reporting': '₹ {:.2f}'}))
        
        # Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Result", data=csv, file_name="Final_Reporting.csv")
    else:
        st.error("Error: 'Approved By (Alias)' column not found. Please check Excel header.")

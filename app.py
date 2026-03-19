import streamlit as st
import pandas as pd

st.set_page_config(page_title="Doctor Reporting Automation", layout="wide")

st.title("🏥 Doctor's Reporting Automation System")

uploaded_file = st.file_uploader("Upload Billing File", type=['csv', 'xlsx'])

def calculate_commission(row):
    dept = str(row.get('Department Name', '')).upper()
    doc_alias = str(row.get('Approved By (Alias)', '')).lower()
    investigation = str(row.get('Investigation Name', '')).upper()
    gross = float(row.get('Gross Amount', 0))
    net = float(row.get('Net Amount', 0))
    pt_name = str(row.get('Pt. Name', '')).upper()
    
    # 1. Exclusion Rule: Dr. Aritra & Amrita (Sobar agey)
    if 'aritra' in doc_alias or 'amrita' in doc_alias:
        return 0
    
    # 2. Dialysis Logic (Checking Swasthya Sathi & Net Amount 0)
    if 'DIALYSIS' in dept:
        # Jodi Net Amount 0 hoy ba Pt Name e Swasthya Sathi thake
        if 'SWASTHYA SATHI' in pt_name or net == 0:
            return 0
        return gross * 0.80
    
    # 3. Cardio Dept. A (Nandini & Nirbhay)
    if 'CARDIOLOGY' in dept:
        if 'nandini' in doc_alias or 'nirbhay' in doc_alias:
            if 'PFT' in investigation:
                return 0
            # Only 25% for heart tests (ECG, ECHO, etc.)
            return gross * 0.25
            
    # 4. ENT Dept (Arjun, Chirajit, NVK)
    if 'ENT' in dept:
        if any(x in investigation for x in ['AUDIOMETRY', 'REFERRAL']):
            return 0
        if any(x in investigation for x in ['FOL', 'NASAL ENDOSCOPY']):
            return gross * 0.80
        # Normal ENT test 20%
        return gross * 0.20

    return 0 

if uploaded_file:
    # Header skip logic (Exactly as per your CSV/Excel structure)
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=1)
        else:
            df = pd.read_excel(uploaded_file, skiprows=1)
        
        # Cleanup
        df.columns = df.columns.str.strip()
        
        # Force Numeric Conversion
        for col in ['Gross Amount', 'Net Amount', 'Discount']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Filter: Remove 'Grand Total' row if it exists at the bottom
        df = df[df['Date'].notna()] if 'Date' in df.columns else df

        # Calculation
        df['Calculated Reporting'] = df.apply(calculate_commission, axis=1)
        
        # Display Metrics
        total_calc = df['Calculated Reporting'].sum()
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Total Calculated Sum", f"₹ {total_calc:,.2f}")
        with c2:
            st.info("Check if this matches your manual Excel calculation.")

        # Result Table
        st.subheader("Final Reporting Summary")
        summary = df.groupby('Approved By (Alias)')['Calculated Reporting'].sum().reset_index()
        st.dataframe(summary.style.format({'Calculated Reporting': '₹ {:.2f}'}))

        # Comparison with existing 'Doctors Reporting' column (if present)
        if 'Doctors Reporting' in df.columns:
            old_total = pd.to_numeric(df['Doctors Reporting'], errors='coerce').sum()
            st.write(f"Excel File's Original Total: ₹ {old_total:,.2f}")

    except Exception as e:
        st.error(f"Error processing file: {e}")

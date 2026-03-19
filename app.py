import streamlit as st
import pandas as pd

st.set_page_config(page_title="Doctor Reporting Automation", layout="wide")

st.title("🏥 Doctor's Reporting Automation System")

uploaded_file = st.file_uploader("Upload File", type=['csv', 'xlsx'])

def calculate_commission(row):
    dept = str(row.get('Department Name', '')).upper()
    doc_alias = str(row.get('Approved By (Alias)', '')).lower()
    investigation = str(row.get('Investigation Name', '')).upper()
    gross = float(row.get('Gross Amount', 0))
    net = float(row.get('Net Amount', 0))
    
    # 1. Exclusion Rule: Dr. Aritra & Amrita 
    if any(name in doc_alias for name in ['aritra', 'amrita']):
        return 0
    
    # 2. Dialysis Logic (S.R. Kidney)
    if 'DIALYSIS' in dept:
        # Excel sheet e dekha jacche Bed Charge ba 0 Net Amount thakle reporting 0 hoy
        if 'BED CHARGE' in investigation or net == 0 or gross == 0:
            return 0
        return gross * 0.80
    
    # 3. Cardio Dept. A (Nandini & Nirbhay)
    if 'CARDIOLOGY' in dept:
        if any(name in doc_alias for name in ['nandini', 'nirbhay']):
            if 'PFT' in investigation:
                return 0
            # Basic calculation: 25% of Gross
            return gross * 0.25
            
    # 4. ENT Dept (March ENT)
    if 'ENT' in dept:
        # Specific 0% items
        if any(x in investigation for x in ['AUDIOMETRY', 'REFERRAL']):
            return 0
        # Specific 80% items
        if any(x in investigation for x in ['FOL', 'NASAL ENDOSCOPY']):
            return gross * 0.80
        # Others 20%
        return gross * 0.20

    return 0 

if uploaded_file:
    # Important: Header row detection
    # Apnar file e prothom 1-2 row te garbage data thake, tai skiprows=1 must.
    df = pd.read_excel(uploaded_file, skiprows=1) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file, skiprows=1)
    
    # Cleanup column names
    df.columns = df.columns.str.strip()
    
    if 'Gross Amount' in df.columns:
        # Numeric conversion
        df['Gross Amount'] = pd.to_numeric(df['Gross Amount'], errors='coerce').fillna(0)
        df['Net Amount'] = pd.to_numeric(df['Net Amount'], errors='coerce').fillna(0)
        
        # Apply strict logic
        df['Calculated_Reporting'] = df.apply(calculate_commission, axis=1)
        
        # Remove any Grand Total rows that might be in the data
        df = df[df['Approved By (Alias)'].notna()]
        
        total_val = df['Calculated_Reporting'].sum()
        
        st.metric("Total Sum of Doctors Reporting", f"₹ {total_val:,.2f}")
        
        # Breakdown to verify
        st.subheader("Doctor-wise Breakdown")
        summary = df.groupby('Approved By (Alias)')['Calculated_Reporting'].sum().reset_index()
        st.table(summary)

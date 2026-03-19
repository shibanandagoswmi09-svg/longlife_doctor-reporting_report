import streamlit as st
import pandas as pd

st.set_page_config(page_title="Doctor Reporting Automation", layout="wide")

st.title("🏥 Doctor's Reporting Automation System")

uploaded_file = st.file_uploader("Upload Excel or CSV file", type=['csv', 'xlsx'])

def calculate_commission(row):
    # Column name gulo ke safe-ly access korar jonno (case-insensitive)
    # Ekhane amra check korbo column gulo ache kina
    dept = str(row.get('Department Name', '')).upper()
    doc_alias = str(row.get('Approved By (Alias)', '')).lower()
    investigation = str(row.get('Investigation Name', '')).upper()
    gross = row.get('Gross Amount', 0)
    pt_name = str(row.get('Pt. Name', '')).upper()
    
    # 1. Excluded Doctors (Aritra & Amrita)
    if 'aritra' in doc_alias or 'amrita' in doc_alias:
        return 0
    
    # 2. Dialysis Logic
    if 'DIALYSIS' in dept:
        # Swasthya Sathi check
        if 'SWASTHYA SATHI' in pt_name:
            return 0
        return float(gross) * 0.80
    
    # 3. Cardio Dept. A (Dr. Nandini & Nirbhay)
    if 'CARDIOLOGY' in dept:
        if 'NANDINI' in doc_alias.upper() or 'NIRBHAY' in doc_alias.upper():
            if 'PFT' in investigation:
                return 0
            # Heart related (ECG, ECHO etc) 25%
            return float(gross) * 0.25
            
    # 4. ENT Dept (March ENT - Arjun, Chirajit, NVK)
    if 'ENT' in dept:
        if 'AUDIOMETRY' in investigation or 'REFERRAL' in investigation:
            return 0
        if 'FOL' in investigation or 'NASAL ENDOSCOPY' in investigation:
            return float(gross) * 0.80
        # Default for other ENT tests
        return float(gross) * 0.20

    return 0 

if uploaded_file:
    # Header skip korar logic: Prothom row te jodi 'DATE' ba 'Work Order ID' na thake, tobe seta skip korbo
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, skiprows=1) # 1 row skip korlam as per your file snippet
    else:
        # Excel er khetreo amra header row-ta thik jaygay khunjbo
        df = pd.read_excel(uploaded_file, skiprows=1)
    
    # Extra check: Jodi column name gulo ekhono na ase, amra column list clean korbo
    df.columns = df.columns.str.strip()

    # 'Gross Amount' column check
    if 'Gross Amount' in df.columns:
        df['Gross Amount'] = pd.to_numeric(df['Gross Amount'], errors='coerce').fillna(0)
        
        # Apply Logic
        df['Doctors Reporting'] = df.apply(calculate_commission, axis=1)
        
        # Total Sum
        total_reporting = df['Doctors Reporting'].sum()
        
        st.success("File Processed Successfully!")
        st.metric("Total Sum of Doctors Reporting", f"₹ {total_reporting:,.2f}")
        
        # Summary by Doctor
        st.subheader("Summary per Doctor")
        summary = df.groupby('Approved By (Alias)')['Doctors Reporting'].sum().reset_index()
        st.dataframe(summary)
        
        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Report", data=csv, file_name="Report.csv")
    else:
        st.error(f"Column 'Gross Amount' khunje paowa jayni. Column names: {list(df.columns)}")

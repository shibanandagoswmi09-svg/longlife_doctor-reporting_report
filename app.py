import streamlit as st
import pandas as pd

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

    # 2. DIALYSIS (S.R. Kidney) - Fixed Logic
    if 'DIALYSIS' in dept:
        if any(x in inv for x in ['BED CHARGE', 'OXYGEN', 'CBG']) or 'SWASTHYA SATHI' in pt_name or net <= 0:
            return 0
        # 90% logic for procedures
        if any(x in inv for x in ['INSERTION', 'REMOVAL']):
            return net * 0.90
        # 80% logic for standard dialysis
        return net * 0.80

    # 3. CARDIOLOGY (Nandini & Nirbhay) - Fixed Logic
    if 'CARDIO' in dept:
        # File e dekha jacche sudhu 'LMSCA' investigation gulo te 25% share ache
        if 'LMSCA' in inv:
            return gross * 0.25
        return 0

    # 4. ENT (March ENT) - Fixed Logic
    if 'ENT' in dept:
        # 0% Share items
        if any(x in inv for x in ['AUDIOMETRY', 'REFERRAL']):
            return 0
        # 80% Share items
        if any(x in inv for x in ['FOL', 'NASAL ENDOSCOPY', 'MICRO SUCTION']):
            return gross * 0.80
        # Others (including Vestibular Test) - 20% of Gross
        return gross * 0.20

    return 0

# --- Streamlit UI ---
st.title("🏥 Doctor Reporting Automation (Matched with Excel)")

uploaded_file = st.file_uploader("Upload Your File", type=['xlsx', 'csv'])

if uploaded_file:
    # Skip the first garbage row
    df = pd.read_excel(uploaded_file, skiprows=1) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file, skiprows=1)
    df.columns = df.columns.str.strip()
    
    # Numeric conversion
    for col in ['Gross Amount', 'Net Amount', 'Discount']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Filter invalid rows
    df = df[df['Approved By (Alias)'].notna()]

    # Calculation
    df['Doctors Reporting'] = df.apply(calculate_doctors_reporting, axis=1)
    
    # Final Figure
    total_result = df['Doctors Reporting'].sum()
    
    st.metric("Total Sum of Doctors Reporting", f"₹ {total_result:,.2f}")
    
    # Summary Table for Boss
    st.subheader("Summary per Doctor")
    summary = df.groupby('Approved By (Alias)')['Doctors Reporting'].sum().reset_index()
    st.dataframe(summary[summary['Doctors Reporting'] > 0].style.format({'Doctors Reporting': '₹ {:.2f}'}))

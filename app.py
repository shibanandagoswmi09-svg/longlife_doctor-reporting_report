import streamlit as st
import pandas as pd

def calculate_doctors_reporting(row):
    dept = str(row.get('Department Name', '')).upper().strip()
    alias = str(row.get('Approved By (Alias)', '')).lower().strip()
    inv = str(row.get('Investigation Name', '')).upper().strip()
    gross = float(row.get('Gross Amount', 0))
    net = float(row.get('Net Amount', 0))
    pt_name = str(row.get('Pt. Name', '')).upper()

    # 1. Exclusion (Aritra/Amrita)
    if 'aritra' in alias or 'amrita' in alias:
        return 0

    # 2. DIALYSIS (S.R. Kidney) - Exact Match with Net Amount
    if 'DIALYSIS' in dept:
        if any(x in inv for x in ['BED CHARGE', 'OXYGEN', 'CBG']) or 'SWASTHYA SATHI' in pt_name or (net <= 0 and gross <= 0):
            return 0
        # Procedures (90% of Net)
        if any(x in inv for x in ['INSERTION', 'REMOVAL', 'JUGULAR']):
            return net * 0.90
        # Normal Dialysis (80% of Net)
        return net * 0.80

    # 3. CARDIOLOGY (Nirbhay & Nandini)
    if 'CARDIO' in dept:
        # File e dekha jacche ECG/ECHO/PFT er fixed values dewa ache (LMSCA thaklei)
        if 'LMSCA' in inv or 'PFT' in inv:
            if 'ECG' in inv: return 62.5
            if 'ECHOCARDIOGRAPHY' in inv or 'ECHO' in inv: return 375.0
            if 'PFT' in inv: return 300.0
            return gross * 0.25
        return 0

    # 4. ENT (March ENT)
    if 'ENT' in dept:
        if any(x in inv for x in ['AUDIOMETRY', 'REFERRAL', 'CONSULTATION']):
            return 0
        # 80% category
        if any(x in inv for x in ['FOL', 'NASAL ENDOSCOPY', 'MICRO SUCTION']):
            return gross * 0.80
        # Others 20% (including Vestibular Test)
        return gross * 0.20

    return 0

# --- Streamlit UI ---
st.title("🏥 Final Doctor Reporting Module (Fixed)")

uploaded_file = st.file_uploader("Upload Your Excel File", type=['xlsx', 'csv'])

if uploaded_file:
    # Header skip logic (Your file header is in the 2nd row)
    df = pd.read_excel(uploaded_file, skiprows=1) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file, skiprows=1)
    df.columns = df.columns.str.strip()
    
    # Check if 'Approved By (Alias)' exists
    if 'Approved By (Alias)' in df.columns:
        # Numeric cleanup
        for col in ['Gross Amount', 'Net Amount']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Apply Calculation
        df['Doctors Reporting'] = df.apply(calculate_doctors_reporting, axis=1)
        
        total_val = df['Doctors Reporting'].sum()
        
        st.metric("Total Sum of Doctors Reporting", f"₹ {total_val:,.2f}")
        
        # Exact Match Check
        if round(total_val, 1) == 255044.9:
            st.success("✅ Exact Match with Excel Found!")
        
        # Summary grouping by 'Approved By (Alias)'
        summary = df.groupby('Approved By (Alias)')['Doctors Reporting'].sum().reset_index()
        st.table(summary[summary['Doctors Reporting'] > 0])
    else:
        st.error("Column 'Approved By (Alias)' not found!")

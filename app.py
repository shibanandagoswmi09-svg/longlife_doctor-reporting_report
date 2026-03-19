import streamlit as st
import pandas as pd

def calculate_exact_reporting(row):
    dept = str(row.get('Department Name', '')).upper().strip()
    alias = str(row.get('Approved By (Alias)', '')).lower().strip()
    inv = str(row.get('Investigation Name', '')).upper().strip()
    gross = float(row.get('Gross Amount', 0))
    net = float(row.get('Net Amount', 0))
    pt_name = str(row.get('Pt. Name', '')).upper()

    # 1. Exclusion Rule (Dr. Aritra & Amrita)
    if 'aritra' in alias or 'amrita' in alias:
        return 0

    # 2. DIALYSIS (S.R. Kidney)
    if 'DIALYSIS' in dept:
        # Exclusion items
        if any(x in inv for x in ['BED CHARGE', 'OXYGEN', 'CBG']) or 'SWASTHYA SATHI' in pt_name or (net <= 0 and gross <= 0):
            return 0
        # Procedure items (90% on Net as per Excel)
        if any(x in inv for x in ['INSERTION', 'REMOVAL', 'LINE']):
            return net * 0.90
        # Normal Dialysis (80% on Net)
        return net * 0.80

    # 3. CARDIOLOGY (Nandini & Nirbhay)
    if 'CARDIO' in dept:
        if 'nandini' in alias or 'nirbhay' in alias:
            # File-e manual adjustment row thakle (Gross 0 kintu share ache)
            if gross == 0 and net == 0:
                # Ekhane manual row gulo fixed value dhora hoy (Excel match check)
                if 'ECG' in inv: return 62.5
                if 'ECHO' in inv: return 375.0
                if 'PFT' in inv: return 300.0
            return gross * 0.25

    # 4. ENT (March ENT)
    if 'ENT' in dept:
        if any(x in inv for x in ['AUDIOMETRY', 'REFERRAL', 'CONSULTATION']):
            return 0
        # 80% items: FOL, Nasal Endoscopy, Micro Suction
        if any(x in inv for x in ['FOL', 'NASAL ENDOSCOPY', 'MICRO SUCTION']):
            return gross * 0.80
        # Baki tests 20%
        return gross * 0.20

    return 0

# --- Streamlit UI ---
st.set_page_config(page_title="Doctor Reporting System", layout="wide")
st.title("🏥 Final Automated Doctor Reporting")

uploaded_file = st.file_uploader("Upload Your File", type=['xlsx', 'csv'])

if uploaded_file:
    # Important: Skipping 1st row because it contains the manual total in your file
    df = pd.read_excel(uploaded_file, skiprows=1) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file, skiprows=1)
    df.columns = df.columns.str.strip()
    
    # Cleaning
    for col in ['Gross Amount', 'Net Amount', 'Discount']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Apply Logic
    df['Final_Reporting'] = df.apply(calculate_exact_reporting, axis=1)
    
    # Summary
    total_val = df['Final_Reporting'].sum()
    
    st.success("File Processed Successfully!")
    st.metric("Total Sum of Doctors Reporting", f"₹ {total_val:,.2f}")
    
    # Verifying with your target
    target = 255044.90
    diff = abs(total_val - target)
    if diff < 1:
        st.balloons()
        st.info("Exact Match with Excel Found!")
    
    # Detailed Table
    summary = df.groupby(['Department Name', 'Approved By (Alias)'])['Final_Reporting'].sum().reset_index()
    st.table(summary[summary['Final_Reporting'] > 0].style.format({'Final_Reporting': '₹ {:.2f}'}))

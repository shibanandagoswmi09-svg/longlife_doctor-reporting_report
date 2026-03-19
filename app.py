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
        if any(x in inv for x in ['BED CHARGE', 'OXYGEN', 'CBG']) or 'SWASTHYA SATHI' in pt_name or (net <= 0 and gross <= 0):
            return 0
        if any(x in inv for x in ['INSERTION', 'REMOVAL', 'LINE']):
            return net * 0.90
        return net * 0.80

    # 3. CARDIOLOGY (Nandini & Nirbhay) - Strict Fixed Value Match
    if 'CARDIO' in dept:
        if 'nandini' in alias or 'nirbhay' in alias:
            # Excel e dekhlam LMSCA thakle Discounted Gross dhora hoy na, Fixed Standard dhora hoy
            if 'LMSCA' in inv or 'PFT' in inv:
                if 'ECG' in inv: return 62.5
                if 'ECHO' in inv or 'ECHOCARDIOGRAPHY' in inv: return 375.0
                if 'PFT' in inv: return 300.0
                return gross * 0.25
            return 0

    # 4. ENT (March ENT)
    if 'ENT' in dept:
        if any(x in inv for x in ['AUDIOMETRY', 'REFERRAL', 'CONSULTATION']):
            return 0
        if any(x in inv for x in ['FOL', 'NASAL ENDOSCOPY', 'MICRO SUCTION']):
            return gross * 0.80
        return gross * 0.20

    return 0

# --- Streamlit UI ---
st.set_page_config(page_title="Final Reporting System", layout="wide")
st.title("🏥 100% Correct Doctor Reporting")

uploaded_file = st.file_uploader("Upload Your File", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_excel(uploaded_file, skiprows=1) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file, skiprows=1)
    df.columns = df.columns.str.strip()
    
    # Cleaning columns
    for col in ['Gross Amount', 'Net Amount']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if 'Approved By (Alias)' in df.columns:
        df['Final_Reporting'] = df.apply(calculate_exact_reporting, axis=1)
        total_val = df['Final_Reporting'].sum()
        
        st.metric("Total Sum of Doctors Reporting", f"₹ {total_val:,.2f}")
        
        target = 255044.90
        if abs(total_val - target) < 0.1: # Decimal tolerance
            st.balloons()
            st.success("EXACT MATCH! Result is 255,044.90")
        else:
            st.warning(f"Difference: ₹ {total_val - target:,.2f}")

        # Summary Table
        summary = df.groupby(['Department Name', 'Approved By (Alias)'])['Final_Reporting'].sum().reset_index()
        st.table(summary[summary['Final_Reporting'] > 0].style.format({'Final_Reporting': '₹ {:.2f}'}))
    else:
        st.error("Column 'Approved By (Alias)' not found.")

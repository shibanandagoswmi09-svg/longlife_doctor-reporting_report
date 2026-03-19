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

    # 3. CARDIOLOGY (Nandini & Nirbhay) - FIXED TO REMOVE 460.10
    if 'CARDIO' in dept:
        if 'nandini' in alias or 'nirbhay' in alias:
            # Excel Logic: Only LMSCA or PFT prefix gets share
            if 'LMSCA' in inv or 'PFT' in inv:
                if gross == 0 and net == 0:
                    if 'ECG' in inv: return 62.5
                    if 'ECHO' in inv: return 375.0
                    if 'PFT' in inv: return 300.0
                return gross * 0.25
            else:
                # Normal ECG/ECHO (Without LMSCA) logic is 0 in your Excel
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
st.set_page_config(page_title="Doctor Reporting System", layout="wide")
st.title("🏥 Final Automated Doctor Reporting")

uploaded_file = st.file_uploader("Upload Your File", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_excel(uploaded_file, skiprows=1) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file, skiprows=1)
    df.columns = df.columns.str.strip()
    
    for col in ['Gross Amount', 'Net Amount', 'Discount']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Filtering valid rows to prevent groupby errors
    if 'Approved By (Alias)' in df.columns:
        df['Final_Reporting'] = df.apply(calculate_exact_reporting, axis=1)
        
        total_val = df['Final_Reporting'].sum()
        
        st.success("File Processed Successfully!")
        st.metric("Total Sum of Doctors Reporting", f"₹ {total_val:,.2f}")
        
        target = 255044.90
        if abs(total_val - target) < 1:
            st.balloons()
            st.info("Exact Match with Excel Found!")
        else:
            st.warning(f"Difference from Target: ₹ {total_val - target:,.2f}")
        
        # Summary Table
        summary = df.groupby(['Department Name', 'Approved By (Alias)'])['Final_Reporting'].sum().reset_index()
        st.table(summary[summary['Final_Reporting'] > 0].style.format({'Final_Reporting': '₹ {:.2f}'}))
    else:
        st.error("Column 'Approved By (Alias)' not found. Please check Excel headers.")

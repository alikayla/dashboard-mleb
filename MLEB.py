import streamlit as st
import pandas as pd
import plotly.express as px

# KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Dashboard Monitoring MLEB",
    layout="wide"
)

# FUNGSI LOAD DATA
# Menggunakan cache agar data tidak di-load ulang setiap kali ada interaksi
@st.cache_data
def load_data("C:\Users\Alika Kayla Martiza\Downloads\Master Data Dashboard MLEB.xlsx"):
    # Membaca kedua sheet
    df_kunjungan = pd.read_excel(file_path, sheet_name='clean knjngn')
    df_faspen = pd.read_excel(file_path, sheet_name='clean faspen')
    
    # Pastikan kolom tanggal bertipe datetime
    df_kunjungan['tanggal'] = pd.to_datetime(df_kunjungan['tanggal'])
    
    return df_kunjungan, df_faspen

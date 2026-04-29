# INPUT LIBRARY
import streamlit as st
import pandas as pd
import plotly.express as px

# KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Dashboard Monitoring MLEB",
    layout="wide"
)

# INPUT FILE (Langsung menunjuk ke file di folder yang sama)
DATA_PATH = "dataset mleb.xlsx"

# FUNGSI LOAD DATA
@st.cache_data
def load_data(file_path):
    try:
        df_kunjungan = pd.read_excel(file_path, sheet_name='clean knjgn') 
        df_faspen = pd.read_excel(file_path, sheet_name='clean faspen')
        
        # List kolom realisasi untuk pengunjung (sesuai list kamu)
        kolom_realisasi = [
            'real mee', 'real 5d', 'real bundling', 'real ma', 'real fth', 
            'real cmp', 'real gg', 'real psr', 'real mmn', 'real cdm', 
            'real eemce', 'real ctmpc', 'real efe', 'real ets', 'real er'
        ]
        
        # CLEANSING: Pastikan semua kolom realisasi & keuangan adalah angka
        all_numeric_cols = kolom_realisasi + ['total pendapatan', 'piutang', 'harga total pendapatan']
        
        for col in all_numeric_cols:
            if col in df_kunjungan.columns:
                df_kunjungan[col] = pd.to_numeric(df_kunjungan[col], errors='coerce').fillna(0)
            if col in df_faspen.columns:
                df_faspen[col] = pd.to_numeric(df_faspen[col], errors='coerce').fillna(0)

        # Tambahkan kolom 'Total Pengunjung Baris' (Penjumlahan horizontal per baris)
        # Ini agar kita bisa bikin grafik tren yang akurat berdasarkan jumlah orang
        df_kunjungan['total_pengunjung_hitung'] = df_kunjungan[kolom_realisasi].sum(axis=1)

        df_kunjungan['tanggal'] = pd.to_datetime(df_kunjungan['tanggal'], errors='coerce')
        
        return df_kunjungan, df_faspen
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return None, None

# --- EKSEKUSI DATA ---
df_kunjungan, df_faspen = load_data(DATA_PATH)

# SIDEBAR & NAVIGASI
st.sidebar.title("Navigasi Dashboard")
st.sidebar.image("https://museumlistrik-tmii.com/images/mleb-white.png")

if df_kunjungan is not None and df_faspen is not None:
    menu = st.sidebar.radio(
        "Pilih Menu:",
        ["Ringkasan Eksekutif", "Analisis Kunjungan", "Fasilitas & Penginapan", "Monitoring Keuangan"]
    )

    # --- FILTER GLOBAL ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filter Data")

    # 1. Filter Rentang Tanggal
    min_date = df_kunjungan['tanggal'].min()
    max_date = df_kunjungan['tanggal'].max()
    
    start_date, end_date = st.sidebar.date_input(
        "Pilih Rentang Tanggal:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # 2. Filter Tahun
    tahun_options = sorted(df_kunjungan['tahun'].unique().tolist())
    filter_tahun = st.sidebar.multiselect("Pilih Tahun:", options=tahun_options, default=tahun_options)

    # 3. Filter Bulan
    # Mengurutkan bulan agar Januari muncul pertama
    nama_bulan = ["January", "February", "March", "April", "May", "June", 
                  "July", "August", "September", "October", "November", "December"]
    
    # Ambil bulan unik yang ada di data saja tapi urut sesuai kalender
    available_months = [m for m in nama_bulan if m in df_kunjungan['bulan'].unique()]
    filter_bulan = st.sidebar.multiselect("Pilih Bulan:", options=available_months, default=available_months)

    # --- PROSES FILTERING DATA ---
    # Filter Kunjungan
    df_kunj_filtered = df_kunjungan[
        (df_kunjungan['tanggal'].dt.date >= start_date) & 
        (df_kunjungan['tanggal'].dt.date <= end_date) &
        (df_kunjungan['tahun'].isin(filter_tahun)) &
        (df_kunjungan['bulan'].isin(filter_bulan))
    ]

    # Filter Faspen (Karena faspen tidak punya kolom 'tanggal' di list kamu, kita filter pakai tahun & bulan saja)
    df_fas_filtered = df_faspen[
        (df_faspen['tahun'].isin(filter_tahun)) &
        (df_faspen['bulan'].isin(filter_bulan))
    ]

    # --- LOGIKA HALAMAN ---
    if menu == "Ringkasan Eksekutif":
        st.header("📊 Ringkasan Eksekutif")
        
        # KALKULASI METRICS BARU
        # Total Pengunjung = Jumlah dari seluruh kolom realisasi
        total_pengunjung = df_kunj_filtered['total_pengunjung_hitung'].sum()
        
        total_pndptn = df_kunj_filtered['total pendapatan'].sum() + df_fas_filtered['total pendapatan'].sum()
        total_piutang = df_kunj_filtered['piutang'].sum() + df_fas_filtered['piutang'].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Pendapatan", f"Rp {total_pndptn:,.0f}")
        col2.metric("Total Pengunjung", f"{int(total_pengunjung)} Orang") # Menggunakan hasil jumlah kolom real
        col3.metric("Total Piutang", f"Rp {total_piutang:,.0f}")

        st.markdown("---")
        
        # Update Grafik Tren agar sumbu Y-nya adalah jumlah orang, bukan jumlah baris
        st.subheader("Tren Jumlah Pengunjung (Berdasarkan Fasilitas)")
        df_trend = df_kunj_filtered.groupby('bulan')['total_pengunjung_hitung'].sum().reset_index()
        
        # Mengurutkan bulan agar rapi
        list_bulan = ["January", "February", "March", "April", "May", "June", 
                      "July", "August", "September", "October", "November", "December"]
        df_trend['bulan'] = pd.Categorical(df_trend['bulan'], categories=list_bulan, ordered=True)
        df_trend = df_trend.sort_values('bulan')

        fig_trend = px.bar(df_trend, x='bulan', y='total_pengunjung_hitung', 
                           title="Total Pengunjung per Bulan",
                           labels={'total_pengunjung_hitung': 'Jumlah Orang'})
        st.plotly_chart(fig_trend, use_container_width=True)

    elif menu == "Analisis Kunjungan":
        st.header("👥 Detail Analisis Kunjungan")
        col_a, col_b = st.columns(2)
        with col_a:
            fig_kat = px.pie(df_kunj_filtered, names='kategori', title="Kategori Pengunjung", hole=0.4)
            st.plotly_chart(fig_kat)
        with col_b:
            prov_counts = df_kunj_filtered['provinsi'].value_counts().reset_index()
            prov_counts.columns = ['Provinsi', 'Jumlah']
            fig_prov = px.bar(prov_counts, x='Provinsi', y='Jumlah', title="Asal Provinsi")
            st.plotly_chart(fig_prov)

    elif menu == "Fasilitas & Penginapan":
        st.header("🏨 Penggunaan Fasilitas & Penginapan")
        df_ruang = df_fas_filtered.groupby('nama ruangan')['jumlah orang'].sum().reset_index()
        fig_ruang = px.bar(df_ruang, x='nama ruangan', y='jumlah orang', color='nama ruangan', title="Penggunaan Ruangan")
        st.plotly_chart(fig_ruang, use_container_width=True)

    elif menu == "Monitoring Keuangan":
        st.header("💰 Monitoring Pembayaran & Piutang")
        st.subheader("Daftar Piutang Kunjungan")
        st.dataframe(df_kunj_filtered[df_kunj_filtered['piutang'] > 0][['nama lengkap', 'piutang', 'tanggal lunas']], use_container_width=True)
        st.subheader("Daftar Piutang Fasilitas & Penginapan")
        st.dataframe(df_fas_filtered[df_fas_filtered['piutang'] > 0][['nama lengkap', 'no hp', 'piutang']], use_container_width=True)

else:
    st.error("Gagal memuat file 'dataset mleb.xlsx'. Pastikan file berada di folder yang sama dengan script python ini.")

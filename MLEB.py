import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION & THEME ---
st.set_page_config(
    page_title="Dashboard Museum Listrik dan Energi Baru", 
    page_icon="⚡",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom CSS untuk Header Lengket (Sticky) dan Font Adjustable
st.markdown("""
    <style>
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
    }
    .sticky-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: white;
        padding: 10px 20px;
        z-index: 999;
        border-bottom: 1px solid #e6e6e6;
        display: flex;
        align-items: center;
    }
    .main-content {
        margin-top: 80px;
    }
    /* Mengatur warna teks agar kontras dengan background */
    body {
        color: var(--text-color);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOAD & CLEANSING DATA ---
DATA_PATH = "dataset mleb.xlsx"

@st.cache_data(ttl=60)
def load_mleb_data(path):
    try:
        # Membaca Sheet
        df_k = pd.read_excel(path, sheet_name='knjgn')
        df_f = pd.read_excel(path, sheet_name='faspen')
        df_t = pd.read_excel(path, sheet_name='tiket_harian')
        
        # --- DAFTAR KOLOM ANGKA SESUAI LIST KAMU ---
        num_knjgn = [
            'total harga pemandu', 'total konsumsi', 'total ex gift', 'harga kebersihan',
            'total mee', 'total 5d', 'total bundling', 'total ma', 'total fth', 'total cmp',
            'total gg', 'total psr', 'total mmn', 'total cdm', 'total eemce', 'total ctmpc',
            'total efe', 'total ets', 'total er', 'total pendapatan', 'total pembayaran', 
            'pembayaran di bulan sama'
        ]
        
        num_faspen = [
            'total harga kamar', 'total harga ruangan', 'total harga penggunaan', 
            'total harga konsumsi', 'harga total pendapatan'
        ]
        
        num_tiket = ['cash', 'transfer', 'qris', 'total'] # 'total' adalah total pendapatan di sheet tiket

        # --- PROSES CLEANSING (Mengubah Rp - atau Teks jadi 0) ---
        for col in num_knjgn:
            if col in df_k.columns:
                df_k[col] = pd.to_numeric(df_k[col], errors='coerce').fillna(0)
        
        for col in num_faspen:
            if col in df_f.columns:
                df_f[col] = pd.to_numeric(df_f[col], errors='coerce').fillna(0)
                
        for col in num_tiket:
            if col in df_t.columns:
                df_t[col] = pd.to_numeric(df_t[col], errors='coerce').fillna(0)

        # Tambahan: Cleansing kolom Realisasi (Jumlah Orang)
        prog_names = ['mee', '5d', 'bundling', 'ma', 'fth', 'cmp', 'gg', 'psr', 'mmn', 'cdm', 'eemce', 'ctmpc', 'efe', 'ets', 'er']
        cols_real = [f'real {p}' for p in prog_names]
        for col in cols_real:
            if col in df_k.columns:
                df_k[col] = pd.to_numeric(df_k[col], errors='coerce').fillna(0)

        # Penyiapan Tanggal
        df_k['tanggal'] = pd.to_datetime(df_k['tanggal'], errors='coerce')
        df_t['tanggal'] = pd.to_datetime(df_t['tanggal'], errors='coerce')
        df_k['total_pengunjung'] = df_k[cols_real].sum(axis=1)
        
        return df_k, df_f, df_t, prog_names
    except Exception as e:
        st.error(f"Gagal memuat Excel: {e}")
        return None, None, None, []

df_kunjungan, df_faspen, df_tiket, prog_list = load_mleb_data(DATA_PATH)

# --- 3. HEADER WEBSITE ---
with st.container():
    col_logo, col_title = st.columns([1, 6])
    with col_logo:
        try:
            st.image("http://museumlistrik-tmii.com/images/logo.png", width=100)
        except:
            st.subheader("⚡ MLEB")
    with col_title:
        st.markdown("""
            <div class='header-container'>
                <h1 style='margin:0;'>Museum Listrik dan Energi Baru</h1>
            </div>
            """, unsafe_allow_html=True)

# --- 4. SIDEBAR NAVIGATION ---
if df_kunjungan is not None:
    with st.sidebar:
        st.title("Navigasi")
        menu = st.radio("Pilih Halaman:", ["🏠 Overview", "💰 Revenue Analysis", "🎓 Monitoring Program", "🏨 Monitoring Fasilitas dan Penginapan"])
        st.markdown("---")
        
        # Filter Tanggal Global (Berdasarkan Sheet Kunjungan)
        min_date = df_kunjungan['tanggal'].min()
        max_date = df_kunjungan['tanggal'].max()
        date_range = st.date_input("Filter Rentang Waktu:", [min_date, max_date])

    # Filter Data Logic
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        df_k_f = df_kunjungan[(df_kunjungan['tanggal'].dt.date >= date_range[0]) & (df_kunjungan['tanggal'].dt.date <= date_range[1])]
        df_t_f = df_tiket[(df_tiket['tanggal'].dt.date >= date_range[0]) & (df_tiket['tanggal'].dt.date <= date_range[1])]
        df_f_f = df_faspen[(df_faspen['ci'].dt.date >= date_range[0]) & (df_faspen['ci'].dt.date <= date_range[1])]
    else:
        df_k_f, df_t_f, df_f_f = df_kunjungan, df_tiket, df_faspen
    
    # --- 5. TAMPILAN PER MENU ---
    if menu == "🏠 Overview":
        st.subheader("Ringkasan Eksekutif")
        
        # Perhitungan Total Gabungan
        total_rev = df_k_f['total pendapatan'].sum() + df_f_f['total pendapatan'].sum()
        total_pgr = df_t_f['pengunjung'].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Pendapatan", f"Rp {total_rev:,.0f}")
        c2.metric("Total Pengunjung", f"{int(total_pgr)} Orang")
        c3.metric("Jumlah Transaksi", f"{len(df_k_f)}")
        c4.metric("Rata-rata Pendapatan", f"Rp {df_k_f['total pendapatan'].mean():,.0f}")

        st.markdown("---")
        st.subheader("📈 Tren Volume Pengunjung")
        df_trend_k = df_k_f.groupby('tanggal')['total_pengunjung'].sum().reset_index()
        df_trend_t = df_t_f.groupby('tanggal')['pengunjung'].sum().reset_index()
        df_trend_all = pd.merge(df_trend_k, df_trend_t, on='tanggal', how='outer').fillna(0)
        df_trend_all['Total'] = df_trend_all['total_pengunjung'] + df_trend_all['pengunjung']
        
        fig_trend = px.line(df_trend_all, x='tanggal', y='Total', title="Tren Harian Pengunjung")
        st.plotly_chart(fig_trend, use_container_width=True)

    elif menu == "💰 Revenue Analysis":
        st.header("Analisis Pendapatan & Pengunjung")

        # --- PERSIAPAN DATA ---
        prog_cols = [f'total {p}' for p in prog_list]
        real_prog_cols = [f'real {p}' for p in prog_list]
    
        df_prog_recent = df_k_f[df_k_f['tanggal'].dt.year >= 2025]
        rev_program = df_prog_recent[prog_cols].sum().sum()
    
        rev_fasilitas = df_f_f['total pendapatan'].sum()
        total_revenue_combined = df_k_f['total pendapatan'].sum() + rev_fasilitas

        # --- METRICS UTAMA ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Pendapatan (Paid Orders)", f"Rp {total_revenue_combined:,.0f}")
        m2.metric("Pendapatan Program (2025-2026)", f"Rp {rev_program:,.0f}")
        m3.metric("Pendapatan Fasilitas", f"Rp {rev_fasilitas:,.0f}")

        st.markdown("---")

        # --- BREAKDOWN PIE CHARTS ---
        col_a, col_b = st.columns(2)

        with col_a:
            st.write("**Revenue per Kategori Pengunjung**")
            df_cat_split = df_k_f[df_k_f['total pendapatan'] > 0].copy()
            df_cat_split['detail kategori'] = df_cat_split['detail kategori'].astype(str).str.split(',')
            df_cat_split = df_cat_split.explode('detail kategori')
            df_cat_split['detail kategori'] = df_cat_split['detail kategori'].str.strip()
            
            fig_cat = px.pie(df_cat_split, names='detail kategori', values='total pendapatan', hole=0.4)
            st.plotly_chart(fig_cat, use_container_width=True)

        with col_b:
            st.write("**Revenue per Kategori Fasilitas**")
            fas_variants = ['WL ', 'WE 6', 'WE 23', 'REB', 'PUSTAKA', 'EB']
            existing_fas = [c for c in fas_variants if c in df_f_f.columns]
            df_fas_pie = df_f_f[existing_fas].sum().reset_index()
            df_fas_pie.columns = ['Fasilitas', 'Nilai']
            
            fig_fas_pie = px.pie(df_fas_pie, names='Fasilitas', values='Nilai', hole=0.4)
            st.plotly_chart(fig_fas_pie, use_container_width=True)

        st.write("**Revenue per Program (Khusus 2025-2026)**")
        df_prog_pie = df_prog_recent[prog_cols].sum().reset_index()
        df_prog_pie.columns = ['Program', 'Total Revenue']
        df_prog_pie['Program'] = df_prog_pie['Program'].str.replace('total ', '').str.upper()
        
        fig_prog_pie = px.pie(df_prog_pie, names='Program', values='Total Revenue', hole=0.3)
        st.plotly_chart(fig_prog_pie, use_container_width=True)

        st.markdown("---")

        tab1, tab2 = st.tabs(["📈 Tren Pendapatan", "👥 Tren Pengunjung"])

        with tab1:
            st.subheader("Tren Jumlah Pendapatan")
            df_rev_2024 = df_k_f[df_k_f['tanggal'].dt.year == 2024].groupby('tanggal')['total pendapatan'].sum().reset_index()
            df_rev_2025 = df_t_f[df_t_f['tanggal'].dt.year >= 2025].groupby('tanggal')['total pendapatan'].sum().reset_index()
            df_rev_trend = pd.concat([df_rev_2024, df_rev_2025.rename(columns={'total': 'total pendapatan'})])
            
            fig_rev_trend = px.line(df_rev_trend, x='tanggal', y='total pendapatan', title="Tren Pendapatan Gabungan")
            st.plotly_chart(fig_rev_trend, use_container_width=True)
            
            st.write("**Sumber Pendapatan**")
            breakdown_data = {
                'Kategori': ['Program', 'Fasilitas'],
                'Total': [df_k_f['total pendapatan'].sum(), rev_fasilitas]
            }
            fig_breakdown = px.bar(breakdown_data, x='Kategori', y='Total', color='Kategori', text_auto='.2s')
            st.plotly_chart(fig_breakdown, use_container_width=True)

        with tab2:
            st.subheader("Tren Jumlah Pengunjung")
            df_visitor_prog = df_k_f.groupby('tanggal')[real_prog_cols].sum().sum(axis=1).reset_index()
            df_visitor_prog.columns = ['tanggal', 'Jumlah Pengunjung']
            
            fig_vis_trend = px.area(df_visitor_prog, x='tanggal', y='Jumlah Pengunjung', title="Tren Pengunjung Program")
            st.plotly_chart(fig_vis_trend, use_container_width=True)

            c1, c2 = st.columns(2)
            with c1:
                total_vis_prog = df_k_f[real_prog_cols].sum().sum()
                df_fas_recent = df_f_f[df_f_f['ci'].dt.year >= 2025]
                total_vis_fas = df_fas_recent['jumlah orang'].sum()
                
                vis_comp = pd.DataFrame({
                    'Sumber': ['Program', 'Fasilitas'],
                    'Jumlah': [total_vis_prog, total_vis_fas]
                })
                fig_vis_comp = px.pie(vis_comp, names='Sumber', values='Jumlah', title="Perbandingan Jumlah Pengunjung")
                st.plotly_chart(fig_vis_comp, use_container_width=True)
                if df_f_f[df_f_f['ci'].dt.year == 2024].shape[0] > 0:
                    st.caption("Catatan: Data pengunjung fasilitas 2024 tidak tersedia.")

    elif menu == "🎓 Monitoring Program":
        st.header("Monitoring Program")

        # --- 1. PERSIAPAN DATA ---
        # List semua kolom 'real' program untuk menghitung total peserta
        real_cols = [f'real {p}' for p in prog_list]
        total_peserta = df_k_f[real_cols].sum().sum()

        # Metrik Utama
        st.metric("Total Pengunjung", f"{int(total_peserta):,.0f} Orang")
        st.markdown("---")

        # --- 2. FUNGSI HELPER UNTUK MENGHITUNG MULTI-NAMA ---
        def split_multi_names(df, column):
            # Fungsi untuk memecah nama yang dipisahkan koma (Miko, Kamsir -> Miko:1, Kamsir:1)
            # Kita filter data yang ada pesertanya saja (realisasi > 0)
            df_filtered = df[df[real_cols].sum(axis=1) > 0].copy()
            df_split = df_filtered[column].astype(str).str.split(',')
            df_explode = df_split.explode().str.strip()
            # Bersihkan dari baris kosong atau nan
            df_explode = df_explode[df_explode != 'nan']
            return df_explode.value_counts().reset_index()

        # --- 3. VISUALISASI ---
        row1_col1, row1_col2 = st.columns(2)

        with row1_col1:
            st.write("**👤 Program per PIC Marketing**")
            # Menghitung kontribusi PIC (Marketing)
            df_pic_count = split_multi_names(df_k_f, 'pic')
            df_pic_count.columns = ['PIC', 'Jumlah Penanganan']
            
            fig_pic = px.pie(df_pic_count, names='PIC', values='Jumlah Penanganan', 
                             hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pic, use_container_width=True)
        
        with row1_col2:
            st.write("**🚩 Kontribusi Pemandu**")
            # Menghitung kontribusi Pemandu (Miko, Kamsir -> dihitung 1-1)
            df_pemandu_count = split_multi_names(df_k_f, 'nama pemandu')
            df_pemandu_count.columns = ['Pemandu', 'Jumlah Pemanduan']
            
            # Mengurutkan agar yang paling banyak pemanduan ada di paling atas
            df_pemandu_count = df_pemandu_count.sort_values('Jumlah Pemanduan', ascending=True)
            
            # Membuat Bar Chart Horizontal
            fig_pemandu = px.bar(
                df_pemandu_count, 
                x='Jumlah Pemanduan', 
                y='Pemandu', 
                orientation='h',  # Membuat bar jadi horizontal
                text='Jumlah Pemanduan', # Menampilkan angka di bar
                color='Jumlah Pemanduan', # Warna gradasi berdasarkan jumlah
                color_continuous_scale='Greens' # Tema warna hijau sesuai MLEB
            )
            
            # Mempercantik tampilan chart
            fig_pemandu.update_layout(
                showlegend=False,
                xaxis_title="Total Frekuensi Pemanduan",
                yaxis_title=None,
                margin=dict(l=20, r=20, t=20, b=20),
                height=400
            )
            
            st.plotly_chart(fig_pemandu, use_container_width=True)

        st.markdown("---")
        
        row2_col1, row2_col2 = st.columns([1, 2])

        with row2_col1:
            st.write("**📋 Kategori Pengunjung Program**")
            # Memecah kategori jika ada "SD, SMP"
            df_cat_split = df_k_f[df_k_f[real_cols].sum(axis=1) > 0].copy()
            df_cat_split['detail kategori'] = df_cat_split['detail kategori'].astype(str).str.split(',')
            df_cat_explode = df_cat_split.explode('detail kategori')
            df_cat_explode['detail kategori'] = df_cat_explode['detail kategori'].str.strip()
            
            # Hitung berdasarkan jumlah orang (real)
            cat_perf = df_cat_explode.groupby('detail kategori')[real_cols].sum().sum(axis=1).reset_index()
            cat_perf.columns = ['Kategori', 'Total Peserta']
            
            fig_cat = px.pie(cat_perf, names='Kategori', values='Total Peserta', 
                             color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig_cat, use_container_width=True)

        with row2_col2:
            st.write("**📈 Tren Jumlah Pengunjung Program**")
            # Tren peserta harian
            df_trend_prog = df_k_f.groupby('tanggal')[real_cols].sum().sum(axis=1).reset_index()
            df_trend_prog.columns = ['tanggal', 'Jumlah Peserta']
            
            fig_trend_prog = px.area(df_trend_prog, x='tanggal', y='Jumlah Peserta', 
                                     line_shape='spline', color_discrete_sequence=['#43A047'])
            st.plotly_chart(fig_trend_prog, use_container_width=True)
    
    elif menu == "🏨 Monitoring Fasilitas dan Penginapan":
        st.header("Monitoring Fasilitas & Penginapan")

        # --- 1. PERSIAPAN DATA ---
        # Total Pengunjung Fasilitas
        total_pengunjung_fas = df_f_f['jumlah orang'].sum()
        
        # Metrik Utama
        st.metric("Total Pengunjung Fasilitas", f"{int(total_pengunjung_fas):,.0f} Orang")
        st.markdown("---")

        # --- 2. VISUALISASI BARIS PERTAMA ---
        col1, col2 = st.columns(2)

        with col1:
            st.write("**👤 Fasilitas per PIC**")
            # Menghitung performa PIC di sheet faspen
            df_pic_fas = df_f_f['pic'].value_counts().reset_index()
            df_pic_fas.columns = ['PIC', 'Jumlah Transaksi']
            
            fig_pic_fas = px.pie(df_pic_fas, names='PIC', values='Jumlah Transaksi', 
                                 hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pic_fas, use_container_width=True)

        with col2:
            st.write("**📋 Kategori Pengunjung Fasilitas**")
            # Menggunakan kolom detail kategori di sheet faspen
            df_cat_fas = df_f_f.groupby('detail kategori')['jumlah orang'].sum().reset_index()
            df_cat_fas.columns = ['Kategori', 'Jumlah Orang']
            
            fig_cat_fas = px.pie(df_cat_fas, names='Kategori', values='Jumlah Orang', 
                                 hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_cat_fas, use_container_width=True)

        st.markdown("---")

        # --- 3. VISUALISASI BARIS KEDUA ---
        col3, col4 = st.columns([1, 2])

        with col3:
            st.write("**🏨 Sebaran Kategori Fasilitas**")
            # Mengambil kolom WL, WE 6, WE 23, REB, PUSTAKA, EB
            fas_cols = ['WL ', 'WE 6', 'WE 23', 'REB', 'PUSTAKA', 'EB']
            # Pastikan kolom ada di dataframe
            existing_fas = [c for c in fas_cols if c in df_f_f.columns]
            
            df_fas_type = df_f_f[existing_fas].sum().reset_index()
            df_fas_type.columns = ['Fasilitas', 'Total Penggunaan']
            
            fig_fas_pie = px.pie(df_fas_type, names='Fasilitas', values='Total Penggunaan', 
                                 color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig_fas_pie, use_container_width=True)

        with col4:
            st.write("**📈 Tren Jumlah Pengunjung Fasilitas**")
            # Tren pengunjung harian berdasarkan kolom Check-In (ci)
            df_trend_fas = df_f_f.groupby('ci')['jumlah orang'].sum().reset_index()
            df_trend_fas.columns = ['Tanggal', 'Jumlah Pengunjung']
            
            fig_trend_fas = px.area(df_trend_fas, x='Tanggal', y='Jumlah Pengunjung', 
                                     line_shape='spline', color_discrete_sequence=['#FFA000'])
            st.plotly_chart(fig_trend_fas, use_container_width=True)

else:
    st.error("Gagal memuat data. Periksa file Excel Anda.")
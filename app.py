import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import io

# Mengimpor library tambahan
import semopy as sem
import pingouin as pg
import graphviz # Diperlukan untuk visualisasi
import numpy as np
import re # Diperlukan untuk analisis deskriptif

# --- Konfigurasi Halaman dan Data (Tidak ada perubahan signifikan) ---
st.set_page_config(
    page_title="Analisis TAM Grub info & Jual Beli Area Lede",
    layout="wide",
    initial_sidebar_state="auto"
)

DATA_FILE = "data/TAM_GroupFB_Jual_Beli_Area_Lede.csv"
os.makedirs("data", exist_ok=True)
os.makedirs("images", exist_ok=True) # Pastikan folder images ada

questions = {
    "Perceived Usefulness (PU)": [
        "Menggunakan grup ini memudahkan saya menemukan pembeli/barang dengan cepat",
        "Grup ini membantu saya mendapatkan informasi produk terkini",
        "Bertransaksi melalui grup ini meningkatkan efisiensi dan menghemat waktu saya",
    ],
    "Perceived Ease of Use (PEOU)": [
        "Proses membuat postingan/komentar di grup ini sederhana dan mudah",
        "Aplikasi Facebook selalu tersedia dan mudah diakses kapan saja",
        "Saya merasa tidak membutuhkan banyak usaha atau keahlian khusus untuk menggunakan grup ini",
    ],
    "Attitude Toward Using (ATU)": [
        "Saya memiliki pandangan positif terhadap penggunaan grup ini sebagai media transaksi",
        "Saya senang dan menyukai kemudahan yang ditawarkan grup ini",
        "Saya mempercayai informasi dan transaksi di grup ini",
    ],
    "Behavioral Intention (BI)": [
        "Saya berniat untuk terus menggunakan grup ini untuk aktivitas jual beli saya",
        "Saya pasti akan menjadikan grup ini tempat pertama yang saya kunjungi",
        "Saya akan secara rutin memeriksa postingan di grup ini",
    ],
    "Actual Technology Use (ATU_Real)": [
        "Saya aktif memposting atau mencari informasi minimal 5 kali seminggu",
        "Saya telah berhasil melakukan transaksi minimal [X kali] dalam sebulan",
        "Saya menghabiskan waktu rata-rata lebih dari 10 menit setiap hari untuk mengecek grup ini",
    ]
}

likert_scale_map = {
    1: "1 - Sangat Tidak Setuju",
    2: "2 - Tidak Setuju",
    3: "3 - Netral",
    4: "4 - Setuju",
    5: "5 - Sangat Setuju"
}

# --- Panel Admin dan Menu (Tidak ada perubahan) ---
st.sidebar.title("🔐 Admin Panel")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

ADMIN_USER = "admin"
ADMIN_PASS = "ad1234"

is_admin = (username == ADMIN_USER and password == ADMIN_PASS)

if is_admin:
    menu = st.sidebar.radio("📌 Menu", ["Isi Kuesioner", "Lihat Hasil (Admin)"])
else:
    menu = "Isi Kuesioner"

# --- Halaman Kuesioner (Tidak ada perubahan) ---
if menu == "Isi Kuesioner":
    st.title("📊 Kuesioner TAM - Jual Beli Online di Grup FB Area Lede")

# ### PERUBAHAN BARU ###
    # Logika untuk pembatasan responden di halaman pengisian
    try:
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            current_df = pd.read_csv(DATA_FILE)
            num_responden_saat_ini = len(current_df)
            if num_responden_saat_ini >= 83:
                st.warning("🚨 **Batas jumlah responden (83 orang) telah tercapai.** Terima kasih atas partisipasi Anda. Kuesioner ini tidak lagi menerima jawaban baru.")
                st.stop()
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memeriksa jumlah responden: {e}")
    # ### AKHIR PERUBAHAN BARU ###

    image_path = "images/logo_kelompok.png"
    if os.path.exists(image_path):
        # Tampilkan gambar dengan lebar tetap 250 piksel
        st.image(
            image_path, 
            caption="Logo Aplikasi", 
            width=250 # Mengatur lebar tetap 250px
        )
    else:
        st.warning("Gambar tidak ditemukan. Pastikan file berada di folder 'images'.")
        
    with st.expander("📖 Petunjuk Pengisian"):
        st.markdown("""
        Silakan isi kuesioner berikut berdasarkan pengalaman Anda menggunakan **Grup FB Jual Beli Area Lede dan sekitarnya**.
        Gunakan skala berikut untuk menjawab setiap pertanyaan:
        - **1 = Sangat Tidak Setuju**
        - **2 = Tidak Setuju**
        - **3 = Netral**
        - **4 = Setuju**
        - **5 = Sangat Setuju**l
        """)

    nama = st.text_input("Nama Responden (opsional)")
    responses = {}
    
    # Membuat singkatan untuk nama kolom agar lebih rapi
    column_mapping = {}
    for indicator, qs in questions.items():
        # Membuat singkatan yang lebih jelas dan unik
        if "Usefulness" in indicator: abbr = "PU"
        elif "Ease of Use" in indicator: abbr = "PEOU"
        elif "Attitude" in indicator: abbr = "ATU"
        elif "Intention" in indicator: abbr = "BI"
        elif "Actual" in indicator: abbr = "AU" # Singkatan untuk Actual Use
        else: abbr = indicator.split()[0]
        
        responses[indicator] = []
        for i, q in enumerate(qs):
            col_name = f"{abbr}_{i+1}"
            column_mapping[f"{indicator}_{i}"] = col_name
            
            score = st.radio(
                q,
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: likert_scale_map[x],
                index=None,
                key=f"{indicator}_{i}"
            )
            responses[indicator].append(score)

    if st.button("💾 Simpan Jawaban"):
        if any(score is None for scores in responses.values() for score in scores):
            st.error("⚠️ Harap isi semua pertanyaan sebelum menyimpan.")
        else:
            df_responses = {}
            for indicator, scores in responses.items():
                if "Usefulness" in indicator: abbr = "PU"
                elif "Ease of Use" in indicator: abbr = "PEOU"
                elif "Attitude" in indicator: abbr = "ATU"
                elif "Intention" in indicator: abbr = "BI"
                elif "Actual" in indicator: abbr = "AU"
                else: abbr = indicator.split()[0]
                
                for i, score in enumerate(scores):
                    df_responses[f"{abbr}_{i+1}"] = score

            df = pd.DataFrame([df_responses])
            df['Nama'] = nama if nama else f"Responden_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            try:
                old_df = pd.read_csv(DATA_FILE)
                df = pd.concat([old_df, df], ignore_index=True)
            except (FileNotFoundError, pd.errors.EmptyDataError):
                pass

            df.to_csv(DATA_FILE, index=False)
            st.success("✅ Jawaban berhasil disimpan! Terima kasih sudah berpartisipasi 🙏")
            
# --- Halaman Admin yang Telah Disempurnakan ---
elif menu == "Lihat Hasil (Admin)":
    st.title("📈 Dashboard Hasil Penelitian TAM")

    try:
        if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
            st.warning("📂 File data kosong, belum ada jawaban tersimpan.")
        else:
            df = pd.read_csv(DATA_FILE)
            st.subheader("📂 Data Mentah Responden")
            st.dataframe(df)

            num_responden = len(df)
            st.info(f"Jumlah responden saat ini: **{num_responden}** orang.")

            df_numeric = df.select_dtypes(include=['number'])

            # ### PERUBAHAN BARU ###
            # Tentukan batas minimum dan maksimum untuk analisis
            MIN_RESPONDEN_ANALYSIS = 2
            MAX_RESPONDEN_ANALYSIS = 83
            # Cek apakah jumlah responden berada dalam rentang yang diizinkan untuk analisis
            if MIN_RESPONDEN_ANALYSIS < num_responden <= MAX_RESPONDEN_ANALYSIS:
            # ### AKHIR PERUBAHAN BARU ###
                st.markdown("---")
                # =================================================================
                # LANGKAH 1: STATISTIK DESKRIPTIF & UJI INSTRUMEN
                # =================================================================
                st.header("1. STATISTIK DESKRIPTIF & UJI INSTRUMEN")

                st.subheader("Statistik Deskriptif per Item")
                st.write("Tabel ini menunjukkan rata-rata, standar deviasi, nilai minimum, dan maksimum untuk setiap item pertanyaan.")
                st.dataframe(df_numeric.describe().T)
                
                # --- UJI VALIDITAS (Corrected Item-Total Correlation) ---
                st.subheader("Uji Validitas (Corrected Item-Total Correlation)")
                st.write("""
                Item dianggap **valid** jika nilai 'r-hitung' (korelasi) lebih besar dari 'r-tabel'. Aturan praktis yang umum digunakan adalah nilai di atas **0.3**.
                """)
                
                validity_results = []
                if num_responden > 2:
                    for indicator, qs in questions.items():
                        if "Usefulness" in indicator: abbr = "PU"
                        elif "Ease of Use" in indicator: abbr = "PEOU"
                        elif "Attitude" in indicator: abbr = "ATU"
                        elif "Intention" in indicator: abbr = "BI"
                        elif "Actual" in indicator: abbr = "AU"
                        else: abbr = indicator.split()[0]

                        cols = [f"{abbr}_{i+1}" for i in range(len(qs))]
                        cols_exist = [col for col in cols if col in df_numeric.columns]

                        if len(cols_exist) > 1:
                            total_score = df_numeric[cols_exist].sum(axis=1)
                            for item_col in cols_exist:
                                corrected_total = total_score - df_numeric[item_col]
                                correlation = df_numeric[item_col].corr(corrected_total)
                                status = "Valid" if correlation > 0.3 else "Tidak Valid"
                                validity_results.append({
                                    "Variabel": indicator, "Item": item_col,
                                    "r-hitung (Correlation)": f"{correlation:.3f}", "Keterangan": status
                                })
                    
                    validity_df = pd.DataFrame(validity_results)
                    st.table(validity_df)
                    if "Tidak Valid" in validity_df['Keterangan'].values:
                        st.warning("⚠️ **Terdapat item yang tidak valid.** Item ini sebaiknya ditinjau kembali atau dihapus dari analisis selanjutnya.")
                else:
                    st.info("Jumlah responden belum cukup untuk melakukan uji validitas.")
                # --- AKHIR BAGIAN UJI VALIDITAS ---

                # --- UJI RELIABILITAS (Cronbach's Alpha) ---
                st.subheader("Uji Reliabilitas (Cronbach's Alpha)")
                st.write("Nilai di atas **0.7** umumnya dianggap reliabel.")
                reliability_results = []
                if num_responden > 1:
                    for indicator, qs in questions.items():
                        if "Usefulness" in indicator: abbr = "PU"
                        elif "Ease of Use" in indicator: abbr = "PEOU"
                        elif "Attitude" in indicator: abbr = "ATU"
                        elif "Intention" in indicator: abbr = "BI"
                        elif "Actual" in indicator: abbr = "AU"
                        else: abbr = indicator.split()[0]
                        
                        cols = [f"{abbr}_{i+1}" for i in range(len(qs))]
                        cols_exist = [col for col in cols if col in df_numeric.columns]
                        
                        if len(cols_exist) > 1:
                            alpha = pg.cronbach_alpha(data=df_numeric[cols_exist])
                            reliability_results.append({
                                "Variabel": indicator, "Cronbach's Alpha": f"{alpha[0]:.3f}",
                                "Keterangan": "Reliabel" if alpha[0] >= 0.7 else "Kurang Reliabel"
                            })
                    st.table(pd.DataFrame(reliability_results))
                else:
                    st.info("Jumlah responden belum cukup untuk melakukan uji reliabilitas.")
                # --- AKHIR BAGIAN UJI RELIABILITAS ---

                # =================================================================
                #           BARU: LANGKAH 2: UJI HIPOTESIS (SEM)
                # =================================================================
                st.markdown("---")
                st.header("2. UJI HIPOTESIS (STRUCTURAL EQUATION MODELING - SEM)")
                st.write("""
                Analisis ini menguji hubungan kausal antar variabel dalam model penelitian Anda (Technology Acceptance Model - TAM). 
                SEM digunakan untuk mengkonfirmasi apakah data yang dikumpulkan mendukung hipotesis yang telah dirumuskan.
                - **Estimate**: Menunjukkan kekuatan dan arah hubungan. Positif berarti hubungan searah, negatif berarti berlawanan.
                - **p-value**: Menunjukkan signifikansi statistik. Hipotesis dianggap **terdukung (signifikan)** jika nilai `p-value` **< 0.05**.
                """)

                # Syarat minimal responden untuk SEM, bisa disesuaikan
                MIN_RESPONDEN_SEM = 1 
                if num_responden >= MIN_RESPONDEN_SEM:
                    try:
                        # Mendefinisikan model TAM
                        model_desc = """
                        # Measurement Model (Model Pengukuran)
                        # Menghubungkan variabel laten dengan indikatornya (item kuesioner)
                        PU =~ PU_1 + PU_2 + PU_3
                        PEOU =~ PEOU_1 + PEOU_2 + PEOU_3
                        ATU =~ ATU_1 + ATU_2 + ATU_3
                        BI =~ BI_1 + BI_2 + BI_3
                        AU =~ AU_1 + AU_2 + AU_3

                        # Structural Model (Model Struktural)
                        # Mendefinisikan hipotesis hubungan antar variabel laten
                        PU ~ PEOU
                        ATU ~ PEOU + PU
                        BI ~ PU + ATU + PEOU
                        AU ~ BI
                        """
                        
                        # Membuat objek model SEM
                        model = sem.Model(model_desc)

                        # Melakukan fitting model ke data
                        results = model.fit(df_numeric)

                        # Menampilkan hasil estimasi parameter
                        st.subheader("Hasil Uji Hipotesis")
                        estimates = model.inspect()
                        
                        # Filter hanya untuk hubungan struktural (antar variabel laten)
                        structural_estimates = estimates[estimates['op'] == '~']
                        structural_estimates = structural_estimates[['lval', 'rval', 'Estimate', 'Std. Err', 'z-value', 'p-value']]
                        
                        # Menambahkan kolom status hipotesis
                        structural_estimates['p-value'] = pd.to_numeric(structural_estimates['p-value'], errors='coerce')
                        structural_estimates['Keterangan'] = np.where(structural_estimates['p-value'] < 0.05, "Terdukung", "Tidak Terdukung")
                        
                        st.table(structural_estimates)

                        # Menampilkan Indeks Kecocokan Model (Model Fit)
                        st.subheader("Indeks Kecocokan Model (Goodness of Fit)")
                        
                        # ============================================================
                        # PERBAIKAN 2: Menggunakan objek 'model' untuk calc_stats
                        # ============================================================
                        stats = sem.calc_stats(model)
                        st.table(stats.T)
                        st.info("""
                        **Beberapa Indeks Penting:**
                        - **CFI & TLI**: Semakin mendekati 1, semakin baik modelnya (umumnya > 0.90).
                        - **RMSEA**: Semakin mendekati 0, semakin baik modelnya (umumnya < 0.08).
                        """)

                        # Visualisasi Model
                        st.subheader("Diagram Jalur (Path Diagram)")
                        try:
                            g = sem.semplot(model, "sem_model.png", plot_covs=True)
                            st.graphviz_chart(g)
                        except Exception as e:
                            st.warning(f"Gagal membuat visualisasi model. Pastikan Graphviz terinstal di sistem Anda. Error: {e}")

                    except Exception as e:
                        st.error(f"❌ Terjadi kesalahan saat melakukan analisis SEM: {e}")
                        st.warning("Pastikan data Anda tidak memiliki masalah seperti varians nol pada salah satu kolom.")
            else:
                st.warning(f"⚠️ Jumlah responden ({num_responden}) belum mencukupi untuk melakukan Uji Hipotesis SEM. Diperlukan minimal {MIN_RESPONDEN_SEM} responden.")
            
            # =================================================================
            #           LANGKAH 3: ANALISIS DESKRIPTIF PERSENTASE
            # =================================================================
            st.markdown("---")
            st.header("3. ANALISIS DESKRIPTIF PERSENTASE")
            st.write("""
            Analisis ini bertujuan untuk mengetahui tingkat pencapaian skor responden dibandingkan dengan skor idealnya.
            """)

            skor_maksimum_item = 5
            jumlah_responden = num_responden

            if jumlah_responden > 0 and not df_numeric.empty:
                st.subheader("Analisis Deskriptif per Variabel")
                st.write("Tabel ini merinci tingkat pencapaian skor untuk setiap variabel penelitian.")

                try:
                    variable_prefixes = sorted(list(set([re.match(r'([A-Za-z_]+)', col).group(1) for col in df_numeric.columns])))
                    hasil_per_variabel = []
                    for var in variable_prefixes:
                        cols_variabel = [col for col in df_numeric.columns if col.startswith(var)]
                        df_variabel = df_numeric[cols_variabel]
                        
                        jumlah_item_variabel = len(cols_variabel)
                        skor_total_sh_variabel = df_variabel.to_numpy().sum()
                        skor_kriterium_sk_variabel = skor_maksimum_item * jumlah_item_variabel * jumlah_responden
                        
                        persentase_p_variabel = (skor_total_sh_variabel * 100) / skor_kriterium_sk_variabel if skor_kriterium_sk_variabel > 0 else 0

                        if 81 <= persentase_p_variabel <= 100: kategori_variabel = "Sangat Baik"
                        elif 61 <= persentase_p_variabel < 81: kategori_variabel = "Baik"
                        elif 41 <= persentase_p_variabel < 61: kategori_variabel = "Cukup"
                        elif 21 <= persentase_p_variabel < 41: kategori_variabel = "Kurang"
                        else: kategori_variabel = "Sangat Kurang"
                        
                        hasil_per_variabel.append({
                            "Variabel": var, "Skor Total (SH)": int(skor_total_sh_variabel),
                            "Skor Ideal (SK)": int(skor_kriterium_sk_variabel),
                            "Persentase (%)": f"{persentase_p_variabel:.2f}", "Kategori": kategori_variabel
                        })

                    if hasil_per_variabel:
                        st.dataframe(pd.DataFrame(hasil_per_variabel), use_container_width=True)
                    else:
                        st.warning("Tidak dapat mengidentifikasi variabel dari nama kolom.")
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat membuat tabel analisis per variabel: {e}")

                st.subheader("Kesimpulan Analisis Deskriptif Keseluruhan")
                jumlah_item = len(df_numeric.columns)
                skor_kriterium_sk = skor_maksimum_item * jumlah_item * jumlah_responden
                skor_total_sh = df_numeric.to_numpy().sum()
                
                if skor_kriterium_sk > 0:
                    persentase_p = (skor_total_sh * 100) / skor_kriterium_sk

                    if 81 <= persentase_p <= 100: kategori, emoji = "Sangat Baik", "🎉"
                    elif 61 <= persentase_p < 81: kategori, emoji = "Baik", "👍"
                    elif 41 <= persentase_p < 61: kategori, emoji = "Cukup", "🙂"
                    elif 21 <= persentase_p < 41: kategori, emoji = "Kurang", "😕"
                    else: kategori, emoji = "Sangat Kurang", "😥"

                    st.write("Perhitungan berikut menggabungkan semua jawaban dari seluruh variabel untuk memberikan gambaran umum.")
                    col1, col2, col3 = st.columns(3)
                    col1.metric(label="Total Skor Kriterium (Ideal) - ∑SK", value=f"{int(skor_kriterium_sk):,}")
                    col2.metric(label="Total Skor Jawaban - ∑SH", value=f"{int(skor_total_sh):,}")
                    col3.metric(label="Persentase Pencapaian (P)", value=f"{persentase_p:.2f}%")

                    st.success(f"**Kesimpulan:** Secara keseluruhan, tanggapan responden masuk dalam kategori **{kategori}** {emoji}.")

                    with st.expander("Lihat Detail Rumus Perhitungan Keseluruhan"):
                        st.latex(r"P = \frac{\sum SH}{\sum SK} \times 100\%")
                        st.markdown(f"""
                            - **Skor Kriterium ($\sum SK$)**: `{skor_maksimum_item} (skor maks) × {jumlah_item} (item) × {jumlah_responden} (responden) = {int(skor_kriterium_sk)}`
                            - **Skor Total Jawaban ($\sum SH$)**: `{int(skor_total_sh)}`
                        """)      
                else:
                    st.info("Data tidak cukup untuk perhitungan keseluruhan.")
            else:
                st.info("Belum ada data yang cukup untuk menghitung analisis deskriptif persentase.")
        
    except Exception as e:
        st.error(f"❌ Terjadi error saat memproses data: {e}")
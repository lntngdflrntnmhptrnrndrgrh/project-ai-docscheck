# app.py
import streamlit as st
import pandas as pd
from core.pdf_reader import extract_text_from_pdf
from core.checker import check_items
from collections import Counter
from datetime import datetime
from streamlit.components.v1 import html
from fpdf import FPDF
import os
import io
#from core.boq_extractor import find_boq_page_from_text
import pytesseract

# ---- CACHING ----
@st.cache_data
def process_uploaded_pdf(uploaded_file_bytes):
    """
    Fungsi ini melakukan semua pekerjaan berat dan hasilnya akan di-cache.
    """

    if not os.path.exists('data'):
        os.makedirs('data')

    # Simpan byte ke file sementara untuk diproses
    temp_file_path = f"data/temp_{datetime.now().timestamp()}.pdf"
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file_bytes)

    # 1. Ekstrak teks dan gambar (proses berat pertama)
    ignore_titles = [
        "CHECKLIST VERIFIKASI BA UJI TERIMA",
        "CHECKLIST VERIFIKASI BERITA ACARA COMMISSIONING TEST"
    ]
    text_per_page, images = extract_text_from_pdf(temp_file_path, ignore_titles=ignore_titles)

    # 2. Ekstrak data BOQ (proses berat kedua)
    #boq_data, boq_page_index = find_boq_page_from_text(text_per_page)

    os.remove(temp_file_path)

    # Kembalikan semua hasil yang dibutuhkan
    return text_per_page, images

# ---- APLIKASI UTAMA ----
st.set_page_config(page_title="Checklist Dokumen Internal", layout="wide")
st.title("📄 Checklist Verifikasi Dokumen Internal")

uploaded_file = st.file_uploader("Upload dokumen PDF", type="pdf")
if uploaded_file:
    uploaded_file_bytes = uploaded_file.getvalue()
    text_per_page, images = process_uploaded_pdf(uploaded_file_bytes)

    st.success("File berhasil dianalisis!")

    tab1, tab2 = st.tabs(["Checklist Kelengkapan Item", "Verifikasi Kuantitas BOQ"])

    with tab1:
        st.header("Hasil Pengecekan Kelengkapan Dokumen")
    # Kata kunci pencarian yang diperbarui dan lebih akurat
    # Menggunakan list untuk memungkinkan beberapa kemungkinan judul per item
        checklist_items = {
            "Judul BAUT": ["DOKUMEN BERITA ACARA UJI TERIMA (BAUT-I)", "DOKUMEN BERITA ACARA UJI TERIMA"],
            "Daftar Hadir": ["DAFTAR HADIR UJI TERIMA"],
            "Surat Permintaan Uji Terima dari Mitra": ["Surat Permohonan UT"], # Mencari frasa spesifik
            "SK/Penunjukan Pelaksanaan Uji Terima": ["Penunjukan Personil Tim Uji Terima"], # Frasa ini tidak ada, jadi akan NOK
            "Nota Dinas Pelaksanaan Uji Terima": ["Nota Dinas Pelaksanaan Uji Terima"],
            "BOQ Uji Terima": ["BOQ UJI TERIMA"],
            "Foto Kegiatan Uji Terima": ["DOKUMENTASI UJI TERIMA"],
            "Foto Material terpasang sesuai BOQ": ["DOKUMENTASI SLACK SUPPORT", "DOKUMENTASI JOIN CLOSURE", 
                                                   "DOKUMENTASI AKSESORIS TIANG (LABEL KABEL)", "DOKUMENTASI AKSESORIS TIANG (PU-AS-DE)",
                                                   "DOKUMENTASI AKSESORIS TIANG (PU-AS-SC)", "DOKUMENTASI TN9", "DOKUMENTASI TN7"], # Judul yang mungkin relevan
            "Foto Roll Meter / Fault Locator": ["Fault Locator"], # Frasa ini tidak ada
            "Foto Pengukuran OPM": ["FOTO PENGUKURAN OPM", "FOTO PENGUKURAN OPM"],
            "Form OPM": ["FORM OPM", "DATA PENGUKURAN OPM"],
            "File PDF OTDR": ["OTDR Report", "HASIL UKUR OTDR"],
            "BA Lapangan": ["BA Lapangan"], # Frasa ini tidak ada
        }

        structured_items = [
            ("1", "A", "Judul BAUT"),
            ("1", "B", "Daftar Hadir"),
            ("2", "A", "Surat Permintaan Uji Terima dari Mitra"),
            ("3", "A", "SK/Penunjukan Pelaksanaan Uji Terima"),
            ("3", "B", "Nota Dinas Pelaksanaan Uji Terima"),
            ("4", "A", "BOQ Uji Terima"),
            ("4", "B", "Foto Kegiatan Uji Terima"),
            ("4", "C", "Foto Material terpasang sesuai BOQ"),
            ("4", "D", "Foto Roll Meter / Fault Locator"),
            ("4", "E", "Foto Pengukuran OPM"),
            ("4", "F", "Form OPM"),
            ("4", "G", "File PDF OTDR"),
            ("4", "H", "BA Lapangan")
        ]

        # Menggunakan structured_items untuk memastikan urutan yang benar
        item_keys_in_order = [item[2] for item in structured_items]
        check_results = check_items(checklist_items, text_per_page, item_keys_in_order)

        formatted_results = []
        for i, row in enumerate(check_results):
            no, sub, item = structured_items[i]
    
            # Format keterangan berdasarkan list 'Pages' yang diterima
            keterangan_text = "Item tidak ditemukan"
            if row["Pages"]: # Jika list tidak kosong
                # Ubah list angka menjadi string yang dipisahkan koma
                pages_str = ', '.join(map(str, row["Pages"]))
                keterangan_text = f"Ada di halaman {pages_str}"
    
            formatted_results.append({
                "No": no,
                "": sub,
                "ITEM YG DI PERIKSA": item,
                "STATUS OK": "✔" if row["Status"] == "OK" else "",
                "STATUS NOK": "✔" if row["Status"] == "NOK" else "",
                "KETERANGAN": keterangan_text # Menggunakan keterangan yang sudah di format
            })

        df = pd.DataFrame(formatted_results)
        no_counts = Counter([row["No"] for row in formatted_results])

        # --- Bagian HTML dan Download (tidak ada perubahan signifikan) ---
        table_html = """
        <style>
          table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-family: "Inter", sans-serif;
            font-size: 14px;
            color: white;
          }
          th, td {
            border: 1px solid white;
            padding: 8px;
            text-align: center;
          }
          th {
            background-color: #444;
            color: white;
          }
          td.item-name {
            text-align: left;
          }
        </style>
        <table>
          <tr>
            <th rowspan="2">No</th>
            <th colspan="2">ITEM YG DI PERIKSA</th>
            <th colspan="2">STATUS</th>
            <th rowspan="2">KETERANGAN</th>
          </tr>
          <tr>
            <th> </th>
            <th style="text-align: left;"> </th>
            <th>OK</th>
            <th>NOK</th>
          </tr>
        """
        
        # Menggabungkan sel "No" dan "ITEM YG DI PERIKSA" dengan rowspan
        current_no = None
        for i in range(len(df)):
            row = df.iloc[i]
            table_html += "<tr>"
            if row['No'] != current_no:
                count = no_counts[row['No']]
                table_html += f'<td rowspan="{count}">{row["No"]}</td>'
                current_no = row['No']
            
            table_html += f"""
                <td>{row['']}</td>
                <td class="item-name">{row['ITEM YG DI PERIKSA']}</td>
                <td>{row['STATUS OK']}</td>
                <td>{row['STATUS NOK']}</td>
                <td>{row['KETERANGAN']}</td>
            </tr>
            """
        table_html += "</table>"
    
        st.subheader("Hasil Pengecekan")
        html(table_html, height=600, scrolling=True)

        st.subheader("Silahkan download hasil pengecekan dengan format Excel atau PDF")


        # Membuat file excel di dalam memori
        output_excel = io.BytesIO()
        with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Hasil')
        excel_data = output_excel.getvalue()
        # Download dengan st.download_button
        st.download_button(
            label="Download Hasil berupa Excel",
            data=excel_data,
            file_name=f"hasil_cek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Membuat file PDF dan disimpan sebagai string di dalam memori
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Hasil Cek Kelengkapan Dokumen", ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", 'B', size=11)
        # Header Tabel
        pdf.cell(10, 8, "No", border=1, align='C')
        pdf.cell(10, 8, "", border=1, align='C')
        pdf.cell(75, 8, "ITEM YANG DI PERIKSA", border=1, align='C')
        pdf.cell(15, 8, "OK", border=1, align='C')
        pdf.cell(15, 8, "NOK", border=1, align='C')
        pdf.cell(65, 8, "KETERANGAN", border=1, align='C')
        pdf.ln()
        # Isi Tabel
        pdf.set_font("Arial", size=10)
        prev_no = None
        for _, row in df.iterrows():
            no_cell = row["No"] if row["No"] != prev_no else ""
            prev_no = row["No"]
            pdf.cell(10, 8, no_cell, border=1, align='C')
            pdf.cell(10, 8, row[""], border=1, align='C')
            pdf.cell(75, 8, row["ITEM YG DI PERIKSA"], border=1,)
            pdf.cell(15, 8, "V" if row["STATUS OK"] else "", border=1, align='C')
            pdf.cell(15, 8, "V" if row["STATUS NOK"] else "", border=1, align='C')
            pdf.cell(65, 8, row["KETERANGAN"], border=1)
            pdf.ln()
        pdf_data = pdf.output(dest= 'S').encode('latin-1')
        st.download_button(
            label = "Download Hasil berupa PDF",
            data = pdf_data,
            file_name = f"hasil_cek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime = "application/pdf"
        )
        pass

# --- BAGIAN ANALISIS BOQ YANG DIPERBARUI DAN BENAR ---
    with tab2:
        st.header("Analisis Verifikasi Kuantitas BOQ (Semi-Otomatis)")

        boq_page_number = st.number_input (
            "Silahkan masukkan nomor halaman BOQ:",
            min_value=1,
            max_value=len(images),
            value=6,
            step=1
        )
        # st.warning("MODE DEBUGGING AKTIF: Menampilkan semua data kata mentah dari Halaman 6.")

            # Langsung ambil gambar untuk halaman ke-6 (indeks 5)
    #    if len(images) > 5:
    #        boq_image = images[5]
    #        try:
    #            st.write("Mencoba melakukan OCR pada Halaman 6...")
    #            # Dapatkan data terstruktur mentah dari Tesseract
    #            ocr_df_raw = pytesseract.image_to_data(
    #                boq_image, 
    #                lang="ind+eng", 
    #                output_type=pytesseract.Output.DATAFRAME
    #            )
    #            
    #            st.write("Data mentah hasil OCR dari Halaman 6 (termasuk kata dengan confidence rendah):")
    #            # Tampilkan seluruh DataFrame mentah untuk kita analisis
    #            st.dataframe(ocr_df_raw)
    #            
    #        except Exception as e:
    #            st.error(f"Terjadi error saat melakukan OCR pada Halaman 6: {e}")
    #    else:
    #        st.error("Dokumen PDF tidak memiliki cukup halaman (kurang dari 6 halaman).")
    

    # Fungsi ekstraksi data BOQ 
        #df_boq, boq_page_index = re_extract_and_parse_boq(images)

        if boq_page_number:
            boq_page_index = boq_page_number - 1
            st.info(f"Referensi Halaman BOQ (Halaman {boq_page_number}):")
            st.image(images[boq_page_index], use_column_width=True)

        st.success("Silakan input kuantitas berdasarkan gambar di atas.")

            # Data untuk diisi oleh pengguna
        boq_input_data = {
            'DESIGNATOR': [
                "SC-OF-SM-24", "OS-SM-1", "ODP Solid-PB-8 AS", "PU-S9.0-140",
                "Slack Support HH", "Label Kabel Distribusi (KU FO)", "PU-S7.0-400NM",
                "AC-OF-SM-ADSS-120", "PU-ASDE--50/70", "PU-AS-SC"
            ],
            'KUANTITAS_BOQ': [0] * 10
        }
        df_boq_input = pd.DataFrame(boq_input_data)
        edited_df_boq = st.data_editor(
            df_boq_input,
            column_config={
                "DESIGNATOR": st.column_config.Column("Designator (dari BOQ)", disabled=True),
                "KUANTITAS_BOQ": st.column_config.NumberColumn("Input Kuantitas", min_value=0, step=1, format="%d")
            },
            hide_index=True, use_container_width=True, key="boq_editor"
        )

        if st.button("Lanjutkan ke Verifikasi Bukti", key="verify_button"):
            # Ambil data BOQ yang sudah diverifikasi pengguna
            final_boq_df = st.session_state.get('final_boq', pd.DataFrame())
            if final_boq_df.empty:
                 final_boq_df = edited_df_boq # Ambil dari editor jika belum ada di session state
            if (final_boq_df['KUANTITAS_BOQ'] == 0).any():
                st.warning("Peringatan: Masih ada kuantitas yang bernilai 0. Pastikan semua data sudah terisi.")
            else:
                st.success("Data kuantitas BOQ telah disimpan. Memulai penghitungan bukti...")
                
                # --- LOGIKA BARU DI SINI ---
                with st.spinner("Memindai dan menghitung bukti dari semua halaman lampiran..."):
                    # Panggil fungsi penghitung bukti
                    from core.evidence_counter import count_evidence
                    counted_evidence_df = count_evidence(images)
                # Gabungkan data BOQ dengan data hasil hitung bukti
                comparison_df = pd.merge(
                    final_boq_df,
                    counted_evidence_df,
                    on="DESIGNATOR",
                    how="left"
                ).fillna(0) # Isi designator yang tidak ada buktinya dengan 0
                # Tentukan status berdasarkan perbandingan kuantitas
                comparison_df['STATUS'] = comparison_df.apply(
                    lambda row: "✅ Sesuai" if row['KUANTITAS_BOQ'] == row['JUMLAH_BUKTI'] else "❌ Tidak Sesuai",
                    axis=1
                )
                
                st.header("Hasil Akhir Verifikasi Kuantitas")
                st.dataframe(comparison_df, use_container_width=True)        #else:
        #    st.error("Halaman 'BOQ UJI TERIMA' tidak dapat ditemukan di dalam dokumen.")

       

# app.py
import streamlit as st
import pandas as pd
from collections import Counter
from datetime import datetime
from streamlit.components.v1 import html
from fpdf import FPDF
import os
import io
import numpy as np  # noqa: F401
import traceback
from core.pdf_reader import extract_text_from_pdf
from core.checker import check_items
from core.evidence_counter import collect_evidence
from core.boq_extractor import find_boq_page, extract_boq_table_with_cv

st.cache_data.clear()
# ---- CACHING ----
@st.cache_data
def process_uploaded_pdf(uploaded_file_bytes):
    if not os.path.exists('data'):
        os.makedirs('data')
    temp_file_path = f"data/temp_{datetime.now().timestamp()}.pdf"
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file_bytes)

    ignore_titles = [
        "CHECKLIST VERIFIKASI BA UJI TERIMA",
        "CHECKLIST VERIFIKASI BERITA ACARA UJI TERIMA",
        "CHECKLIST VERIFIKASI BERITA ACARA COMMISSIONING TEST",
        "DOKUMEN BERITA ACARA UJI TERIMA KESATU",
        "DOKUMEN BERITA ACARA UJI TERIMA",
    ]
    text_per_page, images = extract_text_from_pdf(temp_file_path, ignore_titles=ignore_titles)

    boq_page_index = find_boq_page(images)
    df_boq_auto = extract_boq_table_with_cv(images, boq_page_index)

    os.remove(temp_file_path)
    return text_per_page, images, boq_page_index, df_boq_auto

# ---- APLIKASI UTAMA ----
st.set_page_config(page_title="SIVERDI | Sistem Verifikasi Dokumen Internal", layout="wide")
st.title("📄 Sistem Verifikasi Dokumen Internal")

if 'boq_submitted' not in st.session_state:
    st.session_state.boq_submitted = False
if 'show_report_form' not in st.session_state:
    st.session_state.show_report_form = False    
if 'final_report_df' not in st.session_state:
    st.session_state.final_report_df = None    
if 'comparison_df' not in st.session_state:
    st.session_state.comparison_df = None
if 'evidence_galleries' not in st.session_state:
    st.session_state.evidence_galleries = None
if 'boq_data_for_gallery' not in st.session_state:
    st.session_state.boq_data_for_gallery = None
if 'stage' not in st.session_state:
    st.session_state.stage = 'input_boq'

uploaded_file = st.file_uploader("Upload dokumen PDF", type="pdf")
if uploaded_file:
    uploaded_file_bytes = uploaded_file.getvalue()
    try:
        text_per_page, images, boq_page_index, df_boq_auto = process_uploaded_pdf(uploaded_file_bytes)
    except Exception as e:
        st.error(f"❌ Terjadi error saat memproses PDF: {e}")
        st.text(traceback.format_exc())
        st.stop()

    if not images:
        st.error("Gagal memproses file PDF.")
        st.stop()
        
    st.success("File berhasil dianalisis!")

    tab1, tab2 = st.tabs(["Checklist Kelengkapan Item", "Verifikasi Kuantitas BOQ"])

    with tab1:
        st.header("Hasil Pengecekan Kelengkapan Dokumen")
    # Kata kunci pencarian yang diperbarui dan lebih akurat
    # Menggunakan list untuk memungkinkan beberapa kemungkinan judul per item
        checklist_items = {
            # Pencarian menggunakan metode regex
            "BAUT": {
                "keywords": [r"BERITA ACARA\s*UJI TERIMA"],
                "method": "regex"
            },
            "Laporan UT": {
                "keywords": ["LAPORAN UJI TERIMA", r"LAPORAN\s*UJI TERIMA"],
                "method": "regex"
            },
            # Pencarian menggunakan metode title
            "BA Test Commissioning": {
                "keywords": ["BERITA ACARA COMMISSIONING TEST"],
                "method": "title"
            },
            "Redline Drawing": {
                "keywords": ["PETA LOKASI", "SKEMA KABEL", "SKEMA"],
                "method": "title"
            },
            "BoQ Akhir": {
                "keywords": ["BILL OF QUANTITY UJI TERIMA", "BOQ UJI TERIMA", "BOQ COMMISSIONING TEST", "LAPORAN BOQ UJI TERIMA"],
                "method": "title"
            },
            "Hasil Capture": {
                "keywords": ["FOTO PENGUKURAN OPM", "HASIL UKUR OTDR", "OTDR REPORT", "OTDR Report",
                             "DATA PENGUKURAN OPM", "EVIDENCE HASIL UKUR", "EVIDENCE HASIL UKUR FEEDER", "EVIDENCE HASIL IN FEEDER OPM"],
                "method": "title"
            },
            # Pencarian menggunakan metode presence (mencari berdasarkan frasa yang ditemukan)
            "Evidence Photo": {
                "keywords": ["LAMPIRAN EVIDENCE UJI TERIMA", "DOKUMENTASI UJI TERIMA", "EVIDENCE ODP", "EVIDENCE TIANG"],
                "method": "presence"
            },
            "Surat Permintaan Uji Terima dari Mitra": {
                "keywords": ["Permohonan Uji Terima SP"],
                "method": "presence"
            },
            "S/K Penunjukan Team Uji Terima": {
                "keywords": ["Penunjukan Personil Tim Uji Terima"],
                "method": "presence"
            },
            "Nota Dinas Pelaksanaan Uji Terima": {
                "keywords": ["Adapun periode waktu pelaksanaan dari tanggal"],
                "method": "presence"
            }
            }

        structured_items = [
            ("1", "A", "BAUT"),
            ("1", "B", "Laporan UT"),
            ("2", "A", "Surat Permintaan Uji Terima dari Mitra"),
            ("2", "B", "BA Test Commissioning dan Lampirannya"),
            ("3", "A", "S/K Penunjukan Team Uji Terima"),
            ("3", "B", "Nota Dinas Pelaksanaan Uji Terima"),
            ("4", "A", "Redline Drawing"),
            ("4", "B", "BoQ Akhir"),
            ("4", "C", "Hasil Capture"),
            ("4", "D", "Evidence Photo")
        ]

        # Menggunakan structured_items untuk memastikan urutan yang benar
        item_keys_in_order = [item[2] for item in structured_items]
        check_results = check_items(checklist_items, text_per_page, item_keys_in_order)

        formatted_results = []
        for i, row in enumerate(check_results):
            no, sub, item = structured_items[i]
    
            # Format keterangan berdasarkan list 'Pages' yang diterima
            keterangan_text = "Halaman tidak ditemukan atau judul tidak sesuai."
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
        # State 1: Tampilkan form untuk input kuantitas BOQ
        if st.session_state.stage == 'input_boq':
            st.header("Langkah 1: Verifikasi Kuantitas BOQ")
            if boq_page_index != -1:
                st.image(images[boq_page_index], caption=f"Halaman BOQ (Otomatis terdeteksi di hal. {boq_page_index + 1})")
                
                with st.form(key="boq_form"):
                    if df_boq_auto is not None and not df_boq_auto.empty:
                        st.success("Sistem berhasil melakukan ekstrak data pada tabel!")
                        st.info("Silahkan lakukan verifikasi ulang agar data sesuai.")
                        initial_data = df_boq_auto
                    else:
                        st.warning ("Ekstraksi gagal. Lakukan pengisian manual pada tabel dibawah ini.")
                        initial_data = pd.DataFrame(columns=['DESIGNATOR', 'KUANTITAS_BOQ'])

                    edited_df_boq = st.data_editor(
                        df_boq_auto,
                        hide_index = True,
                        use_container_width = True,
                        num_rows="dynamic"
                    )
                    submit_button = st.form_submit_button(label="Kumpulkan Bukti & Lanjutkan ke Verifikasi")

                    if submit_button:
                        st.session_state.final_boq_data = edited_df_boq
                        st.session_state.stage = 'verify_evidence' # Pindah ke tahap berikutnya
                        st.rerun() # Refresh untuk menampilkan tahap berikutnya
            else:
                st.error("Halaman 'BOQ UJI TERIMA' tidak dapat ditemukan secara otomatis.")

        # State 2: Tampilkan galeri bukti dan form laporan
        elif st.session_state.stage == 'verify_evidence':
            st.header("Langkah 2: Laporan Verifikasi Akhir")
            st.info("Berikut adalah bukti yang terkumpul. Berikan status dan catatan verifikasi Anda.")
            
            with st.spinner("Mengumpulkan semua bukti dari lampiran..."):
                evidence_galleries = collect_evidence(images, st.session_state.final_boq_data, text_per_page, boq_page_index)

            with st.form(key="report_form"):
                for index, row in st.session_state.final_boq_data.iterrows():
                    designator, boq_qty = row['DESIGNATOR'], row['KUANTITAS_BOQ']
                    st.subheader(f"Item: {designator}")
                    st.markdown(f"Kuantitas Menurut BOQ: **{boq_qty}**")

                    gallery_images = evidence_galleries.get(designator, [])
                    if gallery_images:
                        st.write(f"Jumlah Halaman Bukti Ditemukan: **{len(gallery_images)}**")
                        cols = st.columns(4) 
                        for i, img in enumerate(gallery_images):
                            cols[i % 4].image(img, use_container_width=True, caption=f"Bukti #{i+1}")
                    else:
                        st.warning("Tidak ada bukti foto yang ditemukan untuk item ini.")
                    
                    # Kolom input untuk verifikasi manual
                    status_verifikasi = st.radio("Status Verifikasi:", ["✅ Sesuai", "❌ Tidak Sesuai", "⚠️ Perlu Diperiksa"], key=f"status_{designator}", horizontal=True)
                    catatan = st.text_area("Catatan (Opsional):", key=f"notes_{designator}", height=100)
                    st.divider()

                report_submit_button = st.form_submit_button("Simpan & Buat Laporan Final")
                if report_submit_button:
                    # Kumpulkan data dari input pengguna
                    report_data = []
                    for index, row in st.session_state.final_boq_data.iterrows():
                        report_data.append({
                            "DESIGNATOR": row['DESIGNATOR'], "KUANTITAS_BOQ": row['KUANTITAS_BOQ'],
                            #"JML_HALAMAN_BUKTI": len(evidence_galleries.get(row['DESIGNATOR'], [])),
                            "STATUS_VERIFIKASI": st.session_state[f"status_{row['DESIGNATOR']}"],
                            "CATATAN": st.session_state[f"notes_{row['DESIGNATOR']}"]
                        })
                    st.session_state.final_report_df = pd.DataFrame(report_data)
                    st.session_state.stage = 'show_report' # Pindah ke tahap akhir
                    st.rerun()

        # State 3: Tampilkan laporan final
        elif st.session_state.stage == 'show_report':
            st.header("Laporan Final Verifikasi Kuantitas BOQ")
            
            final_df = st.session_state.final_report_df
            report_table_html = """
            <style>
              table { width: 100%; 
                        border-collapse: collapse; 
                        margin-top: 20px; 
                        font-family: "Inter", sans-serif;
                        font-size: 14px;
                        color: white;
                    }
              th, td { border: 1px solid white; 
                        padding: 8px;
                        text-align: center;
                        vertical-align: middle;
                        color: white
                    }
              th { background-color: #444; color: white; }
              td.item-name { text-align: left; }
              td.notes { text-align: left; max-width: 300px; word-wrap: break-word; }
            </style>
            <table>
              <tr>
                <th>DESIGNATOR</th>
                <th>KUANTITAS BOQ</th>
                <th>STATUS VERIFIKASI</th>
                <th>CATATAN</th>
              </tr>
            """
            
            for _, row in final_df.iterrows():
                report_table_html += f"""
                <tr>
                    <td class="item-name">{row['DESIGNATOR']}</td>
                    <td>{row['KUANTITAS_BOQ']}</td>
                    <td>{row['STATUS_VERIFIKASI']}</td>
                    <td class="notes">{row['CATATAN']}</td>
                </tr>
                """
            report_table_html += "</table>"

            html(report_table_html, height=400, scrolling=True)
            
            st.subheader("Download Laporan Final")
            final_df = st.session_state.final_report_df
            #col1, col2 = st.columns(2)

            #with col1:
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False, sheet_name='Laporan Verifikasi')
            excel_data = output_excel.getvalue()
            st.download_button(
                label="Download Laporan (Excel)",
                data=excel_data,
                file_name=f"laporan_verifikasi_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            #with col2:
            pdf = FPDF(orientation='L') # Lanskap
            pdf.add_page()
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Laporan Final Verifikasi Kuantitas BOQ", 0, 1, 'C')
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 8)
            
            # Header Tabel
            header_widths = {'DESIGNATOR': 60, 'KUANTITAS_BOQ': 30, #'JML_HALAMAN_BUKTI': 40, 
                             'STATUS_VERIFIKASI': 40, 'CATATAN': 100}
            for col_name in final_df.columns:
                # Ganti nama kolom untuk tampilan yang lebih baik di PDF jika perlu
                display_name = col_name.replace('_', ' ').title()
                pdf.cell(header_widths.get(col_name, 40), 8, display_name, 1, 0, 'C')
            pdf.ln()
            
            # Isi Tabel
            pdf.set_font("Arial", '', 8)
            for index, row in final_df.iterrows():
                # --- PERBAIKAN DI SINI ---
                # Buat versi teks bersih dari status verifikasi
                clean_status = str(row['STATUS_VERIFIKASI']).replace('✅', '').replace('❌', '').replace('⚠️', '').strip()
                pdf.cell(header_widths['DESIGNATOR'], 8, str(row['DESIGNATOR']), 1)
                pdf.cell(header_widths['KUANTITAS_BOQ'], 8, str(row['KUANTITAS_BOQ']), 1, 0, 'C')
                #pdf.cell(header_widths['JML_HALAMAN_BUKTI'], 8, str(row['JML_HALAMAN_BUKTI']), 1, 0, 'C')
                pdf.cell(header_widths['STATUS_VERIFIKASI'], 8, clean_status, 1) # Gunakan teks bersih
                pdf.cell(header_widths['CATATAN'], 8, str(row['CATATAN']), 1)
                pdf.ln()
            pdf_data = pdf.output(dest='S').encode('latin-1')
            
            st.download_button(
                label="Download Laporan (PDF)",
                data=pdf_data,
                file_name=f"laporan_verifikasi_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
            st.divider()
            if st.button("Lakukan Verifikasi Baru"):
                # Reset state untuk memulai dari awal
                st.session_state.stage = 'input_boq'
                st.session_state.final_boq_data = None
                st.session_state.final_report_df = None
                st.rerun()
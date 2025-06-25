import streamlit as st
import pandas as pd
from core.pdf_reader import extract_text_from_pdf
from core.checker import check_items
from datetime import datetime
from fpdf import FPDF
from streamlit.components.v1 import html
from collections import Counter
from core.predict import predict_signature
from pdf2image import convert_from_path
import shutil
import os

st.set_page_config(page_title="PED Unit Document Checker", layout="wide")
st.title("📄 Pemeriksa kelengkapan dokumen internal Unit PED")
st.subheader("Upload dokumen PDF")

uploaded_file = st.file_uploader("Upload dokumen PDF", type="pdf")
if uploaded_file:
    file_path = f"data/{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    st.success("File berhasil diupload!")

    # Bersihkan folder page_images
    if os.path.exists("page_images"):
        shutil.rmtree("page_images")
    os.makedirs("page_images", exist_ok=True)

    # Konversi semua halaman PDF ke gambar
    images = convert_from_path(file_path, dpi=200)
    st.subheader("📷 Deteksi Tanda Tangan")

    for idx, img in enumerate(images):
        img_path = os.path.join("page_images", f"page_{idx+1}.png")
        img.save(img_path)

        label, confidence = predict_signature(img_path)
        st.markdown(f"**Halaman {idx+1}:** {label.upper()} ({confidence:.2%})")

    # Ekstrak teks dari PDF
    text_per_page = extract_text_from_pdf(file_path)

    # Daftar item checklist
    checklist_items = {
        "BAUT": "Berita Acara Uji Terima",
        "Laporan UT": "Dokumen UT",
        "Surat Permintaan Uji Terima dari Mitra": "Permohonan Uji Terima",
        "BA Test Commissioning dan Lampirannya": "BA Test Commissioning dan Lampirannya",
        "SK/Penunjukan Team Uji Terima": "Penunjukan Personil Tim Uji Terima",
        "Nota Dinas Pelaksanaan Uji Terima": "Nota Dinas Pelaksanaan Uji Terima",
        "Red line drawing": "Red line drawing",
        "BoQ akhir": "Lampiran BOQ Uji Terima",
        "Hasil Capture": "Hasil Capture",
        "Evidence Photo": "Evidence Photo"
    }

    results = check_items(checklist_items, text_per_page)

    # Struktur dengan subitem dan grouping No
    structured_items = [
        ("1", "A", "BAUT"),
        ("1", "B", "Laporan UT"),
        ("2", "A", "Surat Permintaan Uji Terima dari Mitra"),
        ("2", "B", "BA Test Commissioning dan Lampirannya"),
        ("3", "A", "SK/Penunjukan Team Uji Terima"),
        ("3", "B", "Nota Dinas Pelaksanaan Uji Terima"),
        ("4", "A", "Red line drawing"),
        ("4", "B", "BoQ akhir"),
        ("4", "C", "Hasil Capture"),
        ("4", "D", "Evidence Photo"),
    ]

    # Gabungkan hasil pengecekan ke dalam format akhir
    formatted_results = []
    for i, row in enumerate(results):
        no, sub, item = structured_items[i]
        formatted_results.append({
            "No": no,
            "": sub,
            "ITEM YG DI PERIKSA": item,
            "STATUS OK": "✔" if row["OK/NOK"] == "OK" else "",
            "STATUS NOK": "✔" if row["OK/NOK"] == "NOK" else "",
            "KETERANGAN": row["Keterangan"]
        })

    df = pd.DataFrame(formatted_results)

    # Hitung jumlah row untuk setiap No untuk rowspan
    no_counts = Counter([row["No"] for row in formatted_results])

    # Buat HTML tabel
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
        <th rowspan="2"> </th>
        <th rowspan="2">ITEM YG DI PERIKSA</th>
        <th colspan="2">STATUS</th>
        <th rowspan="2">KETERANGAN</th>
      </tr>
      <tr>
        <th>OK</th>
        <th>NOK</th>
      </tr>
    """

    # Bangun baris-baris tabel HTML
    prev_no = None
    for row in formatted_results:
        current_no = row["No"]
        show_no = current_no != prev_no
        no_cell = f'<td rowspan="{no_counts[current_no]}">{current_no}</td>' if show_no else ""
        prev_no = current_no

        table_html += f"""
        <tr>
          {no_cell}
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

    # Tombol download Excel
    if st.button("📥 Download hasil (Excel)"):
        export_name = f"hasil_cek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(export_name, index=False)
        with open(export_name, "rb") as f:
            st.download_button(
                label="Klik untuk download Excel",
                data=f,
                file_name=export_name,
                mime="application/vnd.ms-excel"
            )

    # Tombol download PDF
    if st.button("📥 Download hasil (PDF)"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Hasil Pengecekan Dokumen", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=10)

        # Header PDF
        pdf.cell(10, 8, "No", border=1)
        pdf.cell(10, 8, "", border=1)
        pdf.cell(80, 8, "ITEM YG DI PERIKSA", border=1)
        pdf.cell(20, 8, "OK", border=1)
        pdf.cell(20, 8, "NOK", border=1)
        pdf.cell(50, 8, "KETERANGAN", border=1)
        pdf.ln()

        prev_no = None
        for row in formatted_results:
            no_cell = row["No"] if row["No"] != prev_no else ""
            prev_no = row["No"]
            pdf.cell(10, 8, no_cell, border=1)
            pdf.cell(10, 8, row[""], border=1)
            pdf.cell(80, 8, row["ITEM YG DI PERIKSA"], border=1)
            pdf.cell(20, 8, "v" if row["STATUS OK"] else "", border=1)
            pdf.cell(20, 8, "v" if row["STATUS NOK"] else "", border=1)
            pdf.cell(50, 8, row["KETERANGAN"], border=1)
            pdf.ln()

        pdf_name = f"hasil_cek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(pdf_name)
        with open(pdf_name, "rb") as f:
            st.download_button(
                label="Klik untuk download PDF",
                data=f,
                file_name=pdf_name,
                mime="application/pdf"
            )
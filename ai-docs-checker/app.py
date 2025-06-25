import streamlit as st
import pandas as pd
from core.pdf_reader import extract_text_from_pdf
from core.checker import check_items
import os
from datetime import datetime

st.set_page_config(page_title="PED Unit Document Checker", layout="wide")
st.title("📄 AI Pengecekan Dokumen Internal PED 📄")
st.subheader("Pemeriksa kelengkapan dokumen internal Unit PED")

uploaded_file = st.file_uploader("Upload dokumen PDF", type="pdf")
if uploaded_file:
    file_path = f"data/{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    st.success("File berhasil diupload!")

    # Ekstrak teks
    text_per_page = extract_text_from_pdf(file_path)

    # Item checklist berdasarkan tabel yang kamu berikan
    checklist_items = [
        "BAUT", "Laporan UT",
        "Surat Permintaan Uji Terima dari Mitra", "BA Test Commissioning dan Lampirannya",
        "SK/Penunjukan Team Uji Terima", "Nota Dinas Pelaksanaan Uji Terima",
        "Red line drawing", "BoQ akhir", "Hasil Capture", "Evidence Photo"
    ]

    # Proses pengecekan
    results = check_items(checklist_items, text_per_page)
    df = pd.DataFrame(results)

    st.subheader("Hasil Pengecekan")
    st.dataframe(df)

    # Ekspor ke Excel
    if st.button("📥 Download hasil (Excel)"):
        export_name = f"hasil_cek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(export_name, index=False)
        with open(export_name, "rb") as f:
            st.download_button(label="Klik untuk download Excel", data=f, file_name=export_name, mime="application/vnd.ms-excel")

    # Ekspor ke PDF (opsional sederhana dengan HTML)
    if st.button("📥 Download hasil (PDF)"):
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Hasil Pengecekan Dokumen", ln=True, align='C')
        pdf.ln(10)
        for _, row in df.iterrows():
            pdf.cell(200, 10, txt=f"{row['Item yg Diperiksa']} - {row['Status']} - {row['Keterangan']}", ln=True)
        pdf_name = f"hasil_cek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(pdf_name)
        with open(pdf_name, "rb") as f:
            st.download_button(label="Klik untuk download PDF", data=f, file_name=pdf_name, mime="application/pdf")

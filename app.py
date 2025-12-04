from flask import Flask, render_template, send_file
import pandas as pd
import tempfile
from weasyprint import HTML
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from PyPDF2 import PdfMerger

app = Flask(__name__)

# --- Config Google Sheets ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds_info = json.loads(os.environ["GOOGLE_CREDS_JSON"])
creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
client = gspread.authorize(creds)

SHEETS = {
    "Bristol": "115K5ZlvVyXEslImRDglSAoJs5cS59LIImEkUgHTcwQA",
    "Cober": "1E9Cwu8hfDwSh8_BR3vY9NoQQ5f2WFPISBwQ6mro11uY",
    "Medicals": "1Gz3k5-eCrjAhtWGVLSM2YG4DPMt7yJEtqEGcafGLsbI",
}

@app.route("/")
def index():
    return "Cartilla se generará para todas las zonas automáticamente."

@app.route("/generar/<cartera>/<plan>", methods=["GET"])
def generar(cartera, plan):
    # Leer hoja Google Sheets
    sheet = client.open_by_key(SHEETS[cartera]).worksheet("App")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Filtrar por plan y Estado, ignorando Cuerpo Médico
    df_filtrado = df[(df[plan] == "SI") & (df["Estado"] == "Alta") & (df["tp_nom"] != "Cuerpo Médico")]

    pdf_files = []

    # Obtener todas las zonas únicas
    zonas = df_filtrado["loc_nombre"].unique()

    # Bloques por tipo de prestador
    tipo_bloques = [
        (["Sanatorio", "Clínica"], "Sanatorios y Clínicas"),
        (["Diagnóstico", "Tratamiento"], "Diagnóstico y Tratamiento")
    ]

    chunk_size = 50  # filas por bloque para no saturar memoria

    for zona in zonas:
        df_zona = df_filtrado[df_filtrado["loc_nombre"] == zona]
        for tipos, titulo_bloque in tipo_bloques:
            df_bloque = df_zona[df_zona["tp_nom"].isin(tipos)]
            # Paginar en bloques pequeños
            for i in range(0, len(df_bloque), chunk_size):
                sub_bloque = df_bloque.iloc[i:i+chunk_size]
                if sub_bloque.empty:
                    continue
                html = render_template(
                    "cartilla_template.html",
                    cartera=cartera,
                    plan=plan,
                    zona=zona,
                    bloque=titulo_bloque,
                    prestadores=sub_bloque.to_dict("records")
                )
                tmp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                HTML(string=html).write_pdf(tmp_pdf.name)
                pdf_files.append(tmp_pdf.name)
                del sub_bloque, html

    # Unir todos los PDFs
    merger = PdfMerger()
    for f in pdf_files:
        merger.append(f)
    tmp_final = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    merger.write(tmp_final.name)
    merger.close()

    # Limpiar PDFs temporales
    for f in pdf_files:
        os.remove(f)

    return send_file(tmp_final.name, download_name="cartilla.pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

from flask import Flask, render_template, request, send_file
import pandas as pd
import tempfile
from weasyprint import HTML
import gspread
from google.oauth2.service_account import Credentials
import os
import json

app = Flask(__name__)

# --- CONFIG GOOGLE SHEETS ---
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
    return render_template("index.html")

@app.route("/generar", methods=["POST"])
def generar():
    cartera = request.form["cartera"]
    plan = request.form["plan"]

    # Leer hoja Google Sheets
    sheet = client.open_by_key(SHEETS[cartera]).worksheet("App")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Filtrar por plan y Estado, ignorando Cuerpo Médico
    df_filtrado = df[(df[plan] == "SI") & (df["Estado"] == "Alta") & (df["tp_nom"] != "Cuerpo Médico")]

    # Generar HTML para todas las zonas y bloques
    html_final = ""
    zonas = df_filtrado["loc_nombre"].unique()
    tipo_bloques = [
        (["Sanatorio", "Clínica"], "Sanatorios y Clínicas"),
        (["Diagnóstico", "Tratamiento"], "Diagnóstico y Tratamiento")
    ]

    for zona in zonas:
        df_zona = df_filtrado[df_filtrado["loc_nombre"] == zona]
        for tipos, titulo_bloque in tipo_bloques:
            df_bloque = df_zona[df_zona["tp_nom"].isin(tipos)]
            if df_bloque.empty:
                continue
            html_final += render_template(
                "cartilla_template.html",
                cartera=cartera,
                plan=plan,
                zona=zona,
                bloque=titulo_bloque,
                prestadores=df_bloque.to_dict("records")
            )

    # Crear PDF final
    tmp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    HTML(string=html_final).write_pdf(tmp_pdf.name)

    return send_file(tmp_pdf.name, download_name="cartilla.pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

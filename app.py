from flask import Flask, render_template, request, send_file
import pandas as pd
import tempfile
import pdfkit
import gspread
from google.oauth2.service_account import Credentials
import os
import json

app = Flask(__name__)

# --- CONFIG GOOGLE SHEETS ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Cargar credenciales desde variable de entorno
creds_info = json.loads(os.environ["GOOGLE_CREDS_JSON"])
creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)

# Crear cliente
client = gspread.authorize(creds)

# IDs de tus Sheets
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
    zona = request.form["zona"]

    # Leer hoja Google Sheets
    sheet = client.open_by_key(SHEETS[cartera]).worksheet("App")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Filtrar
    df_filtrado = df[
        (df[plan] == "SI") &
        (df["loc_nombre"] == zona) &
        (df["Estado"] == "Alta")
    ]

    # Crear HTML desde template
    html = render_template(
        "cartilla_template.html",
        cartera=cartera,
        plan=plan,
        zona=zona,
        prestadores=df_filtrado.to_dict("records")
    )

    # PDF temporal
    tmp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    pdfkit.from_string(html, tmp_pdf.name)

    return send_file(tmp_pdf.name, download_name="cartilla.pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

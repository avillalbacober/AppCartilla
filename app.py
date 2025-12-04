from flask import Flask, render_template, request, send_file
import pandas as pd
import tempfile
from weasyprint import HTML

import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# --- CONFIG GOOGLE SHEETS ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
CREDS = Credentials.from_service_account_file(
    "creds.json", scopes=SCOPES
)
client = gspread.authorize(CREDS)

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

    # Abrir Google Sheet
    sheet = client.open_by_key(SHEETS[cartera]).sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Filtrado
    df_filtrado = df[
        (df[plan] == "SI") &
        (df["loc_nombre"] == zona) &
        (df["Estado"] == "Alta")
    ]

    # Generar PDF dinámico
    html = render_template(
        "cartilla_template.html",
        cartera=cartera,
        plan=plan,
        zona=zona,
        prestadores=df_filtrado.to_dict("records")
    )

    tmp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    HTML(string=html).write_pdf(tmp_pdf.name)

    return send_file(tmp_pdf.name, download_name="cartilla.pdf")

if __name__ == "__main__":
    app.run()

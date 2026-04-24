import json, re
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import gspread
from google.oauth2.service_account import Credentials
from config import SPREADSHEET_ID, SHEET_NAME, GOOGLE_CREDS_JSON

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def _get_sheet():
    creds = Credentials.from_service_account_info(
        json.loads(GOOGLE_CREDS_JSON), scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    return gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

def _parse_brl(val):
    if pd.isna(val) or str(val).strip() in ("", "-"):
        return 0.0
    return float(re.sub(r"[R$\s\.]", "", str(val)).replace(",", "."))

def _parse_date(val):
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(val).strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Formato de data não reconhecido: {val}")

def ler_e_consolidar():
    sheet = _get_sheet()
    df = pd.DataFrame(sheet.get_all_records())

    # Filtrar estornados
    df = df[df["Status Pedido"].str.lower() != "estornado"].copy()

    # Parsing
    df["Data"]     = df["Data Pagamento"].apply(_parse_date)
    df["Valor"]    = df["Valor Pago pelo Cliente"].apply(_parse_brl)
    df["Taxa"]     = df["Valor Taxas Pedido"].apply(_parse_brl)
    df["Tipo"]     = df["Tipo Pagamento"].apply(
        lambda x: "PIX" if "pix" in str(x).lower() else "Credito"
    )
    df["Parcelas"] = df["Parcelas"].astype(int)

    # Consolidar por Dia + Tipo + Parcelas
    consolidado = df.groupby(["Data", "Tipo", "Parcelas"]).agg(
        Valor_Total=("Valor", "sum"),
        Taxa_Total=("Taxa",  "sum")
    ).reset_index()

    lancamentos = []
    for _, row in consolidado.iterrows():
        data = row["Data"]
        tipo = row["Tipo"]
        n    = int(row["Parcelas"])

        if tipo == "PIX":
            titulo = f"Vendas PIX {data.strftime('%d/%m/%Y')}"
            lancamentos.append({
                "titulo":           titulo,
                "data_competencia": data,
                "data_vencimento":  data,
                "tipo":             tipo,
                "parcela":          1,
                "total_parcelas":   1,
                "valor_receber":    round(row["Valor_Total"], 2),
                "valor_taxa":       round(row["Taxa_Total"], 2),
            })
        else:
            titulo       = f"Vendas Crédito {n}x {data.strftime('%d/%m/%Y')}"
            val_parcela  = round(row["Valor_Total"] / n, 2)
            taxa_parcela = round(row["Taxa_Total"]  / n, 2)
            for i in range(1, n + 1):
                lancamentos.append({
                    "titulo":           titulo,
                    "data_competencia": data,
                    "data_vencimento":  data + relativedelta(months=i),
                    "tipo":             tipo,
                    "parcela":          i,
                    "total_parcelas":   n,
                    "valor_receber":    val_parcela,
                    "valor_taxa":       taxa_parcela,
                })

    return lancamentos

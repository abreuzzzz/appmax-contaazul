import os

SPREADSHEET_ID                = os.environ["SPREADSHEET_ID"]
SHEET_NAME                    = os.environ.get("SHEET_NAME", "Sheet1")
GOOGLE_CREDS_JSON             = os.environ["GOOGLE_CREDS_JSON"]

CLIENT_ID                     = os.environ["CONTA_AZUL_CLIENT_ID"]
CLIENT_SECRET                 = os.environ["CONTA_AZUL_CLIENT_SECRET"]
CONTA_AZUL_BASE_URL           = "https://api-v2.contaazul.com/financeiro/v1"
CONTA_FINANCEIRA_RECEBER_ID   = os.environ.get("CONTA_FINANCEIRA_RECEBER_ID", "")
CONTA_FINANCEIRA_PAGAR_ID     = os.environ.get("CONTA_FINANCEIRA_PAGAR_ID", "")
CATEGORIA_RECEBER_ID          = os.environ.get("CATEGORIA_RECEBER_ID", "")
CATEGORIA_PAGAR_ID            = os.environ.get("CATEGORIA_PAGAR_ID", "")

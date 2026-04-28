import os

SPREADSHEET_ID                = os.environ["SPREADSHEET_ID"]
SHEET_NAME                    = os.environ.get("SHEET_NAME", "Sheet1")
GOOGLE_CREDS_JSON             = os.environ["GOOGLE_CREDS_JSON"]

CLIENT_ID                     = os.environ["CONTA_AZUL_CLIENT_ID"]
CLIENT_SECRET                 = os.environ["CONTA_AZUL_CLIENT_SECRET"]
CONTA_FINANCEIRA_RECEBER_ID   = os.environ.get("CONTA_FINANCEIRA_RECEBER_ID", "")
CONTA_FINANCEIRA_PAGAR_ID     = os.environ.get("CONTA_FINANCEIRA_PAGAR_ID", "")
CATEGORIA_RECEBER_ID          = os.environ["CATEGORIA_RECEBER_ID"]
CATEGORIA_PAGAR_ID            = os.environ["CATEGORIA_PAGAR_ID"]
CENTRO_CUSTO_RECEBER_ID       = os.environ.get("CENTRO_CUSTO_RECEBER_ID", "")  # novo
CENTRO_CUSTO_PAGAR_ID         = os.environ.get("CENTRO_CUSTO_PAGAR_ID", "")    # novo

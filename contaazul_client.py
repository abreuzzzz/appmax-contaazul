import requests
from auth_contaazul import get_access_token
from config import (
    CONTA_AZUL_BASE_URL,
    CONTA_FINANCEIRA_RECEBER_ID,
    CONTA_FINANCEIRA_PAGAR_ID,
    CATEGORIA_RECEBER_ID,
    CATEGORIA_PAGAR_ID,
)

def _headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type":  "application/json",
    }

def _ja_existe(endpoint, titulo):
    resp = requests.get(
        f"{CONTA_AZUL_BASE_URL}/{endpoint}/parcelas",
        headers=_headers(),
        params={"nome": titulo, "tamanho_pagina": 1},
        timeout=15,
    )
    resp.raise_for_status()
    return len(resp.json().get("items", [])) > 0

def _agrupar(lancamentos):
    eventos = {}
    for l in lancamentos:
        t = l["titulo"]
        if t not in eventos:
            eventos[t] = {
                "titulo":           t,
                "data_competencia": l["data_competencia"],
                "parcelas":         [],
            }
        eventos[t]["parcelas"].append(l)
    return eventos

def _post_receber(titulo, data_comp, parcelas):
    body = {
        "descricao":        titulo,
        "data_competencia": data_comp.strftime("%Y-%m-%d"),
        "parcelas": [
            {
                "descricao":        f"{titulo} ({p['parcela']}/{p['total_parcelas']})",
                "data_vencimento":  p["data_vencimento"].strftime("%Y-%m-%d"),
                "valor_bruto":      p["valor_receber"],
                **({"id_conta_financeira": CONTA_FINANCEIRA_RECEBER_ID}
                   if CONTA_FINANCEIRA_RECEBER_ID else {}),
            }
            for p in parcelas
        ],
        **({"id_categoria": CATEGORIA_RECEBER_ID} if CATEGORIA_RECEBER_ID else {}),
    }
    resp = requests.post(
        f"{CONTA_AZUL_BASE_URL}/contas-receber",
        headers=_headers(), json=body, timeout=15
    )
    resp.raise_for_status()
    return resp.json()

def _post_pagar(titulo, data_comp, parcelas):
    titulo_taxa = f"Taxa - {titulo}"
    body = {
        "descricao":        titulo_taxa,
        "data_competencia": data_comp.strftime("%Y-%m-%d"),
        "parcelas": [
            {
                "descricao":        f"{titulo_taxa} ({p['parcela']}/{p['total_parcelas']})",
                "data_vencimento":  p["data_vencimento"].strftime("%Y-%m-%d"),
                "valor_bruto":      p["valor_taxa"],
                **({"id_conta_financeira": CONTA_FINANCEIRA_PAGAR_ID}
                   if CONTA_FINANCEIRA_PAGAR_ID else {}),
            }
            for p in parcelas
        ],
        **({"id_categoria": CATEGORIA_PAGAR_ID} if CATEGORIA_PAGAR_ID else {}),
    }
    resp = requests.post(
        f"{CONTA_AZUL_BASE_URL}/contas-pagar",
        headers=_headers(), json=body, timeout=15
    )
    resp.raise_for_status()
    return resp.json()

def lancar_no_conta_azul(lancamentos):
    eventos    = _agrupar(lancamentos)
    resultado  = {"criados": [], "ignorados": [], "erros": []}

    for titulo, ev in eventos.items():
        try:
            if _ja_existe("contas-receber", titulo):
                print(f"[SKIP] Já existe: {titulo}")
                resultado["ignorados"].append(titulo)
                continue

            r = _post_receber(titulo, ev["data_competencia"], ev["parcelas"])
            print(f"[OK] Receber: {titulo} | id={r.get('id')}")

            total_taxa = sum(p["valor_taxa"] for p in ev["parcelas"])
            if total_taxa > 0:
                titulo_taxa = f"Taxa - {titulo}"
                if not _ja_existe("contas-pagar", titulo_taxa):
                    rp = _post_pagar(titulo, ev["data_competencia"], ev["parcelas"])
                    print(f"[OK] Pagar: Taxa - {titulo} | id={rp.get('id')}")
                else:
                    print(f"[SKIP] Já existe (taxa): Taxa - {titulo}")

            resultado["criados"].append(titulo)

        except requests.HTTPError as e:
            msg = f"{titulo}: {e.response.status_code} - {e.response.text}"
            print(f"[ERRO] {msg}")
            resultado["erros"].append(msg)

    return resultado

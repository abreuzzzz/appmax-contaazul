import requests
from auth_contaazul import get_access_token
from config import (
    CONTA_FINANCEIRA_RECEBER_ID,
    CONTA_FINANCEIRA_PAGAR_ID,
    CATEGORIA_RECEBER_ID,
    CATEGORIA_PAGAR_ID,
)

BASE = "https://api-v2.contaazul.com/v1/financeiro/eventos-financeiros"

def _headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type":  "application/json",
    }

# ─── Anti-duplicata ───────────────────────────────────────────────────────────

def _ja_existe_receber(titulo: str, data_comp: str) -> bool:
    resp = requests.get(
        f"{BASE}/contas-a-receber/buscar",
        headers=_headers(),
        params={
            "pagina": 1,
            "tamanho_pagina": 10,
            "descricao":            titulo,
            "data_competencia_de":  data_comp,
            "data_competencia_ate": data_comp,
            "data_vencimento_de":   "2020-01-01",
            "data_vencimento_ate":  "2099-12-31",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("itens_totais", 0) > 0

def _ja_existe_pagar(titulo: str, data_comp: str) -> bool:
    resp = requests.get(
        f"{BASE}/contas-a-pagar/buscar",
        headers=_headers(),
        params={
            "pagina": 1,
            "tamanho_pagina": 10,
            "descricao":            titulo,
            "data_competencia_de":  data_comp,
            "data_competencia_ate": data_comp,
            "data_vencimento_de":   "2020-01-01",
            "data_vencimento_ate":  "2099-12-31",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("itens_totais", 0) > 0

# ─── Agrupamento por evento ───────────────────────────────────────────────────

def _agrupar(lancamentos: list) -> dict:
    eventos = {}
    for l in lancamentos:
        t = l["titulo"]
        if t not in eventos:
            eventos[t] = {
                "titulo":           t,
                "data_competencia": l["data_competencia"],
                "valor_total":      0,
                "taxa_total":       0,
                "parcelas":         [],
            }
        eventos[t]["valor_total"] += l["valor_receber"]
        eventos[t]["taxa_total"]  += l["valor_taxa"]
        eventos[t]["parcelas"].append(l)
    return eventos

# ─── POST Contas a Receber ────────────────────────────────────────────────────

def _post_receber(evento: dict):
    valor_total = round(evento["valor_total"], 2)

    body = {
        "data_competencia": evento["data_competencia"].strftime("%Y-%m-%d"),
        "valor":            valor_total,
        "descricao":        evento["titulo"],
        "observacao":       "Lançamento automático via integração Appmax",
        "conta_financeira": CONTA_FINANCEIRA_RECEBER_ID,
        "rateio": [
            {
                "id_categoria": CATEGORIA_RECEBER_ID,
                "valor":        valor_total,
            }
        ],
        "condicao_pagamento": {
            "parcelas": [
                {
                    "descricao":        f"{evento['titulo']} ({p['parcela']}/{p['total_parcelas']})",
                    "data_vencimento":  p["data_vencimento"].strftime("%Y-%m-%d"),
                    "nota":             "Lançamento automático Appmax",
                    "conta_financeira": CONTA_FINANCEIRA_RECEBER_ID,
                    "detalhe_valor": {
                        "valor_bruto":   round(p["valor_receber"], 2),
                        "valor_liquido": round(p["valor_receber"], 2),
                    },
                }
                for p in evento["parcelas"]
            ]
        },
    }

    resp = requests.post(
        f"{BASE}/contas-a-receber",
        headers=_headers(),
        json=body,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()

# ─── POST Contas a Pagar ──────────────────────────────────────────────────────

def _post_pagar(evento: dict):
    titulo_taxa  = f"Taxa - {evento['titulo']}"
    taxa_total   = round(evento["taxa_total"], 2)

    body = {
        "data_competencia": evento["data_competencia"].strftime("%Y-%m-%d"),
        "valor":            taxa_total,
        "descricao":        titulo_taxa,
        "observacao":       "Taxa Appmax — lançamento automático",
        "conta_financeira": CONTA_FINANCEIRA_PAGAR_ID,
        "rateio": [
            {
                "id_categoria": CATEGORIA_PAGAR_ID,
                "valor":        taxa_total,
            }
        ],
        "condicao_pagamento": {
            "parcelas": [
                {
                    "descricao":        f"{titulo_taxa} ({p['parcela']}/{p['total_parcelas']})",
                    "data_vencimento":  p["data_vencimento"].strftime("%Y-%m-%d"),
                    "nota":             "Taxa Appmax — lançamento automático",
                    "conta_financeira": CONTA_FINANCEIRA_PAGAR_ID,
                    "detalhe_valor": {
                        "valor_bruto":   round(p["valor_taxa"], 2),
                        "valor_liquido": round(p["valor_taxa"], 2),
                    },
                }
                for p in evento["parcelas"]
            ]
        },
    }

    resp = requests.post(
        f"{BASE}/contas-a-pagar",
        headers=_headers(),
        json=body,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()

# ─── Função principal ─────────────────────────────────────────────────────────

def lancar_no_conta_azul(lancamentos: list) -> dict:
    eventos   = _agrupar(lancamentos)
    resultado = {"criados": [], "ignorados": [], "erros": []}

    for titulo, evento in eventos.items():
        data_comp_str = evento["data_competencia"].strftime("%Y-%m-%d")
        try:
            if _ja_existe_receber(titulo, data_comp_str):
                print(f"[SKIP] Já existe (receber): {titulo}")
                resultado["ignorados"].append(titulo)
                continue

            r = _post_receber(evento)
            print(f"[OK] Receber: {titulo} | protocolId={r.get('protocolId')} status={r.get('status')}")

            taxa_total = evento["taxa_total"]
            if taxa_total > 0:
                titulo_taxa = f"Taxa - {titulo}"
                if not _ja_existe_pagar(titulo_taxa, data_comp_str):
                    rp = _post_pagar(evento)
                    print(f"[OK] Pagar: {titulo_taxa} | protocolId={rp.get('protocolId')} status={rp.get('status')}")
                else:
                    print(f"[SKIP] Já existe (pagar): {titulo_taxa}")

            resultado["criados"].append(titulo)

        except requests.HTTPError as e:
            msg = f"{titulo}: {e.response.status_code} - {e.response.text[:300]}"
            print(f"[ERRO] {msg}")
            resultado["erros"].append(msg)

    return resultado

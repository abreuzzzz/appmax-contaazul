import sys
from sheets_reader import ler_e_consolidar
from contaazul_client import lancar_no_conta_azul

def main():
    print("=== Iniciando lançamentos ===")
    lancamentos = ler_e_consolidar()
    print(f"[INFO] {len(lancamentos)} lançamentos gerados")

    resultado = lancar_no_conta_azul(lancamentos)

    print("\n=== RESULTADO FINAL ===")
    print(f"✅ Criados:   {len(resultado['criados'])}")
    print(f"⏭️  Ignorados: {len(resultado['ignorados'])}")
    print(f"❌ Erros:     {len(resultado['erros'])}")
    if resultado["erros"]:
        for e in resultado["erros"]:
            print(f"  - {e}")

    # Só falha o workflow se TUDO deu errado (zero criados E zero ignorados)
    if resultado["erros"] and not resultado["criados"] and not resultado["ignorados"]:
        sys.exit(1)

if __name__ == "__main__":
    main()

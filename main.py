"""MoneyTrack — ponto de entrada.

    python main.py          # usa seus dados reais (data/moneytrack.db)
    python main.py --demo   # abre direto no modo demonstração (banco separado)
"""
import sys


def main() -> None:
    try:
        import customtkinter  # noqa: F401
    except ImportError:
        sys.exit("CustomTkinter não está instalado. Execute:  pip install -r requirements.txt")

    from database.schema import initialize_database
    from interface.app import App

    initialize_database()      # cria o banco e as categorias padrão na 1ª execução
    app = App()
    if "--demo" in sys.argv:
        app.set_demo_mode(True)
    app.mainloop()


if __name__ == "__main__":
    main()

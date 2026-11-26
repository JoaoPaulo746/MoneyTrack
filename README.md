# 💲 MoneyTrack — Educação e controle financeiro pessoal

Desafio Tech Solutions 2026 · 3º A · Técnico em Desenvolvimento de Sistemas

O MoneyTrack ajuda estudantes e jovens a registrar receitas e despesas, acompanhar o saldo, entender
seus hábitos de consumo e aprender educação financeira. Funciona 100% **offline**.

**Tecnologias:** Python 3 · CustomTkinter · SQLite · Pandas · NumPy · Matplotlib

## Instalação e execução

```bash
# 1. (opcional) ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows      |  source .venv/bin/activate  (Linux/macOS)

# 2. dependências
pip install -r requirements.txt

# 3. executar
python main.py                  # seus dados reais  (data/moneytrack.db)
python main.py --demo           # modo demonstração (banco separado, com dados de exemplo)
```

Requisitos: Python 3.10+ com Tkinter (já incluso no instalador oficial do Python para Windows/macOS;
no Ubuntu/Debian: `sudo apt install python3-tk`).

> O banco é criado automaticamente na primeira execução e os dados persistem entre execuções.
> O **modo demonstração** (também em *Configurações*) usa o arquivo `data/moneytrack_demo.db`,
> totalmente separado dos dados reais.

## Testes

```bash
python -m unittest discover -s tests -v
```
23 testes automatizados cobrem cadastro, edição, exclusão, saldo, filtros, categorias vinculadas,
metas, validações, SQL Injection, persistência, precisão decimal e análises automáticas
(usam banco temporário, nunca os dados reais).

## Estrutura

```
MoneyTrack/
├── main.py                    # ponto de entrada
├── requirements.txt
├── database/   connection.py · schema.py · operations.py · demo_data.py
├── models/     transaction.py · category.py · goal.py · money.py
├── services/   finance_service.py · analytics_service.py · validation_service.py
├── interface/  app.py · dashboard.py · transactions.py · categories.py · reports.py
│               goals.py · education.py · settings.py · charts.py · widgets.py · theme.py
├── data/       moneytrack.db  (banco SQLite)
├── tests/      test_core.py
└── docs/       modelo_er.png · fluxograma_*.png · FUNCIONALIDADES.md ·
                ROTEIRO_APRESENTACAO.md · PERGUNTAS_BANCA.md · gerar_diagramas.py
```

Separação de responsabilidades: **interface** só exibe e coleta dados → **services** validam e aplicam
as regras → **database** executa SQL parametrizado → **analytics** usa Pandas/NumPy para indicadores
e análises → **charts** desenha com Matplotlib.

## Decisões técnicas importantes

- **Saldo nunca é armazenado**: `Saldo = Σ receitas − Σ despesas`, calculado do banco a cada consulta.
- **Precisão monetária**: valores em `Decimal` no Python e em **centavos inteiros** no SQLite
  (colunas `*_cents`). Assim `10 × R$ 0,10 = R$ 1,00` exato.
- **Integridade**: chaves estrangeiras (`ON DELETE RESTRICT`), `CHECK`, `UNIQUE` e *triggers* que
  impedem tipo de movimentação diferente do tipo da categoria.
- **Segurança**: 100% de consultas parametrizadas; coluna de ordenação via lista branca.
- **Metas** são informativas e não alteram o saldo.

## Documentação

[Modelo ER](docs/modelo_er.png) · [Fluxograma geral](docs/fluxograma_sistema.png) ·
[Fluxograma de cadastro](docs/fluxograma_movimentacao.png) · [Funcionalidades](docs/FUNCIONALIDADES.md) ·
[Roteiro da apresentação](docs/ROTEIRO_APRESENTACAO.md) · [Perguntas e respostas](docs/PERGUNTAS_BANCA.md)

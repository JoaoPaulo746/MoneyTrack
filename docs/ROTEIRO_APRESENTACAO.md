# Roteiro de apresentação — 25/11/2026 (≈ 10 a 12 min)

**Preparação (antes da banca):** `python main.py --demo` · tela cheia · conferir que o Dashboard está em "Este mês".

## 1. Introdução (2 min)
- **Apresentar:** "MoneyTrack é uma plataforma de educação e controle financeiro pessoal."
- **Contexto:** muitos jovens começam a vida financeira sem saber para onde o dinheiro vai.
- **Problema:** controle em papel/cabeça falha; planilhas são trabalhosas e não explicam os números.
- **Solução:** registrar movimentações e transformar dados em informação e aprendizado.

## 2. Demonstração (5 min)
1. **Dashboard:** indicadores, gráficos, últimas movimentações, análises. Trocar o período.
2. **Cadastrar receita** (botão "Nova movimentação" → Receita → Freelance, R$ 300,00). Mostrar aviso verde.
3. **Cadastrar despesa** (Lazer, R$ 80,00).
4. **Saldo automático:** voltar ao Dashboard — saldo, receitas e gráficos mudaram. Frisar: *saldo não é guardado, é calculado do banco*.
5. **Categorias:** criar "Pets"; tentar excluir uma categoria com movimentações → mensagem de bloqueio.
6. **Movimentações:** pesquisar "mercado", filtrar por categoria/período, ordenar por valor, editar e excluir (com confirmação).
7. **Gráficos (Relatórios):** os 5 gráficos obrigatórios.
8. **Análises:** ler 2 observações automáticas e mostrar que mudam com os dados. Mostrar a mensagem de "dados insuficientes" no modo real vazio (opcional).
9. **Metas:** criar "Comprar um celular", adicionar valor, mostrar barra e "guarde R$ X por mês". Reforçar: *não altera o saldo*.
10. *(opcional)* **Educação financeira:** reserva de emergência calculada com os gastos reais.
11. **Persistência:** fechar e abrir o programa — dados continuam.

## 3. Explicação técnica (3 min)
- **Python:** linguagem única; código modular em camadas (interface / services / database / models).
- **SQLite:** 3 tabelas (`categories`, `transactions`, `goals`), PK, FK `RESTRICT`, `CHECK`, triggers. Mostrar `docs/modelo_er.png`.
- **CRUD:** `finance_service` → `operations` com SQL parametrizado.
- **Dados:** consulta → DataFrame do **Pandas** → `pivot_table`/`groupby` → indicadores e frases.
- **Gráficos:** **Matplotlib** embutido no CustomTkinter, recriado a cada atualização.
- **Arquitetura:** mostrar `docs/fluxograma_sistema.png`.

## 4. Conclusão (1 min)
- **Benefícios:** simples, offline, visual, educativo.
- **Contribuição:** o usuário entende *por que* gasta, não só *quanto*.
- **Evolução:** orçamento por categoria, despesas recorrentes, importação de extratos (CSV/OFX), backup na nuvem, versão mobile/web, metas vinculadas a aportes.

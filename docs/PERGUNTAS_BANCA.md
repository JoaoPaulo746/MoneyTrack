# Perguntas técnicas prováveis e respostas

**1. Por que SQLite e não MySQL?**
O sistema é local e individual: o SQLite não exige servidor, é um único arquivo, suporta SQL, chaves estrangeiras e transações. Simplicidade e facilidade de demonstração.

**2. Como o saldo é calculado? Ele fica salvo?**
Não. Saldo = soma das receitas − soma das despesas, calculado do banco a cada consulta. Assim nunca fica desatualizado após editar ou excluir.

**3. Por que usar Decimal e centavos?**
`float` gera erros (0,1 + 0,2 = 0,30000000000000004). Usamos `Decimal` no Python e guardamos **inteiros em centavos** no banco: cálculo exato.

**4. Como evitam SQL Injection?**
Todas as consultas usam parâmetros (`?`); o texto digitado nunca é concatenado ao SQL. A única parte dinâmica, a coluna de ordenação, vem de uma lista branca. Há um teste automatizado com `'); DROP TABLE...`.

**5. O que impede dados inválidos?** Duas camadas: `validation_service` (valor > 0, data real, obrigatórios) e o banco (`CHECK`, `NOT NULL`, `FOREIGN KEY`, `UNIQUE`, triggers).

**6. O que acontece ao excluir uma categoria com movimentações?**
É bloqueado: o serviço verifica os vínculos e o banco usa `ON DELETE RESTRICT`. O usuário vê uma mensagem explicando.

**7. Onde está a Ciência de Dados?**
Os dados viram DataFrames do Pandas; usamos `pivot_table`, `groupby`, `cumsum` e NumPy para séries mensais, saldo acumulado, percentuais, variação mês a mês e a categoria que mais cresceu. O módulo `analytics_service` transforma isso em frases, sempre calculadas dos dados reais.

**8. Como funciona a análise "despesas aumentaram X%"?**
`(despesa do mês − despesa do mês anterior) ÷ despesa do mês anterior × 100`. Sem mês anterior ou com menos de 3 registros, o sistema informa que faltam dados.

**9. Como a tela atualiza após cadastrar?**
Cada tela recarrega os dados do banco ao ser exibida, e o Dashboard também se recarrega ao salvar uma movimentação.

**10. Os gráficos usam dados reais?**
Sim, vêm de consultas ao banco. Só o modo demonstração usa dados de exemplo, em outro arquivo (`moneytrack_demo.db`).

**11. Por que as metas não alteram o saldo?**
Meta é um acompanhamento de planejamento; o saldo reflete apenas o que foi registrado como receita/despesa. Evita contabilizar duas vezes.

**12. Como o código está organizado?**
Camadas: interface (exibe) → services (regras) → database (SQL) → models. Isso facilita testar e manter; os 23 testes rodam sem a interface.

**13. Como foi testado?**
`python -m unittest discover -s tests`: CRUD, saldo, filtros, integridade, injeção de SQL, persistência, metas e análises, em banco temporário.

**14. O que há de limitação e como evoluiria?**
É monousuário e local, sem login. Evoluções: orçamento por categoria, despesas recorrentes, importação de extratos, backup em nuvem e versão web/mobile.

**15. Por que CustomTkinter?**
É Python puro, gera visual moderno sobre o Tkinter e dispensa navegador/servidor, mantendo o projeto offline.

# Funcionalidades do MoneyTrack

| Seção | O que faz |
|---|---|
| **Dashboard** | Saldo atual, receitas, despesas, resultado e nº de movimentações do período (Este mês, Mês anterior, Últimos 3 meses, Este ano, Todo o período). Gráficos: receitas × despesas, despesas por categoria, evolução do saldo e comparação de períodos. Listas: últimas movimentações, maiores despesas, resumo mensal (▲ positivo / ▼ negativo), categoria que mais gasta e análises. Botão de nova movimentação com atualização imediata. |
| **Movimentações** | CRUD completo (descrição, valor, tipo, categoria, data, observação). Pesquisa por descrição (ignora maiúsculas/acentos), filtros por tipo, categoria e período, ordenação por data ou valor (crescente/decrescente), duplo clique para editar, confirmação antes de excluir, totais do filtro. |
| **Categorias** | 14 categorias iniciais (5 de receita, 9 de despesa). Criar, editar e excluir categorias personalizadas com cor e ícone. Categoria com movimentações não pode ser excluída nem mudar de tipo. |
| **Relatórios** | 6 indicadores (média mensal de despesas, categoria que mais consome, % da receita comprometida, variação vs. mês anterior, maior despesa, total economizado), análises automáticas em linguagem natural, meses positivos/negativos e os 5 gráficos obrigatórios. Exporta CSV (compatível com Excel). |
| **Metas financeiras** | Nome, valor desejado, acumulado, criação, prazo, % de progresso com barra, quanto falta e quanto guardar por mês. Adicionar valor, editar, excluir. Não alteram o saldo. |
| **Educação financeira** | Conceitos, planejamento (regra 50-30-20), controle de gastos, consumo consciente e reserva de emergência. Calculadoras que usam **seus dados reais** (reserva ideal de 3 a 6 meses; divisão 50-30-20 da sua renda média). |
| **Configurações** | Modo demonstração (banco separado), restaurar demo, apagar dados (dupla confirmação), informações do sistema. |

## Análises automáticas (calculadas dos dados reais)
- "Seus gastos com *alimentação* representam 35% das despesas de *novembro de 2026*."
- "Suas despesas aumentaram 12% em comparação ao mês anterior."
- "Você teve um resultado financeiro positivo…" / "…negativo: você gastou R$ X a mais do que recebeu."
- "X% da sua receita foi comprometida com despesas."
- "A categoria *lazer* apresentou o maior crescimento de gastos (+R$ …)."
- Com menos de 3 registros: mensagem pedindo mais movimentações.

## Validações e segurança
Valor > 0 com no máx. 2 casas (aceita `1.234,56`); campos obrigatórios; datas inexistentes rejeitadas;
categoria compatível com o tipo; erros mostrados no próprio formulário; avisos verde/vermelho após cada
operação; confirmação antes de excluir; SQL parametrizado.

"""Testes automatizados do núcleo do MoneyTrack.

Executar:  python -m unittest discover -s tests -v
Usam um banco temporário: nunca tocam nos dados reais do usuário.
"""
import os
import sys
import tempfile
import unittest
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connection, operations as ops
from database.demo_data import seed_demo_data
from database.schema import initialize_database, wipe_all_data
from services import analytics_service as an
from services import finance_service as fs
from services import validation_service as vs
from services.finance_service import BusinessError
from services.validation_service import ValidationError


def cat_id(name, type_):
    return next(c.id for c in fs.list_categories(type_) if c.name == name)


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        connection.set_database(os.path.join(self.tmp.name, "test.db"))
        initialize_database()

    def tearDown(self):
        connection.set_database(connection.REAL_DB_PATH)
        self.tmp.cleanup()


class TestValidation(unittest.TestCase):
    def test_money_formats(self):
        self.assertEqual(vs.parse_money("1.234,56"), Decimal("1234.56"))
        self.assertEqual(vs.parse_money("1234.56"), Decimal("1234.56"))
        self.assertEqual(vs.parse_money("R$ 10"), Decimal("10.00"))
        self.assertEqual(vs.parse_money("1.234"), Decimal("1234.00"))

    def test_money_invalid(self):
        for bad in ["", "abc", "-5", "0", "10,999", "1e5", "9999999999"]:
            with self.assertRaises(ValidationError, msg=bad):
                vs.parse_money(bad)

    def test_dates(self):
        self.assertEqual(vs.parse_date("25/11/2026"), date(2026, 11, 25))
        for bad in ["31/02/2026", "xx", "", "2026-13-01", "01/01/1990"]:
            with self.assertRaises(ValidationError, msg=bad):
                vs.parse_date(bad)


class TestDatabase(BaseTest):
    def test_default_categories_and_persistence(self):
        self.assertEqual(len(fs.list_categories("receita")), 5)
        self.assertEqual(len(fs.list_categories("despesa")), 9)
        fs.add_transaction("Salário", "1000", "receita", cat_id("Salário", "receita"), "05/11/2026")
        initialize_database()  # "reabrir" o programa não pode apagar nem duplicar nada
        self.assertEqual(len(fs.list_transactions()), 1)
        self.assertEqual(len(fs.list_categories()), 14)

    def test_foreign_keys_and_checks_enforced(self):
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            ops.insert_transaction("x", 100, "despesa", 9999, "2026-01-01")  # categoria inexistente
        with self.assertRaises(sqlite3.IntegrityError):
            ops.insert_transaction("x", -5, "despesa", cat_id("Lazer", "despesa"), "2026-01-01")
        with self.assertRaises(sqlite3.IntegrityError):  # tipo diferente do da categoria (trigger)
            ops.insert_transaction("x", 100, "receita", cat_id("Lazer", "despesa"), "2026-01-01")

    def test_sql_injection_is_harmless(self):
        evil = "x'); DROP TABLE transactions;--"
        fs.add_transaction(evil, "10", "despesa", cat_id("Lazer", "despesa"), "01/11/2026")
        self.assertEqual(len(fs.list_transactions(search="DROP TABLE")), 1)
        self.assertEqual(len(fs.list_transactions(search="' OR 1=1 --")), 0)
        self.assertEqual(len(fs.list_transactions()), 1)  # tabela continua existindo


class TestTransactions(BaseTest):
    def test_crud_and_balance(self):
        sal, ali = cat_id("Salário", "receita"), cat_id("Alimentação", "despesa")
        a = fs.add_transaction("Salário", "2.000,00", "receita", sal, "05/11/2026")
        b = fs.add_transaction("Mercado", "350,75", "despesa", ali, "06/11/2026", "semana")
        self.assertEqual(fs.current_balance(), Decimal("1649.25"))
        fs.update_transaction(b, "Mercado", "400", "despesa", ali, "06/11/2026")
        self.assertEqual(fs.current_balance(), Decimal("1600.00"))
        fs.delete_transaction(a)
        self.assertEqual(fs.current_balance(), Decimal("-400.00"))
        self.assertEqual(fs.summary()["count"], 1)

    def test_decimal_precision(self):
        ali = cat_id("Alimentação", "despesa")
        for _ in range(10):
            fs.add_transaction("Bala", "0,10", "despesa", ali, "01/11/2026")
        self.assertEqual(fs.summary()["expense"], Decimal("1.00"))  # 10 x 0,10 = 1,00 exato

    def test_type_must_match_category(self):
        with self.assertRaises(BusinessError):
            fs.add_transaction("x", "10", "receita", cat_id("Lazer", "despesa"), "01/11/2026")

    def test_invalid_inputs_rejected(self):
        lazer = cat_id("Lazer", "despesa")
        for args in [("", "10", "despesa", lazer, "01/11/2026"),
                     ("x", "-10", "despesa", lazer, "01/11/2026"),
                     ("x", "10", "despesa", lazer, "32/11/2026"),
                     ("x", "10", "despesa", None, "01/11/2026"),
                     ("x", "10", "outro", lazer, "01/11/2026")]:
            with self.assertRaises(ValidationError):
                fs.add_transaction(*args)
        self.assertEqual(len(fs.list_transactions()), 0)

    def test_filters_and_sorting(self):
        sal, ali, laz = cat_id("Salário", "receita"), cat_id("Alimentação", "despesa"), cat_id("Lazer", "despesa")
        fs.add_transaction("Salário", "1000", "receita", sal, "01/10/2026")
        fs.add_transaction("Pizza", "50", "despesa", ali, "10/10/2026")
        fs.add_transaction("Cinema", "30", "despesa", laz, "20/10/2026")
        fs.add_transaction("Ração", "80", "despesa", ali, "05/11/2026")
        self.assertEqual(len(fs.list_transactions(type_="despesa")), 3)
        self.assertEqual(len(fs.list_transactions(category_id=ali)), 2)
        self.assertEqual(len(fs.list_transactions(search="pizza")), 1)
        self.assertEqual(len(fs.list_transactions(search="RAÇÃO")), 1)   # acento + maiúscula
        self.assertEqual(len(fs.list_transactions(date_from="2026-10-05", date_to="2026-10-31")), 2)
        by_value = fs.list_transactions(order_by="amount", descending=True)
        self.assertEqual(by_value[0].description, "Salário")
        by_date = fs.list_transactions(order_by="date", descending=False)
        self.assertEqual(by_date[0].description, "Salário")
        self.assertEqual(len(fs.list_transactions(search="50%")), 0)     # '%' é literal

    def test_period_totals(self):
        sal, ali = cat_id("Salário", "receita"), cat_id("Alimentação", "despesa")
        fs.add_transaction("S", "1000", "receita", sal, "05/10/2026")
        fs.add_transaction("M", "100", "despesa", ali, "05/11/2026")
        s = fs.summary("2026-11-01", "2026-11-30")
        self.assertEqual((s["income"], s["expense"], s["result"]), (Decimal(0), Decimal(100), Decimal(-100)))
        self.assertEqual(fs.current_balance(), Decimal("900.00"))


class TestCategories(BaseTest):
    def test_custom_crud(self):
        cid = fs.create_category("Pets", "despesa", "#ff00aa", "🐶")
        fs.update_category(cid, "Animais", "despesa", "#00FF00", "🐕")
        self.assertEqual(next(c for c in fs.list_categories() if c.id == cid).name, "Animais")
        fs.delete_category(cid)
        self.assertFalse(any(c.id == cid for c in fs.list_categories()))

    def test_duplicate_and_invalid(self):
        with self.assertRaises(BusinessError):
            fs.create_category("Lazer", "despesa", "#000000", "")
        fs.create_category("Lazer", "receita", "#000000", "")  # mesmo nome, tipo diferente: ok
        with self.assertRaises(ValidationError):
            fs.create_category("X", "despesa", "vermelho", "")

    def test_cannot_delete_or_retype_linked_category(self):
        laz = cat_id("Lazer", "despesa")
        fs.add_transaction("Cinema", "30", "despesa", laz, "20/10/2026")
        with self.assertRaises(BusinessError):
            fs.delete_category(laz)
        with self.assertRaises(BusinessError):
            fs.update_category(laz, "Lazer", "receita", "#000000", "")


class TestGoals(BaseTest):
    def test_goals_do_not_change_balance(self):
        fs.add_transaction("S", "1000", "receita", cat_id("Salário", "receita"), "05/11/2026")
        gid = fs.create_goal("Notebook", "3000", "500", "")
        goal = fs.add_to_goal(gid, "250,50")
        self.assertEqual(goal.current, Decimal("750.50"))
        self.assertAlmostEqual(goal.progress, 25.0167, places=2)
        self.assertEqual(fs.current_balance(), Decimal("1000.00"))  # saldo intacto
        fs.update_goal(gid, "Notebook novo", "3000", "3000", "")
        self.assertTrue(fs.list_goals()[0].completed)
        fs.delete_goal(gid)
        self.assertEqual(fs.list_goals(), [])

    def test_goal_validation(self):
        with self.assertRaises(ValidationError):
            fs.create_goal("", "100", "0", "")
        with self.assertRaises(ValidationError):
            fs.create_goal("Viagem", "0", "0", "")
        with self.assertRaises(ValidationError):
            fs.create_goal("Viagem", "100", "0", "01/01/2020")  # prazo no passado


class TestAnalytics(BaseTest):
    def test_insufficient_data_message(self):
        fs.add_transaction("S", "100", "receita", cat_id("Salário", "receita"), "05/11/2026")
        insights = an.generate_insights(an.load_dataframe())
        self.assertEqual(len(insights), 1)
        self.assertIn("não há dados suficientes", insights[0].text)

    def test_insights_values(self):
        sal, ali, laz = cat_id("Salário", "receita"), cat_id("Alimentação", "despesa"), cat_id("Lazer", "despesa")
        fs.add_transaction("S", "2000", "receita", sal, "05/10/2026")
        fs.add_transaction("Mercado", "100", "despesa", ali, "10/10/2026")
        fs.add_transaction("Cinema", "100", "despesa", laz, "11/10/2026")
        fs.add_transaction("S", "2000", "receita", sal, "05/11/2026")
        fs.add_transaction("Mercado", "210", "despesa", ali, "10/11/2026")   # 70% de 300
        fs.add_transaction("Cinema", "90", "despesa", laz, "11/11/2026")     # total 300 vs 200 = +50%
        df = an.load_dataframe()
        text = " ".join(i.text for i in an.generate_insights(df, today=date(2026, 11, 20)))
        self.assertIn("alimentação representam 70% das despesas de novembro de 2026", text)
        self.assertIn("aumentaram 50%", text)
        self.assertIn("resultado financeiro positivo", text)
        self.assertIn("maior crescimento de gastos", text)
        self.assertIn("alimentação", text.split("maior crescimento")[0].split(".")[-1].lower())

    def test_indicators_and_series(self):
        sal, ali = cat_id("Salário", "receita"), cat_id("Alimentação", "despesa")
        fs.add_transaction("S", "1000", "receita", sal, "05/10/2026")
        fs.add_transaction("A", "200", "despesa", ali, "06/10/2026")
        fs.add_transaction("B", "400", "despesa", ali, "06/12/2026")
        df = an.load_dataframe()
        monthly = an.monthly_summary(df)
        self.assertEqual(list(monthly.index), ["2026-10", "2026-11", "2026-12"])  # mês vazio incluído
        self.assertEqual(int(monthly.loc["2026-10", "resultado"]), 80000)
        self.assertEqual(int(monthly["acumulado"].iloc[-1]), 40000)
        ind = an.indicators(df, df, today=date(2026, 12, 10))
        self.assertEqual(ind["saved"], Decimal("400.00"))
        self.assertEqual(ind["biggest_expense"]["description"], "B")
        self.assertAlmostEqual(ind["committed_percent"], 60.0)
        self.assertEqual(ind["avg_monthly_expense"], Decimal("200.00"))
        self.assertEqual(int(an.daily_balance(df).iloc[-1]), 40000)

    def test_empty_database_is_safe(self):
        df = an.load_dataframe()
        self.assertTrue(an.monthly_summary(df).empty)
        self.assertTrue(an.expenses_by_category(df).empty)
        self.assertIsNone(an.period_comparison(df))
        self.assertIsNone(an.indicators(df, df)["top_category"])
        self.assertTrue(an.category_month_comparison(df).empty)


class TestDemoAndPeriods(BaseTest):
    def test_demo_seed_and_wipe(self):
        seed_demo_data()
        self.assertGreater(len(fs.list_transactions()), 30)
        self.assertEqual(len(fs.list_goals()), 3)
        df = an.load_dataframe()
        self.assertGreater(len(an.generate_insights(df)), 2)
        wipe_all_data()
        self.assertEqual(len(fs.list_transactions()), 0)
        self.assertEqual(len(fs.list_categories()), 14)

    def test_period_ranges(self):
        t = date(2026, 1, 15)
        self.assertEqual(fs.period_range("Este mês", t), ("2026-01-01", "2026-01-31"))
        self.assertEqual(fs.period_range("Mês anterior", t), ("2025-12-01", "2025-12-31"))
        self.assertEqual(fs.period_range("Últimos 3 meses", t), ("2025-11-01", "2026-01-31"))
        self.assertEqual(fs.period_range("Todo o período", t), (None, None))


if __name__ == "__main__":
    unittest.main()

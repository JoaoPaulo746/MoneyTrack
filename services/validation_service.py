"""Validações de entrada. Nada inválido chega ao banco de dados."""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from models.category import TYPES
from models.money import CENT

MAX_AMOUNT = Decimal("999999999.99")


class ValidationError(Exception):
    """Erro de validação com mensagem amigável para o usuário."""


def parse_money(text, field="Valor", allow_zero=False) -> Decimal:
    """Converte texto ('1.234,56', '1234.56', 'R$ 10') em Decimal positivo com 2 casas."""
    raw = str(text or "").strip().replace("R$", "").replace(" ", "")
    if not raw:
        raise ValidationError(f"Informe o campo {field.lower()}.")
    if raw.startswith("-"):
        raise ValidationError(f"{field} não pode ser negativo.")
    if "," in raw:                      # formato brasileiro: 1.234,56
        raw = raw.replace(".", "").replace(",", ".")
    elif raw.count(".") > 1:            # 1.234.567
        raw = raw.replace(".", "")
    elif "." in raw:                    # '1.234' = mil; '12.5' = decimal
        inteiro, frac = raw.split(".")
        if len(frac) == 3:
            raw = inteiro + frac
    if not re.fullmatch(r"\d+(\.\d+)?", raw):
        raise ValidationError(f"{field} inválido. Use apenas números, por exemplo 1.250,90.")
    try:
        value = Decimal(raw)
    except InvalidOperation:
        raise ValidationError(f"{field} inválido.")
    if value.as_tuple().exponent < -2:
        raise ValidationError(f"{field} deve ter no máximo 2 casas decimais.")
    if value == 0 and not allow_zero:
        raise ValidationError(f"{field} deve ser maior que zero.")
    if value > MAX_AMOUNT:
        raise ValidationError(f"{field} muito alto (máximo R$ 999.999.999,99).")
    return value.quantize(CENT)


def parse_date(text, field="Data") -> date:
    """Aceita DD/MM/AAAA ou AAAA-MM-DD e rejeita datas inexistentes."""
    raw = str(text or "").strip()
    if not raw:
        raise ValidationError(f"Informe a {field.lower()}.")
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(raw, fmt).date()
            break
        except ValueError:
            continue
    else:
        raise ValidationError(f"{field} inválida. Use o formato DD/MM/AAAA.")
    if not (2000 <= parsed.year <= 2100):
        raise ValidationError(f"{field} fora do intervalo permitido (2000 a 2100).")
    return parsed


def iso_to_br(iso: Optional[str]) -> str:
    """'2026-11-25' -> '25/11/2026'."""
    if not iso:
        return ""
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"


def _required_text(value, field, max_len) -> str:
    text = " ".join(str(value or "").split())  # remove espaços duplicados
    if not text:
        raise ValidationError(f"O campo {field.lower()} é obrigatório.")
    if len(text) > max_len:
        raise ValidationError(f"{field} deve ter no máximo {max_len} caracteres.")
    return text


def validate_transaction(description, amount_text, type_, category_id, date_text, notes="") -> dict:
    if type_ not in TYPES:
        raise ValidationError("Selecione o tipo: receita ou despesa.")
    clean_notes = str(notes or "").strip()
    if len(clean_notes) > 300:
        raise ValidationError("A observação deve ter no máximo 300 caracteres.")
    if not category_id:
        raise ValidationError("Selecione uma categoria.")
    return {
        "description": _required_text(description, "Descrição", 100),
        "amount": parse_money(amount_text),
        "type": type_,
        "category_id": int(category_id),
        "transaction_date": parse_date(date_text).isoformat(),
        "notes": clean_notes,
    }


def validate_category(name, type_, color, icon) -> dict:
    if type_ not in TYPES:
        raise ValidationError("Selecione o tipo da categoria.")
    color = str(color or "").strip()
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
        raise ValidationError("Cor inválida. Use o formato #RRGGBB, por exemplo #16A34A.")
    icon = str(icon or "").strip()
    if len(icon) > 4:
        raise ValidationError("O ícone deve ter no máximo 4 caracteres.")
    return {"name": _required_text(name, "Nome", 30), "type": type_,
            "color": color.upper(), "icon": icon}


def validate_goal(name, target_text, current_text, deadline_text, check_future=True) -> dict:
    target = parse_money(target_text, "Valor desejado")
    current = parse_money(current_text or "0", "Valor acumulado", allow_zero=True)
    deadline = None
    if str(deadline_text or "").strip():
        parsed = parse_date(deadline_text, "Prazo")
        if check_future and parsed < date.today():
            raise ValidationError("O prazo não pode estar no passado.")
        deadline = parsed.isoformat()
    return {"name": _required_text(name, "Nome da meta", 60), "target": target,
            "current": current, "deadline": deadline}

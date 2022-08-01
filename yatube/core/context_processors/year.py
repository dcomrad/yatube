from datetime import date


def year(_):
    """Добавляет переменную с текущим годом."""
    return {
        'year': date.today().year,
    }

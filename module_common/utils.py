import jdatetime


def to_jalali_date(value):
    """تبدیل datetime یا date میلادی به رشته جلالی، فقط تاریخ بدون ساعت"""
    if value is None:
        return '-'
    if hasattr(value, 'date'):
        value = value.date()
    jalali = jdatetime.date.fromgregorian(date=value)
    return jalali.strftime('%Y/%m/%d')
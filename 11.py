import tkinter as tk
from tkinter import ttk, messagebook
import json
import os
from datetime import datetime

# ------------------------ ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ------------------------
DATA_FILE = "expenses.json"            # файл для хранения данных

expenses = []                          # все расходы (список словарей)
filtered_expenses = []                 # отфильтрованные расходы для отображения

# Виджеты, к которым нужен доступ из разных функций
tree = None
status_var = None

# Поля ввода (добавление)
amount_entry = None
category_combo = None
date_entry = None

# Поля фильтров
filter_category = None
date_from_entry = None
date_to_entry = None


def load_data():
    """Загружает расходы из JSON-файла"""
    global expenses
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                expenses = json.load(f)
        except:
            expenses = []
    else:
        expenses = []

def save_data():
    """Сохраняет расходы в JSON-файл"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(expenses, f, ensure_ascii=False, indent=4)

# ------------------------ ОТОБРАЖЕНИЕ ТАБЛИЦЫ ------------------------
def update_display():
    """Обновляет таблицу на основе filtered_expenses"""
    # Очищаем таблицу
    for row in tree.get_children():
        tree.delete(row)
    # Заполняем
    for idx, exp in enumerate(filtered_expenses, start=1):
        tree.insert('', tk.END, values=(idx, exp['amount'], exp['category'], exp['date']))
    # Обновляем статусную строку
    total = sum(exp['amount'] for exp in filtered_expenses)
    status_var.set(f"Показано: {len(filtered_expenses)} | Сумма отфильтрованных: {total:.2f}")

# ------------------------ ДОБАВЛЕНИЕ РАСХОДА ------------------------
def add_expense():
    """Обрабатывает ввод и добавляет новый расход"""
    global expenses

    # 1. Проверка суммы
    try:
        amount = float(amount_entry.get())
        if amount <= 0:
            messagebox.showerror("Ошибка", "Сумма должна быть положительным числом.")
            return
    except ValueError:
        messagebox.showerror("Ошибка", "Введите корректную сумму (число).")
        return

    # 2. Категория
    category = category_combo.get().strip()
    if not category:
        messagebox.showerror("Ошибка", "Введите или выберите категорию.")
        return

    # 3. Дата
    date_str = date_entry.get().strip()
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Ошибка", "Дата должна быть в формате ГГГГ-ММ-ДД (пример: 2025-04-25).")
        return

    # Генерируем новый ID
    new_id = max([e['id'] for e in expenses], default=0) + 1
    expense = {
        'id': new_id,
        'amount': amount,
        'category': category,
        'date': date_str
    }
    expenses.append(expense)
    save_data()

    # Применяем текущие фильтры (чтобы таблица обновилась)
    apply_filter()

    # Очищаем поля ввода, но дату ставим сегодняшнюю
    amount_entry.delete(0, tk.END)
    category_combo.set('')
    date_entry.delete(0, tk.END)
    date_entry.insert(0, datetime.today().strftime("%Y-%m-%d"))

    status_var.set(f"Добавлен расход: {amount} ({category})")

# ------------------------ ФИЛЬТРАЦИЯ ------------------------
def apply_filter():
    """Фильтрует expenses по выбранной категории и диапазону дат, сохраняет в filtered_expenses и обновляет таблицу"""
    global filtered_expenses

    cat = filter_category.get()
    date_from_str = date_from_entry.get().strip()
    date_to_str = date_to_entry.get().strip()

    filtered = expenses[:]      # начинаем со всех

    # Фильтр по категории
    if cat != 'Все':
        filtered = [e for e in filtered if e['category'] == cat]

    # Фильтр по дате "от"
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, "%Y-%m-%d")

filtered = [e for e in filtered if datetime.strptime(e['date'], "%Y-%m-%d") >= date_from]
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты 'от' (ГГГГ-ММ-ДД).")
            return

    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, "%Y-%m-%d")
            filtered = [e for e in filtered if datetime.strptime(e['date'], "%Y-%m-%d") <= date_to]
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты 'до' (ГГГГ-ММ-ДД).")
            return

    filtered_expenses = filtered
    update_display()

def clear_filter():
    """Сбрасывает все фильтры в исходное состояние"""
    filter_category.set('Все')
    date_from_entry.delete(0, tk.END)
    date_to_entry.delete(0, tk.END)
    apply_filter()

# ------------------------ УДАЛЕНИЕ ЗАПИСИ ------------------------
def delete_selected():
    """Удаляет выбранную в таблице запись (из expenses и из файла)"""
    global expenses
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Внимание", "Не выбрана запись для удаления.")
        return

    # Получаем № строки в отфильтрованном списке
    item_values = tree.item(selected[0])['values']
    idx_in_filtered = int(item_values[0]) - 1   # первый столбец - порядковый номер
    if 0 <= idx_in_filtered < len(filtered_expenses):
        expense_id = filtered_expenses[idx_in_filtered]['id']
        confirm = messagebox.askyesno("Подтверждение", f"Удалить расход с ID {expense_id}?")
        if confirm:
            expenses = [e for e in expenses if e['id'] != expense_id]
            save_data()
            apply_filter()   # обновляет filtered_expenses и таблицу
            status_var.set(f"Запись ID {expense_id} удалена.")

# ------------------------ ПОДСЧЁТ СУММЫ ЗА ПЕРИОД ------------------------
def calc_sum_period():
    """Рассчитывает сумму расходов за период, указанный в полях фильтра"""
    date_from_str = date_from_entry.get().strip()
    date_to_str = date_to_entry.get().strip()
    if not date_from_str or not date_to_str:
        messagebox.showwarning("Внимание", "Укажите обе даты (от и до) для подсчёта суммы.")
        return
    try:
        date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
        date_to = datetime.strptime(date_to_str, "%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД.")
        return

    total = 0
    for e in expenses:
        e_date = datetime.strptime(e['date'], "%Y-%m-%d")
        if date_from <= e_date <= date_to:
            total += e['amount']
    messagebox.showinfo("Сумма за период", f"Общая сумма расходов с {date_from_str} по {date_to_str}: {total:.2f}")

# ------------------------ ПОСТРОЕНИЕ GUI ------------------------
def build_gui():
    global tree, status_var, amount_entry, category_combo, date_entry
    global filter_category, date_from_entry, date_to_entry

    root = tk.Tk()
    root.title("Expense Tracker")
    root.geometry("900x600")
    root.resizable(True, True)

    # ----- Блок добавления -----
    input_frame = ttk.LabelFrame(root, text="Добавить расход", padding=10)
    input_frame.pack(fill="x", padx=10, pady=5)

    ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    amount_entry = ttk.Entry(input_frame, width=15)
    amount_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(input_frame, text="Категория:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
    category_combo = ttk.Combobox(input_frame, width=15)
    category_combo['values'] = ('Еда', 'Транспорт', 'Развлечения', 'Здоровье', 'Дом', 'Другое')
    category_combo.grid(row=0, column=3, padx=5, pady=5)

    ttk.Label(input_frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=4, padx=5, pady=5, sticky="e")
    date_entry = ttk.Entry(input_frame, width=12)
    date_entry.grid(row=0, column=5, padx=5, pady=5)

date_entry.insert(0, datetime.today().strftime("%Y-%m-%d"))

    add_btn = ttk.Button(input_frame, text="Добавить расход", command=add_expense)
    add_btn.grid(row=0, column=6, padx=10, pady=5)

    # ----- Блок фильтров -----
    filter_frame = ttk.LabelFrame(root, text="Фильтры", padding=10)
    filter_frame.pack(fill="x", padx=10, pady=5)

    ttk.Label(filter_frame, text="Категория:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    filter_category = ttk.Combobox(filter_frame, width=15)
    filter_category['values'] = ('Все', 'Еда', 'Транспорт', 'Развлечения', 'Здоровье', 'Дом', 'Другое')
    filter_category.set('Все')
    filter_category.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(filter_frame, text="Дата от:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
    date_from_entry = ttk.Entry(filter_frame, width=12)
    date_from_entry.grid(row=0, column=3, padx=5, pady=5)

    ttk.Label(filter_frame, text="Дата до:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
    date_to_entry = ttk.Entry(filter_frame, width=12)
    date_to_entry.grid(row=0, column=5, padx=5, pady=5)

    filter_btn = ttk.Button(filter_frame, text="Применить фильтр", command=apply_filter)
    filter_btn.grid(row=0, column=6, padx=5, pady=5)

    clear_btn = ttk.Button(filter_frame, text="Сбросить фильтр", command=clear_filter)
    clear_btn.grid(row=0, column=7, padx=5, pady=5)

    sum_btn = ttk.Button(filter_frame, text="Подсчитать сумму за период (из фильтра)", command=calc_sum_period)
    sum_btn.grid(row=1, column=0, columnspan=8, pady=5)

    # ----- Таблица расходов -----
    table_frame = ttk.LabelFrame(root, text="Список расходов", padding=10)
    table_frame.pack(fill="both", expand=True, padx=10, pady=5)

    columns = ('num', 'amount', 'category', 'date')
    tree = ttk.Treeview(table_frame, columns=columns, show='headings')
    tree.heading('num', text='№')
    tree.heading('amount', text='Сумма')
    tree.heading('category', text='Категория')
    tree.heading('date', text='Дата')
    tree.column('num', width=50, anchor='center')
    tree.column('amount', width=120, anchor='e')
    tree.column('category', width=150)
    tree.column('date', width=120, anchor='center')
    tree.pack(side='left', fill='both', expand=True)

    scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
    scrollbar.pack(side='right', fill='y')
    tree.configure(yscrollcommand=scrollbar.set)

    # ----- Кнопка удаления -----
    del_btn = ttk.Button(root, text="Удалить выбранную запись", command=delete_selected)
    del_btn.pack(pady=5)

    # ----- Статусная строка -----
    status_var = tk.StringVar()
    status_bar = ttk.Label(root, textvariable=status_var, relief=tk.SUNKEN, anchor=tk.W)
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    return root

# ------------------------ ЗАПУСК ------------------------
def main():
    global filtered_expenses
    load_data()
    # Изначально filtered_expenses = всем расходам
    filtered_expenses = expenses[:]
    root = build_gui()
    update_display()
    root.mainloop()

if __name__ == "__main__":
    main()







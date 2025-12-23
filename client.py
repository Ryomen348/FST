# client.py - полная версия с админ-панелью
import tkinter as tk
from tkinter import ttk, messagebox
import json
import socket
import threading
from datetime import datetime, timedelta
import os
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class FaceItOnlineTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("FaceIt Online Scoreboard")
        self.root.geometry("1400x900")
        self.root.configure(bg="white")
        
        # Настройки сервера
        self.server_host = "26.90.218.164"
        self.server_port = 5555
        self.socket = None
        self.connected = False
        self.current_user = None
        self.current_role = None
        
        # Локальные данные
        self.local_data_file = "faceit_local.json"
        
        # Уровни FaceIt
        self.levels = {
            1: {"min_elo": 0, "max_elo": 500, "color": "#808080"},
            2: {"min_elo": 501, "max_elo": 750, "color": "#006400"},
            3: {"min_elo": 751, "max_elo": 900, "color": "#006400"},
            4: {"min_elo": 901, "max_elo": 1050, "color": "#00008B"},
            5: {"min_elo": 1051, "max_elo": 1200, "color": "#00008B"},
            6: {"min_elo": 1201, "max_elo": 1350, "color": "#800080"},
            7: {"min_elo": 1351, "max_elo": 1530, "color": "#800080"},
            8: {"min_elo": 1531, "max_elo": 1750, "color": "#FFD700"},
            9: {"min_elo": 1751, "max_elo": 2000, "color": "#FFD700"},
            10: {"min_elo": 2001, "max_elo": 10000, "color": "#FF4500"}
        }
        
        # Локальные данные
        self.load_local_data()
        
        # Установка стилей
        self.setup_styles()
        
        # Подключение к серверу
        self.connect_to_server()
        
        # Создание интерфейса
        self.create_interface()
        
    def setup_styles(self):
        """Настройка стилей для белой темы"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Основные стили
        style.configure('TFrame', background='white')
        style.configure('TLabel', background='white', foreground='black')
        style.configure('TLabelframe', background='white', foreground='black')
        style.configure('TLabelframe.Label', background='white', foreground='black')
        
        # Кнопки
        style.configure('TButton', background='#4CAF50', foreground='white')
        style.map('TButton', 
                 background=[('active', '#45a049')],
                 foreground=[('active', 'white')])
        
        style.configure('Primary.TButton', background='#2196F3', foreground='white')
        style.map('Primary.TButton',
                 background=[('active', '#1976D2')])
        
        style.configure('Danger.TButton', background='#f44336', foreground='white')
        style.map('Danger.TButton',
                 background=[('active', '#d32f2f')])
        
        style.configure('Warning.TButton', background='#ff9800', foreground='white')
        style.map('Warning.TButton',
                 background=[('active', '#f57c00')])
        
        style.configure('Success.TButton', background='#4CAF50', foreground='white')
        
        # Вкладки
        style.configure('TNotebook', background='white')
        style.configure('TNotebook.Tab', background='#f0f0f0', foreground='black')
        style.map('TNotebook.Tab',
                 background=[('selected', '#2196F3')],
                 foreground=[('selected', 'white')])
        
        # Treeview (таблицы)
        style.configure('Treeview',
                       background='white',
                       foreground='black',
                       fieldbackground='white')
        style.map('Treeview',
                 background=[('selected', '#2196F3')],
                 foreground=[('selected', 'white')])
        
    def load_local_data(self):
        """Загрузка локальных данных"""
        if os.path.exists(self.local_data_file):
            try:
                with open(self.local_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.local_stats = data
            except:
                self.local_stats = self.get_default_stats()
        else:
            self.local_stats = self.get_default_stats()
    
    def get_default_stats(self):
        """Статистика по умолчанию"""
        return {
            "elo": 1050,
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "matches": 0,
            "avg_kd": 0.0,
            "avg_hs": 0.0,
            "win_percentage": 0.0,
            "total_kills": 0,
            "total_deaths": 0,
            "avg_kills": 0.0,
            "match_history": [],
            "match_details": []
        }
    
    def save_local_data(self):
        """Сохранение локальных данных"""
        try:
            with open(self.local_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.local_stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения локальных данных: {e}")
    
    def connect_to_server(self):
        """Подключение к серверу"""
        def connect():
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.server_host, self.server_port))
                self.connected = True
                
                # Тестовый запрос
                response = self.send_request({'action': 'ping'})
                if response and isinstance(response, dict) and response.get('success'):
                    print("[*] Успешно подключено к серверу")
                else:
                    self.connected = False
                    print("[!] Ошибка подключения к серверу")
                    
            except Exception as e:
                self.connected = False
                print(f"[!] Ошибка подключения: {e}")
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=connect)
        thread.daemon = True
        thread.start()
    
    def send_request(self, data, timeout=5):
        """Отправка запроса на сервер"""
        if not self.connected:
            return None
            
        try:
            self.socket.settimeout(timeout)
            self.socket.send(json.dumps(data).encode('utf-8'))
            
            response = self.socket.recv(65536).decode('utf-8')
            return json.loads(response)
            
        except Exception as e:
            print(f"Ошибка отправки запроса: {e}")
            self.connected = False
            return None
    
    def create_interface(self):
        """Создание интерфейса"""
        # Верхняя панель с подключением
        self.create_connection_panel()
        
        # Вкладки
        self.create_tabs()
        
    def create_connection_panel(self):
        """Создание панели подключения"""
        connection_frame = ttk.Frame(self.root, padding=10)
        connection_frame.pack(fill=tk.X)
        
        # Статус подключения
        self.status_var = tk.StringVar(value="Отключено")
        status_label = ttk.Label(connection_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=5)
        
        # Индикатор статуса
        self.status_indicator = tk.Label(connection_frame, text="●", font=("Arial", 14))
        self.status_indicator.pack(side=tk.LEFT, padx=5)
        self.update_connection_status()
        
        # Кнопка переподключения
        reconnect_btn = ttk.Button(connection_frame, text="Переподключиться", 
                                   command=self.reconnect)
        reconnect_btn.pack(side=tk.LEFT, padx=5)
        
        # Поле для ника (если не авторизован)
        self.nickname_var = tk.StringVar()
        nickname_entry = ttk.Entry(connection_frame, textvariable=self.nickname_var, width=20)
        nickname_entry.pack(side=tk.LEFT, padx=5)
        
        # Поле для пароля
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(connection_frame, textvariable=self.password_var, 
                                   show="*", width=15)
        password_entry.pack(side=tk.LEFT, padx=5)
        
        # Кнопки регистрации/входа
        register_btn = ttk.Button(connection_frame, text="Регистрация", 
                                  command=self.register)
        register_btn.pack(side=tk.LEFT, padx=5)
        
        login_btn = ttk.Button(connection_frame, text="Вход", 
                               command=self.login, style="Primary.TButton")
        login_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка выхода
        logout_btn = ttk.Button(connection_frame, text="Выход", 
                                command=self.logout, style="Danger.TButton")
        logout_btn.pack(side=tk.LEFT, padx=5)
        
        # Информация о текущем пользователе
        self.user_info_var = tk.StringVar(value="Гость")
        user_label = ttk.Label(connection_frame, textvariable=self.user_info_var)
        user_label.pack(side=tk.RIGHT, padx=10)
    
    def create_tabs(self):
        """Создание вкладок"""
        tab_control = ttk.Notebook(self.root)
        
        # Создаем вкладки
        self.stats_tab = ttk.Frame(tab_control)
        self.scoreboard_tab = ttk.Frame(tab_control)
        self.history_tab = ttk.Frame(tab_control)
        self.match_tab = ttk.Frame(tab_control)
        self.seasons_tab = ttk.Frame(tab_control)
        self.premium_tab = ttk.Frame(tab_control)
        self.chat_tab = ttk.Frame(tab_control)
        self.tournaments_tab = ttk.Frame(tab_control)
        
        tab_control.add(self.stats_tab, text="📊 Моя статистика")
        tab_control.add(self.scoreboard_tab, text="🏆 Скорборд")
        tab_control.add(self.history_tab, text="📋 История")
        tab_control.add(self.match_tab, text="🎮 Новый матч")
        tab_control.add(self.seasons_tab, text="🎯 Сезоны")
        tab_control.add(self.premium_tab, text="⭐ Премиум")
        tab_control.add(self.chat_tab, text="💬 Чаты")
        tab_control.add(self.tournaments_tab, text="🏅 Турниры")
        
        tab_control.pack(expand=1, fill="both")
        
        # Создание содержимого вкладок
        self.create_stats_tab()
        self.create_scoreboard_tab()
        self.create_history_tab()
        self.create_match_tab()
        self.create_seasons_tab()
        self.create_premium_tab()
        self.create_chat_tab()
        self.create_tournaments_tab()
        
        # Обновляем данные
        self.update_display()
    
    def create_stats_tab(self):
        """Создание вкладки статистики"""
        container = ttk.Frame(self.stats_tab, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        header = ttk.Label(container, text="Моя статистика", 
                          font=("Arial", 20, "bold"))
        header.pack(pady=(0, 20))
        
        # Основная информация
        info_frame = ttk.LabelFrame(container, text="Основная информация", padding=15)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Уровень и ELO
        level_frame = ttk.Frame(info_frame)
        level_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(level_frame, text="Уровень:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.level_var = tk.StringVar()
        ttk.Label(level_frame, textvariable=self.level_var, 
                 font=("Arial", 12, "bold"), foreground="#2196F3").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(level_frame, text="ELO:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(20, 0))
        self.elo_var = tk.StringVar()
        ttk.Label(level_frame, textvariable=self.elo_var, 
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
        
        # Статистика в две колонки
        stats_frame = ttk.Frame(info_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Левая колонка
        left_col = ttk.Frame(stats_frame)
        left_col.grid(row=0, column=0, padx=(0, 20), sticky=tk.N)
        
        stats_left = [
            ("Матчей сыграно:", "matches_var"),
            ("Побед:", "wins_var"),
            ("Поражений:", "losses_var"),
            ("Ничьих:", "ties_var"),
            ("Процент побед:", "win_perc_var")
        ]
        
        for i, (label, var_name) in enumerate(stats_left):
            ttk.Label(left_col, text=label, font=("Arial", 10)).grid(
                row=i, column=0, sticky=tk.W, pady=3)
            setattr(self, var_name, tk.StringVar())
            ttk.Label(left_col, textvariable=getattr(self, var_name), 
                     font=("Arial", 10, "bold")).grid(row=i, column=1, sticky=tk.W, pady=3, padx=(10, 0))
        
        # Правая колонка
        right_col = ttk.Frame(stats_frame)
        right_col.grid(row=0, column=1, sticky=tk.N)
        
        stats_right = [
            ("K/D:", "kd_var"),
            ("HS%:", "hs_var"),
            ("Убийств:", "kills_var"),
            ("Смертей:", "deaths_var"),
            ("AVG убийств:", "avg_kills_var")
        ]
        
        for i, (label, var_name) in enumerate(stats_right):
            ttk.Label(right_col, text=label, font=("Arial", 10)).grid(
                row=i, column=0, sticky=tk.W, pady=3)
            setattr(self, var_name, tk.StringVar())
            ttk.Label(right_col, textvariable=getattr(self, var_name), 
                     font=("Arial", 10, "bold")).grid(row=i, column=1, sticky=tk.W, pady=3, padx=(10, 0))
        
        # Кнопки синхронизации
        sync_frame = ttk.Frame(container)
        sync_frame.pack(pady=20)
        
        ttk.Button(sync_frame, text="🔄 Синхронизировать с сервером", 
                  command=self.sync_with_server).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(sync_frame, text="💾 Сохранить локально", 
                  command=self.save_local_data).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(sync_frame, text="📤 Загрузить с сервера", 
                  command=self.load_from_server).pack(side=tk.LEFT, padx=5)
        
        # График ELO (будет создан после авторизации)
        self.elo_chart_frame = None
        
        # Кнопка просмотра детального профиля (будет показана после авторизации)
        self.profile_button = None
    
    def create_scoreboard_tab(self):
        """Создание вкладки скорборда"""
        container = ttk.Frame(self.scoreboard_tab, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок и управление
        header_frame = ttk.Frame(container)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="Онлайн скорборд", 
                 font=("Arial", 20, "bold")).pack(side=tk.LEFT)
        
        # Фильтры
        filter_frame = ttk.Frame(header_frame)
        filter_frame.pack(side=tk.RIGHT)
        
        ttk.Label(filter_frame, text="Сортировать по:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.sort_var = tk.StringVar(value="elo")
        sort_combo = ttk.Combobox(filter_frame, textvariable=self.sort_var,
                                 values=["elo", "wins", "win_percentage", "avg_kd", "avg_kills"],
                                 state="readonly", width=15)
        sort_combo.pack(side=tk.LEFT, padx=(0, 10))
        sort_combo.bind("<<ComboboxSelected>>", self.update_scoreboard)
        
        ttk.Button(filter_frame, text="Обновить", 
                  command=self.update_scoreboard).pack(side=tk.LEFT)
        
        # Таблица лидеров
        table_frame = ttk.Frame(container)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создание Treeview
        columns = ("#", "Игрок", "Уровень", "ELO", "Победы", "Поражения", 
                  "Винрейт", "K/D", "HS%", "AVG убийств")
        
        self.scoreboard_tree = ttk.Treeview(table_frame, columns=columns, 
                                           show="headings", height=25)
        
        # Настройка колонок
        column_config = [
            ("#", 50, "center"),
            ("Игрок", 150, "center"),
            ("Уровень", 80, "center"),
            ("ELO", 80, "center"),
            ("Победы", 80, "center"),
            ("Поражения", 80, "center"),
            ("Винрейт", 80, "center"),
            ("K/D", 80, "center"),
            ("HS%", 80, "center"),
            ("AVG убийств", 100, "center")
        ]
        
        for col, width, anchor in column_config:
            self.scoreboard_tree.heading(col, text=col)
            self.scoreboard_tree.column(col, width=width, anchor=anchor)
        
        # Добавляем прокрутку
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", 
                                 command=self.scoreboard_tree.yview)
        self.scoreboard_tree.configure(yscrollcommand=scrollbar.set)
        
        self.scoreboard_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Обработчик двойного клика для просмотра профиля
        self.scoreboard_tree.bind("<Double-1>", self.on_player_double_click)
        
        # Кнопки под таблицей
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Экспорт в CSV", 
                  command=self.export_scoreboard).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Сравнить с игроком", 
                  command=self.compare_with_player).pack(side=tk.LEFT, padx=5)
    
    def create_history_tab(self):
        """Создание вкладки истории"""
        container = ttk.Frame(self.history_tab, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        ttk.Label(container, text="История матчей", 
                 font=("Arial", 20, "bold")).pack(pady=(0, 20))
        
        # Таблица истории
        table_frame = ttk.Frame(container)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("#", "Результат", "ELO", "ΔELO", "Убийства", "Смерти", 
                  "K/D", "HS%", "Карта", "Дата")
        
        self.history_tree = ttk.Treeview(table_frame, columns=columns, 
                                        show="headings", height=20)
        
        # Настройка колонок
        column_config = [
            ("#", 50, "center"),
            ("Результат", 100, "center"),
            ("ELO", 80, "center"),
            ("ΔELO", 80, "center"),
            ("Убийства", 80, "center"),
            ("Смерти", 80, "center"),
            ("K/D", 80, "center"),
            ("HS%", 80, "center"),
            ("Карта", 120, "center"),
            ("Дата", 120, "center")
        ]
        
        for col, width, anchor in column_config:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=width, anchor=anchor)
        
        # Прокрутка
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                 command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_match_tab(self):
        """Создание вкладки нового матча"""
        container = ttk.Frame(self.match_tab, padding=30)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        ttk.Label(container, text="Добавить новый матч", 
                 font=("Arial", 20, "bold")).pack(pady=(0, 30))
        
        # Форма ввода
        form_frame = ttk.Frame(container)
        form_frame.pack(expand=True)
        
        # Результат
        ttk.Label(form_frame, text="Результат:", font=("Arial", 12)).grid(
            row=0, column=0, sticky=tk.W, pady=15, padx=(0, 20))
        
        self.match_result_var = tk.StringVar()
        result_combo = ttk.Combobox(form_frame, textvariable=self.match_result_var,
                                   values=["Победа", "Поражение", "Ничья"],
                                   state="readonly", width=15, font=("Arial", 12))
        result_combo.grid(row=0, column=1, pady=15)
        
        # Убийства
        ttk.Label(form_frame, text="Убийства:", font=("Arial", 12)).grid(
            row=1, column=0, sticky=tk.W, pady=15, padx=(0, 20))
        
        self.match_kills_var = tk.StringVar()
        kills_entry = ttk.Entry(form_frame, textvariable=self.match_kills_var,
                               width=10, font=("Arial", 12))
        kills_entry.grid(row=1, column=1, pady=15)
        
        # Смерти
        ttk.Label(form_frame, text="Смерти:", font=("Arial", 12)).grid(
            row=2, column=0, sticky=tk.W, pady=15, padx=(0, 20))
        
        self.match_deaths_var = tk.StringVar()
        deaths_entry = ttk.Entry(form_frame, textvariable=self.match_deaths_var,
                                width=10, font=("Arial", 12))
        deaths_entry.grid(row=2, column=1, pady=15)
        
        # HS%
        ttk.Label(form_frame, text="HS%:", font=("Arial", 12)).grid(
            row=3, column=0, sticky=tk.W, pady=15, padx=(0, 20))
        
        self.match_hs_var = tk.StringVar()
        hs_entry = ttk.Entry(form_frame, textvariable=self.match_hs_var,
                            width=10, font=("Arial", 12))
        hs_entry.grid(row=3, column=1, pady=15)
        
        # Карта
        ttk.Label(form_frame, text="Карта:", font=("Arial", 12)).grid(
            row=4, column=0, sticky=tk.W, pady=15, padx=(0, 20))
        
        self.match_map_var = tk.StringVar()
        maps = ["Mirage", "Dust II", "Inferno", "Nuke", "Overpass", 
                "Vertigo", "Ancient", "Anubis", "Cache", "Train"]
        map_combo = ttk.Combobox(form_frame, textvariable=self.match_map_var,
                                values=maps, state="readonly", width=15, font=("Arial", 12))
        map_combo.grid(row=4, column=1, pady=15)
        
        # Кнопка добавления
        add_button = ttk.Button(container, text="✅ Добавить матч", 
                               command=self.add_match_online,
                               style="Primary.TButton", width=20)
        add_button.pack(pady=30)
        
        # Статус добавления
        self.add_status_var = tk.StringVar()
        status_label = ttk.Label(container, textvariable=self.add_status_var,
                                font=("Arial", 10))
        status_label.pack()
    
    def update_connection_status(self):
        """Обновление статуса подключения"""
        if self.connected:
            self.status_var.set("Подключено")
            self.status_indicator.config(foreground="green")
        else:
            self.status_var.set("Отключено")
            self.status_indicator.config(foreground="red")
        
        # Обновляем каждые 5 секунд
        self.root.after(5000, self.update_connection_status)
    
    def reconnect(self):
        """Переподключение к серверу"""
        self.connected = False
        self.update_connection_status()
        self.connect_to_server()
        
        # Ждем немного и обновляем статус
        self.root.after(1000, self.update_connection_status)
    
    def register(self):
        """Регистрация нового пользователя"""
        nickname = self.nickname_var.get().strip()
        password = self.password_var.get().strip()
        
        if not nickname or not password:
            messagebox.showerror("Ошибка", "Введите ник и пароль")
            return
        
        if not self.connected:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
            return
        
        response = self.send_request({
            'action': 'register',
            'nickname': nickname,
            'password': password,
            'email': ''  # Отправляем пустой email, так как он не обязателен
        })
        
        if response and isinstance(response, dict):
            if response.get('success'):
                messagebox.showinfo("Успех", response.get('message', 'Регистрация успешна!'))
                self.current_user = nickname
                self.current_role = 'player'
                self.user_info_var.set(f"Игрок: {nickname}")
            else:
                messagebox.showerror("Ошибка", response.get('message', 'Ошибка регистрации'))
        else:
            messagebox.showerror("Ошибка", "Нет ответа от сервера")
    
    def login(self):
        """Вход пользователя"""
        nickname = self.nickname_var.get().strip()
        password = self.password_var.get().strip()
        
        if not nickname or not password:
            messagebox.showerror("Ошибка", "Введите ник и пароль")
            return
        
        if not self.connected:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
            return
        
        response = self.send_request({
            'action': 'login',
            'nickname': nickname,
            'password': password
        })
        
        if response and isinstance(response, dict):
            if response.get('success'):
                messagebox.showinfo("Успех", response.get('message', 'Вход выполнен!'))
                self.current_user = nickname
                self.current_role = response.get('role', 'player')
                
                role_text = {
                    'admin': 'Админ',
                    'moderator': 'Модератор',
                    'player': 'Игрок'
                }.get(self.current_role, 'Игрок')
                
                self.user_info_var.set(f"{role_text}: {nickname}")
                
                # Добавляем админ-панель если нужно
                if self.current_role in ['admin', 'moderator']:
                    self.add_admin_tab()
                
                # Добавляем график ELO и кнопку профиля
                self.add_stats_analytics()
                
            else:
                messagebox.showerror("Ошибка", response.get('message', 'Ошибка входа'))
        else:
            messagebox.showerror("Ошибка", "Нет ответа от сервера")
    
    def add_admin_tab(self):
        """Добавление админ-панели"""
        # Получаем текущий notebook
        notebook = self.root.winfo_children()[1]  # Первый child после connection_frame
        
        # Создаем админ-панель
        self.admin_tab = ttk.Frame(notebook)
        notebook.add(self.admin_tab, text="🛡️ Админ-панель")
        
        # Создаем содержимое админ-панели
        self.create_admin_tab_content()
    
    def create_admin_tab_content(self):
        """Создание содержимого админ-панели"""
        container = ttk.Frame(self.admin_tab, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок с ролью
        role_color = "#FF0000" if self.current_role == 'admin' else "#FF9800"
        role_text = "Администратор" if self.current_role == 'admin' else "Модератор"
        
        header_frame = ttk.Frame(container)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text=f"🛡️ {role_text} Панель", 
                 font=("Arial", 20, "bold")).pack(side=tk.LEFT)
        
        ttk.Button(header_frame, text="Обновить все", 
                  command=self.update_admin_panel,
                  style="Primary.TButton").pack(side=tk.RIGHT)
        
        # Простой интерфейс админ-панели
        admin_frame = ttk.LabelFrame(container, text="Быстрые действия", padding=15)
        admin_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Кнопки для админов
        if self.current_role == 'admin':
            ttk.Button(admin_frame, text="👥 Управление игроками", 
                      command=self.show_player_management,
                      width=25).pack(pady=10)
            
            ttk.Button(admin_frame, text="🛠️ Изменить роль игрока", 
                      command=self.show_change_role_dialog,
                      width=25).pack(pady=10)
            
            ttk.Button(admin_frame, text="➕ Создать модератора", 
                      command=self.create_moderator_dialog,
                      width=25).pack(pady=10)
            
            ttk.Button(admin_frame, text="🎯 Создать сезон", 
                      command=self.show_create_season_dialog,
                      width=25).pack(pady=10)
            
            ttk.Button(admin_frame, text="🏅 Создать турнир", 
                      command=self.show_create_tournament_dialog,
                      width=25).pack(pady=10)
        
        # Кнопки для админов и модераторов
        ttk.Button(admin_frame, text="⭐ Выдать премиум", 
                  command=self.show_grant_premium_dialog,
                  style="Warning.TButton", width=25).pack(pady=10)
        
        ttk.Button(admin_frame, text="🚫 Забанить игрока", 
                  command=self.show_ban_dialog,
                  style="Danger.TButton", width=25).pack(pady=10)
        
        ttk.Button(admin_frame, text="✅ Разбанить игрока", 
                  command=self.show_unban_dialog,
                  style="Success.TButton", width=25).pack(pady=10)
        
        ttk.Button(admin_frame, text="🎮 Управление матчами", 
                  command=self.show_match_management,
                  width=25).pack(pady=10)
        
        ttk.Button(admin_frame, text="📊 Статистика сервера", 
                  command=self.show_server_stats,
                  width=25).pack(pady=10)
    
    def show_player_management(self):
        """Показать управление игроками"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Управление игроками")
        dialog.geometry("800x500")
        dialog.transient(self.root)
        
        ttk.Label(dialog, text="Список игроков", 
                 font=("Arial", 16, "bold")).pack(pady=20)
        
        # Получаем список игроков
        response = self.send_request({
            'action': 'admin_get_players',
            'nickname': self.current_user,
            'limit': 50,
            'offset': 0
        })
        
        if response and response.get('success'):
            players = response.get('players', [])
            
            # Создаем таблицу
            table_frame = ttk.Frame(dialog)
            table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Treeview
            columns = ("Ник", "ELO", "Роль", "Матчи", "Бан")
            tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
            
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=150, anchor="center")
            
            # Добавляем игроков
            for player in players:
                ban_status = "✅" if not player.get('is_banned') else "❌"
                role_icon = {
                    'admin': '🛡️',
                    'moderator': '👮',
                    'player': '👤'
                }.get(player.get('role', 'player'), '👤')
                
                tree.insert("", "end", values=(
                    player.get('nickname', ''),
                    player.get('elo', 0),
                    f"{role_icon} {player.get('role', 'player')}",
                    player.get('matches', 0),
                    ban_status
                ))
            
            scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def show_change_role_dialog(self):
        """Диалог изменения роли"""
        if self.current_role != 'admin':
            messagebox.showerror("Ошибка", "Только для администраторов")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Изменение роли игрока")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Изменение роли игрока", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        
        ttk.Label(dialog, text="Никнейм игрока:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        nickname_var = tk.StringVar()
        nickname_entry = ttk.Entry(dialog, textvariable=nickname_var, width=30)
        nickname_entry.pack(padx=20, pady=(5, 10))
        
        ttk.Label(dialog, text="Новая роль:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        role_var = tk.StringVar(value="player")
        role_combo = ttk.Combobox(dialog, textvariable=role_var,
                                 values=["player", "moderator", "admin"],
                                 state="readonly", width=15)
        role_combo.pack(padx=20, pady=(5, 10))
        
        def apply_role():
            nickname = nickname_var.get().strip()
            if not nickname:
                messagebox.showerror("Ошибка", "Введите никнейм игрока")
                return
            
            response = self.send_request({
                'action': 'admin_change_role',
                'admin_nickname': self.current_user,
                'target_nickname': nickname,
                'new_role': role_var.get()
            })
            
            if response and response.get('success'):
                messagebox.showinfo("Успех", response.get('message', 'Роль изменена'))
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", response.get('message', 'Ошибка изменения роли'))
        
        ttk.Button(dialog, text="Применить", 
                  command=apply_role, style="Primary.TButton").pack(pady=20)
    
    def show_ban_dialog(self):
        """Диалог бана игрока"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Бан игрока")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Бан игрока", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        
        ttk.Label(dialog, text="Никнейм игрока:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        nickname_var = tk.StringVar()
        nickname_entry = ttk.Entry(dialog, textvariable=nickname_var, width=30)
        nickname_entry.pack(padx=20, pady=(5, 10))
        
        ttk.Label(dialog, text="Причина:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        reason_var = tk.StringVar(value="Нарушение правил")
        reason_entry = ttk.Entry(dialog, textvariable=reason_var, width=30)
        reason_entry.pack(padx=20, pady=(5, 10))
        
        ttk.Label(dialog, text="Срок (дней, 0 = навсегда):").pack(anchor=tk.W, padx=20, pady=(10, 0))
        days_var = tk.StringVar(value="7")
        days_entry = ttk.Entry(dialog, textvariable=days_var, width=10)
        days_entry.pack(padx=20, pady=(5, 10))
        
        def apply_ban():
            nickname = nickname_var.get().strip()
            if not nickname:
                messagebox.showerror("Ошибка", "Введите никнейм игрока")
                return
            
            try:
                days = int(days_var.get())
                if days < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректное количество дней")
                return
            
            response = self.send_request({
                'action': 'admin_ban_player',
                'admin_nickname': self.current_user,
                'target_nickname': nickname,
                'reason': reason_var.get(),
                'days': days
            })
            
            if response and response.get('success'):
                messagebox.showinfo("Успех", response.get('message', 'Игрок забанен'))
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", response.get('message', 'Ошибка бана'))
        
        ttk.Button(dialog, text="Забанить", 
                  command=apply_ban, style="Danger.TButton").pack(pady=20)
    
    def show_unban_dialog(self):
        """Диалог разбана игрока"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Разбан игрока")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Разбан игрока", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        
        ttk.Label(dialog, text="Никнейм игрока:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        nickname_var = tk.StringVar()
        nickname_entry = ttk.Entry(dialog, textvariable=nickname_var, width=30)
        nickname_entry.pack(padx=20, pady=(5, 10))
        
        def apply_unban():
            nickname = nickname_var.get().strip()
            if not nickname:
                messagebox.showerror("Ошибка", "Введите никнейм игрока")
                return
            
            response = self.send_request({
                'action': 'admin_unban_player',
                'admin_nickname': self.current_user,
                'target_nickname': nickname
            })
            
            if response and response.get('success'):
                messagebox.showinfo("Успех", response.get('message', 'Игрок разбанен'))
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", response.get('message', 'Ошибка разбана'))
        
        ttk.Button(dialog, text="Разбанить", 
                  command=apply_unban, style="Success.TButton").pack(pady=20)
    
    def show_match_management(self):
        """Показать управление матчами"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Управление матчами")
        dialog.geometry("1000x600")
        dialog.transient(self.root)
        
        ttk.Label(dialog, text="Последние матчи", 
                 font=("Arial", 16, "bold")).pack(pady=20)
        
        # Получаем список матчей
        response = self.send_request({
            'action': 'admin_get_matches',
            'nickname': self.current_user,
            'limit': 30
        })
        
        if response and response.get('success'):
            matches = response.get('matches', [])
            
            # Создаем таблицу
            table_frame = ttk.Frame(dialog)
            table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Treeview
            columns = ("ID", "Игрок", "Результат", "Убийства", "Смерти", "HS%", "Статус")
            tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
            
            column_config = [
                ("ID", 50, "center"),
                ("Игрок", 120, "center"),
                ("Результат", 80, "center"),
                ("Убийства", 80, "center"),
                ("Смерти", 80, "center"),
                ("HS%", 80, "center"),
                ("Статус", 100, "center")
            ]
            
            for col, width, anchor in column_config:
                tree.heading(col, text=col)
                tree.column(col, width=width, anchor=anchor)
            
            # Добавляем матчи
            for match in matches:
                result_icon = {
                    'W': '✅',
                    'L': '❌',
                    'T': '⚫'
                }.get(match.get('result', 'W'), '❓')
                
                status_icon = '✅' if match.get('is_verified') else '❓'
                
                tree.insert("", "end", values=(
                    match.get('id', ''),
                    match.get('player', ''),
                    f"{result_icon} {match.get('result', '')}",
                    match.get('kills', 0),
                    match.get('deaths', 0),
                    f"{match.get('hs_percentage', 0):.1f}%",
                    status_icon
                ))
            
            scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Контекстное меню
            menu = tk.Menu(dialog, tearoff=0)
            
            def verify_selected():
                selection = tree.selection()
                if selection:
                    item = selection[0]
                    values = tree.item(item)['values']
                    match_id = values[0]
                    
                    response = self.send_request({
                        'action': 'admin_verify_match',
                        'admin_nickname': self.current_user,
                        'match_id': match_id,
                        'verify': True
                    })
                    
                    if response and response.get('success'):
                        messagebox.showinfo("Успех", "Матч подтвержден")
                        tree.set(item, "Статус", "✅")
            
            def unverify_selected():
                selection = tree.selection()
                if selection:
                    item = selection[0]
                    values = tree.item(item)['values']
                    match_id = values[0]
                    
                    response = self.send_request({
                        'action': 'admin_verify_match',
                        'admin_nickname': self.current_user,
                        'match_id': match_id,
                        'verify': False
                    })
                    
                    if response and response.get('success'):
                        messagebox.showinfo("Успех", "Матч отклонен")
                        tree.set(item, "Статус", "❓")
            
            def delete_selected():
                selection = tree.selection()
                if selection:
                    item = selection[0]
                    values = tree.item(item)['values']
                    match_id = values[0]
                    
                    # Подтверждение удаления
                    if not messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить матч #{match_id}?"):
                        return
                    
                    response = self.send_request({
                        'action': 'admin_delete_match',
                        'admin_nickname': self.current_user,
                        'match_id': match_id
                    })
                    
                    if response and response.get('success'):
                        messagebox.showinfo("Успех", "Матч удален")
                        tree.delete(item)
                    else:
                        messagebox.showerror("Ошибка", response.get('message', 'Ошибка удаления матча'))
            
            menu.add_command(label="Подтвердить матч", command=verify_selected)
            menu.add_command(label="Отклонить матч", command=unverify_selected)
            menu.add_command(label="Удалить матч", command=delete_selected)
            
            def show_context_menu(event):
                item = tree.identify_row(event.y)
                if item:
                    tree.selection_set(item)
                    menu.post(event.x_root, event.y_root)
            
            tree.bind("<Button-3>", show_context_menu)
    
    def show_server_stats(self):
        """Показать статистику сервера"""
        response = self.send_request({
            'action': 'admin_get_stats',
            'nickname': self.current_user
        })
        
        if response and response.get('success'):
            stats = response.get('stats', {})
            
            dialog = tk.Toplevel(self.root)
            dialog.title("Статистика сервера")
            dialog.geometry("500x400")
            dialog.transient(self.root)
            
            ttk.Label(dialog, text="Статистика сервера", 
                     font=("Arial", 16, "bold")).pack(pady=20)
            
            # Создаем текстовое поле
            text = tk.Text(dialog, wrap=tk.WORD, font=("Arial", 10))
            text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            stats_text = f"""📊 Статистика сервера:

👥 Игроки:
  Всего игроков: {stats.get('total_players', 0)}
  Активных игроков: {stats.get('active_players', 0)}
  Забаненных игроков: {stats.get('banned_players', 0)}

🎮 Матчи:
  Всего матчей: {stats.get('total_matches', 0)}
  Непроверенных матчей: {stats.get('unverified_matches', 0)}

👑 Распределение по ролям:"""
            
            # Добавляем распределение по ролям
            roles_dist = stats.get('roles_distribution', {})
            for role, count in roles_dist.items():
                role_name = {
                    'admin': 'Администраторы',
                    'moderator': 'Модераторы',
                    'player': 'Игроки'
                }.get(role, role)
                stats_text += f"\n  {role_name}: {count}"
            
            text.insert(1.0, stats_text)
            text.config(state=tk.DISABLED)
    
    def create_moderator_dialog(self):
        """Диалог создания модератора"""
        if self.current_role != 'admin':
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Создание модератора")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Создание нового модератора", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        
        ttk.Label(dialog, text="Никнейм:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        nickname_var = tk.StringVar()
        nickname_entry = ttk.Entry(dialog, textvariable=nickname_var, width=30)
        nickname_entry.pack(padx=20, pady=(5, 10))
        
        ttk.Label(dialog, text="Пароль:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        password_var = tk.StringVar()
        password_entry = ttk.Entry(dialog, textvariable=password_var, show="*", width=30)
        password_entry.pack(padx=20, pady=(5, 10))
        
        def create_mod():
            nickname = nickname_var.get().strip()
            password = password_var.get().strip()
            
            if not nickname or not password:
                messagebox.showerror("Ошибка", "Заполните все поля")
                return
            
            # Сначала регистрируем игрока
            response = self.send_request({
                'action': 'register',
                'nickname': nickname,
                'password': password
            })
            
            if response and response.get('success'):
                # Затем назначаем роль модератора
                role_response = self.send_request({
                    'action': 'admin_change_role',
                    'admin_nickname': self.current_user,
                    'target_nickname': nickname,
                    'new_role': 'moderator'
                })
                
                if role_response and role_response.get('success'):
                    messagebox.showinfo("Успех", f"Модератор {nickname} создан!")
                    dialog.destroy()
                else:
                    messagebox.showerror("Ошибка", "Не удалось назначить роль модератора")
            else:
                messagebox.showerror("Ошибка", response.get('message', 'Ошибка регистрации'))
        
        ttk.Button(dialog, text="Создать", 
                  command=create_mod, style="Success.TButton").pack(pady=20)
    
    def show_create_season_dialog(self):
        """Диалог создания сезона"""
        if self.current_role != 'admin':
            messagebox.showerror("Ошибка", "Только для администраторов")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Создание сезона")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Создание нового сезона", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        
        ttk.Label(dialog, text="Название сезона:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=40).pack(padx=20, pady=(5, 10))
        
        ttk.Label(dialog, text="Дата начала (YYYY-MM-DD HH:MM):").pack(anchor=tk.W, padx=20, pady=(10, 0))
        start_date_var = tk.StringVar()
        start_entry = ttk.Entry(dialog, textvariable=start_date_var, width=40)
        start_entry.pack(padx=20, pady=(5, 10))
        start_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        ttk.Label(dialog, text="Дата окончания (YYYY-MM-DD HH:MM):").pack(anchor=tk.W, padx=20, pady=(10, 0))
        end_date_var = tk.StringVar()
        end_entry = ttk.Entry(dialog, textvariable=end_date_var, width=40)
        end_entry.pack(padx=20, pady=(5, 10))
        end_entry.insert(0, (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M"))
        
        ttk.Label(dialog, text="Премиум награда (дней):").pack(anchor=tk.W, padx=20, pady=(10, 0))
        premium_reward_var = tk.StringVar(value="7")
        ttk.Entry(dialog, textvariable=premium_reward_var, width=10).pack(padx=20, pady=(5, 10))
        
        def create_season():
            name = name_var.get().strip()
            start_date = start_date_var.get().strip()
            end_date = end_date_var.get().strip()
            
            if not all([name, start_date, end_date]):
                messagebox.showerror("Ошибка", "Заполните все поля")
                return
            
            try:
                premium_reward = int(premium_reward_var.get()) if premium_reward_var.get() else 0
            except ValueError:
                messagebox.showerror("Ошибка", "Премиум награда должна быть числом")
                return
            
            response = self.send_request({
                'action': 'create_season',
                'admin_nickname': self.current_user,
                'name': name,
                'start_date': start_date,
                'end_date': end_date,
                'premium_reward': premium_reward
            })
            
            if response and response.get('success'):
                messagebox.showinfo("Успех", response.get('message', 'Сезон создан!'))
                dialog.destroy()
                # Обновляем список сезонов если открыта вкладка
                if hasattr(self, 'seasons_tree'):
                    self.update_seasons()
            else:
                messagebox.showerror("Ошибка", response.get('message', 'Ошибка создания сезона'))
        
        ttk.Button(dialog, text="Создать сезон", 
                  command=create_season, style="Success.TButton").pack(pady=20)
    
    def show_grant_premium_dialog(self):
        """Диалог выдачи премиума"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Выдача премиума")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Выдача премиум статуса", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        
        ttk.Label(dialog, text="Никнейм игрока:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        nickname_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=nickname_var, width=30).pack(padx=20, pady=(5, 10))
        
        ttk.Label(dialog, text="Количество дней:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        days_var = tk.StringVar(value="30")
        ttk.Entry(dialog, textvariable=days_var, width=10).pack(padx=20, pady=(5, 10))
        
        ttk.Label(dialog, text="Источник:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        source_var = tk.StringVar(value="gift")
        source_combo = ttk.Combobox(dialog, textvariable=source_var,
                                   values=["gift", "season", "purchase"],
                                   state="readonly", width=15)
        source_combo.pack(padx=20, pady=(5, 10))
        
        def grant_premium():
            nickname = nickname_var.get().strip()
            if not nickname:
                messagebox.showerror("Ошибка", "Введите никнейм игрока")
                return
            
            try:
                days = int(days_var.get())
                if days <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректное количество дней")
                return
            
            response = self.send_request({
                'action': 'grant_premium',
                'admin_nickname': self.current_user,
                'nickname': nickname,
                'days': days,
                'source': source_var.get()
            })
            
            if response and response.get('success'):
                messagebox.showinfo("Успех", response.get('message', 'Премиум выдан!'))
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", response.get('message', 'Ошибка выдачи премиума'))
        
        ttk.Button(dialog, text="Выдать премиум", 
                  command=grant_premium, style="Warning.TButton").pack(pady=20)
    
    def show_create_tournament_dialog(self):
        """Диалог создания турнира"""
        if self.current_role not in ['admin', 'moderator']:
            messagebox.showerror("Ошибка", "Недостаточно прав")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Создание турнира")
        dialog.geometry("500x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Создание нового турнира", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        
        ttk.Label(dialog, text="Название турнира:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=40).pack(padx=20, pady=(5, 10))
        
        ttk.Label(dialog, text="Описание:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        description_var = tk.StringVar()
        description_entry = tk.Text(dialog, width=40, height=4)
        description_entry.pack(padx=20, pady=(5, 10))
        
        ttk.Label(dialog, text="Дата начала (YYYY-MM-DD HH:MM):").pack(anchor=tk.W, padx=20, pady=(10, 0))
        start_date_var = tk.StringVar()
        start_entry = ttk.Entry(dialog, textvariable=start_date_var, width=40)
        start_entry.pack(padx=20, pady=(5, 10))
        start_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        ttk.Label(dialog, text="Дата окончания (YYYY-MM-DD HH:MM):").pack(anchor=tk.W, padx=20, pady=(10, 0))
        end_date_var = tk.StringVar()
        end_entry = ttk.Entry(dialog, textvariable=end_date_var, width=40)
        end_entry.pack(padx=20, pady=(5, 10))
        end_entry.insert(0, (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M"))
        
        ttk.Label(dialog, text="Максимум участников:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        max_players_var = tk.StringVar(value="16")
        ttk.Entry(dialog, textvariable=max_players_var, width=10).pack(padx=20, pady=(5, 10))
        
        ttk.Label(dialog, text="Призовой фонд:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        prize_pool_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=prize_pool_var, width=40).pack(padx=20, pady=(5, 10))
        
        def create_tournament():
            name = name_var.get().strip()
            description = description_entry.get(1.0, tk.END).strip()
            start_date = start_date_var.get().strip()
            end_date = end_date_var.get().strip()
            
            if not all([name, start_date, end_date]):
                messagebox.showerror("Ошибка", "Заполните обязательные поля")
                return
            
            try:
                max_players = int(max_players_var.get()) if max_players_var.get() else 16
            except ValueError:
                messagebox.showerror("Ошибка", "Максимум участников должен быть числом")
                return
            
            prize_pool = prize_pool_var.get().strip()
            
            response = self.send_request({
                'action': 'create_tournament',
                'admin_nickname': self.current_user,
                'name': name,
                'description': description,
                'start_date': start_date,
                'end_date': end_date,
                'max_players': max_players,
                'prize_pool': prize_pool
            })
            
            if response and response.get('success'):
                messagebox.showinfo("Успех", response.get('message', 'Турнир создан!'))
                dialog.destroy()
                if hasattr(self, 'tournaments_tree'):
                    self.update_tournaments()
            else:
                messagebox.showerror("Ошибка", response.get('message', 'Ошибка создания турнира'))
        
        ttk.Button(dialog, text="Создать турнир", 
                  command=create_tournament, style="Success.TButton").pack(pady=20)
    
    def update_admin_panel(self):
        """Обновление админ-панели"""
        # Эта функция просто показывает сообщение
        messagebox.showinfo("Обновление", "Админ-панель обновлена")
    
    def logout(self):
        """Выход пользователя"""
        self.current_user = None
        self.current_role = None
        self.user_info_var.set("Гость")
        
        # Удаляем админ-панель если она есть
        notebook = self.root.winfo_children()[1]
        for tab_id in notebook.tabs():
            if "🛡️ Админ-панель" in notebook.tab(tab_id, "text"):
                notebook.forget(tab_id)
                break
        
        messagebox.showinfo("Выход", "Вы вышли из системы")
    
    def get_current_level(self):
        """Определение текущего уровня по ELO"""
        elo = self.local_stats.get('elo', 1050)
        for level, data in self.levels.items():
            if data["min_elo"] <= elo <= data["max_elo"]:
                return level
        return 1
    
    def get_random_elo_change(self, result='W'):
        """Случайное изменение ELO"""
        import random
        
        if result == 'W':
            # За победу: от 9 до 25 ELO
            return random.randint(9, 25)
        elif result == 'L':
            # За поражение: от 25 до 35 ELO
            return random.randint(25, 35)
        else:
            # Ничья: 0 ELO
            return 0
    
    def update_display(self):
        """Обновление отображения статистики"""
        if not self.current_user:
            return
            
        # Обновляем переменные
        level = self.get_current_level()
        self.level_var.set(f"{level}")
        self.elo_var.set(f"{self.local_stats.get('elo', 0)}")
        
        self.matches_var.set(f"{self.local_stats.get('matches', 0)}")
        self.wins_var.set(f"{self.local_stats.get('wins', 0)}")
        self.losses_var.set(f"{self.local_stats.get('losses', 0)}")
        self.ties_var.set(f"{self.local_stats.get('ties', 0)}")
        self.win_perc_var.set(f"{self.local_stats.get('win_percentage', 0)}%")
        
        self.kd_var.set(f"{self.local_stats.get('avg_kd', 0):.2f}")
        self.hs_var.set(f"{self.local_stats.get('avg_hs', 0):.1f}%")
        self.kills_var.set(f"{self.local_stats.get('total_kills', 0)}")
        self.deaths_var.set(f"{self.local_stats.get('total_deaths', 0)}")
        self.avg_kills_var.set(f"{self.local_stats.get('avg_kills', 0):.1f}")
        
        # Обновляем историю
        self.update_history_display()
        
        # Обновляем график ELO если доступен
        if MATPLOTLIB_AVAILABLE and hasattr(self, 'elo_chart_frame') and self.elo_chart_frame:
            self.update_elo_chart()
    
    def update_history_display(self):
        """Обновление отображения истории"""
        # Очищаем таблицу
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Добавляем матчи
        match_details = self.local_stats.get('match_details', [])
        for i, match in enumerate(reversed(match_details[-50:]), 1):
            result_text = "Победа ✅" if match.get('result') == 'W' else \
                         "Поражение ❌" if match.get('result') == 'L' else "Ничья ⚫"
            
            elo_change = match.get('elo_change', 0)
            elo_change_text = f"+{elo_change}" if match.get('result') == 'W' else \
                             f"-{elo_change}" if match.get('result') == 'L' else "0"
            
            self.history_tree.insert("", "end", values=(
                i,
                result_text,
                match.get('elo_after', 0),
                elo_change_text,
                match.get('kills', 0),
                match.get('deaths', 0),
                f"{match.get('kd', 0):.2f}",
                f"{match.get('hs', 0):.1f}%",
                match.get('map', 'N/A'),
                match.get('date', 'N/A')
            ))
    
    def update_scoreboard(self, event=None):
        """Обновление скорборда"""
        if not self.connected:
            messagebox.showinfo("Информация", "Нет подключения к серверу")
            return
        
        # Очищаем таблицу
        for item in self.scoreboard_tree.get_children():
            self.scoreboard_tree.delete(item)
        
        # Получаем данные с сервера
        response = self.send_request({
            'action': 'get_leaderboard',
            'sort_by': self.sort_var.get(),
            'limit': 100
        })
        
        if not response:
            messagebox.showerror("Ошибка", "Нет ответа от сервера")
            return
        
        # Обработка ответа
        if isinstance(response, dict) and response.get('success'):
            leaderboard = response.get('leaderboard', [])
        elif isinstance(response, list):
            # Если сервер возвращает список напрямую
            leaderboard = response
        else:
            messagebox.showerror("Ошибка", "Не удалось загрузить скорборд")
            return
        
        # Добавляем данные в таблицу
        for i, player in enumerate(leaderboard, 1):
            # Получаем данные игрока
            if isinstance(player, dict):
                nickname = player.get('nickname', 'Unknown')
                elo = player.get('elo', 0)
                wins = player.get('wins', 0)
                losses = player.get('losses', 0)
                win_percentage = player.get('win_percentage', 0)
                avg_kd = player.get('avg_kd', 0)
                avg_hs = player.get('avg_hs', 0)
                avg_kills = player.get('avg_kills', 0)
            else:
                # Если это не словарь, пропускаем
                continue
            
            # Определяем уровень
            level = 1
            for lvl, data in self.levels.items():
                if data["min_elo"] <= elo <= data["max_elo"]:
                    level = lvl
                    break
            
            # Форматируем данные
            win_rate = f"{win_percentage:.1f}%"
            kd = f"{avg_kd:.2f}"
            hs = f"{avg_hs:.1f}%"
            avg_kills_fmt = f"{avg_kills:.1f}"
            
            # Вставляем строку
            self.scoreboard_tree.insert("", "end", values=(
                i,
                nickname,
                level,
                elo,
                wins,
                losses,
                win_rate,
                kd,
                hs,
                avg_kills_fmt
            ))
    
    def sync_with_server(self):
        """Синхронизация с сервером"""
        if not self.current_user:
            messagebox.showerror("Ошибка", "Сначала войдите в систему")
            return
        
        if not self.connected:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
            return
        
        # Отправляем статистику на сервер
        response = self.send_request({
            'action': 'update_stats',
            'nickname': self.current_user,
            'stats': self.local_stats
        })
        
        if response:
            if isinstance(response, list):
                if len(response) >= 2 and response[0]:
                    messagebox.showinfo("Успех", "Статистика синхронизирована с сервером")
                elif len(response) >= 2:
                    messagebox.showerror("Ошибка", response[1])
            elif isinstance(response, dict):
                if response.get('success'):
                    messagebox.showinfo("Успех", "Статистика синхронизирована с сервером")
                else:
                    messagebox.showerror("Ошибка", "Ошибка синхронизации")
        else:
            messagebox.showerror("Ошибка", "Нет ответа от сервера")
    
    def load_from_server(self):
        """Загрузка статистики с сервера"""
        if not self.current_user:
            messagebox.showerror("Ошибка", "Сначала войдите в систему")
            return
        
        if not self.connected:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
            return
        
        response = self.send_request({
            'action': 'get_stats',
            'nickname': self.current_user
        })
        
        if response:
            if isinstance(response, dict) and response.get('success'):
                server_stats = response.get('stats')
                if server_stats:
                    # Обновляем локальную статистику
                    for key in self.local_stats:
                        if key in server_stats:
                            self.local_stats[key] = server_stats[key]
                    
                    self.save_local_data()
                    self.update_display()
                    messagebox.showinfo("Успех", "Статистика загружена с сервера")
                else:
                    messagebox.showinfo("Информация", "Статистика на сервере не найдена")
            elif isinstance(response, list):
                # Если сервер возвращает список со статистикой
                if response and isinstance(response[0], dict):
                    server_stats = response[0]
                    # Обновляем локальную статистику
                    for key in self.local_stats:
                        if key in server_stats:
                            self.local_stats[key] = server_stats[key]
                    
                    self.save_local_data()
                    self.update_display()
                    messagebox.showinfo("Успех", "Статистика загружена с сервера")
                else:
                    messagebox.showinfo("Информация", "Статистика на сервере не найдена")
            else:
                messagebox.showerror("Ошибка", "Не удалось загрузить статистику")
        else:
            messagebox.showerror("Ошибка", "Нет ответа от сервера")
    
    def add_match_online(self):
        """Добавление матча с синхронизацией на сервер"""
        try:
            # Проверяем вход
            if not self.current_user:
                messagebox.showerror("Ошибка", "Сначала войдите в систему")
                return
            
            # Проверяем данные
            result = self.match_result_var.get()
            kills = int(self.match_kills_var.get())
            deaths = int(self.match_deaths_var.get())
            hs = float(self.match_hs_var.get())
            map_name = self.match_map_var.get()
            
            if not all([result, map_name]):
                raise ValueError("Заполните все поля")
            
            if kills < 0 or deaths < 0:
                raise ValueError("Количество убийств и смертей не может быть отрицательным")
            
            if not 0 <= hs <= 100:
                raise ValueError("HS% должен быть от 0 до 100")
            
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
            return
        
        # Локальные расчеты
        kd_ratio = round(kills / deaths if deaths > 0 else kills, 2)
        old_elo = self.local_stats.get('elo', 1050)
        
        # Обновляем локальную статистику
        result_char = "W" if result == "Победа" else "L" if result == "Поражение" else "T"
        
        # Получаем изменение ELO в зависимости от результата
        elo_change = self.get_random_elo_change(result_char)
        
        if result_char == "W":
            self.local_stats['wins'] = self.local_stats.get('wins', 0) + 1
            self.local_stats['elo'] = self.local_stats.get('elo', 1050) + elo_change
        elif result_char == "L":
            self.local_stats['losses'] = self.local_stats.get('losses', 0) + 1
            self.local_stats['elo'] = self.local_stats.get('elo', 1050) - elo_change
        else:
            self.local_stats['ties'] = self.local_stats.get('ties', 0) + 1
            elo_change = 0
        
        self.local_stats['matches'] = self.local_stats.get('matches', 0) + 1
        
        # Обновляем общую статистику
        self.local_stats['total_kills'] = self.local_stats.get('total_kills', 0) + kills
        self.local_stats['total_deaths'] = self.local_stats.get('total_deaths', 0) + deaths
        
        # Пересчитываем средние значения
        old_matches = self.local_stats['matches'] - 1
        self.local_stats['avg_kd'] = round(
            (self.local_stats.get('avg_kd', 0) * old_matches + kd_ratio) / self.local_stats['matches'], 2
        )
        
        self.local_stats['avg_hs'] = round(
            (self.local_stats.get('avg_hs', 0) * old_matches + hs) / self.local_stats['matches'], 1
        )
        
        self.local_stats['avg_kills'] = round(
            self.local_stats['total_kills'] / self.local_stats['matches'], 1
        )
        
        # Процент побед
        self.local_stats['win_percentage'] = round(
            (self.local_stats['wins'] / self.local_stats['matches']) * 100, 1
        )
        
        # Сохраняем детали матча
        match_detail = {
            'result': result_char,
            'elo_before': old_elo,
            'elo_after': self.local_stats['elo'],
            'elo_change': elo_change,
            'kills': kills,
            'deaths': deaths,
            'kd': kd_ratio,
            'hs': hs,
            'map': map_name,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        if 'match_details' not in self.local_stats:
            self.local_stats['match_details'] = []
        self.local_stats['match_details'].append(match_detail)
        
        # Сохраняем локально
        self.save_local_data()
        
        # Синхронизируем с сервером
        if self.connected:
            response = self.send_request({
                'action': 'update_stats',
                'nickname': self.current_user,
                'stats': self.local_stats,
                'match': match_detail
            })
            
            if response:
                if isinstance(response, list):
                    if len(response) >= 2 and response[0]:
                        self.add_status_var.set("✅ Матч добавлен и синхронизирован!")
                    elif len(response) >= 2:
                        self.add_status_var.set(f"⚠️ {response[1]}")
                elif isinstance(response, dict):
                    if response.get('success'):
                        self.add_status_var.set("✅ Матч добавлен и синхронизирован!")
                    else:
                        self.add_status_var.set("⚠️ Матч добавлен локально, но не синхронизирован")
                else:
                    self.add_status_var.set("⚠️ Матч добавлен локально, но не синхронизирован")
            else:
                self.add_status_var.set("⚠️ Матч добавлен только локально")
        else:
            self.add_status_var.set("⚠️ Матч добавлен только локально")
        
        # Очищаем поля
        self.match_result_var.set("")
        self.match_kills_var.set("")
        self.match_deaths_var.set("")
        self.match_hs_var.set("")
        self.match_map_var.set("")
        
        # Обновляем отображение
        self.update_display()
        
        # Обновляем скорборд
        self.update_scoreboard()
    
    def export_scoreboard(self):
        """Экспорт скорборда в CSV"""
        try:
            from tkinter import filedialog
            import csv
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Заголовки
                    headers = ["#", "Игрок", "Уровень", "ELO", "Победы", "Поражения", 
                              "Ничьи", "Винрейт", "K/D", "HS%", "AVG убийств"]
                    writer.writerow(headers)
                    
                    # Данные
                    for item in self.scoreboard_tree.get_children():
                        values = self.scoreboard_tree.item(item)['values']
                        writer.writerow(values)
                
                messagebox.showinfo("Успех", f"Скорборд экспортирован в {filename}")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {e}")
    
    def compare_with_player(self):
        """Сравнение с другим игроком"""
        # Получаем выбранного игрока
        selection = self.scoreboard_tree.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите игрока для сравнения")
            return
        
        item = selection[0]
        values = self.scoreboard_tree.item(item)['values']
        player_nickname = values[1]  # Второй столбец - ник
        
        # Получаем статистику игрока
        if self.connected:
            response = self.send_request({
                'action': 'get_stats',
                'nickname': player_nickname
            })
            
            if response:
                if isinstance(response, dict) and response.get('success'):
                    player_stats = response.get('stats')
                    self.show_comparison(player_stats)
                elif isinstance(response, list) and response:
                    if isinstance(response[0], dict):
                        player_stats = response[0]
                        self.show_comparison(player_stats)
                    else:
                        messagebox.showerror("Ошибка", "Некорректный формат данных")
                else:
                    messagebox.showerror("Ошибка", "Не удалось получить статистику игрока")
            else:
                messagebox.showerror("Ошибка", "Нет ответа от сервера")
    
    def show_comparison(self, player_stats):
        """Показать сравнение статистики"""
        comparison_window = tk.Toplevel(self.root)
        comparison_window.title(f"Сравнение: {self.current_user} vs {player_stats['nickname']}")
        comparison_window.geometry("600x400")
        comparison_window.configure(bg="white")
        
        # Заголовок
        header = ttk.Label(comparison_window, 
                          text=f"Сравнение статистики",
                          font=("Arial", 16, "bold"))
        header.pack(pady=20)
        
        # Таблица сравнения
        columns = ("Параметр", f"{self.current_user}", f"{player_stats['nickname']}", "Разница")
        
        tree = ttk.Treeview(comparison_window, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")
        
        # Данные для сравнения
        my_stats = self.local_stats
        compare_stats = [
            ("ELO", my_stats.get('elo', 0), player_stats.get('elo', 0)),
            ("Уровень", self.get_current_level(), 
             self.get_level_from_elo(player_stats.get('elo', 0))),
            ("Победы", my_stats.get('wins', 0), player_stats.get('wins', 0)),
            ("Поражения", my_stats.get('losses', 0), player_stats.get('losses', 0)),
            ("Ничьи", my_stats.get('ties', 0), player_stats.get('ties', 0)),
            ("Матчи", my_stats.get('matches', 0), player_stats.get('matches', 0)),
            ("Винрейт", f"{my_stats.get('win_percentage', 0)}%", 
             f"{player_stats.get('win_percentage', 0)}%"),
            ("K/D", f"{my_stats.get('avg_kd', 0):.2f}", 
             f"{player_stats.get('avg_kd', 0):.2f}"),
            ("HS%", f"{my_stats.get('avg_hs', 0):.1f}%", 
             f"{player_stats.get('avg_hs', 0):.1f}%"),
            ("AVG убийств", f"{my_stats.get('avg_kills', 0):.1f}", 
             f"{player_stats.get('avg_kills', 0):.1f}")
        ]
        
        for param, my_val, other_val in compare_stats:
            # Вычисляем разницу
            if isinstance(my_val, (int, float)) and isinstance(other_val, (int, float)):
                diff = my_val - other_val
                diff_text = f"{diff:+.0f}" if diff >= 0 else f"{diff}"
            else:
                diff_text = "-"
            
            tree.insert("", "end", values=(param, my_val, other_val, diff_text))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Кнопка закрытия
        ttk.Button(comparison_window, text="Закрыть", 
                  command=comparison_window.destroy).pack(pady=10)
    
    def get_level_from_elo(self, elo):
        """Определение уровня по ELO"""
        for level, data in self.levels.items():
            if data["min_elo"] <= elo <= data["max_elo"]:
                return level
        return 1
    
    def create_seasons_tab(self):
        """Создание вкладки сезонов"""
        container = ttk.Frame(self.seasons_tab, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(container, text="Активные сезоны", 
                 font=("Arial", 20, "bold")).pack(pady=(0, 20))
        
        # Таблица сезонов
        table_frame = ttk.Frame(container)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Название", "Начало", "Конец", "Премиум награда")
        self.seasons_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.seasons_tree.heading(col, text=col)
            self.seasons_tree.column(col, width=200, anchor="center")
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.seasons_tree.yview)
        self.seasons_tree.configure(yscrollcommand=scrollbar.set)
        
        self.seasons_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопка обновления
        ttk.Button(container, text="Обновить сезоны", 
                  command=self.update_seasons).pack(pady=10)
    
    def create_premium_tab(self):
        """Создание вкладки премиума"""
        container = ttk.Frame(self.premium_tab, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(container, text="Премиум статус", 
                 font=("Arial", 20, "bold")).pack(pady=(0, 20))
        
        # Статус премиума
        self.premium_status_var = tk.StringVar(value="Проверка...")
        ttk.Label(container, textvariable=self.premium_status_var, 
                 font=("Arial", 14)).pack(pady=10)
        
        # Кнопка проверки статуса
        ttk.Button(container, text="Проверить премиум статус", 
                  command=self.check_premium).pack(pady=10)
        
        # Форма для игры 2 на 2
        form_frame = ttk.LabelFrame(container, text="Добавить игру 2 на 2", padding=15)
        form_frame.pack(fill=tk.X, pady=20)
        
        ttk.Label(form_frame, text="Сезон:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.season_var = tk.StringVar()
        self.season_combo = ttk.Combobox(form_frame, textvariable=self.season_var, width=20)
        self.season_combo.grid(row=0, column=1, pady=5)
        ttk.Button(form_frame, text="Загрузить сезоны", 
                  command=self.load_seasons_for_premium).grid(row=0, column=2, padx=5)
        
        ttk.Label(form_frame, text="Напарник:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.teammate_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.teammate_var, width=20).grid(row=1, column=1, pady=5)
        
        ttk.Label(form_frame, text="Противник 1:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.opponent1_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.opponent1_var, width=20).grid(row=2, column=1, pady=5)
        
        ttk.Label(form_frame, text="Противник 2:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.opponent2_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.opponent2_var, width=20).grid(row=3, column=1, pady=5)
        
        ttk.Label(form_frame, text="Счет команды 1:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.team1_score_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.team1_score_var, width=10).grid(row=4, column=1, pady=5)
        
        ttk.Label(form_frame, text="Счет команды 2:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.team2_score_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.team2_score_var, width=10).grid(row=5, column=1, pady=5)
        
        ttk.Button(form_frame, text="Добавить игру 2 на 2", 
                  command=self.add_2v2_match).grid(row=6, column=0, columnspan=2, pady=10)
    
    def create_chat_tab(self):
        """Создание вкладки чатов"""
        container = ttk.Frame(self.chat_tab, padding=10)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель со списком чатов
        left_panel = ttk.Frame(container, width=200)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        ttk.Label(left_panel, text="Чаты", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Список чатов
        self.chats_listbox = tk.Listbox(left_panel)
        self.chats_listbox.pack(fill=tk.BOTH, expand=True)
        self.chats_listbox.bind('<<ListboxSelect>>', self.on_chat_select)
        
        ttk.Button(left_panel, text="Обновить", command=self.update_chats_list).pack(pady=5)
        
        # Правая панель с сообщениями
        right_panel = ttk.Frame(container)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(right_panel, text="Сообщения", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Область сообщений
        messages_frame = ttk.Frame(right_panel)
        messages_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_msg = ttk.Scrollbar(messages_frame)
        scrollbar_msg.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.messages_text = tk.Text(messages_frame, wrap=tk.WORD, yscrollcommand=scrollbar_msg.set)
        self.messages_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_msg.config(command=self.messages_text.yview)
        
        # Поле ввода сообщения
        input_frame = ttk.Frame(right_panel)
        input_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(input_frame, text="Получатель:").pack(side=tk.LEFT, padx=5)
        self.receiver_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.receiver_var, width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(input_frame, text="Сообщение:").pack(side=tk.LEFT, padx=5)
        self.message_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.message_var, width=30).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(input_frame, text="Отправить", command=self.send_chat_message).pack(side=tk.LEFT, padx=5)
    
    def update_seasons(self):
        """Обновление списка сезонов"""
        if not self.connected:
            messagebox.showinfo("Информация", "Нет подключения к серверу")
            return
        
        response = self.send_request({'action': 'get_active_seasons'})
        
        if response and response.get('success'):
            seasons = response.get('seasons', [])
            for item in self.seasons_tree.get_children():
                self.seasons_tree.delete(item)
            
            for season in seasons:
                self.seasons_tree.insert("", "end", values=(
                    season.get('name', ''),
                    season.get('start_date', ''),
                    season.get('end_date', ''),
                    f"{season.get('premium_reward', 0)} дней"
                ))
        else:
            messagebox.showerror("Ошибка", "Не удалось загрузить сезоны")
    
    def load_seasons_for_premium(self):
        """Загрузка сезонов для комбобокса"""
        if not self.connected:
            messagebox.showinfo("Информация", "Нет подключения к серверу")
            return
        
        response = self.send_request({'action': 'get_active_seasons'})
        
        if response and response.get('success'):
            seasons = response.get('seasons', [])
            season_values = [f"{s.get('id')} - {s.get('name', '')}" for s in seasons]
            self.season_combo['values'] = season_values
        else:
            messagebox.showerror("Ошибка", "Не удалось загрузить сезоны")
    
    def check_premium(self):
        """Проверка премиум статуса"""
        if not self.current_user:
            messagebox.showerror("Ошибка", "Сначала войдите в систему")
            return
        
        if not self.connected:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
            return
        
        response = self.send_request({
            'action': 'check_premium_status',
            'nickname': self.current_user
        })
        
        if response and response.get('success'):
            premium_data = response.get('premium_data', {})
            if premium_data.get('is_premium'):
                until = premium_data.get('premium_until', '')
                self.premium_status_var.set(f"⭐ Премиум активен до {until}")
            else:
                self.premium_status_var.set("❌ Премиум не активен")
        else:
            self.premium_status_var.set("Ошибка проверки статуса")
    
    def add_2v2_match(self):
        """Добавление игры 2 на 2"""
        if not self.current_user:
            messagebox.showerror("Ошибка", "Сначала войдите в систему")
            return
        
        try:
            season_str = self.season_var.get()
            if season_str:
                season_id = int(season_str.split(' - ')[0])
            else:
                season_id = None
            
            teammate = self.teammate_var.get().strip()
            opponent1 = self.opponent1_var.get().strip()
            opponent2 = self.opponent2_var.get().strip()
            team1_score = int(self.team1_score_var.get()) if self.team1_score_var.get() else 0
            team2_score = int(self.team2_score_var.get()) if self.team2_score_var.get() else 0
            
            if not all([season_id, teammate, opponent1, opponent2]):
                raise ValueError("Заполните все поля")
            
            response = self.send_request({
                'action': 'add_2v2_match',
                'nickname': self.current_user,
                'season_id': season_id,
                'teammate_nickname': teammate,
                'opponent1_nickname': opponent1,
                'opponent2_nickname': opponent2,
                'team1_score': team1_score,
                'team2_score': team2_score
            })
            
            if response and response.get('success'):
                messagebox.showinfo("Успех", "Игра 2 на 2 добавлена!")
                # Очистка полей
                self.teammate_var.set("")
                self.opponent1_var.set("")
                self.opponent2_var.set("")
                self.team1_score_var.set("")
                self.team2_score_var.set("")
            else:
                messagebox.showerror("Ошибка", response.get('message', 'Ошибка добавления игры'))
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Некорректные данные: {e}")
    
    def update_chats_list(self):
        """Обновление списка чатов"""
        if not self.current_user:
            return
        
        if not self.connected:
            return
        
        response = self.send_request({
            'action': 'get_user_chats',
            'nickname': self.current_user
        })
        
        if response and response.get('success'):
            chats = response.get('chats', [])
            self.chats_listbox.delete(0, tk.END)
            for chat in chats:
                self.chats_listbox.insert(tk.END, chat.get('other_player', 'Unknown'))
    
    def on_chat_select(self, event):
        """Обработка выбора чата"""
        selection = self.chats_listbox.curselection()
        if not selection:
            return
        
        other_player = self.chats_listbox.get(selection[0])
        self.load_chat_messages(other_player)
    
    def load_chat_messages(self, other_player):
        """Загрузка сообщений из чата"""
        if not self.current_user or not self.connected:
            return
        
        response = self.send_request({
            'action': 'get_chat_messages',
            'player1_nickname': self.current_user,
            'player2_nickname': other_player,
            'limit': 50
        })
        
        if response and response.get('success'):
            messages = response.get('messages', [])
            self.messages_text.delete(1.0, tk.END)
            for msg in messages:
                sender = msg.get('sender', 'Unknown')
                text = msg.get('text', '')
                time = msg.get('time', '')
                self.messages_text.insert(tk.END, f"[{time}] {sender}: {text}\n")
            self.messages_text.see(tk.END)
    
    def send_chat_message(self):
        """Отправка сообщения"""
        if not self.current_user:
            messagebox.showerror("Ошибка", "Сначала войдите в систему")
            return
        
        receiver = self.receiver_var.get().strip()
        message_text = self.message_var.get().strip()
        
        if not receiver or not message_text:
            messagebox.showerror("Ошибка", "Введите получателя и сообщение")
            return
        
        if not self.connected:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
            return
        
        response = self.send_request({
            'action': 'send_message',
            'sender_nickname': self.current_user,
            'receiver_nickname': receiver,
            'message_text': message_text
        })
        
        if response and response.get('success'):
            self.message_var.set("")
            self.load_chat_messages(receiver)
        else:
            messagebox.showerror("Ошибка", response.get('message', 'Ошибка отправки'))
    
    def create_tournaments_tab(self):
        """Создание вкладки турниров"""
        container = ttk.Frame(self.tournaments_tab, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(container, text="Турниры", 
                 font=("Arial", 20, "bold")).pack(pady=(0, 20))
        
        # Фильтр по статусу
        filter_frame = ttk.Frame(container)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Статус:").pack(side=tk.LEFT, padx=5)
        self.tournament_status_var = tk.StringVar(value="all")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.tournament_status_var,
                                    values=["all", "planned", "ongoing", "finished"],
                                    state="readonly", width=15)
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self.update_tournaments())
        
        ttk.Button(filter_frame, text="Обновить", 
                  command=self.update_tournaments).pack(side=tk.LEFT, padx=5)
        
        # Таблица турниров
        table_frame = ttk.Frame(container)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Название", "Начало", "Конец", "Участники", "Призовой фонд", "Статус")
        self.tournaments_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tournaments_tree.heading(col, text=col)
            self.tournaments_tree.column(col, width=150, anchor="center")
        
        self.tournaments_tree.bind("<Double-1>", self.on_tournament_double_click)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tournaments_tree.yview)
        self.tournaments_tree.configure(yscrollcommand=scrollbar.set)
        
        self.tournaments_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопка регистрации
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Зарегистрироваться на турнир", 
                  command=self.register_for_selected_tournament).pack(side=tk.LEFT, padx=5)
    
    def update_tournaments(self):
        """Обновление списка турниров"""
        if not self.connected:
            return
        
        status = self.tournament_status_var.get()
        status_filter = None if status == "all" else status
        
        response = self.send_request({
            'action': 'get_tournaments',
            'status': status_filter
        })
        
        if response and response.get('success'):
            tournaments = response.get('tournaments', [])
            for item in self.tournaments_tree.get_children():
                self.tournaments_tree.delete(item)
            
            for tour in tournaments:
                status_text = {
                    'planned': 'Запланирован',
                    'ongoing': 'Идет',
                    'finished': 'Завершен',
                    'cancelled': 'Отменен'
                }.get(tour.get('status', 'planned'), 'Неизвестно')
                
                self.tournaments_tree.insert("", "end", values=(
                    tour.get('name', ''),
                    tour.get('start_date', ''),
                    tour.get('end_date', ''),
                    f"{tour.get('current_players', 0)}/{tour.get('max_players', 16)}",
                    tour.get('prize_pool', 'Нет'),
                    status_text
                ), tags=(tour.get('id'),))
    
    def on_tournament_double_click(self, event):
        """Обработка двойного клика на турнир"""
        selection = self.tournaments_tree.selection()
        if selection:
            item = selection[0]
            tags = self.tournaments_tree.item(item, 'tags')
            if tags:
                tournament_id = tags[0]
                self.show_tournament_details(tournament_id)
    
    def register_for_selected_tournament(self):
        """Регистрация на выбранный турнир"""
        if not self.current_user:
            messagebox.showerror("Ошибка", "Сначала войдите в систему")
            return
        
        selection = self.tournaments_tree.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите турнир")
            return
        
        item = selection[0]
        tags = self.tournaments_tree.item(item, 'tags')
        if not tags:
            return
        
        tournament_id = int(tags[0])
        
        response = self.send_request({
            'action': 'register_for_tournament',
            'nickname': self.current_user,
            'tournament_id': tournament_id
        })
        
        if response and response.get('success'):
            messagebox.showinfo("Успех", response.get('message', 'Регистрация успешна!'))
            self.update_tournaments()
        else:
            messagebox.showerror("Ошибка", response.get('message', 'Ошибка регистрации'))
    
    def show_tournament_details(self, tournament_id):
        """Показать детали турнира"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Детали турнира")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        
        ttk.Label(dialog, text="Информация о турнире", 
                 font=("Arial", 16, "bold")).pack(pady=20)
        
        # Здесь можно добавить детальную информацию о турнире
        ttk.Label(dialog, text=f"ID турнира: {tournament_id}").pack(pady=5)
    
    def show_detailed_player_profile(self, nickname):
        """Показать детальный профиль игрока"""
        if not self.connected:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
            return
        
        response = self.send_request({
            'action': 'get_detailed_player_profile',
            'nickname': nickname
        })
        
        if not response or not response.get('success'):
            messagebox.showerror("Ошибка", "Не удалось загрузить профиль")
            return
        
        profile = response.get('profile', {})
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Профиль: {nickname}")
        dialog.geometry("700x600")
        dialog.transient(self.root)
        
        # Создаем notebook для вкладок
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка общей информации
        info_tab = ttk.Frame(notebook)
        notebook.add(info_tab, text="Общая информация")
        
        info_text = f"""Никнейм: {profile.get('nickname', 'N/A')}
ELO: {profile.get('elo', 0)}
Роль: {profile.get('role', 'player')}
Премиум: {'Да' if profile.get('is_premium') else 'Нет'}
Премиум до: {profile.get('premium_until', 'N/A')}

Статистика:
Матчей: {profile.get('matches', 0)}
Побед: {profile.get('wins', 0)}
Поражений: {profile.get('losses', 0)}
Ничьих: {profile.get('ties', 0)}
Винрейт: {profile.get('win_percentage', 0)}%

K/D: {profile.get('avg_kd', 0):.2f}
HS%: {profile.get('avg_hs', 0):.1f}%
AVG убийств: {profile.get('avg_kills', 0):.1f}
Всего убийств: {profile.get('total_kills', 0)}
Всего смертей: {profile.get('total_deaths', 0)}
"""
        
        text_widget = tk.Text(info_tab, wrap=tk.WORD, font=("Arial", 11))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, info_text)
        text_widget.config(state=tk.DISABLED)
        
        # Вкладка графика ELO
        if MATPLOTLIB_AVAILABLE:
            elo_tab = ttk.Frame(notebook)
            notebook.add(elo_tab, text="График ELO")
            self.create_elo_chart(elo_tab, nickname)
        
        # Вкладка статистики по картам
        maps_tab = ttk.Frame(notebook)
        notebook.add(maps_tab, text="Статистика по картам")
        self.create_map_statistics_tab(maps_tab, nickname)
        
        # Вкладка статистики по времени
        time_tab = ttk.Frame(notebook)
        notebook.add(time_tab, text="Статистика по времени")
        self.create_time_statistics_tab(time_tab, nickname)
        
        # Вкладка сравнения сезонов
        seasons_tab = ttk.Frame(notebook)
        notebook.add(seasons_tab, text="Сравнение сезонов")
        self.create_season_comparison_tab(seasons_tab, nickname)
    
    def create_elo_chart(self, parent, nickname):
        """Создание графика изменения ELO"""
        if not MATPLOTLIB_AVAILABLE:
            ttk.Label(parent, text="Для отображения графика установите matplotlib:\npip install matplotlib").pack(pady=20)
            return
        
        response = self.send_request({
            'action': 'get_elo_history',
            'nickname': nickname,
            'limit': 100
        })
        
        if not response or not response.get('success'):
            ttk.Label(parent, text="Не удалось загрузить историю ELO").pack(pady=20)
            return
        
        history = response.get('history', [])
        if not history:
            ttk.Label(parent, text="Нет данных для отображения").pack(pady=20)
            return
        
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        elos = [h['elo'] for h in history]
        dates = [h['date'] for h in history]
        
        ax.plot(range(len(elos)), elos, marker='o', linestyle='-', linewidth=2, markersize=4)
        ax.set_xlabel('Матч')
        ax.set_ylabel('ELO')
        ax.set_title(f'Изменение ELO: {nickname}')
        ax.grid(True, alpha=0.3)
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_map_statistics_tab(self, parent, nickname):
        """Создание вкладки статистики по картам"""
        response = self.send_request({
            'action': 'get_map_statistics',
            'nickname': nickname
        })
        
        if not response or not response.get('success'):
            ttk.Label(parent, text="Не удалось загрузить статистику по картам").pack(pady=20)
            return
        
        stats = response.get('stats', [])
        if not stats:
            ttk.Label(parent, text="Нет данных").pack(pady=20)
            return
        
        # Таблица статистики
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("Карта", "Матчей", "Побед", "Поражений", "Винрейт", "AVG K", "AVG D")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")
        
        for stat in stats:
            tree.insert("", "end", values=(
                stat.get('map', 'N/A'),
                stat.get('total_matches', 0),
                stat.get('wins', 0),
                stat.get('losses', 0),
                f"{stat.get('win_rate', 0):.1f}%",
                f"{stat.get('avg_kills', 0):.1f}",
                f"{stat.get('avg_deaths', 0):.1f}"
            ))
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_time_statistics_tab(self, parent, nickname):
        """Создание вкладки статистики по времени"""
        response = self.send_request({
            'action': 'get_time_statistics',
            'nickname': nickname
        })
        
        if not response or not response.get('success'):
            ttk.Label(parent, text="Не удалось загрузить статистику по времени").pack(pady=20)
            return
        
        stats = response.get('stats', {})
        hour_stats = stats.get('hours', [])
        day_stats = stats.get('days', [])
        
        # Статистика по часам
        hours_frame = ttk.LabelFrame(parent, text="По часам", padding=10)
        hours_frame.pack(fill=tk.X, padx=10, pady=5)
        
        if hour_stats:
            best_hour = max(hour_stats, key=lambda x: x.get('win_rate', 0))
            ttk.Label(hours_frame, text=f"Лучший час: {best_hour.get('hour', 0)}:00 (Винрейт: {best_hour.get('win_rate', 0):.1f}%)").pack()
        
        # Статистика по дням недели
        days_frame = ttk.LabelFrame(parent, text="По дням недели", padding=10)
        days_frame.pack(fill=tk.X, padx=10, pady=5)
        
        day_names = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
        if day_stats:
            best_day = max(day_stats, key=lambda x: x.get('win_rate', 0))
            ttk.Label(days_frame, text=f"Лучший день: {day_names[best_day.get('day', 0)]} (Винрейт: {best_day.get('win_rate', 0):.1f}%)").pack()
    
    def create_season_comparison_tab(self, parent, nickname):
        """Создание вкладки сравнения сезонов"""
        response = self.send_request({
            'action': 'get_season_comparison',
            'nickname': nickname
        })
        
        if not response or not response.get('success'):
            ttk.Label(parent, text="Не удалось загрузить сравнение сезонов").pack(pady=20)
            return
        
        seasons = response.get('seasons', [])
        if not seasons:
            ttk.Label(parent, text="Нет данных по сезонам").pack(pady=20)
            return
        
        # Таблица сравнения
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("Сезон", "Матчей", "Побед", "Винрейт", "Средний ELO")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        
        for season in seasons:
            tree.insert("", "end", values=(
                season.get('name', 'N/A'),
                season.get('matches', 0),
                season.get('wins', 0),
                f"{season.get('win_rate', 0):.1f}%",
                int(season.get('avg_elo', 0))
            ))
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def add_stats_analytics(self):
        """Добавление аналитики на вкладку статистики после авторизации"""
        if not self.current_user:
            return
        
        container = self.stats_tab.winfo_children()[0]  # Получаем контейнер вкладки
        
        # График ELO (если доступен matplotlib)
        if MATPLOTLIB_AVAILABLE:
            chart_frame = ttk.LabelFrame(container, text="График изменения ELO", padding=10)
            chart_frame.pack(fill=tk.BOTH, expand=True, pady=20)
            self.elo_chart_frame = chart_frame
            self.update_elo_chart()
        
        # Кнопка просмотра детального профиля
        if not self.profile_button:
            self.profile_button = ttk.Button(container, text="👤 Просмотреть детальный профиль", 
                          command=lambda: self.show_detailed_player_profile(self.current_user))
            self.profile_button.pack(pady=10)
    
    def update_elo_chart(self):
        """Обновление графика ELO на вкладке статистики"""
        if not MATPLOTLIB_AVAILABLE or not self.current_user or not self.connected:
            return
        
        if not self.elo_chart_frame:
            return
        
        # Очищаем предыдущий график
        for widget in self.elo_chart_frame.winfo_children():
            widget.destroy()
        
        response = self.send_request({
            'action': 'get_elo_history',
            'nickname': self.current_user,
            'limit': 100
        })
        
        if not response or not response.get('success'):
            ttk.Label(self.elo_chart_frame, text="Не удалось загрузить историю ELO").pack(pady=20)
            return
        
        history = response.get('history', [])
        if not history:
            ttk.Label(self.elo_chart_frame, text="Нет данных для отображения").pack(pady=20)
            return
        
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        elos = [h['elo'] for h in history]
        
        ax.plot(range(len(elos)), elos, marker='o', linestyle='-', linewidth=2, markersize=3)
        ax.set_xlabel('Матч')
        ax.set_ylabel('ELO')
        ax.set_title('Изменение ELO')
        ax.grid(True, alpha=0.3)
        
        canvas = FigureCanvasTkAgg(fig, self.elo_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def on_player_double_click(self, event):
        """Обработка двойного клика на игрока в скорборде"""
        selection = self.scoreboard_tree.selection()
        if selection:
            item = selection[0]
            values = self.scoreboard_tree.item(item)['values']
            player_nickname = values[1]  # Второй столбец - ник
            self.show_detailed_player_profile(player_nickname)

if __name__ == "__main__":
    root = tk.Tk()
    app = FaceItOnlineTracker(root)
    
    def on_closing():
        app.save_local_data()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
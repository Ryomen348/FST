# server.py - с админ панелью
import socket
import threading
import json
import sqlite3
from datetime import datetime
import hashlib
import secrets
import string

class FaceItScoreboardServer:
    def __init__(self, host='26.90.218.164', port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []
        
        # Инициализация базы данных
        self.init_database()
        
        # Создаем администратора по умолчанию
        self.create_default_admin()
        
    def init_database(self):
        """Инициализация базы данных SQLite"""
        self.conn = sqlite3.connect('faceit_scoreboard.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Таблица пользователей с ролью
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                email TEXT,
                role TEXT DEFAULT 'player', -- player, moderator, admin
                elo INTEGER DEFAULT 1050,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                ties INTEGER DEFAULT 0,
                matches INTEGER DEFAULT 0,
                avg_kd REAL DEFAULT 0,
                avg_hs REAL DEFAULT 0,
                win_percentage REAL DEFAULT 0,
                total_kills INTEGER DEFAULT 0,
                total_deaths INTEGER DEFAULT 0,
                avg_kills REAL DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                ban_reason TEXT,
                ban_until TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица матчей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER,
                result TEXT,
                kills INTEGER,
                deaths INTEGER,
                hs_percentage REAL,
                map_name TEXT,
                elo_before INTEGER,
                elo_after INTEGER,
                elo_change INTEGER,
                is_verified INTEGER DEFAULT 1, -- Проверен ли матч модератором
                verified_by INTEGER,
                match_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players (id),
                FOREIGN KEY (verified_by) REFERENCES players (id)
            )
        ''')
        
        # Таблица банов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER,
                admin_id INTEGER,
                reason TEXT,
                ban_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                unban_date TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (player_id) REFERENCES players (id),
                FOREIGN KEY (admin_id) REFERENCES players (id)
            )
        ''')
        
        # Таблица действий админов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action_type TEXT,
                target_id INTEGER,
                details TEXT,
                action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES players (id),
                FOREIGN KEY (target_id) REFERENCES players (id)
            )
        ''')
        
        # РўР°Р±Р»РёС†Р° СЃРµР·РѕРЅРѕРІ
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP NOT NULL,
                premium_reward INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # РўР°Р±Р»РёС†Р° РїСЂРµРјРёСѓРј РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS premium_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER UNIQUE NOT NULL,
                premium_until TIMESTAMP,
                is_premium INTEGER DEFAULT 0,
                premium_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players (id)
            )
        ''')

        # РўР°Р±Р»РёС†Р° РёРіСЂ 2 РЅР° 2
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches_2v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_id INTEGER,
                team1_player1_id INTEGER,
                team1_player2_id INTEGER,
                team2_player1_id INTEGER,
                team2_player2_id INTEGER,
                team1_score INTEGER DEFAULT 0,
                team2_score INTEGER DEFAULT 0,
                winner_team INTEGER,
                match_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_verified INTEGER DEFAULT 0,
                FOREIGN KEY (season_id) REFERENCES seasons (id),
                FOREIGN KEY (team1_player1_id) REFERENCES players (id),
                FOREIGN KEY (team1_player2_id) REFERENCES players (id),
                FOREIGN KEY (team2_player1_id) REFERENCES players (id),
                FOREIGN KEY (team2_player2_id) REFERENCES players (id)
            )
        ''')

        # РўР°Р±Р»РёС†Р° С‡Р°С‚РѕРІ
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player1_id INTEGER NOT NULL,
                player2_id INTEGER NOT NULL,
                last_message_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player1_id) REFERENCES players (id),
                FOREIGN KEY (player2_id) REFERENCES players (id),
                UNIQUE(player1_id, player2_id)
            )
        ''')

        # РўР°Р±Р»РёС†Р° СЃРѕРѕР±С‰РµРЅРёР№
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                message_text TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chats (id),
                FOREIGN KEY (sender_id) REFERENCES players (id)
            )
        ''')

        # РўР°Р±Р»РёС†Р° СѓС‡Р°СЃС‚РЅРёРєРѕРІ С‚СѓСЂРЅРёСЂР°
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournament_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                final_position INTEGER,
                prize TEXT,
                FOREIGN KEY (tournament_id) REFERENCES tournaments (id),
                FOREIGN KEY (player_id) REFERENCES players (id),
                UNIQUE(tournament_id, player_id)
            )
        ''')

        # РўР°Р±Р»РёС†Р° РјР°С‚С‡РµР№ С‚СѓСЂРЅРёСЂР°
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournament_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                player1_id INTEGER,
                player2_id INTEGER,
                winner_id INTEGER,
                score1 INTEGER DEFAULT 0,
                score2 INTEGER DEFAULT 0,
                match_date TIMESTAMP,
                status TEXT DEFAULT 'scheduled',
                FOREIGN KEY (tournament_id) REFERENCES tournaments (id),
                FOREIGN KEY (player1_id) REFERENCES players (id),
                FOREIGN KEY (player2_id) REFERENCES players (id),
                FOREIGN KEY (winner_id) REFERENCES players (id)
            )
        ''')
        

        # Р”РѕР±Р°РІР»СЏРµРј РєРѕР»РѕРЅРєРё email Рё role, РµСЃР»Рё РёС… РЅРµС‚ (РґР»СЏ СЃСѓС‰РµСЃС‚РІСѓСЋС‰РёС… С‚Р°Р±Р»РёС†)
        try:
            self.cursor.execute('ALTER TABLE players ADD COLUMN email TEXT')
        except sqlite3.OperationalError:
            pass  # РљРѕР»РѕРЅРєР° СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚
        
        try:
            self.cursor.execute('ALTER TABLE players ADD COLUMN role TEXT DEFAULT ''player''')
        except sqlite3.OperationalError:
            pass  # РљРѕР»РѕРЅРєР° СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚
        

        try:
            self.cursor.execute('ALTER TABLE players ADD COLUMN is_banned INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass  # РљРѕР»РѕРЅРєР° СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚
        
        try:
            self.cursor.execute('ALTER TABLE players ADD COLUMN ban_reason TEXT')
        except sqlite3.OperationalError:
            pass  # РљРѕР»РѕРЅРєР° СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚
        
        try:
            self.cursor.execute('ALTER TABLE players ADD COLUMN ban_until TIMESTAMP')
        except sqlite3.OperationalError:
            pass  # РљРѕР»РѕРЅРєР° СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚
        

        # Р”РѕР±Р°РІР»СЏРµРј РєРѕР»РѕРЅРєРё РІ С‚Р°Р±Р»РёС†Сѓ bans, РµСЃР»Рё РёС… РЅРµС‚
        try:
            self.cursor.execute('ALTER TABLE bans ADD COLUMN is_active INTEGER DEFAULT 1')
        except sqlite3.OperationalError:
            pass  # РљРѕР»РѕРЅРєР° СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚
        
        # Р”РѕР±Р°РІР»СЏРµРј РєРѕР»РѕРЅРєРё РІ С‚Р°Р±Р»РёС†Сѓ matches, РµСЃР»Рё РёС… РЅРµС‚
        try:
            self.cursor.execute('ALTER TABLE matches ADD COLUMN is_verified INTEGER DEFAULT 1')
        except sqlite3.OperationalError:
            pass  # РљРѕР»РѕРЅРєР° СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚
        
        try:
            self.cursor.execute('ALTER TABLE matches ADD COLUMN verified_by INTEGER')
        except sqlite3.OperationalError:
            pass  # РљРѕР»РѕРЅРєР° СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚
        
        self.conn.commit()
        print("[*] База данных инициализирована")
        
    def create_default_admin(self):
        """Создание администратора по умолчанию"""
        try:
            # Генерируем случайный пароль
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(12))
            
            admin_data = {
                'nickname': 'admin',
                'password': password,
                'email': 'admin@faceit.local',
                'role': 'admin'
            }
            
            # Проверяем, существует ли уже админ
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', ('admin',))
            if not self.cursor.fetchone():
                self.register_player('admin', password, 'admin@faceit.local', 'admin')
                print(f"[*] Создан администратор по умолчанию")
                print(f"[*] Логин: admin")
                print(f"[*] Пароль: {password}")
                print(f"[*] СОХРАНИТЕ ЭТОТ ПАРОЛЬ!")
            else:
                print("[*] Администратор уже существует")
                
        except Exception as e:
            print(f"Ошибка создания администратора: {e}")
    
    def hash_password(self, password):
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_player(self, nickname, password, email='', role='player'):
        """Регистрация нового игрока"""
        try:
            password_hash = self.hash_password(password)
            self.cursor.execute('''
                INSERT INTO players (nickname, password_hash, email, role) 
                VALUES (?, ?, ?, ?)
            ''', (nickname, password_hash, email, role))
            self.conn.commit()
            return True, "Регистрация успешна!"
        except sqlite3.IntegrityError:
            return False, "Игрок с таким ником уже существует"
        except Exception as e:
            print(f"Ошибка регистрации: {e}")
            return False, f"Ошибка регистрации: {e}"
    
    def authenticate_player(self, nickname, password):
        """Аутентификация игрока"""
        try:
            self.cursor.execute('''
                SELECT password_hash, role, is_banned, ban_until 
                FROM players WHERE nickname = ?
            ''', (nickname,))
            result = self.cursor.fetchone()
            
            if not result:
                return False, "Игрок не найден", None
            
            password_hash, role, is_banned, ban_until = result
            
            # Проверяем бан
            if is_banned:
                if ban_until and datetime.strptime(ban_until, '%Y-%m-%d %H:%M:%S') > datetime.now():
                    return False, f"Аккаунт забанен до {ban_until}", None
                else:
                    # Снимаем бан если время истекло
                    self.cursor.execute('UPDATE players SET is_banned = 0 WHERE nickname = ?', (nickname,))
                    self.conn.commit()
            
            if password_hash == self.hash_password(password):
                return True, "Аутентификация успешна", role
            return False, "Неверный пароль", None
            
        except Exception as e:
            print(f"Ошибка аутентификации: {e}")
            return False, f"Ошибка аутентификации: {e}", None
    
    def get_user_role(self, nickname):
        """Получение роли пользователя"""
        try:
            self.cursor.execute('SELECT role FROM players WHERE nickname = ?', (nickname,))
            result = self.cursor.fetchone()
            return result[0] if result else 'player'
        except:
            return 'player'
    
    def update_player_stats(self, nickname, stats):
        """Обновление статистики игрока"""
        try:
            # Проверяем существование игрока
            self.cursor.execute('SELECT id, is_banned FROM players WHERE nickname = ?', (nickname,))
            result = self.cursor.fetchone()
            
            if not result:
                return False, "Игрок не найден"
            
            player_id, is_banned = result
            
            if is_banned:
                return False, "Игрок забанен"
            
            # Обновляем статистику
            self.cursor.execute('''
                UPDATE players 
                SET elo = ?, wins = ?, losses = ?, ties = ?, matches = ?,
                    avg_kd = ?, avg_hs = ?, win_percentage = ?, total_kills = ?,
                    total_deaths = ?, avg_kills = ?, last_updated = CURRENT_TIMESTAMP
                WHERE nickname = ?
            ''', (
                stats.get('elo', 1050),
                stats.get('wins', 0),
                stats.get('losses', 0),
                stats.get('ties', 0),
                stats.get('matches', 0),
                stats.get('avg_kd', 0),
                stats.get('avg_hs', 0),
                stats.get('win_percentage', 0),
                stats.get('total_kills', 0),
                stats.get('total_deaths', 0),
                stats.get('avg_kills', 0),
                nickname
            ))
            
            self.conn.commit()
            return True, "Статистика обновлена"
        except Exception as e:
            print(f"Ошибка обновления статистики: {e}")
            return False, f"Ошибка обновления: {e}"
    
    def add_match(self, nickname, match_data):
        """Добавление матча игрока"""
        try:
            # Получаем ID игрока
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (nickname,))
            result = self.cursor.fetchone()
            
            if not result:
                return False, "Игрок не найден"
            
            player_id = result[0]
            
            # Добавляем матч
            self.cursor.execute('''
                INSERT INTO matches 
                (player_id, result, kills, deaths, hs_percentage, map_name, 
                 elo_before, elo_after, elo_change)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                player_id,
                match_data.get('result', 'W'),
                match_data.get('kills', 0),
                match_data.get('deaths', 0),
                match_data.get('hs', 0),
                match_data.get('map', 'Unknown'),
                match_data.get('elo_before', 1050),
                match_data.get('elo_after', 1050),
                match_data.get('elo_change', 0)
            ))
            
            self.conn.commit()
            return True, "Матч добавлен"
        except Exception as e:
            print(f"Ошибка добавления матча: {e}")
            return False, f"Ошибка добавления матча: {e}"
    
    def get_player_stats(self, nickname):
        """Получение статистики игрока"""
        try:
            self.cursor.execute('''
                SELECT nickname, elo, wins, losses, ties, matches, avg_kd, 
                       avg_hs, win_percentage, total_kills, total_deaths, avg_kills,
                       role, is_banned, ban_reason
                FROM players 
                WHERE nickname = ?
            ''', (nickname,))
            
            result = self.cursor.fetchone()
            if result:
                return {
                    'nickname': result[0],
                    'elo': result[1],
                    'wins': result[2],
                    'losses': result[3],
                    'ties': result[4],
                    'matches': result[5],
                    'avg_kd': result[6],
                    'avg_hs': result[7],
                    'win_percentage': result[8],
                    'total_kills': result[9],
                    'total_deaths': result[10],
                    'avg_kills': result[11],
                    'role': result[12],
                    'is_banned': bool(result[13]),
                    'ban_reason': result[14]
                }
            return None
        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
            return None
    
    def get_all_players(self, limit=100, offset=0):
        """Получение списка всех игроков (для админов)"""
        try:
            self.cursor.execute('''
                SELECT id, nickname, elo, wins, losses, matches, 
                       win_percentage, role, is_banned, created_at
                FROM players 
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            players = []
            for row in self.cursor.fetchall():
                players.append({
                    'id': row[0],
                    'nickname': row[1],
                    'elo': row[2],
                    'wins': row[3],
                    'losses': row[4],
                    'matches': row[5],
                    'win_percentage': row[6],
                    'role': row[7],
                    'is_banned': bool(row[8]),
                    'created_at': row[9]
                })
            
            # Получаем общее количество
            self.cursor.execute('SELECT COUNT(*) FROM players')
            total = self.cursor.fetchone()[0]
            
            return players, total
        except Exception as e:
            print(f"Ошибка получения списка игроков: {e}")
            return [], 0
    
    def get_recent_matches(self, limit=50):
        """Получение последних матчей (для админов)"""
        try:
            self.cursor.execute('''
                SELECT m.id, p.nickname, m.result, m.kills, m.deaths, 
                       m.hs_percentage, m.map_name, m.elo_before, m.elo_after,
                       m.elo_change, m.match_date, m.is_verified
                FROM matches m
                JOIN players p ON m.player_id = p.id
                ORDER BY m.match_date DESC
                LIMIT ?
            ''', (limit,))
            
            matches = []
            for row in self.cursor.fetchall():
                matches.append({
                    'id': row[0],
                    'player': row[1],
                    'result': row[2],
                    'kills': row[3],
                    'deaths': row[4],
                    'hs_percentage': row[5],
                    'map': row[6],
                    'elo_before': row[7],
                    'elo_after': row[8],
                    'elo_change': row[9],
                    'date': row[10],
                    'is_verified': bool(row[11])
                })
            
            return matches
        except Exception as e:
            print(f"Ошибка получения матчей: {e}")
            return []
    
    def get_leaderboard(self, limit=50, sort_by='elo'):
        """Получение таблицы лидеров"""
        try:
            valid_sorts = ['elo', 'wins', 'win_percentage', 'avg_kd', 'avg_kills']
            sort_by = sort_by if sort_by in valid_sorts else 'elo'
            
            self.cursor.execute(f'''
                SELECT nickname, elo, wins, losses, ties, matches, avg_kd, 
                       avg_hs, win_percentage, total_kills, total_deaths, avg_kills
                FROM players 
                WHERE matches > 0 AND is_banned = 0
                ORDER BY {sort_by} DESC
                LIMIT ?
            ''', (limit,))
            
            leaderboard = []
            for row in self.cursor.fetchall():
                leaderboard.append({
                    'nickname': row[0],
                    'elo': row[1],
                    'wins': row[2],
                    'losses': row[3],
                    'ties': row[4],
                    'matches': row[5],
                    'avg_kd': row[6],
                    'avg_hs': row[7],
                    'win_percentage': row[8],
                    'total_kills': row[9],
                    'total_deaths': row[10],
                    'avg_kills': row[11]
                })
            
            return leaderboard
        except Exception as e:
            print(f"Ошибка получения лидерборда: {e}")
            return []
    
    def admin_change_role(self, admin_nickname, target_nickname, new_role):
        """Изменение роли игрока (админ)"""
        try:
            # Проверяем права админа
            admin_role = self.get_user_role(admin_nickname)
            if admin_role not in ['admin', 'moderator']:
                return False, "Недостаточно прав"
            
            # Проверяем, что модератор не может назначать админов
            if admin_role == 'moderator' and new_role == 'admin':
                return False, "Модераторы не могут назначать администраторов"
            
            # Проверяем существование целевого игрока
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (target_nickname,))
            if not self.cursor.fetchone():
                return False, "Игрок не найден"
            
            # Обновляем роль
            self.cursor.execute('UPDATE players SET role = ? WHERE nickname = ?', 
                              (new_role, target_nickname))
            
            # Логируем действие
            self.log_admin_action(admin_nickname, 'change_role', target_nickname, 
                                f"Изменена роль на {new_role}")
            
            self.conn.commit()
            return True, f"Роль игрока {target_nickname} изменена на {new_role}"
            
        except Exception as e:
            print(f"Ошибка изменения роли: {e}")
            return False, f"Ошибка изменения роли: {e}"
    
    def admin_ban_player(self, admin_nickname, target_nickname, reason, days=0):
        """Бан игрока (админ/модератор)"""
        try:
            # Проверяем права
            admin_role = self.get_user_role(admin_nickname)
            if admin_role not in ['admin', 'moderator']:
                return False, "Недостаточно прав"
            
            # Проверяем существование игрока
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (target_nickname,))
            result = self.cursor.fetchone()
            if not result:
                return False, "Игрок не найден"
            
            target_id = result[0]
            
            # Получаем ID админа
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (admin_nickname,))
            admin_id = self.cursor.fetchone()[0]
            
            # Устанавливаем дату разбана
            ban_until = None
            if days > 0:
                from datetime import timedelta
                ban_until = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Добавляем запись о бане
            self.cursor.execute('''
                INSERT INTO bans (player_id, admin_id, reason, unban_date)
                VALUES (?, ?, ?, ?)
            ''', (target_id, admin_id, reason, ban_until))
            
            # Обновляем статус игрока
            self.cursor.execute('''
                UPDATE players 
                SET is_banned = 1, ban_reason = ?, ban_until = ?
                WHERE nickname = ?
            ''', (reason, ban_until, target_nickname))
            
            # Логируем действие
            ban_duration = f"{days} дней" if days > 0 else "навсегда"
            self.log_admin_action(admin_nickname, 'ban', target_nickname, 
                                f"Бан: {reason} ({ban_duration})")
            
            self.conn.commit()
            
            duration_msg = f" на {days} дней" if days > 0 else " навсегда"
            return True, f"Игрок {target_nickname} забанен{duration_msg}. Причина: {reason}"
            
        except Exception as e:
            print(f"Ошибка бана: {e}")
            return False, f"Ошибка бана: {e}"
    
    def admin_unban_player(self, admin_nickname, target_nickname):
        """Разбан игрока (админ/модератор)"""
        try:
            # Проверяем права
            admin_role = self.get_user_role(admin_nickname)
            if admin_role not in ['admin', 'moderator']:
                return False, "Недостаточно прав"
            
            # Проверяем существование игрока
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (target_nickname,))
            result = self.cursor.fetchone()
            if not result:
                return False, "Игрок не найден"
            
            target_id = result[0]
            
            # Получаем ID админа
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (admin_nickname,))
            admin_id = self.cursor.fetchone()[0]
            
            # Обновляем активные баны
            self.cursor.execute('''
                UPDATE bans 
                SET is_active = 0 
                WHERE player_id = ? AND is_active = 1
            ''', (target_id,))
            
            # Снимаем бан с игрока
            self.cursor.execute('''
                UPDATE players 
                SET is_banned = 0, ban_reason = NULL, ban_until = NULL
                WHERE nickname = ?
            ''', (target_nickname,))
            
            # Логируем действие
            self.log_admin_action(admin_nickname, 'unban', target_nickname, "Разбан")
            
            self.conn.commit()
            return True, f"Игрок {target_nickname} разбанен"
            
        except Exception as e:
            print(f"Ошибка разбана: {e}")
            return False, f"Ошибка разбана: {e}"
    
    def admin_verify_match(self, admin_nickname, match_id, verify=True):
        """Верификация матча (модератор)"""
        try:
            # Проверяем права
            admin_role = self.get_user_role(admin_nickname)
            if admin_role not in ['admin', 'moderator']:
                return False, "Недостаточно прав"
            
            # Получаем ID админа
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (admin_nickname,))
            admin_id = self.cursor.fetchone()[0]
            
            # Обновляем статус матча
            self.cursor.execute('''
                UPDATE matches 
                SET is_verified = ?, verified_by = ?
                WHERE id = ?
            ''', (1 if verify else 0, admin_id, match_id))
            
            # Логируем действие
            action = "verify_match" if verify else "unverify_match"
            self.log_admin_action(admin_nickname, action, None, f"Матч #{match_id}")
            
            self.conn.commit()
            status = "подтвержден" if verify else "отклонен"
            return True, f"Матч #{match_id} {status}"
            
        except Exception as e:
            print(f"Ошибка верификации матча: {e}")
            return False, f"Ошибка верификации: {e}"
    

    def admin_delete_match(self, admin_nickname, match_id):
        """РЈРґР°Р»РµРЅРёРµ РјР°С‚С‡Р° (Р°РґРјРёРЅ/РјРѕРґРµСЂР°С‚РѕСЂ)"""
        try:
            # РџСЂРѕРІРµСЂСЏРµРј СЂРѕР»СЊ
            admin_role = self.get_user_role(admin_nickname)
            if admin_role not in ['admin', 'moderator']:
                return False, "РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ"
            
            # РџСЂРѕРІРµСЂСЏРµРј СЃСѓС‰РµСЃС‚РІРѕРІР°РЅРёРµ РјР°С‚С‡Р°
            self.cursor.execute('SELECT id FROM matches WHERE id = ?', (match_id,))
            if not self.cursor.fetchone():
                return False, "РњР°С‚С‡ РЅРµ РЅР°Р№РґРµРЅ"
            
            # РЈРґР°Р»СЏРµРј РјР°С‚С‡
            self.cursor.execute('DELETE FROM matches WHERE id = ?', (match_id,))
            
            # Р›РѕРіРёСЂСѓРµРј РґРµР№СЃС‚РІРёРµ
            self.log_admin_action(admin_nickname, 'delete_match', None, f"РњР°С‚С‡ #{match_id}")
            
            self.conn.commit()
            return True, f"РњР°С‚С‡ #{match_id} СѓРґР°Р»РµРЅ"
            
        except Exception as e:
            print(f"РћС€РёР±РєР° СѓРґР°Р»РµРЅРёСЏ РјР°С‚С‡Р°: {e}")
            return False, f"РћС€РёР±РєР° СѓРґР°Р»РµРЅРёСЏ: {e}"
    def admin_reset_stats(self, admin_nickname, target_nickname):
        """Сброс статистики игрока (админ)"""
        try:
            # Проверяем права (только админ)
            admin_role = self.get_user_role(admin_nickname)
            if admin_role != 'admin':
                return False, "Недостаточно прав. Только для администраторов"
            
            # Сбрасываем статистику
            self.cursor.execute('''
                UPDATE players 
                SET elo = 1050, wins = 0, losses = 0, ties = 0, matches = 0,
                    avg_kd = 0, avg_hs = 0, win_percentage = 0, 
                    total_kills = 0, total_deaths = 0, avg_kills = 0
                WHERE nickname = ?
            ''', (target_nickname,))
            
            # Удаляем матчи игрока
            self.cursor.execute('''
                DELETE FROM matches 
                WHERE player_id = (SELECT id FROM players WHERE nickname = ?)
            ''', (target_nickname,))
            
            # Логируем действие
            self.log_admin_action(admin_nickname, 'reset_stats', target_nickname, 
                                "Сброс статистики")
            
            self.conn.commit()
            return True, f"Статистика игрока {target_nickname} сброшена"
            
        except Exception as e:
            print(f"Ошибка сброса статистики: {e}")
            return False, f"Ошибка сброса: {e}"
    
    def admin_get_stats(self):
        """Получение статистики сервера (для админов)"""
        try:
            stats = {}
            
            # Количество игроков
            self.cursor.execute('SELECT COUNT(*) FROM players')
            stats['total_players'] = self.cursor.fetchone()[0]
            
            # Количество активных игроков (с матчами)
            self.cursor.execute('SELECT COUNT(*) FROM players WHERE matches > 0')
            stats['active_players'] = self.cursor.fetchone()[0]
            
            # Количество забаненных
            self.cursor.execute('SELECT COUNT(*) FROM players WHERE is_banned = 1')
            stats['banned_players'] = self.cursor.fetchone()[0]
            
            # Количество матчей
            self.cursor.execute('SELECT COUNT(*) FROM matches')
            stats['total_matches'] = self.cursor.fetchone()[0]
            
            # Количество непроверенных матчей
            self.cursor.execute('SELECT COUNT(*) FROM matches WHERE is_verified = 0')
            stats['unverified_matches'] = self.cursor.fetchone()[0]
            
            # Распределение по ролям
            self.cursor.execute('''
                SELECT role, COUNT(*) 
                FROM players 
                GROUP BY role
            ''')
            stats['roles_distribution'] = dict(self.cursor.fetchall())
            
            # Последние действия админов
            self.cursor.execute('''
                SELECT a.action_date, p.nickname, a.action_type, a.details
                FROM admin_actions a
                JOIN players p ON a.admin_id = p.id
                ORDER BY a.action_date DESC
                LIMIT 10
            ''')
            
            recent_actions = []
            for row in self.cursor.fetchall():
                recent_actions.append({
                    'date': row[0],
                    'admin': row[1],
                    'action': row[2],
                    'details': row[3]
                })
            
            stats['recent_admin_actions'] = recent_actions
            
            return stats
            
        except Exception as e:
            print(f"Ошибка получения статистики сервера: {e}")
            return {}
    
    def log_admin_action(self, admin_nickname, action_type, target_nickname, details):
        """Логирование действий админа"""
        try:
            # Получаем ID админа
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (admin_nickname,))
            admin_id_result = self.cursor.fetchone()
            
            if not admin_id_result:
                return
            
            admin_id = admin_id_result[0]
            
            # Получаем ID цели если указана
            target_id = None
            if target_nickname:
                self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (target_nickname,))
                target_id_result = self.cursor.fetchone()
                if target_id_result:
                    target_id = target_id_result[0]
            
            # Добавляем запись
            self.cursor.execute('''
                INSERT INTO admin_actions (admin_id, action_type, target_id, details)
                VALUES (?, ?, ?, ?)
            ''', (admin_id, action_type, target_id, details))
            
            self.conn.commit()

        except Exception as e:
            print(f"Ошибка логирования действия: {e}")
    

    # ========== Р¤РЈРќРљР¦РР Р”Р›РЇ РЎР•Р—РћРќРћР’ ==========
    def create_season(self, admin_nickname, name, start_date, end_date, premium_reward=0):
        """РЎРѕР·РґР°РЅРёРµ РЅРѕРІРѕРіРѕ СЃРµР·РѕРЅР° (Р°РґРјРёРЅ)"""
        try:
            admin_role = self.get_user_role(admin_nickname)
            if admin_role != 'admin':
                return False, 'РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ'
            self.cursor.execute('''
                INSERT INTO seasons (name, start_date, end_date, premium_reward)
                VALUES (?, ?, ?, ?)
            ''', (name, start_date, end_date, premium_reward))
            self.conn.commit()
            return True, 'РЎРµР·РѕРЅ СЃРѕР·РґР°РЅ'
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    
    def get_active_seasons(self):
        """РџРѕР»СѓС‡РёС‚СЊ Р°РєС‚РёРІРЅС‹Рµ СЃРµР·РѕРЅС‹"""
        try:
            self.cursor.execute('SELECT * FROM seasons WHERE is_active = 1 ORDER BY start_date DESC')
            seasons = []
            for row in self.cursor.fetchall():
                seasons.append({
                    'id': row[0], 'name': row[1], 'start_date': row[2],
                    'end_date': row[3], 'premium_reward': row[4]
                })
            return True, seasons
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    
    # ========== Р¤РЈРќРљР¦РР Р”Р›РЇ РџР Р•РњРРЈРњРђ ==========
    def check_premium_status(self, nickname):
        """РџСЂРѕРІРµСЂРёС‚СЊ РїСЂРµРјРёСѓРј СЃС‚Р°С‚СѓСЃ РёРіСЂРѕРєР°"""
        try:
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (nickname,))
            result = self.cursor.fetchone()
            if not result:
                return False, 'РРіСЂРѕРє РЅРµ РЅР°Р№РґРµРЅ'
            player_id = result[0]
            self.cursor.execute('SELECT premium_until, is_premium FROM premium_users WHERE player_id = ?', (player_id,))
            result = self.cursor.fetchone()
            if result:
                premium_until, is_premium = result
                if premium_until and datetime.strptime(premium_until, '%Y-%m-%d %H:%M:%S') > datetime.now():
                    return True, {'is_premium': True, 'premium_until': premium_until}
                else:
                    self.cursor.execute('UPDATE premium_users SET is_premium = 0 WHERE player_id = ?', (player_id,))
                    self.conn.commit()
            return True, {'is_premium': False, 'premium_until': None}
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    
    def grant_premium(self, nickname, days, source='gift'):
        """Р’С‹РґР°С‚СЊ РїСЂРµРјРёСѓРј СЃС‚Р°С‚СѓСЃ"""
        try:
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (nickname,))
            result = self.cursor.fetchone()
            if not result:
                return False, 'РРіСЂРѕРє РЅРµ РЅР°Р№РґРµРЅ'
            player_id = result[0]
            from datetime import timedelta
            premium_until = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute('''
                INSERT OR REPLACE INTO premium_users (player_id, premium_until, is_premium, premium_source)
                VALUES (?, ?, 1, ?)
            ''', (player_id, premium_until, source))
            self.conn.commit()
            return True, f'РџСЂРµРјРёСѓРј РІС‹РґР°РЅ РЅР° {days} РґРЅРµР№'
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    
    def add_2v2_match(self, nickname, season_id, teammate_nickname, opponent1_nickname, opponent2_nickname, team1_score, team2_score):
        """Р”РѕР±Р°РІРёС‚СЊ РёРіСЂСѓ 2 РЅР° 2"""
        try:
            success, premium_data = self.check_premium_status(nickname)
            if not success or not premium_data.get('is_premium'):
                return False, 'РўСЂРµР±СѓРµС‚СЃСЏ РїСЂРµРјРёСѓРј СЃС‚Р°С‚СѓСЃ РґР»СЏ РёРіСЂ 2 РЅР° 2'
            players = {}
            for nick in [nickname, teammate_nickname, opponent1_nickname, opponent2_nickname]:
                self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (nick,))
                result = self.cursor.fetchone()
                if not result:
                    return False, f'РРіСЂРѕРє {nick} РЅРµ РЅР°Р№РґРµРЅ'
                players[nick] = result[0]
            winner_team = 1 if team1_score > team2_score else 2
            self.cursor.execute('''
                INSERT INTO matches_2v2 (season_id, team1_player1_id, team1_player2_id,
                    team2_player1_id, team2_player2_id, team1_score, team2_score, winner_team)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (season_id, players[nickname], players[teammate_nickname],
                  players[opponent1_nickname], players[opponent2_nickname],
                  team1_score, team2_score, winner_team))
            self.conn.commit()
            return True, 'РРіСЂР° 2 РЅР° 2 РґРѕР±Р°РІР»РµРЅР°'
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    
    # ========== Р¤РЈРќРљР¦РР Р”Р›РЇ Р§РђРўРћР’ ==========
    def get_or_create_chat(self, player1_nickname, player2_nickname):
        """РџРѕР»СѓС‡РёС‚СЊ РёР»Рё СЃРѕР·РґР°С‚СЊ С‡Р°С‚ РјРµР¶РґСѓ РґРІСѓРјСЏ РёРіСЂРѕРєР°РјРё"""
        try:
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (player1_nickname,))
            p1_result = self.cursor.fetchone()
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (player2_nickname,))
            p2_result = self.cursor.fetchone()
            if not p1_result or not p2_result:
                return False, 'РРіСЂРѕРє РЅРµ РЅР°Р№РґРµРЅ'
            p1_id, p2_id = p1_result[0], p2_result[0]
            self.cursor.execute('SELECT id FROM chats WHERE (player1_id = ? AND player2_id = ?) OR (player1_id = ? AND player2_id = ?)',
                          (p1_id, p2_id, p2_id, p1_id))
            chat = self.cursor.fetchone()
            if chat:
                return True, chat[0]
            self.cursor.execute('INSERT INTO chats (player1_id, player2_id) VALUES (?, ?)', (p1_id, p2_id))
            self.conn.commit()
            return True, self.cursor.lastrowid
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    
    def send_message(self, sender_nickname, receiver_nickname, message_text):
        """РћС‚РїСЂР°РІРёС‚СЊ СЃРѕРѕР±С‰РµРЅРёРµ"""
        try:
            success, chat_id = self.get_or_create_chat(sender_nickname, receiver_nickname)
            if not success:
                return False, chat_id
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (sender_nickname,))
            sender_id = self.cursor.fetchone()[0]
            self.cursor.execute('INSERT INTO messages (chat_id, sender_id, message_text) VALUES (?, ?, ?)',
                          (chat_id, sender_id, message_text))
            self.cursor.execute('UPDATE chats SET last_message_time = CURRENT_TIMESTAMP WHERE id = ?', (chat_id,))
            self.conn.commit()
            return True, 'РЎРѕРѕР±С‰РµРЅРёРµ РѕС‚РїСЂР°РІР»РµРЅРѕ'
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    
    def get_chat_messages(self, player1_nickname, player2_nickname, limit=50):
        """РџРѕР»СѓС‡РёС‚СЊ СЃРѕРѕР±С‰РµРЅРёСЏ РёР· С‡Р°С‚Р°"""
        try:
            success, chat_id = self.get_or_create_chat(player1_nickname, player2_nickname)
            if not success:
                return False, chat_id
            self.cursor.execute('''
                SELECT m.id, p.nickname, m.message_text, m.sent_at, m.is_read
                FROM messages m
                JOIN players p ON m.sender_id = p.id
                WHERE m.chat_id = ?
                ORDER BY m.sent_at DESC
                LIMIT ?
            ''', (chat_id, limit))
            messages = []
            for row in self.cursor.fetchall():
                messages.append({
                    'id': row[0], 'sender': row[1], 'text': row[2],
                    'time': row[3], 'is_read': row[4]
                })
            return True, list(reversed(messages))
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    
    def get_user_chats(self, nickname):
        """РџРѕР»СѓС‡РёС‚СЊ СЃРїРёСЃРѕРє С‡Р°С‚РѕРІ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ"""
        try:
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (nickname,))
            result = self.cursor.fetchone()
            if not result:
                return False, 'РРіСЂРѕРє РЅРµ РЅР°Р№РґРµРЅ'
            player_id = result[0]
            self.cursor.execute('''
                SELECT c.id, CASE WHEN c.player1_id = ? THEN p2.nickname ELSE p1.nickname END as other_player,
                       c.last_message_time
                FROM chats c
                JOIN players p1 ON c.player1_id = p1.id
                JOIN players p2 ON c.player2_id = p2.id
                WHERE c.player1_id = ? OR c.player2_id = ?
                ORDER BY c.last_message_time DESC
            ''', (player_id, player_id, player_id))
            chats = []
            for row in self.cursor.fetchall():
                chats.append({'id': row[0], 'other_player': row[1], 'last_message': row[2]})
            return True, chats
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'

    # ========== Р¤РЈРќРљР¦РР Р”Р›РЇ РўРЈР РќРР РћР’ ==========
    def create_tournament(self, admin_nickname, name, description, start_date, end_date, max_players, prize_pool):
        """РЎРѕР·РґР°РЅРёРµ С‚СѓСЂРЅРёСЂР° (Р°РґРјРёРЅ/РјРѕРґРµСЂР°С‚РѕСЂ)"""
        try:
            admin_role = self.get_user_role(admin_nickname)
            if admin_role not in ['admin', 'moderator']:
                return False, 'РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ'
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (admin_nickname,))
            admin_id = self.cursor.fetchone()[0]
            self.cursor.execute('''
                INSERT INTO tournaments (name, description, start_date, end_date, max_players, prize_pool, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, description, start_date, end_date, max_players, prize_pool, admin_id))
            self.conn.commit()
            return True, 'РўСѓСЂРЅРёСЂ СЃРѕР·РґР°РЅ'
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    
    def get_tournaments(self, status=None):
        """РџРѕР»СѓС‡РёС‚СЊ С‚СѓСЂРЅРёСЂС‹"""
        try:
            if status:
                self.cursor.execute('SELECT * FROM tournaments WHERE status = ? ORDER BY start_date DESC', (status,))
            else:
                self.cursor.execute('SELECT * FROM tournaments ORDER BY start_date DESC')
            tournaments = []
            for row in self.cursor.fetchall():
                tournaments.append({
                    'id': row[0], 'name': row[1], 'description': row[2],
                    'start_date': row[3], 'end_date': row[4],
                    'max_players': row[5], 'current_players': row[6],
                    'prize_pool': row[7], 'status': row[8]
                })
            return True, tournaments
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    
    def register_for_tournament(self, nickname, tournament_id):
        """Р РµРіРёСЃС‚СЂР°С†РёСЏ РЅР° С‚СѓСЂРЅРёСЂ"""
        try:
            self.cursor.execute('SELECT id, max_players, current_players, status FROM tournaments WHERE id = ?', (tournament_id,))
            tour = self.cursor.fetchone()
            if not tour:
                return False, 'РўСѓСЂРЅРёСЂ РЅРµ РЅР°Р№РґРµРЅ'
            if tour[3] != 'planned':
                return False, 'Р РµРіРёСЃС‚СЂР°С†РёСЏ Р·Р°РєСЂС‹С‚Р°'
            if tour[2] >= tour[1]:
                return False, 'РўСѓСЂРЅРёСЂ Р·Р°РїРѕР»РЅРµРЅ'
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (nickname,))
            player_id = self.cursor.fetchone()[0]
            self.cursor.execute('INSERT INTO tournament_participants (tournament_id, player_id) VALUES (?, ?)', (tournament_id, player_id))
            self.cursor.execute('UPDATE tournaments SET current_players = current_players + 1 WHERE id = ?', (tournament_id,))
            self.conn.commit()
            return True, 'Р РµРіРёСЃС‚СЂР°С†РёСЏ СѓСЃРїРµС€РЅР°'
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    
    # ========== Р¤РЈРќРљР¦РР Р”Р›РЇ РЎРўРђРўРРЎРўРРљР ==========
    def get_elo_history(self, nickname, limit=100):
        """РџРѕР»СѓС‡РёС‚СЊ РёСЃС‚РѕСЂРёСЋ РёР·РјРµРЅРµРЅРёСЏ ELO"""
        try:
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (nickname,))
            result = self.cursor.fetchone()
            if not result:
                return False, 'РРіСЂРѕРє РЅРµ РЅР°Р№РґРµРЅ'
            player_id = result[0]
            self.cursor.execute('''
                SELECT elo_after, match_date
                FROM matches
                WHERE player_id = ?
                ORDER BY match_date ASC
                LIMIT ?
            ''', (player_id, limit))
            history = []
            for row in self.cursor.fetchall():
                history.append({'elo': row[0], 'date': row[1]})
            return True, history
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    
    def get_map_statistics(self, nickname):
        """РџРѕР»СѓС‡РёС‚СЊ СЃС‚Р°С‚РёСЃС‚РёРєСѓ РїРѕ РєР°СЂС‚Р°Рј"""
        try:
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (nickname,))
            result = self.cursor.fetchone()
            if not result:
                return False, 'РРіСЂРѕРє РЅРµ РЅР°Р№РґРµРЅ'
            player_id = result[0]
            self.cursor.execute('''
                SELECT map_name, 
                       COUNT(*) as total_matches,
                       SUM(CASE WHEN result = 'W' THEN 1 ELSE 0 END) as wins,
                       SUM(CASE WHEN result = 'L' THEN 1 ELSE 0 END) as losses,
                       AVG(kills) as avg_kills,
                       AVG(deaths) as avg_deaths
                FROM matches
                WHERE player_id = ? AND map_name IS NOT NULL
                GROUP BY map_name
            ''', (player_id,))
            stats = []
            for row in self.cursor.fetchall():
                total = row[1]
                wins = row[2]
                win_rate = (wins / total * 100) if total > 0 else 0
                stats.append({
                    'map': row[0], 'total_matches': total,
                    'wins': wins, 'losses': row[3],
                    'win_rate': round(win_rate, 1),
                    'avg_kills': round(row[4] or 0, 1),
                    'avg_deaths': round(row[5] or 0, 1)
                })
            return True, stats
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    
    def get_time_statistics(self, nickname):
        """РџРѕР»СѓС‡РёС‚СЊ СЃС‚Р°С‚РёСЃС‚РёРєСѓ РїРѕ РІСЂРµРјРµРЅРё"""
        try:
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (nickname,))
            result = self.cursor.fetchone()
            if not result:
                return False, 'РРіСЂРѕРє РЅРµ РЅР°Р№РґРµРЅ'
            player_id = result[0]
            self.cursor.execute('''
                SELECT strftime('%H', match_date) as hour,
                       COUNT(*) as total_matches,
                       SUM(CASE WHEN result = 'W' THEN 1 ELSE 0 END) as wins
                FROM matches
                WHERE player_id = ?
                GROUP BY hour
                ORDER BY hour
            ''', (player_id,))
            hour_stats = []
            for row in self.cursor.fetchall():
                total = row[1]
                wins = row[2]
                win_rate = (wins / total * 100) if total > 0 else 0
                hour_stats.append({
                    'hour': int(row[0]), 'total_matches': total,
                    'wins': wins, 'win_rate': round(win_rate, 1)
                })
            self.cursor.execute('''
                SELECT strftime('%w', match_date) as day_of_week,
                       COUNT(*) as total_matches,
                       SUM(CASE WHEN result = 'W' THEN 1 ELSE 0 END) as wins
                FROM matches
                WHERE player_id = ?
                GROUP BY day_of_week
                ORDER BY day_of_week
            ''', (player_id,))
            day_stats = []
            for row in self.cursor.fetchall():
                total = row[1]
                wins = row[2]
                win_rate = (wins / total * 100) if total > 0 else 0
                day_stats.append({
                    'day': int(row[0]), 'total_matches': total,
                    'wins': wins, 'win_rate': round(win_rate, 1)
                })
            return True, {'hours': hour_stats, 'days': day_stats}
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    
    def get_season_comparison(self, nickname):
        """РЎСЂР°РІРЅРµРЅРёРµ СЃС‚Р°С‚РёСЃС‚РёРєРё РјРµР¶РґСѓ СЃРµР·РѕРЅР°РјРё"""
        try:
            self.cursor.execute('SELECT id FROM players WHERE nickname = ?', (nickname,))
            result = self.cursor.fetchone()
            if not result:
                return False, 'РРіСЂРѕРє РЅРµ РЅР°Р№РґРµРЅ'
            player_id = result[0]
            self.cursor.execute('''
                SELECT s.id, s.name, s.start_date, s.end_date,
                       COUNT(m.id) as matches,
                       SUM(CASE WHEN m.result = 'W' THEN 1 ELSE 0 END) as wins,
                       AVG(m.elo_after) as avg_elo
                FROM seasons s
                LEFT JOIN matches m ON m.match_date BETWEEN s.start_date AND s.end_date AND m.player_id = ?
                GROUP BY s.id
                ORDER BY s.start_date DESC
            ''', (player_id,))
            seasons = []
            for row in self.cursor.fetchall():
                matches = row[4] or 0
                wins = row[5] or 0
                win_rate = (wins / matches * 100) if matches > 0 else 0
                seasons.append({
                    'season_id': row[0], 'name': row[1],
                    'matches': matches, 'wins': wins,
                    'win_rate': round(win_rate, 1),
                    'avg_elo': round(row[6] or 0, 0)
                })
            return True, seasons
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    
    def get_detailed_player_profile(self, nickname):
        """РџРѕР»СѓС‡РёС‚СЊ РґРµС‚Р°Р»СЊРЅС‹Р№ РїСЂРѕС„РёР»СЊ РёРіСЂРѕРєР°"""
        try:
            self.cursor.execute('''
                SELECT p.*, pu.is_premium, pu.premium_until
                FROM players p
                LEFT JOIN premium_users pu ON p.id = pu.player_id
                WHERE p.nickname = ?
            ''', (nickname,))
            result = self.cursor.fetchone()
            if not result:
                return False, 'РРіСЂРѕРє РЅРµ РЅР°Р№РґРµРЅ'
            profile = {
                'nickname': result[1], 'elo': result[5], 'wins': result[6],
                'losses': result[7], 'ties': result[8], 'matches': result[9],
                'avg_kd': result[10], 'avg_hs': result[11],
                'win_percentage': result[12], 'total_kills': result[13],
                'total_deaths': result[14], 'avg_kills': result[15],
                'role': result[4], 'is_premium': bool(result[20] if result[20] else False),
                'premium_until': result[21]
            }
            return True, profile
        except Exception as e:
            return False, f'РћС€РёР±РєР°: {e}'
    def handle_client(self, client, address):
        """Обработка клиентского соединения"""
        print(f"[+] Новое соединение: {address}")
        
        while True:
            try:
                # Получаем сообщение от клиента
                message = client.recv(10240).decode('utf-8')
                if not message:
                    break
                
                data = json.loads(message)
                response = self.process_request(data)
                
                # Отправляем ответ
                client.send(json.dumps(response).encode('utf-8'))
                
            except (ConnectionResetError, ConnectionAbortedError):
                print(f"[-] Соединение разорвано: {address}")
                break
            except json.JSONDecodeError:
                print(f"[-] Некорректный JSON от {address}")
                client.send(json.dumps({'success': False, 'message': 'Некорректный формат данных'}).encode('utf-8'))
                break
            except Exception as e:
                print(f"Ошибка обработки клиента {address}: {e}")
                break
        
        # Закрываем соединение
        print(f"[-] Соединение закрыто: {address}")
        client.close()
    
    def process_request(self, data):
        """Обработка запроса от клиента"""
        try:
            action = data.get('action')
            
            if action == 'register':
                nickname = data.get('nickname', '').strip()
                password = data.get('password', '').strip()
                email = data.get('email', '').strip()
                
                if not nickname or not password:
                    return {'success': False, 'message': 'Ник и пароль обязательны'}
                
                success, message = self.register_player(nickname, password, email)
                return {'success': success, 'message': message}
            
            elif action == 'login':
                nickname = data.get('nickname', '').strip()
                password = data.get('password', '').strip()
                
                if not nickname or not password:
                    return {'success': False, 'message': 'Ник и пароль обязательны'}
                
                success, message, role = self.authenticate_player(nickname, password)
                return {'success': success, 'message': message, 'role': role}
            
            elif action == 'update_stats':
                nickname = data.get('nickname', '').strip()
                stats = data.get('stats', {})
                
                if not nickname:
                    return {'success': False, 'message': 'Ник обязателен'}
                
                success, message = self.update_player_stats(nickname, stats)
                
                if success and 'match' in data:
                    match_success, match_message = self.add_match(nickname, data['match'])
                    if not match_success:
                        message += f" (матч не сохранен: {match_message})"
                
                return {'success': success, 'message': message}
            
            elif action == 'get_stats':
                nickname = data.get('nickname', '').strip()
                
                if not nickname:
                    return {'success': False, 'message': 'Ник обязателен'}
                
                stats = self.get_player_stats(nickname)
                if stats:
                    return {'success': True, 'stats': stats}
                else:
                    return {'success': False, 'message': 'Игрок не найден'}
            
            elif action == 'get_leaderboard':
                limit = data.get('limit', 50)
                sort_by = data.get('sort_by', 'elo')
                
                leaderboard = self.get_leaderboard(limit, sort_by)
                return {'success': True, 'leaderboard': leaderboard}
            
            elif action == 'admin_get_players':
                nickname = data.get('nickname', '').strip()
                limit = data.get('limit', 100)
                offset = data.get('offset', 0)
                
                # Проверяем права
                role = self.get_user_role(nickname)
                if role not in ['admin', 'moderator']:
                    return {'success': False, 'message': 'Недостаточно прав'}
                
                players, total = self.get_all_players(limit, offset)
                return {'success': True, 'players': players, 'total': total}
            
            elif action == 'admin_get_matches':
                nickname = data.get('nickname', '').strip()
                limit = data.get('limit', 50)
                
                # Проверяем права
                role = self.get_user_role(nickname)
                if role not in ['admin', 'moderator']:
                    return {'success': False, 'message': 'Недостаточно прав'}
                
                matches = self.get_recent_matches(limit)
                return {'success': True, 'matches': matches}
            
            elif action == 'admin_change_role':
                admin_nickname = data.get('admin_nickname', '').strip()
                target_nickname = data.get('target_nickname', '').strip()
                new_role = data.get('new_role', 'player')
                
                success, message = self.admin_change_role(admin_nickname, target_nickname, new_role)
                return {'success': success, 'message': message}
            
            elif action == 'admin_ban_player':
                admin_nickname = data.get('admin_nickname', '').strip()
                target_nickname = data.get('target_nickname', '').strip()
                reason = data.get('reason', 'Нарушение правил')
                days = data.get('days', 0)
                
                success, message = self.admin_ban_player(admin_nickname, target_nickname, reason, days)
                return {'success': success, 'message': message}
            
            elif action == 'admin_unban_player':
                admin_nickname = data.get('admin_nickname', '').strip()
                target_nickname = data.get('target_nickname', '').strip()
                
                success, message = self.admin_unban_player(admin_nickname, target_nickname)
                return {'success': success, 'message': message}
            
            elif action == 'admin_verify_match':
                admin_nickname = data.get('admin_nickname', '').strip()
                match_id = data.get('match_id')
                verify = data.get('verify', True)
                
                success, message = self.admin_verify_match(admin_nickname, match_id, verify)
                return {'success': success, 'message': message}
            
            
            elif action == 'admin_delete_match':
                admin_nickname = data.get('admin_nickname', '').strip()
                match_id = data.get('match_id')
                
                success, message = self.admin_delete_match(admin_nickname, match_id)
                return {'success': success, 'message': message}
            elif action == 'admin_reset_stats':
                admin_nickname = data.get('admin_nickname', '').strip()
                target_nickname = data.get('target_nickname', '').strip()
                
                success, message = self.admin_reset_stats(admin_nickname, target_nickname)
                return {'success': success, 'message': message}
            
            elif action == 'admin_get_stats':
                nickname = data.get('nickname', '').strip()
                
                # Проверяем права
                role = self.get_user_role(nickname)
                if role not in ['admin', 'moderator']:
                    return {'success': False, 'message': 'Недостаточно прав'}
                
                stats = self.admin_get_stats()
                return {'success': True, 'stats': stats}
            
            
            elif action == 'create_season':
                admin_nickname = data.get('admin_nickname', '').strip()
                name = data.get('name', '').strip()
                start_date = data.get('start_date', '').strip()
                end_date = data.get('end_date', '').strip()
                premium_reward = data.get('premium_reward', 0)
                success, message = self.create_season(admin_nickname, name, start_date, end_date, premium_reward)
                return {'success': success, 'message': message}
            
            elif action == 'get_active_seasons':
                success, seasons = self.get_active_seasons()
                return {'success': success, 'seasons': seasons if success else []}
            
            elif action == 'check_premium_status':
                nickname = data.get('nickname', '').strip()
                success, premium_data = self.check_premium_status(nickname)
                return {'success': success, 'premium_data': premium_data if success else {}}
            
            elif action == 'grant_premium':
                admin_nickname = data.get('admin_nickname', '').strip()
                nickname = data.get('nickname', '').strip()
                days = data.get('days', 0)
                source = data.get('source', 'gift')
                admin_role = self.get_user_role(admin_nickname)
                if admin_role not in ['admin', 'moderator']:
                    return {'success': False, 'message': 'РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ'}
                success, message = self.grant_premium(nickname, days, source)
                return {'success': success, 'message': message}
            
            elif action == 'add_2v2_match':
                nickname = data.get('nickname', '').strip()
                season_id = data.get('season_id')
                teammate_nickname = data.get('teammate_nickname', '').strip()
                opponent1_nickname = data.get('opponent1_nickname', '').strip()
                opponent2_nickname = data.get('opponent2_nickname', '').strip()
                team1_score = data.get('team1_score', 0)
                team2_score = data.get('team2_score', 0)
                success, message = self.add_2v2_match(nickname, season_id, teammate_nickname, opponent1_nickname, opponent2_nickname, team1_score, team2_score)
                return {'success': success, 'message': message}
            
            elif action == 'send_message':
                sender_nickname = data.get('sender_nickname', '').strip()
                receiver_nickname = data.get('receiver_nickname', '').strip()
                message_text = data.get('message_text', '').strip()
                success, message = self.send_message(sender_nickname, receiver_nickname, message_text)
                return {'success': success, 'message': message}
            
            elif action == 'get_chat_messages':
                player1_nickname = data.get('player1_nickname', '').strip()
                player2_nickname = data.get('player2_nickname', '').strip()
                limit = data.get('limit', 50)
                success, messages = self.get_chat_messages(player1_nickname, player2_nickname, limit)
                return {'success': success, 'messages': messages if success else []}
            
            elif action == 'get_user_chats':
                nickname = data.get('nickname', '').strip()
                success, chats = self.get_user_chats(nickname)
                return {'success': success, 'chats': chats if success else []}
            
            elif action == 'create_tournament':
                admin_nickname = data.get('admin_nickname', '').strip()
                name = data.get('name', '').strip()
                description = data.get('description', '').strip()
                start_date = data.get('start_date', '').strip()
                end_date = data.get('end_date', '').strip()
                max_players = data.get('max_players', 16)
                prize_pool = data.get('prize_pool', '').strip()
                success, message = self.create_tournament(admin_nickname, name, description, start_date, end_date, max_players, prize_pool)
                return {'success': success, 'message': message}
            
            elif action == 'get_tournaments':
                status = data.get('status')
                success, tournaments = self.get_tournaments(status)
                return {'success': success, 'tournaments': tournaments if success else []}
            
            elif action == 'register_for_tournament':
                nickname = data.get('nickname', '').strip()
                tournament_id = data.get('tournament_id')
                success, message = self.register_for_tournament(nickname, tournament_id)
                return {'success': success, 'message': message}
            
            elif action == 'get_elo_history':
                nickname = data.get('nickname', '').strip()
                limit = data.get('limit', 100)
                success, history = self.get_elo_history(nickname, limit)
                return {'success': success, 'history': history if success else []}
            
            elif action == 'get_map_statistics':
                nickname = data.get('nickname', '').strip()
                success, stats = self.get_map_statistics(nickname)
                return {'success': success, 'stats': stats if success else []}
            
            elif action == 'get_time_statistics':
                nickname = data.get('nickname', '').strip()
                success, stats = self.get_time_statistics(nickname)
                return {'success': success, 'stats': stats if success else {}}
            
            elif action == 'get_season_comparison':
                nickname = data.get('nickname', '').strip()
                success, seasons = self.get_season_comparison(nickname)
                return {'success': success, 'seasons': seasons if success else []}
            
            elif action == 'get_detailed_player_profile':
                nickname = data.get('nickname', '').strip()
                success, profile = self.get_detailed_player_profile(nickname)
                return {'success': success, 'profile': profile if success else {}}
            elif action == 'ping':
                return {'success': True, 'message': 'pong'}
            
            else:
                return {'success': False, 'message': 'Неизвестное действие'}
                
        except Exception as e:
            print(f"Ошибка обработки запроса: {e}")
            return {'success': False, 'message': f'Внутренняя ошибка сервера: {e}'}
    
    def start_server(self):
        """Запуск сервера"""
        try:
            self.server.bind((self.host, self.port))
            self.server.listen(5)
            print(f"[*] Сервер запущен на {self.host}:{self.port}")
            print(f"[*] Ожидание подключений...")
            
            while True:
                client, address = self.server.accept()
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client, address),
                    daemon=True
                )
                thread.start()
                print(f"[*] Активных соединений: {threading.active_count() - 1}")
                
        except KeyboardInterrupt:
            print("\n[*] Остановка сервера...")
        except Exception as e:
            print(f"Ошибка сервера: {e}")
        finally:
            self.server.close()
            self.conn.close()
            print("[*] Сервер остановлен")

def main():
    """Основная функция запуска сервера"""
    print("=" * 50)
    print("FaceIt Scoreboard Server с админ-панелью")
    print("=" * 50)
    
    # Настройки сервера
    host = input("Введите host (по умолчанию 0.0.0.0): ").strip() or '0.0.0.0'
    port_input = input("Введите порт (по умолчанию 5555): ").strip()
    port = int(port_input) if port_input.isdigit() else 5555
    
    server = FaceItScoreboardServer(host=host, port=port)
    
    try:
        server.start_server()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()

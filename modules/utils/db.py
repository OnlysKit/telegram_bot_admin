import aiosqlite
import os
from typing import List, Optional, Dict, Any, Tuple
from modules.configs.config import DB_NAME


class DatabaseRow(dict):
    """
    Кастомный класс для строк базы данных, который поддерживает метод .get()
    и другие методы словаря, но также позволяет обращаться к данным как к атрибутам.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def __getattr__(self, key):
        """Позволяет обращаться к данным как к атрибутам: row.key"""
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")
    
    def get(self, key, default=None):
        """Поддерживает метод .get() как у обычного словаря"""
        return super().get(key, default)
    
    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

async def ensure_database_exists() -> None:
    """
    Проверяет существование файла базы данных и создает его, если необходимо.
    Также создает папку pfiles, если она не существует.
    Использует безопасный подход с проверкой подключения к БД.
    """
    try:
        # Проверяем существование папки pfiles
        pfiles_dir = os.path.dirname(DB_NAME)
        if not os.path.exists(pfiles_dir):
            os.makedirs(pfiles_dir, exist_ok=True)  # exist_ok=True предотвращает ошибку если папка уже создана
            print(f"Создана папка: {pfiles_dir}")
        
        # Проверяем существование файла базы данных
        if not os.path.exists(DB_NAME):
            print(f"Файл базы данных не найден: {DB_NAME}. Создаем новый...")
            # Создаем файл базы данных, подключившись к нему
            async with aiosqlite.connect(DB_NAME, isolation_level=None) as connection:
                cursor = await connection.cursor()
                # Выполняем простой запрос для создания файла
                await cursor.execute("SELECT 1")
                await connection.commit()
                await cursor.close()
            print(f"Файл базы данных успешно создан: {DB_NAME}")
        else:
            # Дополнительная проверка: пытаемся подключиться к существующей БД
            try:
                async with aiosqlite.connect(DB_NAME, isolation_level=None) as connection:
                    cursor = await connection.cursor()
                    await cursor.execute("SELECT 1")
                    await cursor.close()
                print(f"Файл базы данных существует и доступен: {DB_NAME}")
            except Exception as db_error:
                print(f"Файл базы данных существует, но недоступен: {db_error}")
                raise Exception(f"База данных {DB_NAME} существует, но недоступна: {db_error}")
            
    except Exception as e:
        print(f"Ошибка при создании/проверке базы данных: {e}")
        raise

async def insert_async(columns: List[str], values: List[Any], table: str) -> None:
    """
    Вставляет запись в указанную таблицу.

    Args:
        columns: Список имен столбцов.
        values: Список значений для вставки.
        table: Имя таблицы.
    """
    async with aiosqlite.connect(DB_NAME, isolation_level=None) as connection:
        cursor = await connection.cursor()
        query = f'INSERT INTO {table} ({", ".join(columns)}) VALUES ({", ".join(["?" for _ in columns])})'
        try:
            await cursor.execute(query, values)
            await connection.commit()
        except aiosqlite.Error as e:
            print(f"Ошибка при вставке в таблицу {table}: {e}")
            raise
        finally:
            await cursor.close()


async def update_generic_async(table: str, columns: List[str], values: List[Any], **where_conditions: Any) -> None:
    """
    Обновляет записи в таблице по заданным условиям.

    Args:
        table: Имя таблицы.
        columns: Список столбцов для обновления.
        values: Список значений для обновления.
        where_conditions: Условия для фильтрации записей.
    """
    async with aiosqlite.connect(DB_NAME, isolation_level=None) as connection:
        cursor = await connection.cursor()
        set_clause = ', '.join([f'{col}=?' for col in columns])
        where_clause = ' AND '.join([f'{key}=?' for key in where_conditions.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        values = tuple(values + list(where_conditions.values()))
        try:
            await cursor.execute(query, values)
            await connection.commit()
        except aiosqlite.Error as e:
            print(f"Ошибка при обновлении таблицы {table}: {e}")
            raise
        finally:
            await cursor.close()


async def get_one_generic_async(table: str, get_random: bool = False, **kwargs: Any) -> Optional[DatabaseRow]:
    """
    Получает одну запись из таблицы по заданным условиям.

    Args:
        table: Имя таблицы.
        get_random: Если True, выбирает случайную запись.
        **kwargs: Условия фильтрации (ключ=значение).

    Returns:
        DatabaseRow с данными записи или None, если запись не найдена.
        Поддерживает обращение как к словарю: row['key'], row.get('key')
        И как к атрибутам: row.key
    """
    get_random_clause = 'ORDER BY RANDOM() LIMIT 1' if get_random else ''
    async with aiosqlite.connect(DB_NAME, isolation_level=None) as connection:
        connection.row_factory = aiosqlite.Row
        cursor = await connection.cursor()
        conditions = " AND ".join([f"{key} = ?" for key in kwargs.keys()])
        values = tuple(kwargs.values())
        where_clause = f"WHERE {conditions}" if conditions else ""
        query = f"SELECT * FROM {table} {where_clause} {get_random_clause}"
        try:
            await cursor.execute(query, values)
            result = await cursor.fetchone()
            if result:
                # Преобразуем aiosqlite.Row в DatabaseRow для поддержки .get() и атрибутов
                return DatabaseRow(dict(result))
            return None
        except aiosqlite.Error as e:
            print(f"Ошибка при получении записи из таблицы {table}: {e}")
            raise
        finally:
            await cursor.close()


async def get_all_generic_async(table: str, limit: Optional[int] = None, **kwargs: Any) -> List[DatabaseRow]:
    """
    Получает все записи из таблицы по заданным условиям.

    Args:
        table: Имя таблицы.
        limit: Максимальное количество возвращаемых записей (опционально).
        **kwargs: Условия фильтрации (ключ=значение).

    Returns:
        Список DatabaseRow с данными записей.
        Каждый элемент поддерживает обращение как к словарю: row['key'], row.get('key')
        И как к атрибутам: row.key
    """
    limit_clause = f' LIMIT {limit}' if limit else ''
    async with aiosqlite.connect(DB_NAME, isolation_level=None) as connection:
        connection.row_factory = aiosqlite.Row
        cursor = await connection.cursor()
        conditions = " AND ".join([f"{key} = ?" for key in kwargs.keys()])
        values = tuple(kwargs.values())
        where_clause = f"WHERE {conditions}" if conditions else ""
        query = f"SELECT * FROM {table} {where_clause}{limit_clause}"
        try:
            await cursor.execute(query, values)
            results = await cursor.fetchall()
            # Преобразуем каждую строку в DatabaseRow
            return [DatabaseRow(dict(row)) for row in results]
        except aiosqlite.Error as e:
            print(f"Ошибка при получении записей из таблицы {table}: {e}")
            raise
        finally:
            await cursor.close()
            
            
async def get_records_from_to_date(table, limit=None, **kwargs) -> List[DatabaseRow]:
    
    """
    Выборка с фильтрами по колонкам.
    
    Аргумент date может быть:
      - date="2025-07-14"                  -> date = ...
      - date=("2025-07-14", "2025-07-25")  -> BETWEEN
      - date=("2025-07-14", None)          -> date >= ...
      - date=(None, "2025-07-25")          -> date <= ...
      - date=["2025-05-13","2025-05-25"]   -> IN (...)
    
    Returns:
        Список DatabaseRow с данными записей.
        Каждый элемент поддерживает обращение как к словарю: row['key'], row.get('key')
        И как к атрибутам: row.key
    """
    limit_clause = f' LIMIT {limit}' if limit else ''

    date_val = kwargs.pop("date", None)

    conditions = []
    values = []

    # обычные равенства
    for key, value in kwargs.items():
        conditions.append(f"{key} = ?")
        values.append(value)

    # обработка date
    if isinstance(date_val, (list, tuple)):
        # список дат (IN)
        if len(date_val) > 0 and all(isinstance(x, str) for x in date_val):
            placeholders = ",".join(["?"] * len(date_val))
            conditions.append(f"date IN ({placeholders})")
            values.extend(date_val)
        else:
            # диапазон
            start, end = (date_val + (None, None))[:2]
            if start and end:
                conditions.append("date BETWEEN ? AND ?")
                values.extend([start, end])
            elif start:
                conditions.append("date >= ?")
                values.append(start)
            elif end:
                conditions.append("date <= ?")
                values.append(end)
    elif date_val:
        conditions.append("date = ?")
        values.append(date_val)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"SELECT * FROM {table} {where_clause} ORDER BY date ASC{limit_clause}"

    async with aiosqlite.connect(DB_NAME, isolation_level=None) as connection:
        connection.row_factory = aiosqlite.Row
        cursor = await connection.cursor()
        try:
            await cursor.execute(query, tuple(values))
            rows = await cursor.fetchall()
            return [DatabaseRow(dict(r)) for r in rows]
        finally:
            await cursor.close()


async def delete_generic_async(table: str, **kwargs: Any) -> None:
    """
    Удаляет записи из таблицы по заданным условиям.

    Args:
        table: Имя таблицы.
        **kwargs: Условия фильтрации (ключ=значение).
    """
    async with aiosqlite.connect(DB_NAME, isolation_level=None) as connection:
        cursor = await connection.cursor()
        conditions = " AND ".join([f"{key} = ?" for key in kwargs.keys()])
        values = tuple(kwargs.values())
        where_clause = f"WHERE {conditions}" if conditions else ""
        query = f"DELETE FROM {table} {where_clause}"
        try:
            await cursor.execute(query, values)
            await connection.commit()
        except aiosqlite.Error as e:
            print(f"Ошибка при удалении из таблицы {table}: {e}")
            raise
        finally:
            await cursor.close()


async def clear_table(table: str) -> None:
    """
    Очищает все записи из указанной таблицы.

    Args:
        table: Имя таблицы.
    """
    async with aiosqlite.connect(DB_NAME, isolation_level=None) as connection:
        cursor = await connection.cursor()
        query = f"DELETE FROM {table}"
        try:
            await cursor.execute(query)
            await connection.commit()
        except aiosqlite.Error as e:
            print(f"Ошибка при очистке таблицы {table}: {e}")
            raise
        finally:
            await cursor.close()


async def update_clear(table: str, columns: List[str], values: List[Any]) -> None:
    """
    Обновляет все записи в таблице без условий.

    Args:
        table: Имя таблицы.
        columns: Список столбцов для обновления.
        values: Список значений для обновления.
    """
    async with aiosqlite.connect(DB_NAME, isolation_level=None) as connection:
        cursor = await connection.cursor()
        set_clause = ', '.join([f'{col}=?' for col in columns])
        query = f"UPDATE {table} SET {set_clause}"
        try:
            await cursor.execute(query, values)
            await connection.commit()
        except aiosqlite.Error as e:
            print(f"Ошибка при обновлении таблицы {table}: {e}")
            raise
        finally:
            await cursor.close()


async def get_extreme_date_records(
    table: str,
    user_id: int,
    category: str,
    limit: Optional[int] = 10,  # Ограничиваем до 10 записей по умолчанию
    **extra_filters: Any,
) -> Tuple[List[DatabaseRow], List[DatabaseRow]]:
    async with aiosqlite.connect(DB_NAME, isolation_level=None) as conn:
        conn.row_factory = aiosqlite.Row

        # Формируем WHERE
        base_conditions = ["user_id = ?", "category = ?", "file_link IS NOT NULL"]
        values = [user_id, category]
        for k, v in extra_filters.items():
            base_conditions.append(f"{k} = ?")
            values.append(v)
        where_clause = " AND ".join(base_conditions)

        # 1) Выбираем одну самую старую запись
        cur_before = await conn.cursor()
        query_before = (
            f"SELECT * FROM {table} "
            f"WHERE {where_clause} "
            f"ORDER BY date ASC "
            f"LIMIT 1"
        )
        await cur_before.execute(query_before, tuple(values))
        before_records = [DatabaseRow(dict(r)) for r in await cur_before.fetchall()]
        await cur_before.close()

        # 2) Выбираем до limit самых новых записей, исключая unique_num из before_records
        cur_after = await conn.cursor()
        limit_clause = f" LIMIT {limit}" if limit is not None else " LIMIT 10"
        if before_records:
            before_ids = [record["unique_num"] for record in before_records]
            query_after = (
                f"SELECT * FROM {table} "
                f"WHERE {where_clause} "
                f"AND unique_num NOT IN ({', '.join('?' for _ in before_ids)}) "
                f"ORDER BY date DESC "
                f"{limit_clause}"
            )
            after_values = values + before_ids
        else:
            query_after = (
                f"SELECT * FROM {table} "
                f"WHERE {where_clause} "
                f"ORDER BY date DESC "
                f"{limit_clause}"
            )
            after_values = values

        await cur_after.execute(query_after, tuple(after_values))
        after_records = [DatabaseRow(dict(r)) for r in await cur_after.fetchall()]
        await cur_after.close()

        return before_records, after_records


async def table_exists(table_name: str) -> bool:
    """
    Проверяет существование таблицы в базе данных.
    
    Args:
        table_name: Имя таблицы для проверки.
        
    Returns:
        True если таблица существует, False в противном случае.
    """
    async with aiosqlite.connect(DB_NAME, isolation_level=None) as connection:
        cursor = await connection.cursor()
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        try:
            await cursor.execute(query, (table_name,))
            result = await cursor.fetchone()
            return result is not None
        except aiosqlite.Error as e:
            print(f"Ошибка при проверке существования таблицы {table_name}: {e}")
            raise
        finally:
            await cursor.close()


async def get_table_columns(table_name: str) -> List[str]:
    """
    Получает список всех колонок в указанной таблице.
    
    Args:
        table_name: Имя таблицы.
        
    Returns:
        Список имен колонок.
    """
    async with aiosqlite.connect(DB_NAME, isolation_level=None) as connection:
        cursor = await connection.cursor()
        query = f"PRAGMA table_info({table_name})"
        try:
            await cursor.execute(query)
            columns_info = await cursor.fetchall()
            return [column[1] for column in columns_info]  # column[1] - это имя колонки
        except aiosqlite.Error as e:
            print(f"Ошибка при получении колонок таблицы {table_name}: {e}")
            raise
        finally:
            await cursor.close()


async def add_column_to_table(table_name: str, column_name: str, column_type: str = "TEXT") -> None:
    """
    Добавляет новую колонку в существующую таблицу.
    
    Args:
        table_name: Имя таблицы.
        column_name: Имя новой колонки.
        column_type: Тип данных колонки (по умолчанию TEXT).
    """
    async with aiosqlite.connect(DB_NAME, isolation_level=None) as connection:
        cursor = await connection.cursor()
        query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        try:
            await cursor.execute(query)
            await connection.commit()
        except aiosqlite.Error as e:
            print(f"Ошибка при добавлении колонки {column_name} в таблицу {table_name}: {e}")
            raise
        finally:
            await cursor.close()


async def create_table_with_columns(table_name: str, columns: List[str], 
                                  column_types: Optional[Dict[str, str]] = None) -> None:
    """
    Создает новую таблицу с указанными колонками.
    
    Args:
        table_name: Имя таблицы.
        columns: Список имен колонок.
        column_types: Словарь с типами данных для колонок (по умолчанию все TEXT).
    """
    if column_types is None:
        column_types = {}
    
    # Формируем определение колонок
    column_definitions = []
    for column in columns:
        column_type = column_types.get(column, "TEXT")
        column_definitions.append(f"{column} {column_type}")
    
    columns_sql = ", ".join(column_definitions)
    
    async with aiosqlite.connect(DB_NAME, isolation_level=None) as connection:
        cursor = await connection.cursor()
        query = f"CREATE TABLE {table_name} ({columns_sql})"
        try:
            await cursor.execute(query)
            await connection.commit()
        except aiosqlite.Error as e:
            print(f"Ошибка при создании таблицы {table_name}: {e}")
            raise
        finally:
            await cursor.close()


async def creator(table: str, column_types: Dict[str, str]) -> None:
    """
    Гибкая функция для создания таблиц и колонок с предварительной проверкой существования.
    
    Создает таблицу, если её нет, и добавляет недостающие колонки в существующую таблицу.
    Автоматически добавляет колонку 'id' с типом 'INTEGER PRIMARY KEY' (автоинкремент) если её нет.
    
    Args:
        table: Имя таблицы для создания/обновления.
        column_types: Словарь с типами данных для колонок.
                     Ключи - имена колонок, значения - их типы данных.
                     Пример: {"age": "INTEGER", "name": "TEXT"}
    
    Примеры использования:
        # Создание простой таблицы (колонка id добавится автоматически)
        await creator(table="users", column_types={
            "name": "TEXT NOT NULL",
            "country": "TEXT"
        })
        
        # Создание таблицы с различными типами данных
        await creator(table="products", column_types={
            "name": "TEXT NOT NULL",
            "price": "REAL",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
        })
    """
    try:
        # Добавляем колонку id с автоматическим инкрементом, если её нет в column_types
        if "id" not in column_types:
            column_types = {"id": "INTEGER PRIMARY KEY", **column_types}
        
        # Получаем список колонок из ключей словаря
        columns = list(column_types.keys())
        
        # Проверяем существование таблицы
        if not await table_exists(table):
            print(f"Таблица {table} не существует. Создаем новую таблицу...")
            await create_table_with_columns(table, columns, column_types)
            print(f"Таблица {table} успешно создана с колонками: {', '.join(columns)}")
        else:
            print(f"Таблица {table} уже существует. Проверяем колонки...")
            
            # Получаем существующие колонки
            existing_columns = await get_table_columns(table)
            
            # Находим недостающие колонки
            missing_columns = [col for col in columns if col not in existing_columns]
            
            if missing_columns:
                print(f"Найдены недостающие колонки: {', '.join(missing_columns)}")
                
                # Добавляем недостающие колонки
                for column in missing_columns:
                    column_type = column_types[column]
                    try:
                        await add_column_to_table(table, column, column_type)
                        print(f"Колонка {column} добавлена в таблицу {table}")
                    except Exception as e:
                        if "PRIMARY KEY" in column_type.upper():
                            print(f"Предупреждение: Нельзя добавить PRIMARY KEY колонку '{column}' к существующей таблице {table}")
                            print(f"PRIMARY KEY колонки можно добавить только при создании новой таблицы")
                        else:
                            print(f"Ошибка при добавлении колонки {column}: {e}")
                        # Продолжаем с другими колонками
                        continue
            else:
                print(f"Все необходимые колонки уже существуют в таблице {table}")
                
    except Exception as e:
        print(f"Ошибка при создании/обновлении таблицы {table}: {e}")
        raise



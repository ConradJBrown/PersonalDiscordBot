import aiosqlite
import datetime
import os

DB_FILE = "tasks.db"
SCHEMA_VERSION = 1

# Automatically run this on startup
async def migrate_schema():
    db_exists = os.path.exists(DB_FILE)

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("PRAGMA journal_mode=WAL")

        if not db_exists:
            print("Creating new database.")
        
        # Create table if it doesn't exist
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                list_type TEXT,
                task TEXT,
                created_at TEXT,
                completed INTEGER DEFAULT 0
            )
        """)
        await db.commit()

# Fetch tasks (filtered by user, list type, and completion)
async def get_tasks(user_id=None, list_type="personal", completed_only=False):
    async with aiosqlite.connect(DB_FILE) as db:
        if list_type == "grocery":
            query = 'SELECT id, task FROM tasks WHERE list_type = ? AND completed = 0'
            params = ("grocery",)
        elif completed_only:
            query = 'SELECT id, task FROM tasks WHERE user_id = ? AND list_type = ? AND completed = 1'
            params = (str(user_id), "personal")
        else:
            query = 'SELECT id, task FROM tasks WHERE user_id = ? AND list_type = ? AND completed = 0'
            params = (str(user_id), "personal")

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [{"id": row[0], "task": row[1]} for row in rows]

# Replace all tasks for a user or list
async def set_tasks(tasks, user_id=None, list_type="personal"):
    async with aiosqlite.connect(DB_FILE) as db:
        if list_type == "grocery":
            await db.execute('DELETE FROM tasks WHERE list_type = ?', ("grocery",))
            await db.executemany(
                'INSERT INTO tasks (user_id, list_type, task, created_at) VALUES (?, ?, ?, ?)', 
                [("shared", "grocery", t["task"] if isinstance(t, dict) else t, datetime.datetime.utcnow().isoformat()) for t in tasks]
            )
        else:
            await db.execute('DELETE FROM tasks WHERE user_id = ? AND list_type = ?', (str(user_id), "personal"))
            await db.executemany(
                'INSERT INTO tasks (user_id, list_type, task, created_at) VALUES (?, ?, ?, ?)', 
                [(str(user_id), "personal", t["task"] if isinstance(t, dict) else t, datetime.datetime.utcnow().isoformat()) for t in tasks]
            )
        await db.commit()

# Mark a task as completed (by ID)
async def complete_task(task_id: int):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('UPDATE tasks SET completed = 1 WHERE id = ?', (task_id,))
        await db.commit()

# Hard-delete a task (rarely needed)
async def delete_task(task_id: int):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        await db.commit()

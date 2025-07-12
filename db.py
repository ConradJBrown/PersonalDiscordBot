import aiosqlite

DB_FILE = "tasks.db"

# -----------------------
# Database Setup / Migrate
# -----------------------

async def migrate_schema():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task TEXT NOT NULL,
                category TEXT DEFAULT 'general'
            )
        """)
        await db.commit()

# -----------------------
# Task Utilities
# -----------------------

async def get_tasks(user_id=None, category=None, list_type=None):
    query = "SELECT id, task, category FROM tasks"
    conditions = []
    params = []

    if list_type == "grocery":
        conditions.append("user_id IS NULL")
        conditions.append("category = 'grocery'")
    else:
        if user_id is not None:
            conditions.append("user_id = ?")
            params.append(user_id)
        if category:
            conditions.append("category = ?")
            params.append(category)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id"

    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        await cursor.close()
        return [dict(row) for row in rows]

async def set_tasks(tasks, user_id=None, category=None, list_type=None):
    async with aiosqlite.connect(DB_FILE) as db:
        # Delete existing tasks for the user/category/list
        if list_type == "grocery":
            await db.execute("DELETE FROM tasks WHERE user_id IS NULL AND category = 'grocery'")
        elif user_id is not None:
            if category:
                await db.execute("DELETE FROM tasks WHERE user_id = ? AND category = ?", (user_id, category))
            else:
                await db.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
        await db.commit()

        # Insert updated tasks
        for task in tasks:
            task_text = task["task"] if isinstance(task, dict) else str(task)
            task_category = task.get("category", category or "general") if isinstance(task, dict) else (category or "general")


            await db.execute(
                "INSERT INTO tasks (user_id, task, category) VALUES (?, ?, ?)",
                (None if list_type == "grocery" else user_id, task_text, task_category)
            )
        await db.commit()

async def complete_task(task_id):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await db.commit()

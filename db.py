import aiosqlite

DB_FILE = "tasks.db"

# -----------------------
# Database Setup / Migrate
# -----------------------

async def migrate_schema():
    async with aiosqlite.connect(DB_FILE) as db:
        # Create tasks table with new fields
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                user_id INTEGER,
                task TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                priority TEXT DEFAULT 'medium',
                due_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create completed_tasks table for history
        await db.execute("""
            CREATE TABLE IF NOT EXISTS completed_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_task_id INTEGER,
                channel_id INTEGER,
                user_id INTEGER,
                task TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                priority TEXT DEFAULT 'medium',
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_by INTEGER
            )
        """)
        
        # Create dinner_ideas table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS dinner_ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_name TEXT NOT NULL,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check and add new columns if they don't exist (for existing databases)
        cursor = await db.execute("PRAGMA table_info(tasks)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'priority' not in column_names:
            await db.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium'")
        if 'due_date' not in column_names:
            await db.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")
        if 'created_at' not in column_names:
            await db.execute("ALTER TABLE tasks ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        if 'channel_id' not in column_names:
            await db.execute("ALTER TABLE tasks ADD COLUMN channel_id INTEGER")

        cursor = await db.execute("PRAGMA table_info(completed_tasks)")
        ct_columns = await cursor.fetchall()
        ct_column_names = [col[1] for col in ct_columns]
        if 'channel_id' not in ct_column_names:
            await db.execute("ALTER TABLE completed_tasks ADD COLUMN channel_id INTEGER")
            
        await db.commit()

# -----------------------
# Task Utilities
# -----------------------

async def get_tasks(user_id=None, category=None, list_type=None, channel_id=None):
    query = "SELECT id, task, category, priority, due_date, created_at FROM tasks"
    conditions = []
    params = []

    if list_type == "grocery":
        conditions.append("user_id IS NULL")
        conditions.append("category = 'grocery'")
    elif channel_id is not None:
        conditions.append("channel_id = ?")
        params.append(channel_id)
    else:
        if user_id is not None:
            conditions.append("user_id = ?")
            params.append(user_id)
        if category:
            conditions.append("category = ?")
            params.append(category)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    # Order by priority (high, medium, low), then due_date, then id
    query += " ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END, due_date, id"

    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        await cursor.close()
        return [dict(row) for row in rows]

async def insert_task(channel_id, user_id, task, category="general", priority="medium", due_date=None):
    """Insert a single task tied to a Discord channel."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO tasks (channel_id, user_id, task, category, priority, due_date) VALUES (?, ?, ?, ?, ?, ?)",
            (channel_id, user_id, task, category, priority, due_date)
        )
        await db.commit()

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
            task_priority = task.get("priority", "medium") if isinstance(task, dict) else "medium"
            task_due_date = task.get("due_date") if isinstance(task, dict) else None

            await db.execute(
                "INSERT INTO tasks (user_id, task, category, priority, due_date) VALUES (?, ?, ?, ?, ?)",
                (None if list_type == "grocery" else user_id, task_text, task_category, task_priority, task_due_date)
            )
        await db.commit()

async def complete_task(task_id, completed_by=None):
    """Mark a task as complete by moving it to completed_tasks table"""
    async with aiosqlite.connect(DB_FILE) as db:
        # Get the task details before deleting
        cursor = await db.execute(
            "SELECT id, channel_id, user_id, task, category, priority FROM tasks WHERE id = ?",
            (task_id,)
        )
        task = await cursor.fetchone()
        
        if task:
            # Insert into completed_tasks
            await db.execute(
                """INSERT INTO completed_tasks 
                   (original_task_id, channel_id, user_id, task, category, priority, completed_by) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (task[0], task[1], task[2], task[3], task[4], task[5], completed_by)
            )
            
            # Delete from active tasks
            await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            await db.commit()
            return True
        return False

async def get_completed_tasks(user_id=None, limit=10):
    """Get completed tasks history"""
    query = "SELECT task, category, priority, completed_at FROM completed_tasks"
    params = []
    
    if user_id is not None:
        query += " WHERE user_id = ?"
        params.append(user_id)
    
    query += " ORDER BY completed_at DESC LIMIT ?"
    params.append(limit)
    
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        await cursor.close()
        return [dict(row) for row in rows]

async def get_categories(user_id=None):
    """Get all unique categories for a user"""
    query = "SELECT DISTINCT category FROM tasks"
    params = []
    
    if user_id is not None:
        query += " WHERE user_id = ?"
        params.append(user_id)
    
    query += " ORDER BY category"
    
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        await cursor.close()
        return [row[0] for row in rows]

async def clear_channel(channel_id):
    """Clear all tasks in a channel."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM tasks WHERE channel_id = ?", (channel_id,))
        await db.commit()

async def get_channels_with_tasks(guild_id=None):
    """Return distinct channel_ids that have active tasks (optionally filtered by a list of channel ids)."""
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT DISTINCT channel_id FROM tasks WHERE channel_id IS NOT NULL ORDER BY channel_id"
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [row[0] for row in rows]

async def clear_category(user_id, category=None):
    """Clear all tasks in a category (or all categories if None)"""
    async with aiosqlite.connect(DB_FILE) as db:
        if category:
            await db.execute("DELETE FROM tasks WHERE user_id = ? AND category = ?", (user_id, category))
        else:
            await db.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_task_summary(user_id):
    """Get summary of tasks by category and priority"""
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        
        # Active tasks count by category
        cursor = await db.execute("""
            SELECT category, priority, COUNT(*) as count 
            FROM tasks 
            WHERE user_id = ? 
            GROUP BY category, priority
        """, (user_id,))
        active = await cursor.fetchall()
        
        # Completed tasks count today
        cursor = await db.execute("""
            SELECT COUNT(*) as count 
            FROM completed_tasks 
            WHERE user_id = ? AND DATE(completed_at) = DATE('now')
        """, (user_id,))
        completed_today = await cursor.fetchone()
        
        # Completed tasks count this week
        cursor = await db.execute("""
            SELECT COUNT(*) as count 
            FROM completed_tasks 
            WHERE user_id = ? AND DATE(completed_at) >= DATE('now', '-7 days')
        """, (user_id,))
        completed_week = await cursor.fetchone()
        
        return {
            'active': [dict(row) for row in active],
            'completed_today': completed_today[0] if completed_today else 0,
            'completed_week': completed_week[0] if completed_week else 0
        }

# Dinner ideas functions
async def add_dinner_idea(meal_name, added_by):
    """Add a dinner idea"""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO dinner_ideas (meal_name, added_by) VALUES (?, ?)",
            (meal_name, added_by)
        )
        await db.commit()

async def get_dinner_ideas():
    """Get all dinner ideas"""
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT id, meal_name FROM dinner_ideas ORDER BY meal_name")
        rows = await cursor.fetchall()
        await cursor.close()
        return [dict(row) for row in rows]

async def remove_dinner_idea(dinner_id):
    """Remove a dinner idea"""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM dinner_ideas WHERE id = ?", (dinner_id,))
        await db.commit()

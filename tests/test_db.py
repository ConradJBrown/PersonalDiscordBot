import pytest
import aiosqlite
import datetime
from db import migrate_schema, get_tasks, set_tasks, DB_FILE

@pytest.mark.asyncio
async def test_schema_migration(tmp_path):
    test_db = tmp_path / "test_migrate.db"

    # Patch DB_FILE
    import db
    original_db_file = db.DB_FILE
    db.DB_FILE = str(test_db)

    await migrate_schema()

    async with aiosqlite.connect(test_db) as conn:
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = await cursor.fetchall()
        assert ('tasks',) in tables

    db.DB_FILE = original_db_file

@pytest.mark.asyncio
async def test_set_and_get_personal_tasks(tmp_path):
    test_db = tmp_path / "test_tasks.db"

    import db
    original_db_file = db.DB_FILE
    db.DB_FILE = str(test_db)

    await migrate_schema()

    user_id = "123456"
    tasks = ["Buy milk", "Take out trash"]
    await set_tasks(tasks, user_id=user_id)
    retrieved = await get_tasks(user_id=user_id)

    assert len(retrieved) == 2
    assert retrieved[0]["task"] == "Buy milk"
    assert retrieved[1]["task"] == "Take out trash"

    db.DB_FILE = original_db_file

@pytest.mark.asyncio
async def test_set_and_get_grocery_tasks(tmp_path):
    test_db = tmp_path / "test_grocery.db"

    import db
    original_db_file = db.DB_FILE
    db.DB_FILE = str(test_db)

    await migrate_schema()

    tasks = ["Apples", "Bananas"]
    await set_tasks(tasks, list_type="grocery")
    retrieved = await get_tasks(list_type="grocery")

    assert len(retrieved) == 2
    assert retrieved[0]["task"] == "Apples"
    assert retrieved[1]["task"] == "Bananas"

    db.DB_FILE = original_db_file

import pytest
import aiosqlite
import datetime
from db import migrate_schema, get_tasks, set_tasks, insert_task, clear_channel, get_channels_with_tasks, DB_FILE

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

        # Verify channel_id column exists
        cursor = await conn.execute("PRAGMA table_info(tasks)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        assert 'channel_id' in column_names

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

    tasks = [{"task": "Apples", "category": "grocery"}, {"task": "Bananas", "category": "grocery"}]
    await set_tasks(tasks, list_type="grocery")
    retrieved = await get_tasks(list_type="grocery")

    assert len(retrieved) == 2
    assert retrieved[0]["task"] == "Apples"
    assert retrieved[1]["task"] == "Bananas"

    db.DB_FILE = original_db_file

@pytest.mark.asyncio
async def test_insert_and_get_channel_tasks(tmp_path):
    test_db = tmp_path / "test_channel_tasks.db"

    import db
    original_db_file = db.DB_FILE
    db.DB_FILE = str(test_db)

    await migrate_schema()

    channel_id = 111222333
    user_id = 999888777
    await insert_task(channel_id, user_id, "Vacuum living room", category="living-room")
    await insert_task(channel_id, user_id, "Dust shelves", category="living-room", priority="low")

    retrieved = await get_tasks(channel_id=channel_id)
    assert len(retrieved) == 2
    task_names = [t["task"] for t in retrieved]
    assert "Vacuum living room" in task_names
    assert "Dust shelves" in task_names

    db.DB_FILE = original_db_file

@pytest.mark.asyncio
async def test_clear_channel(tmp_path):
    test_db = tmp_path / "test_clear_channel.db"

    import db
    original_db_file = db.DB_FILE
    db.DB_FILE = str(test_db)

    await migrate_schema()

    channel_id = 555666777
    await insert_task(channel_id, 1, "Task A")
    await insert_task(channel_id, 1, "Task B")
    assert len(await get_tasks(channel_id=channel_id)) == 2

    await clear_channel(channel_id)
    assert len(await get_tasks(channel_id=channel_id)) == 0

    db.DB_FILE = original_db_file

@pytest.mark.asyncio
async def test_get_channels_with_tasks(tmp_path):
    test_db = tmp_path / "test_channels.db"

    import db
    original_db_file = db.DB_FILE
    db.DB_FILE = str(test_db)

    await migrate_schema()

    await insert_task(100, 1, "Task in channel 100")
    await insert_task(200, 1, "Task in channel 200")
    await insert_task(100, 2, "Another task in channel 100")

    channel_ids = await get_channels_with_tasks()
    assert 100 in channel_ids
    assert 200 in channel_ids
    assert len(channel_ids) == 2

    db.DB_FILE = original_db_file

import discord
from discord.ext import commands
import config

intents = discord.Intents.default()
intents.typing = True  # Enable typing intent (optional)
intents.presences = True  # Enable presence intent (optional)
intents.members = True  # Enable server members intent
intents.message_content = True  # Enable message content intent

bot = commands.Bot(command_prefix='!', intents=intents)

TOKEN = config.TOKEN
client_id = config.client_id
permissions_value = config.permissions_value
scope = config.scope

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

# Function to retrieve the current list of tasks from a database.
async def get_tasks(user_id=None, list_type="personal"):
    import sqlite3

    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    # Update schema to support user_id and list_type
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            user_id TEXT,
            list_type TEXT,
            task TEXT
        )
    ''')

    if list_type == "grocery":
        cursor.execute('SELECT task FROM tasks WHERE list_type = ?', ("grocery",))
    else:
        cursor.execute('SELECT task FROM tasks WHERE user_id = ? AND list_type = ?', (str(user_id), "personal"))

    return [row[0] for row in cursor.fetchall()]

# Function to update the current list of tasks in a database.
async def set_tasks(tasks, user_id=None, list_type="personal"):
    import sqlite3

    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    # Remove old tasks for this user/list_type
    if list_type == "grocery":
        cursor.execute('DELETE FROM tasks WHERE list_type = ?', ("grocery",))
        cursor.executemany('INSERT INTO tasks (user_id, list_type, task) VALUES (?, ?, ?)', [("shared", "grocery", task) for task in tasks])
    else:
        cursor.execute('DELETE FROM tasks WHERE user_id = ? AND list_type = ?', (str(user_id), "personal"))
        cursor.executemany('INSERT INTO tasks (user_id, list_type, task) VALUES (?, ?, ?)', [(str(user_id), "personal", task) for task in tasks])
    conn.commit()

@bot.command(name='help', help='Displays a list of available commands')
async def help_command(ctx):
    help_message = "**Available Commands:**\n"
    for command in bot.commands:
        if not command.hidden:
            help_message += f'`!{command.name}`: {command.help}\n'
    await ctx.send(help_message)


@bot.command(name='todo', help='Displays your personal todo list')
async def display_todo(ctx):
    tasks = await get_tasks(user_id=ctx.author.id)
    if not tasks:
        await ctx.send('No tasks added yet!')
    else:
        await ctx.send("Your Todo List:")
        for i, task in enumerate(tasks, start=1):
            await ctx.send(f'{i}. {task}')

@bot.command(name='todo_user', help="Displays another user's todo list. Usage: !todo_user @username")
async def display_todo_user(ctx, member: discord.Member):
    tasks = await get_tasks(user_id=member.id)
    if not tasks:
        await ctx.send(f'No tasks found for {member.display_name}!')
    else:
        await ctx.send(f"{member.display_name}'s Todo List:")
        for i, task in enumerate(tasks, start=1):
            await ctx.send(f'{i}. {task}')

# Command to add a new task.
@bot.command(name='add', help='Adds a new task to your personal list')
async def add_task(ctx, *, task):
    tasks = await get_tasks(user_id=ctx.author.id)
    tasks.append(task)
    await set_tasks(tasks, user_id=ctx.author.id)
    await ctx.send(f'Task added!')


# Command to add a task to another user's list.
# Usage: !add_user @username task
@bot.command(name='add_user', help="Adds a task to another user's list. Usage: !add_user @username task")
async def add_task_user(ctx, member: discord.Member, *, task):
    tasks = await get_tasks(user_id=member.id)
    tasks.append(task)
    await set_tasks(tasks, user_id=member.id)
    await ctx.send(f'Added task for {member.display_name}!')


# Command to mark a task as completed.
@bot.command(name='complete', help='Marks a personal task as completed')
async def complete_task(ctx, index: int):
    tasks = await get_tasks(user_id=ctx.author.id)
    try:
        del tasks[index - 1]
        await set_tasks(tasks, user_id=ctx.author.id)
        await ctx.send(f'Task {index} marked as completed!')
    except IndexError:
        await ctx.send('Invalid task number!')

@bot.command(name='grocery', help='Displays the shared grocery list')
async def display_grocery(ctx):
    tasks = await get_tasks(list_type="grocery")
    if not tasks:
        await ctx.send('Grocery list is empty!')
    else:
        await ctx.send("Grocery List:")
        for i, task in enumerate(tasks, start=1):
            await ctx.send(f'{i}. {task}')

@bot.command(name='grocery_add', help='Adds an item to the grocery list')
async def add_grocery(ctx, *, item):
    tasks = await get_tasks(list_type="grocery")
    tasks.append(item)
    await set_tasks(tasks, list_type="grocery")
    await ctx.send(f'Added "{item}" to the grocery list!')

@bot.command(name='grocery_complete', help='Removes an item from the grocery list')
async def complete_grocery(ctx, index: int):
    tasks = await get_tasks(list_type="grocery")
    try:
        removed = tasks.pop(index - 1)
        await set_tasks(tasks, list_type="grocery")
        await ctx.send(f'Removed "{removed}" from the grocery list!')
    except IndexError:
        await ctx.send('Invalid item number!')

# Run the bot using a token.
bot.run(TOKEN)

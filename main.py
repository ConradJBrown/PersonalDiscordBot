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
async def get_tasks():
    import sqlite3

    # Database setup.
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    # Create the table for tasks if it doesn't exist.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            task TEXT
        )
    ''')

    # Retrieve the current list of tasks from a database.
    cursor.execute('SELECT * FROM tasks')
    return [row[1] for row in cursor.fetchall()]

# Function to update the current list of tasks in a database.
async def set_tasks(tasks):
    import sqlite3

    # Database setup.
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    # Update the current list of tasks in a database.
    cursor.executemany('INSERT OR REPLACE INTO tasks (task) VALUES (?)', [(task,) for task in tasks])
    conn.commit()

@bot.command(name='help', help='Displays a list of available commands')
async def help_command(ctx):
    await ctx.send('Available Commands:')
    for cog in bot.cogs:
        await ctx.send(f'- {cog}:')
        for cmd in bot.get_cog(cog).get_commands():
            await ctx.send(f'  - !{cmd.name} ({cmd.help})')

# Run the help command when no arguments are passed
@bot.command(name='help', invoke_without_command=True)
async def default_help(ctx):
    await help_command(ctx)

# Run a specific command's help message by passing its name as an argument
@bot.command(name='help')
async def cmd_help(ctx, *, cmd_name: str):
    for cog in bot.cogs:
        if f'{cog}.{cmd_name}' in [cmd.name for cmd in bot.get_cog(cog).get_commands()]:
            await ctx.send(f'Command: !{cmd_name} ({bot.get_cog(cog).get_command(cmd_name).help})')
            return
    await ctx.send('Unknown Command!')


@bot.command(name='todo', help='Displays your todo list')
async def display_todo(ctx):
    tasks = await get_tasks()
    if not ctx.message.content.startswith('!todo'):
        # If they didn't type !todo, send a response explaining how to use it.
        await ctx.send('Type !todo to view your todo list, or use !todo add <task> to add a new task!')
        return
    elif ctx.message.content == '!todo':
        # If they just typed !todo without specifying an action, send the current tasks.
        if not tasks:
            await ctx.send('No tasks added yet!')
        else:
            for i, task in enumerate(tasks, start=1):
                await ctx.send(f'{i}. {task}')
    elif ctx.message.content.startswith('!todo add '):
        # Handle adding a new task
        pass



# Command to add a new task.
@bot.command(name='add', help='Adds a new task')
async def add_task(ctx, *, task):
    # Add a new task to the database and display it in Discord.
    tasks = await get_tasks()
    tasks.append(task)
    await set_tasks(tasks)
    await ctx.send(f'Task added! Current tasks: {tasks}')


# Command to mark a task as completed.
@bot.command(name='complete', help='Marks a task as completed')
async def complete_task(ctx, index):
    # Mark a task as completed in the database and display it in Discord.
    tasks = await get_tasks()
    try:
        del tasks[index - 1]
        await set_tasks(tasks)
        await ctx.send(f'Task {index} marked as completed!')
    except IndexError:
        await ctx.send('Invalid task number!')


# Run the bot using a token.
bot.run(TOKEN)

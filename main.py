import discord
from discord.ext import commands
import config
import aiosqlite
from db import migrate_schema, get_tasks, set_tasks, complete_task
import asyncio  # Make sure this is imported at the top

DB_FILE = "tasks.db"  # Path to your SQLite database file

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = config.TOKEN

# Tracks which message corresponds to which task
bot.task_message_map = {}

@bot.event
async def on_ready():
    await migrate_schema()
    print(f'{bot.user.name} is online!')

# ================================
#           TASK COMMANDS
# ================================

@bot.command(name='todo', help='Displays your personal todo list. Optional: !todo <category>')
async def display_todo(ctx, category: str = "general"):
    tasks = await get_tasks(user_id=ctx.author.id, category=category)

    if not tasks:
        await ctx.send(f'No tasks found in **{category}** category!')
    else:
        await ctx.send(f"**{category.capitalize()} Tasks:**")
        for i, task in enumerate(tasks, start=1):
            msg = await ctx.send(f'{i}. {task["task"]}')
            await msg.add_reaction("✅")
            bot.task_message_map[msg.id] = {
                "task_id": task["id"],
                "user_id": ctx.author.id
            }
            await asyncio.sleep(1.2)  # Avoid rate limiting




@bot.command(name='add', help='Adds a task. Usage: !add <category> <task>')
async def add_task(ctx, category: str, *, task: str):
    tasks = await get_tasks(user_id=ctx.author.id, category=category)
    tasks.append({"task": task, "category": category})
    await set_tasks(tasks, user_id=ctx.author.id, category=category)
    await ctx.send(f'Task added to **{category}**!')



@bot.command(name='edit', help='Edit a task: !edit <task_number> <new_task>')
async def edit_task(ctx, index: int, *, new_task):
    tasks = await get_tasks(user_id=ctx.author.id)
    if 1 <= index <= len(tasks):
        tasks[index - 1] = new_task
        await set_tasks(tasks, user_id=ctx.author.id)
        await ctx.send(f'Task {index} updated!')
    else:
        await ctx.send('Invalid task number!')

@bot.command(name='complete', help='Mark a task as complete: !complete <task_number>')
async def complete_task_cmd(ctx, index: int):
    tasks = await get_tasks(user_id=ctx.author.id)
    if 1 <= index <= len(tasks):
        task = tasks[index - 1]
        await complete_task(task["id"])
        await ctx.send(f'Task {index} marked as completed!')
    else:
        await ctx.send('Invalid task number!')

@bot.command(name='todo_user', help="View another user's list: !todo_user @username")
async def display_todo_user(ctx, member: discord.Member):
    tasks = await get_tasks(user_id=member.id)
    if not tasks:
        await ctx.send(f'No tasks found for {member.display_name}!')
        return

    await ctx.send(f"{member.display_name}'s Todo List:")
    for i, task in enumerate(tasks, start=1):
        await ctx.send(f'{i}. {task["task"]}')

@bot.command(name='add_user', help="Adds a task to another user's list. Usage: !add_user @user task --category=home")
async def add_task_user(ctx, member: discord.Member, *, content):
    parts = content.split('--category=')
    task_text = parts[0].strip()
    category = parts[1].strip() if len(parts) > 1 else None

    tasks = await get_tasks(user_id=member.id)
    tasks.append({"task": task_text, "category": category})
    await set_tasks(tasks, user_id=member.id)
    await ctx.send(f'Task added for {member.display_name}{" to " + category if category else ""}!')


@bot.command(name='edit_user', help="Edit a user's task: !edit_user @username <num> <new_task>")
async def edit_task_user(ctx, member: discord.Member, index: int, *, new_task):
    tasks = await get_tasks(user_id=member.id)
    if 1 <= index <= len(tasks):
        tasks[index - 1] = new_task
        await set_tasks(tasks, user_id=member.id)
        await ctx.send(f'Task {index} updated for {member.display_name}!')
    else:
        await ctx.send('Invalid task number!')

# ================================
#         GROCERY COMMANDS
# ================================

@bot.command(name='grocery', help='Displays the shared grocery list')
async def display_grocery(ctx):
    tasks = await get_tasks(list_type="grocery")
    if not tasks:
        await ctx.send("Grocery list is empty!")
    else:
        await ctx.send("**Grocery List:**")
        for i, task in enumerate(tasks, start=1):
            msg = await ctx.send(f'{i}. {task["task"]}')
            await msg.add_reaction("✅")
            bot.task_message_map[msg.id] = {
                "task_id": task["id"],
                "user_id": "shared"
            }
            await asyncio.sleep(1.2)


@bot.command(name='grocery_add', help='Adds an item to the grocery list')
async def add_grocery(ctx, *, item):
    tasks = await get_tasks(list_type="grocery")
    
    # Ensure we're only appending the task text
    tasks.append(item if isinstance(item, str) else str(item))

    await set_tasks(tasks, list_type="grocery")
    await ctx.send(f'Added \"{item}\" to the grocery list!')

@bot.command(name='grocery_complete', help='Remove item: !grocery_complete <item_number>')
async def complete_grocery(ctx, index: int):
    tasks = await get_tasks(list_type="grocery")
    if 1 <= index <= len(tasks):
        removed = tasks.pop(index - 1)
        await set_tasks(tasks, list_type="grocery")
        await ctx.send(f'Removed "{removed}" from the grocery list!')
    else:
        await ctx.send('Invalid item number!')

# ================================
#          REACTION EVENT
# ================================

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    msg_id = reaction.message.id

    if reaction.emoji == "✅" and msg_id in bot.task_message_map:
        mapping = bot.task_message_map[msg_id]
        task_id = mapping["task_id"]

        if mapping["user_id"] and user.id != mapping["user_id"]:
            await reaction.message.channel.send("You can't complete someone else's task.")
            return

        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            await db.commit()

        await reaction.message.channel.send(f'Task completed by {user.display_name} ✅')
        del bot.task_message_map[msg_id]


# ================================
#              HELP COMMAND
# ================================
bot.remove_command('help')

@bot.command(name='help', help='Displays all commands')
async def help_command(ctx):
    help_text = "**Available Commands:**\n"
    seen = set()

    for command in bot.commands:
        if command.qualified_name not in seen and not command.hidden and not command.aliases:
            help_text += f'`!{command.qualified_name}` - {command.help}\n'
            seen.add(command.qualified_name)

    await ctx.send(help_text)



# ================================
#              ERROR HANDLING
# ================================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands silently

    error_details = (
        f"**Error:** `{type(error).__name__}`\n"
        f"**Message:** {str(error)}"
    )

    # Log to console
    print(f"Ignoring exception in command {ctx.command}:", error)

    # Try sending to the user
    try:
        await ctx.send(f"⚠️ An error occurred:\n{error_details}")
    except discord.Forbidden:
        pass  # Bot can't send messages in that channel


# ================================
#           RUN THE BOT
# ================================

bot.run(TOKEN)

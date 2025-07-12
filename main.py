import discord
from discord.ext import commands
import config
import aiosqlite
import asyncio
from db import migrate_schema, get_tasks, set_tasks, complete_task

DB_FILE = "tasks.db"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = config.TOKEN
bot.task_message_map = {}

def parse_task_and_category(content: str):
    if '--category=' in content:
        task_text, category_part = content.split('--category=', 1)
        return task_text.strip(), category_part.strip()
    return content.strip(), "general"

@bot.event
async def on_ready():
    await migrate_schema()
    print(f'{bot.user.name} is online!')

# ======================
#        TASKS
# ======================

@bot.command(name='todo', help='Displays your personal todo list. Optional: !todo <category>')
async def display_todo(ctx, category: str = "general"):
    tasks = await get_tasks(user_id=ctx.author.id, category=category)
    if not tasks:
        await ctx.send(f'No tasks found in **{category}** category!')
        return

    await ctx.send(f"**{category.capitalize()} Tasks:**")
    for i, task in enumerate(tasks, start=1):
        msg = await ctx.send(f'{i}. {task["task"]}')
        await msg.add_reaction("✅")
        bot.task_message_map[msg.id] = {
            "task_id": task["id"],
            "user_id": ctx.author.id
        }
        await asyncio.sleep(1.2)

@bot.command(name='add', help='Adds a task. Usage: !add <task> [--category=category_name]')
async def add_task(ctx, *, content):
    task_text, category = parse_task_and_category(content)
    tasks = await get_tasks(user_id=ctx.author.id, category=category)
    tasks.append({"task": task_text, "category": category})
    await set_tasks(tasks, user_id=ctx.author.id, category=category)
    await ctx.send(f'Task added to **{category}**!')

@bot.command(name='edit', help='Edit a task: !edit <task_number> <new_task>')
async def edit_task(ctx, index: int, *, new_task):
    tasks = await get_tasks(user_id=ctx.author.id)
    if 1 <= index <= len(tasks):
        tasks[index - 1]["task"] = new_task
        await set_tasks(tasks, user_id=ctx.author.id)
        await ctx.send(f'Task {index} updated!')
    else:
        await ctx.send('Invalid task number!')

@bot.command(name='complete', help='Mark a task as complete: !complete <task_number>')
async def complete_task_cmd(ctx, index: int):
    tasks = await get_tasks(user_id=ctx.author.id)
    if 1 <= index <= len(tasks):
        await complete_task(tasks[index - 1]["id"])
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
    task_text, category = parse_task_and_category(content)
    tasks = await get_tasks(user_id=member.id, category=category)
    tasks.append({"task": task_text, "category": category})
    await set_tasks(tasks, user_id=member.id, category=category)
    await ctx.send(f'Task added for {member.display_name} to **{category}**!')

@bot.command(name='edit_user', help="Edit a user's task: !edit_user @username <num> <new_task>")
async def edit_task_user(ctx, member: discord.Member, index: int, *, new_task):
    tasks = await get_tasks(user_id=member.id)
    if 1 <= index <= len(tasks):
        tasks[index - 1]["task"] = new_task
        await set_tasks(tasks, user_id=member.id)
        await ctx.send(f'Task {index} updated for {member.display_name}!')
    else:
        await ctx.send('Invalid task number!')

# ======================
#     GROCERY LIST
# ======================

@bot.command(name='grocery', help='Displays the shared grocery list')
async def display_grocery(ctx):
    tasks = await get_tasks(list_type="grocery")
    if not tasks:
        await ctx.send("Grocery list is empty!")
        return

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

    tasks.append({"task": item.strip(), "category": "grocery"})

    await set_tasks(tasks, list_type="grocery")
    await ctx.send(f'Added \"{item}\" to the grocery list!')


@bot.command(name='grocery_complete', help='Remove item: !grocery_complete <item_number>')
async def complete_grocery(ctx, index: int):
    tasks = await get_tasks(list_type="grocery")
    if 1 <= index <= len(tasks):
        removed = tasks.pop(index - 1)["task"]
        await set_tasks(tasks, list_type="grocery")
        await ctx.send(f'Removed "{removed}" from the grocery list!')
    else:
        await ctx.send('Invalid item number!')

# ======================
#     REACTION EVENT
# ======================

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    msg_id = reaction.message.id
    if reaction.emoji == "✅" and msg_id in bot.task_message_map:
        mapping = bot.task_message_map[msg_id]
        task_id = mapping["task_id"]

        if mapping["user_id"] != "shared" and user.id != mapping["user_id"]:
            await reaction.message.channel.send("You can't complete someone else's task.")
            return

        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            await db.commit()

        await reaction.message.channel.send(f'Task completed by {user.display_name} ✅')
        del bot.task_message_map[msg_id]

# ======================
#        HELP
# ======================

bot.remove_command('help')

@bot.command(name='help', help='Displays all commands')
async def help_command(ctx):
    help_text = "**Available Commands:**\n"
    for command in bot.commands:
        if not command.hidden:
            help_text += f'`!{command.name}` - {command.help}\n'
    await ctx.send(help_text)

# ======================
#     ERROR HANDLING
# ======================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"Ignoring exception in command {ctx.command}:", error)
    try:
        await ctx.send(f"⚠️ Error: `{type(error).__name__}` - {str(error)}")
    except discord.Forbidden:
        pass

# ======================
#         RUN
# ======================

bot.run(TOKEN)

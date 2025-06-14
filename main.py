import discord
from discord.ext import commands
import config
from db import migrate_schema, get_tasks, set_tasks, complete_task

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

@bot.command(name='todo', help='Displays your personal todo list')
async def display_todo(ctx):
    tasks = await get_tasks(user_id=ctx.author.id)
    if not tasks:
        await ctx.send('No tasks added yet!')
        return

    for i, task in enumerate(tasks, start=1):
        msg = await ctx.send(f'{i}. {task["task"]}')
        await msg.add_reaction("✅")
        bot.task_message_map[msg.id] = {
            "task_id": task["id"],
            "user_id": ctx.author.id
        }

@bot.command(name='add', help='Adds a new task to your personal list')
async def add_task(ctx, *, task_text):
    tasks = await get_tasks(user_id=ctx.author.id)
    tasks.append(task_text)
    await set_tasks(tasks, user_id=ctx.author.id)
    await ctx.send('Task added!')

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

@bot.command(name='add_user', help="Add task to user's list: !add_user @username task")
async def add_task_user(ctx, member: discord.Member, *, task_text):
    tasks = await get_tasks(user_id=member.id)
    tasks.append(task_text)
    await set_tasks(tasks, user_id=member.id)
    await ctx.send(f'Task added for {member.display_name}!')

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

@bot.command(name='grocery', help='View the shared grocery list')
async def display_grocery(ctx):
    tasks = await get_tasks(list_type="grocery")
    if not tasks:
        await ctx.send("The grocery list is empty!")
        return

    await ctx.send("**Grocery List:**")
    for i, task in enumerate(tasks, start=1):
        await ctx.send(f'{i}. {task["task"]}')

@bot.command(name='grocery_add', help='Add to the grocery list: !grocery_add item')
async def add_grocery(ctx, *, item):
    tasks = await get_tasks(list_type="grocery")
    tasks.append(item)
    await set_tasks(tasks, list_type="grocery")
    await ctx.send(f'Added "{item}" to the grocery list!')

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
    if reaction.emoji != "✅" or msg_id not in bot.task_message_map:
        return

    mapping = bot.task_message_map[msg_id]
    if user.id != mapping["user_id"]:
        await reaction.message.channel.send("You can't complete someone else's task.")
        return

    await complete_task(mapping["task_id"])
    await reaction.message.channel.send(f'Task completed by {user.display_name} 🎉')
    del bot.task_message_map[msg_id]

# ================================
#              HELP
# ================================
bot.remove_command('help')
@bot.command(name='help', help='Displays all commands')
async def help_command(ctx):
    help_text = "**Available Commands:**\n"
    for command in bot.commands:
        if not command.hidden:
            help_text += f'`!{command.name}` - {command.help}\n'
    await ctx.send(help_text)

# ================================
#           RUN THE BOT
# ================================

bot.run(TOKEN)

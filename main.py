import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import aiosqlite
import asyncio
from datetime import datetime, timedelta
import random
from db import (
    migrate_schema, get_tasks, set_tasks, insert_task, complete_task,
    get_completed_tasks, get_categories, clear_category, clear_channel,
    get_channels_with_tasks, get_task_summary,
    add_dinner_idea, get_dinner_ideas, remove_dinner_idea
)

# Load environment variables
load_dotenv()

DB_FILE = "tasks.db"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = os.getenv('DISCORD_TOKEN')
bot.task_message_map = {}

# Priority emoji mapping
PRIORITY_EMOJI = {
    'high': '🔴',
    'medium': '🟡',
    'low': '🟢'
}

def parse_task_arguments(content: str):
    """Parse task text, priority, and due date from command"""
    task_text = content
    priority = "medium"
    due_date = None
    
    # Parse priority
    if '--priority=' in task_text:
        parts = task_text.split('--priority=', 1)
        task_text = parts[0].strip()
        priority_part = parts[1].strip().split()[0].lower()
        if priority_part in ['high', 'medium', 'low']:
            priority = priority_part
    
    # Parse due date
    if '--due=' in task_text:
        parts = task_text.split('--due=', 1)
        task_text = parts[0].strip()
        due_date = parts[1].strip().split()[0]
    
    return task_text.strip(), priority, due_date

def format_task_display(task, index=None):
    """Format a task for display with priority and due date"""
    priority_emoji = PRIORITY_EMOJI.get(task.get('priority', 'medium'), '⚪')
    task_text = task['task']
    
    # Add index if provided
    display = f"{index}. " if index else ""
    display += f"{priority_emoji} {task_text}"
    
    # Add due date if exists
    if task.get('due_date'):
        display += f" ⏰ Due: {task['due_date']}"
    
    return display

@bot.event
async def on_ready():
    await migrate_schema()
    check_due_dates.start()  # Start the reminder task
    print(f'{bot.user.name} is online!')

# ======================
#   HOUSEHOLD SETUP
# ======================

HOUSEHOLD_ROOMS = [
    'general',
    'groceries',
    'kitchen',
    'living-room',
    'bedroom',
    'bathroom',
    'garage',
]

@bot.command(name='setup_home', help='Creates a Home category with household channels. Usage: !setup_home')
@commands.has_permissions(manage_channels=True)
async def setup_home(ctx):
    guild = ctx.guild
    if not guild:
        await ctx.send('This command can only be used in a server!')
        return

    existing = discord.utils.get(guild.categories, name='Home')
    if existing:
        await ctx.send('A **Home** category already exists! Use the existing channels to manage household tasks.')
        return

    await ctx.send('🏠 Setting up household channels...')
    category = await guild.create_category('Home')
    for room in HOUSEHOLD_ROOMS:
        await guild.create_text_channel(room, category=category)

    room_list = ', '.join(f'**#{r}**' for r in HOUSEHOLD_ROOMS)
    await ctx.send(
        f'✅ Created the **Home** category with channels: {room_list}\n'
        f'Use `!add <task>` in any of these channels to add tasks to that room\'s list!'
    )

# ======================
#    DUE DATE REMINDERS
# ======================

@tasks.loop(hours=1)
async def check_due_dates():
    """Check for tasks due soon and send reminders"""
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        
        # Get tasks due today or tomorrow
        cursor = await db.execute("""
            SELECT user_id, task, due_date, priority 
            FROM tasks 
            WHERE due_date IS NOT NULL 
            AND DATE(due_date) <= DATE('now', '+1 day')
            AND user_id IS NOT NULL
        """)
        tasks = await cursor.fetchall()
        
        for task in tasks:
            user = await bot.fetch_user(task['user_id'])
            if user:
                priority_emoji = PRIORITY_EMOJI.get(task['priority'], '⚪')
                try:
                    await user.send(f"⏰ Reminder: {priority_emoji} {task['task']} is due on {task['due_date']}!")
                except discord.Forbidden:
                    pass  # User has DMs disabled

@check_due_dates.before_loop
async def before_check_due_dates():
    await bot.wait_until_ready()

# ======================
#        TASKS
# ======================

@bot.command(name='todo', help='Displays the to-do list for this channel. Usage: !todo')
async def display_todo(ctx):
    channel_id = ctx.channel.id
    tasks = await get_tasks(channel_id=channel_id)
    if not tasks:
        await ctx.send(f'No tasks found in **#{ctx.channel.name}**!')
        return

    await ctx.send(f'**📋 #{ctx.channel.name} Tasks:**')
    for i, task in enumerate(tasks, start=1):
        msg_text = format_task_display(task, i)
        msg = await ctx.send(msg_text)
        await msg.add_reaction("✅")
        bot.task_message_map[msg.id] = {
            "task_id": task["id"],
            "channel_id": channel_id
        }
        await asyncio.sleep(1.2)

@bot.command(name='add', help='Adds a task to this channel\'s list. Usage: !add <task> [--priority=high/medium/low] [--due=YYYY-MM-DD]')
async def add_task(ctx, *, content):
    task_text, priority, due_date = parse_task_arguments(content)
    channel_id = ctx.channel.id
    category = ctx.channel.name
    await insert_task(channel_id, ctx.author.id, task_text, category=category, priority=priority, due_date=due_date)
    
    priority_emoji = PRIORITY_EMOJI.get(priority, '⚪')
    due_msg = f" due {due_date}" if due_date else ""
    await ctx.send(f'Task added to **#{ctx.channel.name}** {priority_emoji}{due_msg}!')

@bot.command(name='edit', help='Edit a task in this channel\'s list: !edit <task_number> <new_task>')
async def edit_task(ctx, index: int, *, new_task):
    tasks = await get_tasks(channel_id=ctx.channel.id)
    
    if 1 <= index <= len(tasks):
        task_id = tasks[index - 1]["id"]
        
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                "UPDATE tasks SET task = ? WHERE id = ?",
                (new_task, task_id)
            )
            await db.commit()
        
        await ctx.send(f'Task {index} updated!')
    else:
        await ctx.send('Invalid task number!')

@bot.command(name='complete', help='Mark a task as complete: !complete <task_number>')
async def complete_task_cmd(ctx, index: int):
    tasks = await get_tasks(channel_id=ctx.channel.id)
    if 1 <= index <= len(tasks):
        await complete_task(tasks[index - 1]["id"], completed_by=ctx.author.id)
        await ctx.send(f'✅ Task {index} marked as completed!')
    else:
        await ctx.send('Invalid task number!')

@bot.command(name='todo_user', help="View tasks added by a user in this channel: !todo_user @username")
async def display_todo_user(ctx, member: discord.Member):
    channel_id = ctx.channel.id
    # Fetch channel tasks then filter by user attribution
    all_tasks = await get_tasks(channel_id=channel_id)
    tasks = [t for t in all_tasks if t.get('user_id') == member.id or str(t.get('user_id')) == str(member.id)]
    if not tasks:
        await ctx.send(f'No tasks found for {member.display_name} in **#{ctx.channel.name}**!')
        return

    await ctx.send(f"**{member.display_name}'s tasks in #{ctx.channel.name}:**")
    for i, task in enumerate(tasks, start=1):
        await ctx.send(f'{i}. {task["task"]}')

@bot.command(name='add_user', help="Adds a task to this channel's list on behalf of another user. Usage: !add_user @user <task> [--priority=high/medium/low]")
async def add_task_user(ctx, member: discord.Member, *, content):
    task_text, priority, due_date = parse_task_arguments(content)
    channel_id = ctx.channel.id
    category = ctx.channel.name
    await insert_task(channel_id, member.id, task_text, category=category, priority=priority, due_date=due_date)
    
    priority_emoji = PRIORITY_EMOJI.get(priority, '⚪')
    await ctx.send(f'Task added for {member.display_name} to **#{ctx.channel.name}** {priority_emoji}!')

@bot.command(name='edit_user', help="Edit a user's task in this channel: !edit_user @username <num> <new_task>")
async def edit_task_user(ctx, member: discord.Member, index: int, *, new_task):
    all_tasks = await get_tasks(channel_id=ctx.channel.id)
    user_tasks = [t for t in all_tasks if str(t.get('user_id')) == str(member.id)]
    if 1 <= index <= len(user_tasks):
        task_id = user_tasks[index - 1]["id"]
        
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                "UPDATE tasks SET task = ? WHERE id = ?",
                (new_task, task_id)
            )
            await db.commit()
        
        await ctx.send(f'Task {index} updated for {member.display_name}!')
    else:
        await ctx.send('Invalid task number!')

# ======================
#  CHANNEL TASK MANAGEMENT
# ======================

@bot.command(name='channels', help='List all channels that have active tasks')
async def list_task_channels(ctx):
    if not ctx.guild:
        await ctx.send('This command can only be used in a server!')
        return

    channel_ids = await get_channels_with_tasks()
    if not channel_ids:
        await ctx.send('No channels have active tasks yet!')
        return

    channel_mentions = []
    for cid in channel_ids:
        ch = ctx.guild.get_channel(cid)
        channel_mentions.append(f'**#{ch.name}**' if ch else f'<#{cid}>')

    await ctx.send(f'Channels with active tasks: {", ".join(channel_mentions)}')

@bot.command(name='clear', help='Clear all tasks in this channel. Usage: !clear')
async def clear_tasks(ctx):
    await ctx.send(f'Are you sure you want to clear ALL tasks in **#{ctx.channel.name}**? Reply with `yes` to confirm.')
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'yes'
    
    try:
        await bot.wait_for('message', check=check, timeout=30.0)
        await clear_channel(ctx.channel.id)
        await ctx.send(f'All tasks in **#{ctx.channel.name}** have been cleared!')
    except asyncio.TimeoutError:
        await ctx.send('Clear cancelled.')

# ======================
#  TASK HISTORY
# ======================

@bot.command(name='history', help='View your recently completed tasks. Usage: !history [limit]')
async def view_history(ctx, limit: int = 10):
    completed = await get_completed_tasks(user_id=ctx.author.id, limit=limit)
    if not completed:
        await ctx.send('No completed tasks yet!')
        return
    
    await ctx.send(f'**Recently Completed Tasks (last {limit}):**')
    for i, task in enumerate(completed, start=1):
        priority_emoji = PRIORITY_EMOJI.get(task.get('priority', 'medium'), '⚪')
        completed_at = task['completed_at'].split('.')[0]  # Remove microseconds
        await ctx.send(f'{i}. {priority_emoji} {task["task"]} - Completed: {completed_at}')

# ======================
#  TASK SUMMARY
# ======================

@bot.command(name='summary', help='View your task summary and statistics')
async def task_summary(ctx):
    summary = await get_task_summary(ctx.author.id)
    
    if not summary['active'] and summary['completed_today'] == 0:
        await ctx.send('No task activity yet!')
        return
    
    msg = "**📊 Your Task Summary**\n\n"
    
    # Active tasks by category and priority
    if summary['active']:
        msg += "**Active Tasks:**\n"
        by_category = {}
        for item in summary['active']:
            cat = item['category']
            if cat not in by_category:
                by_category[cat] = {'high': 0, 'medium': 0, 'low': 0}
            by_category[cat][item['priority']] = item['count']
        
        for category, priorities in by_category.items():
            total = sum(priorities.values())
            msg += f"• **{category}**: {total} tasks "
            if priorities['high']:
                msg += f"({PRIORITY_EMOJI['high']}{priorities['high']}) "
            if priorities['medium']:
                msg += f"({PRIORITY_EMOJI['medium']}{priorities['medium']}) "
            if priorities['low']:
                msg += f"({PRIORITY_EMOJI['low']}{priorities['low']})"
            msg += "\n"
    
    msg += f"\n**✅ Completed Today:** {summary['completed_today']}\n"
    msg += f"**📅 Completed This Week:** {summary['completed_week']}\n"
    
    await ctx.send(msg)

# ======================
#     GROCERY LIST
# ======================

@bot.command(name='grocery', help='Displays the shared grocery list')
async def display_grocery(ctx):
    tasks = await get_tasks(list_type="grocery")
    if not tasks:
        await ctx.send("Grocery list is empty!")
        return

    await ctx.send("**🛒 Grocery List:**")
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
        await ctx.send(f'✅ Removed "{removed}" from the grocery list!')
    else:
        await ctx.send('Invalid item number!')

# ======================
#    DINNER PICKER
# ======================

@bot.command(name='dinner_add', help='Add a dinner idea. Usage: !dinner_add <meal name>')
async def add_dinner(ctx, *, meal_name):
    await add_dinner_idea(meal_name, ctx.author.id)
    await ctx.send(f'Added "{meal_name}" to dinner ideas! 🍽️')

@bot.command(name='dinner_list', help='List all dinner ideas')
async def list_dinners(ctx):
    dinners = await get_dinner_ideas()
    if not dinners:
        await ctx.send('No dinner ideas yet! Add some with !dinner_add')
        return
    
    await ctx.send('**🍽️ Dinner Ideas:**')
    for i, dinner in enumerate(dinners, start=1):
        await ctx.send(f'{i}. {dinner["meal_name"]}')

@bot.command(name='dinner_pick', help='Randomly pick a dinner from your ideas')
async def pick_dinner(ctx):
    dinners = await get_dinner_ideas()
    if not dinners:
        await ctx.send('No dinner ideas yet! Add some with !dinner_add')
        return
    
    chosen = random.choice(dinners)
    await ctx.send(f'🎲 Tonight\'s dinner: **{chosen["meal_name"]}**! 🍽️')

@bot.command(name='dinner_remove', help='Remove a dinner idea. Usage: !dinner_remove <number>')
async def remove_dinner(ctx, index: int):
    dinners = await get_dinner_ideas()
    if 1 <= index <= len(dinners):
        dinner_id = dinners[index - 1]["id"]
        await remove_dinner_idea(dinner_id)
        await ctx.send(f'Removed "{dinners[index - 1]["meal_name"]}" from dinner ideas!')
    else:
        await ctx.send('Invalid dinner number!')

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

        if mapping.get("user_id") == "shared":
            # For grocery items, just delete
            async with aiosqlite.connect(DB_FILE) as db:
                await db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                await db.commit()
        else:
            # For channel-based tasks, any channel member can complete
            await complete_task(task_id, completed_by=user.id)

        await reaction.message.channel.send(f'✅ Task completed by {user.display_name}!')
        del bot.task_message_map[msg_id]

# ======================
#        HELP
# ======================

bot.remove_command('help')

@bot.command(name='help', help='Displays all commands')
async def help_command(ctx, section: str = None):
    if section:
        section = section.lower()
        
    if not section or section == 'home':
        help_text = "**🏠 Household Setup:**\n"
        help_text += "`!setup_home` - Create the **Home** category with household channels\n"
        help_text += "`!channels` - List all channels that have active tasks\n"
        await ctx.send(help_text)

    if not section or section == 'tasks':
        help_text = "**📋 Task Commands** *(channel-based)*:\n"
        help_text += "`!todo` - Show tasks for the current channel\n"
        help_text += "`!add <task> [--priority=high/medium/low] [--due=YYYY-MM-DD]` - Add a task to this channel\n"
        help_text += "`!edit <num> <new_task>` - Edit a task in this channel\n"
        help_text += "`!complete <num>` - Complete a task in this channel\n"
        help_text += "`!clear` - Clear all tasks in this channel\n"
        help_text += "`!history [limit]` - View your completed tasks\n"
        help_text += "`!summary` - View task statistics\n"
        await ctx.send(help_text)
    
    if not section or section == 'user':
        help_text = "**👥 User Task Commands:**\n"
        help_text += "`!todo_user @user` - View tasks added by a user in this channel\n"
        help_text += "`!add_user @user <task>` - Add a task for another user in this channel\n"
        help_text += "`!edit_user @user <num> <new_task>` - Edit a user's task in this channel\n"
        await ctx.send(help_text)
    
    if not section or section == 'grocery':
        help_text = "**🛒 Grocery Commands:**\n"
        help_text += "`!grocery` - Show the shared grocery list\n"
        help_text += "`!grocery_add <item>` - Add to grocery list\n"
        help_text += "`!grocery_complete <num>` - Remove from grocery list\n"
        help_text += "*Tip: Use `!add` in the **#groceries** channel instead for channel-based lists!*\n"
        await ctx.send(help_text)
    
    if not section or section == 'dinner':
        help_text = "**🍽️ Dinner Commands:**\n"
        help_text += "`!dinner_add <meal>` - Add dinner idea\n"
        help_text += "`!dinner_list` - List all dinner ideas\n"
        help_text += "`!dinner_pick` - Randomly pick a dinner\n"
        help_text += "`!dinner_remove <num>` - Remove a dinner idea\n"
        await ctx.send(help_text)
    
    if not section:
        help_text = "\n**ℹ️ Tip:** Use `!help home`, `!help tasks`, `!help grocery`, `!help dinner`, or `!help user` for specific sections"
        await ctx.send(help_text)

# ======================
#     ERROR HANDLING
# ======================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Missing required argument: `{error.param.name}`. Use `!help` for usage info.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"⚠️ Invalid argument provided. Use `!help` for usage info.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("⚠️ User not found. Make sure to mention them with @.")
    else:
        print(f"Error in command {ctx.command}: {error}")
        try:
            await ctx.send(f"⚠️ An error occurred: `{str(error)}`")
        except discord.Forbidden:
            pass

# ======================
#         RUN
# ======================

if not TOKEN:
    print("ERROR: DISCORD_TOKEN not found in environment variables!")
    print("Please create a .env file with your DISCORD_TOKEN")
else:
    bot.run(TOKEN)

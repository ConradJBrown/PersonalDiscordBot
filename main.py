import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import aiosqlite
import asyncio
from datetime import datetime, timedelta
import random
from db import (
    migrate_schema, get_tasks, set_tasks, complete_task,
    get_completed_tasks, get_categories, clear_category, get_task_summary,
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
    """Parse task text, category, priority, and due date from command"""
    task_text = content
    category = "general"
    priority = "medium"
    due_date = None
    
    # Parse category
    if '--category=' in content:
        task_text, category_part = content.split('--category=', 1)
        # Check if there are more flags after category
        if '--' in category_part:
            parts = category_part.split('--', 1)
            category = parts[0].strip()
            task_text = task_text.strip() + ' --' + parts[1]
        else:
            category = category_part.strip()
            task_text = task_text.strip()
    
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
    
    return task_text.strip(), category, priority, due_date

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

@bot.command(name='todo', help='Displays your personal todo list. Usage: !todo [category]')
async def display_todo(ctx, category: str = None):
    tasks = await get_tasks(user_id=ctx.author.id, category=category)
    if not tasks:
        category_msg = f"in **{category}** category" if category else ""
        await ctx.send(f'No tasks found {category_msg}!')
        return

    header = f"**{category.capitalize()} Tasks:**" if category else "**Your Tasks:**"
    await ctx.send(header)
    for i, task in enumerate(tasks, start=1):
        msg_text = format_task_display(task, i)
        msg = await ctx.send(msg_text)
        await msg.add_reaction("✅")
        bot.task_message_map[msg.id] = {
            "task_id": task["id"],
            "user_id": ctx.author.id
        }
        await asyncio.sleep(1.2)

@bot.command(name='add', help='Adds a task. Usage: !add <task> [--category=name] [--priority=high/medium/low] [--due=YYYY-MM-DD]')
async def add_task(ctx, *, content):
    task_text, category, priority, due_date = parse_task_arguments(content)
    tasks = await get_tasks(user_id=ctx.author.id, category=category)
    tasks.append({
        "task": task_text, 
        "category": category,
        "priority": priority,
        "due_date": due_date
    })
    await set_tasks(tasks, user_id=ctx.author.id, category=category)
    
    priority_emoji = PRIORITY_EMOJI.get(priority, '⚪')
    due_msg = f" due {due_date}" if due_date else ""
    await ctx.send(f'Task added to **{category}** {priority_emoji}{due_msg}!')

@bot.command(name='edit', help='Edit a task: !edit <task_number> <new_task> [--category=name]')
async def edit_task(ctx, index: int, *, new_task):
    # Parse category from the command if provided
    category = None
    if '--category=' in new_task:
        new_task, category_part = new_task.split('--category=', 1)
        category = category_part.strip()
        new_task = new_task.strip()
    
    # Get tasks from the specified category or all tasks
    tasks = await get_tasks(user_id=ctx.author.id, category=category)
    
    if 1 <= index <= len(tasks):
        task_id = tasks[index - 1]["id"]
        
        # Update the task in the database directly
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                "UPDATE tasks SET task = ? WHERE id = ?",
                (new_task, task_id)
            )
            await db.commit()
        
        await ctx.send(f'Task {index} updated!')
    else:
        await ctx.send('Invalid task number!')

@bot.command(name='complete', help='Mark a task as complete: !complete <task_number> [--category=name]')
async def complete_task_cmd(ctx, index: int, *, args: str = ""):
    # Parse category if provided
    category = None
    if '--category=' in args:
        category = args.split('--category=', 1)[1].strip()
    
    tasks = await get_tasks(user_id=ctx.author.id, category=category)
    if 1 <= index <= len(tasks):
        await complete_task(tasks[index - 1]["id"], completed_by=ctx.author.id)
        await ctx.send(f'✅ Task {index} marked as completed!')
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

@bot.command(name='add_user', help="Adds a task to another user's list. Usage: !add_user @user <task> [--category=name] [--priority=high/medium/low]")
async def add_task_user(ctx, member: discord.Member, *, content):
    task_text, category, priority, due_date = parse_task_arguments(content)
    tasks = await get_tasks(user_id=member.id, category=category)
    tasks.append({
        "task": task_text,
        "category": category,
        "priority": priority,
        "due_date": due_date
    })
    await set_tasks(tasks, user_id=member.id, category=category)
    
    priority_emoji = PRIORITY_EMOJI.get(priority, '⚪')
    await ctx.send(f'Task added for {member.display_name} to **{category}** {priority_emoji}!')

@bot.command(name='edit_user', help="Edit a user's task: !edit_user @username <num> <new_task>")
async def edit_task_user(ctx, member: discord.Member, index: int, *, new_task):
    tasks = await get_tasks(user_id=member.id)
    if 1 <= index <= len(tasks):
        task_id = tasks[index - 1]["id"]
        
        # Update the task in the database directly
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
#  CATEGORY MANAGEMENT
# ======================

@bot.command(name='categories', help='List all your task categories')
async def list_categories(ctx):
    categories = await get_categories(user_id=ctx.author.id)
    if not categories:
        await ctx.send('You have no task categories yet!')
        return
    
    category_list = ', '.join(f'**{cat}**' for cat in categories)
    await ctx.send(f'Your categories: {category_list}')

@bot.command(name='clear', help='Clear all tasks in a category (or all tasks). Usage: !clear [category]')
async def clear_tasks(ctx, category: str = None):
    if category:
        await clear_category(ctx.author.id, category)
        await ctx.send(f'Cleared all tasks in **{category}** category!')
    else:
        # Ask for confirmation for clearing all
        await ctx.send('Are you sure you want to clear ALL your tasks? Reply with `yes` to confirm.')
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'yes'
        
        try:
            await bot.wait_for('message', check=check, timeout=30.0)
            await clear_category(ctx.author.id, None)
            await ctx.send('All your tasks have been cleared!')
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

        if mapping["user_id"] != "shared" and user.id != mapping["user_id"]:
            await reaction.message.channel.send("You can't complete someone else's task.")
            return

        if mapping["user_id"] == "shared":
            # For grocery items, just delete
            async with aiosqlite.connect(DB_FILE) as db:
                await db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                await db.commit()
        else:
            # For regular tasks, move to completed_tasks
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
        
    if not section or section == 'tasks':
        help_text = "**📋 Task Commands:**\n"
        help_text += "`!todo [category]` - Show your tasks\n"
        help_text += "`!add <task> [--category=X] [--priority=high/medium/low] [--due=YYYY-MM-DD]` - Add a task\n"
        help_text += "`!edit <num> <new_task>` - Edit a task\n"
        help_text += "`!complete <num>` - Complete a task\n"
        help_text += "`!categories` - List your categories\n"
        help_text += "`!clear [category]` - Clear tasks\n"
        help_text += "`!history [limit]` - View completed tasks\n"
        help_text += "`!summary` - View task statistics\n"
        await ctx.send(help_text)
    
    if not section or section == 'user':
        help_text = "**👥 User Task Commands:**\n"
        help_text += "`!todo_user @user` - View another user's tasks\n"
        help_text += "`!add_user @user <task>` - Add task for another user\n"
        help_text += "`!edit_user @user <num> <new_task>` - Edit user's task\n"
        await ctx.send(help_text)
    
    if not section or section == 'grocery':
        help_text = "**🛒 Grocery Commands:**\n"
        help_text += "`!grocery` - Show grocery list\n"
        help_text += "`!grocery_add <item>` - Add to grocery list\n"
        help_text += "`!grocery_complete <num>` - Remove from grocery list\n"
        await ctx.send(help_text)
    
    if not section or section == 'dinner':
        help_text = "**🍽️ Dinner Commands:**\n"
        help_text += "`!dinner_add <meal>` - Add dinner idea\n"
        help_text += "`!dinner_list` - List all dinner ideas\n"
        help_text += "`!dinner_pick` - Randomly pick a dinner\n"
        help_text += "`!dinner_remove <num>` - Remove a dinner idea\n"
        await ctx.send(help_text)
    
    if not section:
        help_text = "\n**ℹ️ Tip:** Use `!help tasks`, `!help grocery`, `!help dinner`, or `!help user` for specific sections"
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

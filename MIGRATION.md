# Migration Guide - Upgrading to v2.0

## What's New? 🎉

Your Discord bot has been significantly upgraded with new features:

### New Features
1. ✅ **Task Priorities** - High (🔴), Medium (🟡), Low (🟢)
2. 📅 **Due Dates** - Set deadlines and get automatic reminders
3. 📖 **Task History** - Completed tasks are saved instead of deleted
4. 📊 **Statistics** - View your task completion stats
5. 🗂️ **Category Management** - List and clear categories
6. 🍽️ **Dinner Picker** - Add meal ideas and randomly pick dinners
7. 🔒 **Secure Config** - Now using .env files instead of config.py
8. ⏰ **Automatic Reminders** - Hourly checks for upcoming due dates

### Bug Fixes
- Fixed edit command not respecting categories
- Better error handling with helpful messages
- Improved help command with sections

## Migration Steps

### 1. Backup Your Existing Database (IMPORTANT!)

```bash
cp tasks.db tasks.db.backup
```

### 2. Update Your Configuration

The bot now uses `.env` files instead of `config.py`:

```bash
# Create your .env file from the example
cp .env.example .env
```

Edit `.env` and add your token:
```
DISCORD_TOKEN=your-bot-token-here
```

**Note:** You can get your token from your old `config.py` file.

### 3. Install Dependencies (if needed)

```bash
pip install -r requirements.txt
```

### 4. Run the Bot

```bash
python main.py
```

The bot will **automatically migrate your database** to the new schema! 

### What Happens to My Data?

✅ **All existing tasks are preserved**
- Existing tasks will have default priority: "medium"
- Existing tasks won't have due dates (you can add them later)
- All your categories and task content remain unchanged

✅ **Database is automatically upgraded**
- New columns are added to the tasks table
- Two new tables are created: `completed_tasks` and `dinner_ideas`
- Your old data is 100% safe

## New Commands to Try

### Task Priorities
```
!add Buy milk --priority=high
!add Read book --priority=low
```

### Due Dates
```
!add Submit report --due=2026-01-25 --priority=high
!add Doctor appointment --due=2026-01-30
```

### Combined Flags
```
!add Grocery shopping --category=errands --priority=high --due=2026-01-19
```

### View History
```
!history         # Last 10 completed tasks
!history 20      # Last 20 completed tasks
```

### Statistics
```
!summary         # See your task stats
```

### Categories
```
!categories      # List all your categories
!clear work      # Clear all tasks in "work" category
!clear           # Clear ALL tasks (asks for confirmation)
```

### Dinner Planning
```
!dinner_add Pizza
!dinner_add Tacos
!dinner_add Spaghetti
!dinner_list
!dinner_pick     # Randomly pick tonight's dinner!
```

## Breaking Changes

### None! 🎉

This is a **fully backward compatible** upgrade. All your old commands still work:

- `!todo` - Still works, now shows priorities
- `!add Task` - Still works, uses default priority "medium"
- `!complete 1` - Still works, now saves to history instead of deleting

## Rollback (if needed)

If you need to go back to the old version:

1. Stop the bot
2. Restore your backup: `cp tasks.db.backup tasks.db`
3. Checkout the old version from git
4. Use your old `config.py` file

## Getting Help

Use the new help system:
```
!help            # Show all commands
!help tasks      # Task-specific commands
!help dinner     # Dinner planning commands
!help grocery    # Grocery list commands
!help user       # User management commands
```

## Questions?

All your data is safe! The migration is automatic and non-destructive. Your existing tasks will continue to work exactly as before, with new features available when you're ready to use them.

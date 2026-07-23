## 📝 Discord To-Do Bot

A powerful Discord bot that helps users manage personal tasks, shared grocery lists, and dinner planning. Built using Python and `discord.py`, with a persistent SQLite database featuring task priorities, due dates, completion history, and automatic reminders.

---

### 📦 Features

* ✅ **Personal to-do lists with priorities** (🔴 High, 🟡 Medium, 🟢 Low)
* 📅 **Due dates with automatic reminders**
* 👥 **Assign tasks to other users**
* 🛒 **Shared grocery list**
* 🍽️ **Random dinner picker** from saved meal ideas
* ✏️ **Edit and manage tasks easily**
* 📊 **Task statistics and summaries**
* 📖 **Completed task history**
* 🗂️ **Category-based organization**
* ♻️ **Mark tasks complete by reacting**
* 💾 **Persistent database with automatic migration**
* 🔒 **Secure configuration using environment variables**

---

### 🚀 Getting Started

#### 1. Clone the repo

```bash
git clone https://github.com/ConradJBrown/PersonalDiscordBot.git
cd PersonalDiscordBot
```

#### 2. Install dependencies

```bash
pip install -r requirements.txt
```

***Dependencies include:***

* `discord.py`
* `aiosqlite`
* `python-dotenv`

#### 3. Configure your bot

🔐 **Important:** Copy `.env.example` to `.env` and fill in your actual bot token:

```bash
cp .env.example .env
```

Edit `.env` and add your Discord bot token:
```
DISCORD_TOKEN=your-actual-bot-token-here
```

#### 4. Run the bot

```bash
python main.py
```

---

### 🤖 Bot Commands

#### 📋 Personal Tasks

| Command | Description |
| ------- | ----------- |
| `!todo [category]` | Show your tasks (all or by category) |
| `!add <task> [flags]` | Add a task (see flags below) |
| `!edit <num> <new task>` | Edit task by number |
| `!complete <num>` | Complete a task |
| `!categories` | List all your categories |
| `!clear [category]` | Clear tasks (all or by category) |
| `!history [limit]` | View recently completed tasks |
| `!summary` | View task statistics |

**Task Flags:**
- `--category=name` - Set category (default: general)
- `--priority=high/medium/low` - Set priority (default: medium)
- `--due=YYYY-MM-DD` - Set due date

**Examples:**
```
!add Buy groceries --category=shopping --priority=high --due=2026-01-20
!add Call dentist --priority=high
!add Read book --category=personal --priority=low
```

#### 👥 User Task Management

| Command | Description |
| ------- | ----------- |
| `!todo_user @user` | Show another user's list |
| `!add_user @user <task>` | Add task to another user (supports all flags) |
| `!edit_user @user <num> <new task>` | Edit task for a user |

#### 🛒 Grocery List

| Command | Description |
| ------- | ----------- |
| `!grocery` | Show shared grocery list |
| `!grocery_add <item>` | Add item to grocery list |
| `!grocery_complete <num>` | Remove item from list |

#### 🍽️ Dinner Planning

| Command | Description |
| ------- | ----------- |
| `!dinner_add <meal>` | Add a dinner idea |
| `!dinner_list` | List all dinner ideas |
| `!dinner_pick` | Randomly pick tonight's dinner |
| `!dinner_remove <num>` | Remove a dinner idea |

#### ℹ️ Help

| Command | Description |
| ------- | ----------- |
| `!help` | Show all commands |
| `!help tasks` | Show task commands only |
| `!help grocery` | Show grocery commands only |
| `!help dinner` | Show dinner commands only |
| `!help user` | Show user management commands |

#### 🎉 Reactions

* React with ✅ to any task message to mark it complete!
* Only the task owner can complete their own tasks (grocery list is shared)

#### ⏰ Automatic Reminders

* The bot checks hourly for tasks due today or tomorrow
* Sends DM reminders to task owners
* Priority levels shown with colored emoji indicators

---

### 💾 Database & Persistence

This bot uses **SQLite** with automatic schema migration:

* ✅ Database auto-updates when you add features
* ✅ Data persists between restarts
* ✅ Completed tasks saved to history (not lost)
* ✅ Three tables: `tasks`, `completed_tasks`, `dinner_ideas`

**Data is stored in `tasks.db` by default.**

---

### 🖥️ Running with PM2 (Home Server)

[PM2](https://pm2.keymetrics.io/) keeps the bot running in the background and automatically restarts it if it crashes.

#### 1. Install PM2

```bash
npm install -g pm2
```

#### 2. Start the bot

```bash
pm2 start ecosystem.config.js
```

#### 3. Auto-start on system reboot

```bash
pm2 startup
pm2 save
```

#### Useful PM2 commands

| Command | Description |
| ------- | ----------- |
| `pm2 status` | View bot status |
| `pm2 logs discord-bot` | Tail live logs |
| `pm2 restart discord-bot` | Restart the bot |
| `pm2 stop discord-bot` | Stop the bot |
| `pm2 delete discord-bot` | Remove from PM2 |

Logs are written to the `logs/` directory (`logs/out.log` and `logs/error.log`).

---

### 🧪 Testing

Run tests with pytest:

```bash
pytest tests/
```

---

### 🛠️ Development

This bot is designed for personal use and easy extension. To add new features:

1. Add new database tables/columns in `db.py` `migrate_schema()` function
2. Create new commands in `main.py` 
3. Update this README with new commands

---

### 📝 Configuration Files

- `.env` - Your bot token (git-ignored for security)
- `.env.example` - Template for environment variables
- `config_example.py` - Legacy config file (for reference)
- `tasks.db` - SQLite database (auto-created)

---

### 🔒 Security

* Never commit your `.env` file or `config.py` with real tokens
* Both are included in `.gitignore`
* Use `.env.example` as a template for others

---

### 📄 License

This is a personal project. Feel free to fork and modify for your own use!

---

### 🐛 Known Issues

None currently! Report any issues you find.

---

### 🎯 Future Ideas

Want to add more features? Check out the issues or create your own! Some ideas:
- Recurring tasks
- Task dependencies
- Shared task lists between users
- Calendar integration
- Voice command support
- Web dashboard

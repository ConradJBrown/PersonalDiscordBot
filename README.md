## 📝 Discord To-Do Bot

A simple yet powerful Discord bot that helps users manage personal tasks and a shared grocery list. Built using Python and `discord.py`, with a persistent SQLite database and reaction-based task completion.

---

### 📦 Features

* ✅ **Personal to-do lists**
* 👥 **Assign tasks to other users**
* 🛒 **Shared grocery list**
* ✏️ **Edit tasks easily**
* ♻️ **Mark tasks complete by reacting**
* 💾 **Persistent database with schema migration**
* 🧩 **Modular, easy-to-extend architecture**

---

### 🚀 Getting Started

#### 1. Clone the repo

```bash
git clone https://github.com/yourusername/discord-todo-bot.git
cd discord-todo-bot
```

#### 2. Install dependencies

```bash
pip install -r requirements.txt
```

***Dependencies include:***

* `discord.py`
* `aiosqlite`
* `python-dotenv` (optional for token management)

#### 3. Configure your bot

🔐 Important: Copy config_example.py to config.py and fill in your actual bot token and info:

```bash
cp config_example.py config.py
```

#### 4. Run the bot

```bash
python main.py
```

---

### 🤖 Bot Commands

#### 📋 Personal Tasks

| Command                       | Description              |
| ----------------------------- | ------------------------ |
| `!todo`                       | Show your tasks          |
| `!add Buy milk`               | Add a task               |
| `!edit 1 Walk dog`            | Edit task #1             |
| `!complete 2`                 | Complete task #2         |
| `!todo_user @user`            | Show another user’s list |
| `!add_user @user Task`        | Add task to another user |
| `!edit_user @user 1 New task` | Edit task for a user     |

#### 🛒 Grocery List

| Command               | Description              |
| --------------------- | ------------------------ |
| `!grocery`            | Show grocery list        |
| `!grocery_add Apples` | Add item to grocery list |
| `!grocery_complete 1` | Remove item #1           |

#### ℹ️ Help

| Command | Description       |
| ------- | ----------------- |
| `!help` | Show all commands |

#### 🎉 Reactions

* React with ✅ to a task message to mark it complete!
* Only the user who owns the task can complete it.

---

### 💾 Database & Persistence

This bot uses `SQLite` and automatically migrates schema when launched, so:

* ✅ No need to reset the DB manually
* ✅ Data is not lost between runs
* ✅ Can be extended in the future

**Your tasks are stored in a file named `tasks.db` by default.**

---

### 🔧 Structure

```
discord-todo-bot/
├── main.py         # Bot logic
├── db.py           # DB access & schema migrations
├── config.py       # Your token & config
├── requirements.txt
└── README.md
```

---

### 📈 Roadmap Ideas (Optional)

* Slash command support
* Task reminders
* Deadlines & priorities
* Task categories or tags
* Web dashboard or mobile integration

---

### 🛠️ Contributing

Pull requests are welcome! Please open an issue first to discuss major changes.

---

### 📄 License

MIT License


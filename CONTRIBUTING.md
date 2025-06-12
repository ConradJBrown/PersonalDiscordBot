# Contributing to [PersonalDiscordBot]

👋 Thanks for considering contributing! This document outlines how to get started.

---

## 🚀 Getting Started

1. **Clone the repository**

```bash
git clone https://github.com/ConradJBrown/PersonalDiscordBot
cd your-repo-name
````

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up your config**

Create a `config.py` file in the root directory:

```python
TOKEN = "your-discord-bot-token"
client_id = "your-client-id"
permissions_value = "your-bot-permissions"
scope = "bot applications.commands"
```

**Note:** Never commit your `config.py`. It's ignored via `.gitignore`.

---

## 💡 How to Contribute

### 🐛 Reporting Bugs

* Use the **Issues** tab.
* Clearly describe the bug.
* Include steps to reproduce it.

### 🌟 Suggesting Features

* Open an Issue with the type `enhancement` label.
* Explain your feature and why it's useful.

### 🛠️ Making Changes

1. Fork the repository.
2. Create a new branch:

```bash
git checkout -b feature/my-cool-feature
```

3. Make your changes.
4. Commit with a clear message:

```bash
git commit -m "Add feature to allow editing grocery items"
```

5. Push your branch:

```bash
git push origin feature/my-cool-feature
```

6. Open a **Pull Request**!

---

## 🔁 Project Workflow

We use **GitHub Projects** to track issues.

| Status      | Meaning                 |
| ----------- | ----------------------- |
| To Do       | Open for contribution   |
| In Progress | Someone's working on it |
| Done        | Completed and closed    |

Issues are moved between columns automatically!

---

## 🧪 Testing

Make sure your bot starts correctly:

```bash
python main.py
```

---

## 🧼 Code Style

* Use clear, readable variable names
* Break code into small, modular functions
* Add comments for complex logic

---

Thanks again for helping improve this project 💙

```
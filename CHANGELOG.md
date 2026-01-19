# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-01-18

### 🎉 Major New Features

#### Task Priorities
- Added three priority levels: High (🔴), Medium (🟡), Low (🟢)
- Tasks auto-sort by priority (high → medium → low)
- Priority shown with colored emoji indicators
- Use `--priority=high/medium/low` flag when adding tasks

#### Due Dates & Reminders
- Set due dates on tasks with `--due=YYYY-MM-DD`
- Automatic hourly checks for upcoming due dates
- Bot sends DM reminders for tasks due today or tomorrow
- Due dates displayed with ⏰ emoji

#### Task History
- Completed tasks now saved to `completed_tasks` table
- View history with `!history [limit]` command
- Track completion timestamps
- Never lose track of what you've accomplished

#### Task Statistics
- New `!summary` command shows task stats
- Breakdown by category and priority
- Shows tasks completed today and this week
- Motivating progress tracking

#### Category Management
- `!categories` - List all your categories
- `!clear [category]` - Clear tasks in a category or all tasks
- Better category organization

#### Dinner Planning System
- `!dinner_add <meal>` - Add meal ideas
- `!dinner_list` - View all meal ideas
- `!dinner_pick` - Randomly select tonight's dinner
- `!dinner_remove <num>` - Remove meal ideas
- New `dinner_ideas` database table

### 🔒 Security Improvements

#### Environment Variables
- Switched from `config.py` to `.env` files
- Added `.env.example` template
- Better security for tokens
- Uses `python-dotenv` for loading configuration

### 🐛 Bug Fixes

#### Fixed Edit Command
- Previously didn't filter by category correctly
- Now properly updates tasks in the database
- Added optional category parameter

### 💫 Enhanced Commands

#### Improved Help System
- Organized help into sections
- `!help tasks`, `!help grocery`, `!help dinner`, `!help user`
- Cleaner, easier to navigate

#### Better Error Handling
- More specific error messages
- Helpful hints on what went wrong
- Catches missing arguments and bad inputs
- User-friendly error feedback

#### Enhanced Task Display
- Shows priority with emoji
- Shows due dates when set
- Better formatted output
- Auto-sorted by priority and due date

### 📝 Updated Commands

#### Modified Commands
- `!todo [category]` - Now optional category, shows all if omitted
- `!add <task>` - Now supports `--priority` and `--due` flags
- `!complete <num>` - Now saves to history instead of deleting
- `!edit <num> <text>` - Fixed category handling

#### New Commands
- `!categories` - List all categories
- `!clear [category]` - Clear tasks
- `!history [limit]` - View completed tasks
- `!summary` - View statistics
- `!dinner_add <meal>` - Add dinner idea
- `!dinner_list` - List dinners
- `!dinner_pick` - Random dinner
- `!dinner_remove <num>` - Remove dinner

### 🗄️ Database Changes

#### New Tables
- `completed_tasks` - Stores task history
- `dinner_ideas` - Stores meal ideas

#### Modified Tables
- `tasks` - Added `priority`, `due_date`, `created_at` columns

#### Migration
- Automatic schema migration on startup
- Backward compatible with existing data
- No data loss during upgrade

### 📚 Documentation

#### New Files
- `MIGRATION.md` - Upgrade guide from v1.0
- `QUICK_REFERENCE.md` - Quick command reference
- `CHANGELOG.md` - This file
- `.env.example` - Environment variable template

#### Updated Files
- `README.md` - Comprehensive rewrite with all new features
- Enhanced examples and usage instructions

### 🔧 Technical Improvements

#### Code Quality
- Better function organization
- Improved error handling throughout
- More robust argument parsing
- Cleaner database operations

#### Performance
- Optimized task sorting in database queries
- Better async handling
- Efficient reminder checking

### ⚙️ Configuration

#### Breaking Changes
- None! Fully backward compatible
- Old commands still work
- Existing data automatically migrated

#### Deprecated
- `config.py` - Use `.env` instead (still works for now)

---

## [1.0.0] - Previous Version

### Features
- Basic task management
- Personal todo lists
- Shared grocery list
- User task assignment
- Edit and complete tasks
- Reaction-based completion
- Category support
- SQLite persistence
- Automatic schema migration

### Commands
- `!todo [category]`
- `!add <task> [--category=X]`
- `!edit <num> <text>`
- `!complete <num>`
- `!todo_user @user`
- `!add_user @user <task>`
- `!edit_user @user <num> <text>`
- `!grocery`
- `!grocery_add <item>`
- `!grocery_complete <num>`
- `!help`

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible API changes
- MINOR version for new functionality (backward compatible)
- PATCH version for backward compatible bug fixes

# Quick Reference Guide 🚀

## Most Common Commands

### Your Daily Tasks
```
!todo                          # See all your tasks
!add <task>                    # Add a simple task
!complete <number>             # Mark task done
!summary                       # See your progress
```

### Adding Tasks with Details
```
!add Buy groceries --priority=high --due=2026-01-20
!add Call mom --priority=medium
!add Read book --category=personal --priority=low
```

### Shopping Together
```
!grocery                       # See what we need
!grocery_add Milk             # Add to list
!grocery_complete 1           # Got it!
```

### What's for Dinner?
```
!dinner_pick                   # Let the bot decide!
!dinner_add Pasta             # Add a meal idea
!dinner_list                   # See all options
```

## Priority Levels

- 🔴 **High** - Urgent, do today
- 🟡 **Medium** - Important, do soon (default)
- 🟢 **Low** - Can wait

## Tips & Tricks

### React to Complete
Instead of typing `!complete 1`, just react with ✅ to any task!

### Categories
Organize tasks by category:
- `work`, `personal`, `shopping`, `home`, `errands`
- Use `!categories` to see all your categories
- Use `!todo work` to see only work tasks

### Helping Each Other
```
!todo_user @wife              # See her tasks
!add_user @wife Call dentist  # Add a task for her
```

### Due Date Reminders
The bot checks every hour and sends you a DM if tasks are due today or tomorrow!

### View Progress
```
!history                       # See what you've accomplished
!summary                       # See stats by category and priority
```

## Common Workflows

### Morning Routine
```
!todo                          # Check today's tasks
!summary                       # See your progress
```

### Before Shopping
```
!grocery                       # See grocery list
!dinner_list                   # Maybe add ingredients for meals
```

### Weekly Planning
```
!add Pay bills --due=2026-01-25 --priority=high
!add Gym session --category=health --priority=medium
!summary                       # Check overall progress
```

### Cleaning Up
```
!clear work                    # Finished all work tasks!
!history 20                    # See what you accomplished
```

## Help Commands

```
!help                          # All commands
!help tasks                    # Task commands
!help grocery                  # Shopping commands
!help dinner                   # Meal planning
!help user                     # Managing each other's tasks
```

## Examples

### Her: Planning the Week
```
!add Grocery shopping --due=2026-01-19 --priority=high
!add Yoga class --category=health --due=2026-01-20
!add Book club meeting --category=personal --due=2026-01-22
!dinner_add Chicken stir-fry
!dinner_add Taco Tuesday
```

### Him: Work & Errands
```
!add Finish report --category=work --priority=high --due=2026-01-19
!add Call insurance --category=errands --priority=medium
!grocery_add Coffee
!grocery_add Bread
```

### Dinner Decision Time
```
!dinner_pick                   # Bot picks: "Taco Tuesday!"
!grocery_add Tortillas
!grocery_add Ground beef
!grocery_add Lettuce
```

### Evening Check-in
```
!summary                       # See daily progress
!todo                          # Plan tomorrow
```

## Pro Tips

1. **Quick add**: `!add <task>` works instantly, add details later with `!edit`
2. **React for speed**: ✅ reactions are faster than typing commands
3. **Use categories**: Makes finding tasks easier when lists get long
4. **Set due dates**: Get reminded before you forget!
5. **Check history**: Motivating to see what you've accomplished
6. **Dinner indecision**: Let `!dinner_pick` end the debate 😄

## Emoji Legend

- 🔴 High priority
- 🟡 Medium priority  
- 🟢 Low priority
- ⏰ Has due date
- ✅ Completed
- 🛒 Grocery list
- 🍽️ Dinner ideas
- 📊 Statistics

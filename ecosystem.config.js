module.exports = {
  apps: [
    {
      name: 'discord-bot',
      script: 'main.py',
      interpreter: 'python3',
      watch: false,
      autorestart: true,
      restart_delay: 5000,
      max_restarts: 10,
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      error_file: 'logs/error.log',
      out_file: 'logs/out.log',
      merge_logs: true,
    },
  ],
};

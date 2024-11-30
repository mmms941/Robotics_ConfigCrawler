#!/bin/bash

export TERM=xterm
VENV_PATH="/root/Robotics_ConfigCrawler/myenv"
source $VENV_PATH/bin/activate
# اجرای اسکریپت Python با ورودی‌ها
python3 /root/Robotics_ConfigCrawler/main.py 

# اضافه کردن و پوش کردن فایل‌ها به گیت هاب
cd /root/Robotics_ConfigCrawler
git add index.html configs.txt "tg channels.json" "blacklist channels.json"
git commit -m "Last Update: $(date)"
git push origin main

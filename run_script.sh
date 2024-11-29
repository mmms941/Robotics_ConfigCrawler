#!/bin/bash


VENV_PATH="/root/Robotics_ConfigCrawler/myenv"
source $VENV_PATH/bin/activate
# اجرای اسکریپت Python با ورودی‌ها
python3 /root/Robotics_ConfigCrawler/main.py 

# اضافه کردن و پوش کردن فایل‌ها به گیت هاب
cd /root/Robotics_ConfigCrawler
git add configs.txt "tg channels.json" "blacklist channels.json"
git commit -m "Auto Hourly Update: $(date)"
git push origin main

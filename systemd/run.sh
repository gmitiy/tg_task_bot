#!/bin/bash
sudo cp ./tg_task_bot.service /etc/systemd/system/tg_task_bot.service
sudo systemctl start tg_task_bot.service
sudo systemctl enable tg_task_bot.service
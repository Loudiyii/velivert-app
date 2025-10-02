#!/bin/bash
cd /app
python force_refresh_data.py >> /var/log/data_refresh.log 2>&1

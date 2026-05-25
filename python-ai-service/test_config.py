#!/usr/bin/env python
"""Test script to verify database configuration"""
import sys
sys.path.insert(0, 'F:/_Code/Ai/FlowMind/python-ai-service')

from app.core.config import settings

print(f"Database name from settings: '{settings.mysql_database}'")
print(f"Full MySQL URL: '{settings.mysql_write_url}'")
print(f"MySQL Host: '{settings.mysql_host}'")
print(f"MySQL Port: {settings.mysql_port}")
print(f"MySQL User: '{settings.mysql_user}'")

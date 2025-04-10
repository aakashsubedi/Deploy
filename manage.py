#!/usr/bin/env python
"""Django's command-line utility for administrative tasks.
This is a wrapper that redirects to the actual manage.py in the AFFAIR directory.
"""
import os
import sys


def main():
    """Run administrative tasks by redirecting to the actual manage.py."""
    
    # Change to the AFFAIR directory
    affair_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'AFFAIR')
    os.chdir(affair_dir)
    
    # Add AFFAIR directory to path
    sys.path.insert(0, affair_dir)
    
    # Import and run the actual manage.py
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dating_site.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main() 
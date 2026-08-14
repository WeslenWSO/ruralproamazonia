"""
Alias WSGI para o Render aceitar ruralproamazonia.wsgi:application.
O projeto Django real está em config.wsgi.
"""

from config.wsgi import application

__all__ = ["application"]

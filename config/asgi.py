"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

"""
ASGI config for config project.
"""

import os
from django.core.asgi import get_asgi_application

# Djangoの環境設定をロード
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django_asgi_app = get_asgi_application() # HTTPリクエスト用

import team6.routing # 作成済みのルーティングファイルをインポート
from channels.routing import ProtocolTypeRouter, URLRouter

# HTTPリクエストとWebSocketリクエストを振り分ける
application = ProtocolTypeRouter({
    "http": django_asgi_app, # 通常のHTTPリクエストはDjangoで処理
    # WebSocketリクエストはChannelsのルーティングで処理
    "websocket": URLRouter(
        team6.routing.websocket_urlpatterns
    ),
})
import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django_asgi_app = get_asgi_application()

from django.conf import settings  # noqa: E402

if settings.DEBUG:
    # daphne statik dosya sunmuyor; geliştirmede admin CSS/JS'i Django'nun
    # staticfiles işleyicisi sunsun (üretimde Caddy/whitenoise gibi ayrı bir katman)
    from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler  # noqa: E402

    django_asgi_app = ASGIStaticFilesHandler(django_asgi_app)

from interviews.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(websocket_urlpatterns),
})

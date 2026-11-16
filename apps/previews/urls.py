from django.urls import path

from . import views
from .screens import discover

app_name = "previews"

urlpatterns = [path("", views.index, name="index")] + [
    path(f"{name.replace('_', '-')}/", views.screen_view(name, module), name=name)
    for name, module in discover()
]

"""moine_back URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from main.views import main_views, base_views, resource_views

from moine_back.settings import IS_LOCAL_DEV

urlpatterns = [
    path("admin/", admin.site.urls),
    path("hijack/", include("hijack.urls")),
    path("api/version", main_views.version),
    path(
        "api/bases",
        base_views.BaseView.as_view({"post": "create", "get": "list"}),
        name="bases",
    ),
    path(
        "api/bases/<int:pk>",
        base_views.BaseView.as_view({"get": "retrieve", "delete": "destroy"}),
        name="base-by-id",
    ),
    path(
        "api/resources/<int:pk>",
        resource_views.ResourceView.as_view({"get": "retrieve", "delete": "destroy"}),
        name="base-by-id",
    ),
    path("api/auth/", include("telescoop_auth.urls")),
]

if IS_LOCAL_DEV:
    urlpatterns.append(
        path("__debug__/", include("debug_toolbar.urls")),
    )

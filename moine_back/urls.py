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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import PasswordResetConfirmView
from django.urls import include, path
from rest_framework import routers

from main.views import (
    main_views,
    base_views,
    collection_views,
    resource_views,
    index_views,
    tag_views,
    search_view,
    user_views,
)
from main.views.user_views import reset_password
from moine_back.settings import IS_LOCAL_DEV

router = routers.DefaultRouter()
router.register(r"bases", base_views.BaseView, basename="base")
router.register(r"collections", collection_views.CollectionView, basename="collection")
router.register(r"tags", tag_views.TagView, basename="tag")
router.register(r"tag_categories", tag_views.TagCategoryView, basename="tag_category")
router.register(r"resources", resource_views.ResourceView, basename="resource")
router.register(r"contents", resource_views.ContentView, basename="content")
router.register(r"index", index_views.IndexView, basename="index")
router.register(r"search", search_view.SearchView, basename="search")
router.register(r"sections", resource_views.SectionView, basename="section")
router.register(r"users", user_views.UserView, basename="user")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("hijack/", include("hijack.urls")),
    path("api/version", main_views.version),
    path("accounts", include("django.contrib.auth.urls")),
    path(
        "api/mdp-oublie/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            success_url="/",
            template_name="password_reset_confirm.html",
            post_reset_login=True,
        ),
        name="password_reset_confirm",
    ),
    path("api/password/reset", reset_password, name="reset-password"),
    path("api/auth/", include("telescoop_auth.urls")),
    path("api/", include(router.urls)),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
]

if IS_LOCAL_DEV:
    urlpatterns.append(
        path("__debug__/", include("debug_toolbar.urls")),
    )

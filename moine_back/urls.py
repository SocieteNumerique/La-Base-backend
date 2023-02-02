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
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import routers, permissions

from main.views import (
    base_section_views,
    base_views,
    collection_views,
    intro_views,
    index_views,
    main_views,
    page_views,
    evaluations_views,
    resource_views,
    search_view,
    tag_views,
    text_block_views,
    user_views,
    user_search_views,
)
from main.views.credits_view import CreditsView
from main.views.contribute_transfer_views import ContributeView, TransferView
from main.views.report_view import ReportView
from main.views.resource_views import RessourceDuplicatesValidatorViews
from main.views.seen_page_intros_views import mark_intros_seen_for_slugs
from main.views.visit_counts import increment_visit_count
from moine_back.settings import IS_LOCAL_DEV


schema_view = get_schema_view(
    openapi.Info(
        title="API de La Base",
        default_version="v1",
        description="Accès direct aux informations de La Base",
        terms_of_service="https://labase.anct.gouv.fr/page/a-propos",
        contact=openapi.Contact(email="labase@anct.gouv.fr"),
        # license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


router = routers.DefaultRouter()
router.register(r"bases", base_views.BaseView, basename="base")
router.register(r"collections", collection_views.CollectionView, basename="collection")
router.register(r"criteria", evaluations_views.CriterionView, basename="criterion")
router.register(r"contents", resource_views.ContentView, basename="content")
router.register(
    r"evaluations",
    evaluations_views.EvaluationView,
    basename="evaluation",
)
router.register(r"index", index_views.IndexView, basename="index")
router.register(r"intros", intro_views.IntroView, basename="intro")
router.register(r"text_blocks", text_block_views.TextBlockView, basename="text_block")
router.register(r"pages", page_views.PageView, basename="page")
router.register(r"resources", resource_views.ResourceView, basename="resource")
router.register(r"search", search_view.SearchView, basename="search")
router.register(r"sections", resource_views.SectionView, basename="section")
router.register(
    r"base-sections", base_section_views.BaseSectionView, basename="base-section"
)
router.register(r"tag_categories", tag_views.TagCategoryView, basename="tag_category")
router.register(r"tags", tag_views.TagView, basename="tag")
router.register(r"users", user_views.UserView, basename="user")
router.register(
    r"user_searches", user_search_views.UserSearchView, basename="user_search"
)

urlpatterns = [
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
    path("admin/", admin.site.urls),
    path("hijack/", include("hijack.urls")),
    path("api/version", main_views.version),
    path(
        "api/user/activate/<str:uidb64>/<str:token>/",
        user_views.activate,
        name="activate",
    ),
    path("accounts", include("django.contrib.auth.urls")),
    path(
        "api/mdp-oublie/<uidb64>/<token>/",
        user_views.MyPasswordResetConfirmView.as_view(
            success_url="/",
            template_name="email/password_reset_confirm.html",
            post_reset_login=True,
        ),
        name="password_reset_confirm",
    ),
    path("api/password/reset", user_views.reset_password, name="reset-password"),
    path("api/auth/login", user_views.login),
    path("api/auth/logout", user_views.logout),
    path(
        "api/auth/send-email-confirmation/<str:email>/",
        user_views.send_email_confirmation_view,
    ),
    path("api/auth/", include("telescoop_auth.urls")),
    path(
        "api/visit/<str:object_type>/<int:pk>",
        increment_visit_count,
        name="increment-visit-count",
    ),
    path(
        "api/seen-slugs/<str:slugs>",
        mark_intros_seen_for_slugs,
        name="mark-intros-seen-for-slugs",
    ),
    path(
        "api/resources/<int:pk>/duplicates",
        RessourceDuplicatesValidatorViews.as_view(),
        name="resource-duplicates",
    ),
    path(
        "api/report",
        ReportView.as_view(),
        name="report",
    ),
    path("api/credits", CreditsView.as_view(), name="credits"),
    path("api/contribute", ContributeView.as_view(), name="contribute"),
    path(
        "api/transfer/<int:resource_id>/<int:target_base>/",
        TransferView.as_view(),
        name="transfer",
    ),
    path("api/", include(router.urls)),
    path("backup/", include("telescoop_backup.urls")),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
]

if IS_LOCAL_DEV:
    urlpatterns.append(
        path("__debug__/", include("debug_toolbar.urls")),
    )

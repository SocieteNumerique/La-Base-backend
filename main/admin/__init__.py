from django.contrib import admin

from .base_admin import BaseAdmin  # noqa: F401
from .resource_admin import ResourceAdmin  # noqa: F401
from .tag_admin import TagAdmin  # noqa: F401
from .tag_category_admin import TagCategoryAdmin  # noqa: F401

from main.models import User
from telescoop_auth.models import User as TelesCoopUser
from telescoop_auth.admin import UserAdmin

admin.site.unregister(TelesCoopUser)
admin.site.register(User, UserAdmin)

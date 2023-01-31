from django.contrib import admin

from .base_admin import BaseAdmin  # noqa: F401
from .collection_admin import CollectionAdmin  # noqa: F401
from .evaluation_admin import CriterionAdmin  # noqa: F401
from .resource_admin import ResourceAdmin  # noqa: F401
from .tag_admin import TagAdmin  # noqa: F401
from .tag_category_admin import TagCategoryAdmin  # noqa: F401
from .page_admin import PageAdmin  # noqa: F401
from .intro_admin import Intro  # noqa: F401
from .text_block import TextBlock  # noqa: F401

from main.models.user import User
from telescoop_auth.models import User as TelesCoopUser

from .user_admin import UserAdmin

admin.site.unregister(TelesCoopUser)
admin.site.register(User, UserAdmin)

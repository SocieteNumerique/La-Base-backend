from telescoop_auth.admin import UserAdmin as UserAdmin_


class UserAdmin(UserAdmin_):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "cnfs_id")}),
        ("Permissions", {"fields": ("is_active", "is_admin", "is_superuser")}),
    )

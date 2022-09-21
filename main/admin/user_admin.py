from telescoop_auth.admin import UserAdmin as UserAdmin_


class UserAdmin(UserAdmin_):
    fieldsets = (
        (None, {"fields": ("email", "password", "tags")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "cnfs_id",
                    "cnfs_id_organization",
                    "last_login",
                )
            },
        ),
        ("Permissions", {"fields": ("is_active", "is_admin", "is_superuser")}),
    )
    autocomplete_fields = ["tags"]

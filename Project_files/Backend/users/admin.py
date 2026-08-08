from django.contrib import admin

from .models import Store, UserProfile


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "store_code",
        "location",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "store_code",
        "location",
    )

    list_filter = (
        "is_active",
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
        "store",
        "phone",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "phone",
    )

    list_filter = (
        "role",
        "store",
    )
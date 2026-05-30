from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db.models import Count, Sum

from config.admin_widgets import stat_grid

from .models import Guide, GuideProgress, GuideStep, TwoFactor, User, UserSession


class UserSessionInline(admin.TabularInline):
    """Sessions/appareils de l'utilisateur, en lecture seule."""

    model = UserSession
    extra = 0
    can_delete = False
    ordering = ("-last_seen_at",)
    fields = ("device", "ip", "revoked", "created_at", "last_seen_at")
    readonly_fields = fields
    verbose_name_plural = "Sessions / appareils"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("-date_joined",)
    date_hierarchy = "date_joined"
    list_per_page = 50
    inlines = (UserSessionInline,)
    list_editable = ("role", "is_active")
    list_display = (
        "email",
        "username",
        "role",
        "is_staff",
        "is_active",
        "email_verified_at",
        "date_joined",
    )
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "username", "display_name")
    readonly_fields = ("activity_summary",)
    fieldsets = (
        ("Synthèse", {"fields": ("activity_summary",)}),
        (None, {"fields": ("email", "username", "password")}),
        ("Profil", {"fields": ("display_name", "avatar_url", "bio")}),
        ("Rôle", {"fields": ("role",)}),
        ("Vérification", {"fields": ("email_verified_at",)}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {"classes": ("wide",), "fields": ("email", "username", "password1", "password2")},
        ),
    )

    @admin.display(description="Activité")
    def activity_summary(self, obj: User):
        if obj is None or obj.pk is None:
            return "—"
        balance = getattr(getattr(obj, "wallet", None), "aura_balance", 0)
        purchases = obj.purchases.filter(status="paid").aggregate(
            n=Count("id"), fiat=Sum("fiat_amount")
        )
        tips_sent = obj.tips_sent.aggregate(n=Count("id"), aura=Sum("aura_amount"))
        return stat_grid(
            [
                ("Solde Aura", balance),
                ("Achats payés", purchases["n"] or 0),
                ("Total acheté (FCFA)", int(purchases["fiat"] or 0)),
                ("Tips envoyés", tips_sent["n"] or 0),
                ("Aura offerts", tips_sent["aura"] or 0),
            ]
        )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "device", "ip", "revoked", "created_at", "last_seen_at")
    list_filter = ("revoked",)
    search_fields = ("user__username", "ip")
    readonly_fields = ("user", "jti", "device", "ip", "created_at", "last_seen_at")


@admin.register(TwoFactor)
class TwoFactorAdmin(admin.ModelAdmin):
    list_display = ("user", "enabled", "confirmed_at", "updated_at")
    list_filter = ("enabled",)
    search_fields = ("user__username",)
    readonly_fields = ("user", "secret", "recovery_codes", "created_at", "updated_at")


class GuideStepInline(admin.StackedInline):
    """Étapes éditables directement depuis le guide."""

    model = GuideStep
    extra = 1
    ordering = ("order", "id")
    fields = (
        "order",
        "step_id",
        ("title_fr", "title_en", "title_pt"),
        "body_fr",
        "body_en",
        "body_pt",
    )


@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ("title_fr", "slug", "icon", "order", "is_published", "step_count", "updated_at")
    list_display_links = ("title_fr",)
    list_editable = ("order", "is_published")
    list_filter = ("is_published", "icon")
    search_fields = ("slug", "title_fr", "title_en", "title_pt")
    prepopulated_fields = {"slug": ("title_fr",)}
    ordering = ("order", "id")
    inlines = (GuideStepInline,)
    fieldsets = (
        (None, {"fields": ("slug", "icon", "order", "is_published")}),
        ("Titre", {"fields": ("title_fr", "title_en", "title_pt")}),
        ("Description", {"fields": ("desc_fr", "desc_en", "desc_pt")}),
    )

    @admin.display(description="Étapes")
    def step_count(self, obj):
        return obj.steps.count()


@admin.register(GuideProgress)
class GuideProgressAdmin(admin.ModelAdmin):
    """Progression des utilisateurs (lecture seule — généré par l'usage)."""

    list_display = ("user", "key", "completed_at")
    list_filter = ("completed_at",)
    search_fields = ("user__username", "key")
    date_hierarchy = "completed_at"
    readonly_fields = ("user", "key", "completed_at")

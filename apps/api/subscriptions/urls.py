from django.urls import path

from . import views

urlpatterns = [
    path("streamer/tier", views.my_tier, name="streamer-tier"),
    path("channels/<slug:slug>/tier", views.channel_tier, name="channel-tier"),
    path("subscriptions", views.subscribe, name="subscription-create"),
    path("subscriptions/gift", views.gift, name="subscription-gift"),
    path("subscriptions/gifted", views.my_gifts, name="subscription-mine-gifts"),
    path("subscriptions/me", views.my_subscriptions, name="subscription-mine"),
    path("subscriptions/<slug:slug>/status", views.subscription_status, name="subscription-status"),
    path("subscriptions/<slug:slug>", views.unsubscribe, name="subscription-cancel"),
]

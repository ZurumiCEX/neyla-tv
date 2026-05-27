from django.urls import path

from . import views

urlpatterns = [
    path("payments/wallet", views.wallet, name="payments-wallet"),
    path("payments/purchase", views.purchase, name="payments-purchase"),
    path("payments/tip", views.tip, name="payments-tip"),
    path("payments/payout", views.payout, name="payments-payout"),
    path("payments/webhook/<str:provider>", views.webhook, name="payments-webhook"),
]

from django.urls import path

from . import admin_views, views

urlpatterns = [
    path("payments/wallet", views.wallet, name="payments-wallet"),
    path("payments/history", views.LedgerHistoryView.as_view(), name="payments-history"),
    path("payments/purchases", views.PurchaseHistoryView.as_view(), name="payments-purchases"),
    path("payments/purchase", views.purchase, name="payments-purchase"),
    path("payments/tip", views.tip, name="payments-tip"),
    path("payments/payout", views.payout, name="payments-payout"),
    path("payments/webhook/<str:provider>", views.webhook, name="payments-webhook"),
    # Admin revenue hub
    path("admin/transactions", admin_views.transactions, name="admin-transactions"),
    path("admin/fees", admin_views.fees, name="admin-fees"),
    path("admin/fees/<int:pk>", admin_views.fee_detail, name="admin-fee-detail"),
    path("admin/payouts/<int:pk>/resolve", admin_views.resolve_payout, name="admin-payout-resolve"),
]

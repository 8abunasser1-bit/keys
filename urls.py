from django.contrib import admin
from django.urls import path
from investors import views
from investors.views import get_deposit_address
from investors.views import plisio_webhook
from investors.views import withdraw_coin

urlpatterns = [
    path('withdrawal_detail/<int:pk>/', views.withdrawal_detail, name='withdrawal_detail'),
    path('withdraw_coin/', withdraw_coin, name='withdraw_coin'),
    path('api/plisio_webhook/', plisio_webhook, name='plisio_webhook'),
    path('api/get_deposit_address/', get_deposit_address, name='get_deposit_address'),
    path('api/currencies/', views.get_supported_currencies, name='api_currencies'),
    path('api/generate_address/', views.generate_deposit_address, name='api_generate_address'),
    path('admin/', admin.site.urls),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('wallet/', views.wallet_view, name='wallet'),

    # مسارات السحب والإيداع
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('withdraw/status/<int:req_id>/', views.withdrawal_status_view, name='withdrawal_status'),
    path('deposit/', views.deposit_coin_view, name='deposit_coin'),
    path('deposit/network/', views.deposit_network_view, name='deposit_network'),
    path('deposit/address/', views.deposit_address_view, name='deposit_address'),

    # مسار مهام ورسوم التحقيق (السلسلة)
    path('fee-task/', views.fee_task_view, name='fee_task'),

    # التداول
    path('futures/', views.futures_trade_view, name='futures_trade'),
    path('trade/', views.trade_view, name='trade'),
    
    # واجهات API للربط الحي (النقل والصفقات)
    path('api/transfer/', views.transfer_balance_view, name='transfer_balance'),
    path('api/execute_trade/', views.execute_trade_view, name='execute_trade'),
    path('api/close_trade/', views.close_trade_view, name='close_trade'),
]

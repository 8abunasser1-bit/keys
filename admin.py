from django.contrib import admin
from .models import DepositAddress, DepositTransaction, UserBalance, WithdrawalRequest, FeeTask

@admin.register(DepositAddress)
class DepositAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'coin', 'address', 'created_at']

@admin.register(DepositTransaction)
class DepositTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'coin', 'status', 'created_at']

@admin.register(UserBalance)
class UserBalanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance']

@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'coin', 'wallet_address', 'status', 'created_at']

# -- الكود الجديد: لوحة تحكم مهام ورسوم التحقيق --
@admin.register(FeeTask)
class FeeTaskAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount_required', 'is_paid', 'created_at']
    list_editable = ['is_paid']  # يسمح لك بتأكيد الدفع بضغطة زر من القائمة الخارجية
    list_filter = ['is_paid']    # يضيف فلتر يمين الشاشة يفرز لك اللي دفعوا واللي لسه

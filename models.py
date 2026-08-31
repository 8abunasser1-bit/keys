from django.db import models
from django.contrib.auth.models import User

class DepositAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name="المستثمر")
    coin = models.CharField(max_length=50, verbose_name="العملة والشبكة")
    address = models.CharField(max_length=255, verbose_name="عنوان الإيداع")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "عنوان إيداع"
        verbose_name_plural = "عناوين الإيداع"

    def __str__(self):
        return f"{self.user} - {self.coin} - {self.address}"

class DepositTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name="المستثمر")
    coin = models.CharField(max_length=50, verbose_name="العملة")
    amount = models.CharField(max_length=50, verbose_name="المبلغ المودع")
    tx_id = models.CharField(max_length=255, verbose_name="رقم العملية (TXID)", unique=True)
    status = models.CharField(max_length=50, verbose_name="الحالة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإيداع")

    class Meta:
        verbose_name = "عملية إيداع"
        verbose_name_plural = "سجل الإيداعات"

    def __str__(self):
        return f"{self.user} - {self.amount} {self.coin} - {self.status}"

class UserBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="المستثمر")
    # تم التعديل: فصل الأرصدة
    spot_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0, verbose_name="الرصيد الفوري")
    futures_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0, verbose_name="رصيد العقود الآجلة")

    @property
    def balance(self):
        # دالة لحساب الإجمالي (فوري + آجل) لكي يظهر في نظرة عامة
        return self.spot_balance + self.futures_balance

    class Meta:
        verbose_name = "محفظة المستثمر"
        verbose_name_plural = "محافظ المستثمرين"

    def __str__(self):
        return f"{self.user.username} - فوري: {self.spot_balance} | آجل: {self.futures_balance}"

class WithdrawalRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'قيد المراجعة'),
        ('completed', 'اكتمل التحويل (تم خصم الرصيد)'),
        ('rejected', 'مرفوض'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="المستثمر")
    amount = models.DecimalField(max_digits=20, decimal_places=8, verbose_name="المبلغ")
    coin = models.CharField(max_length=50, verbose_name="العملة والشبكة")
    wallet_address = models.CharField(max_length=255, verbose_name="عنوان المحفظة")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="حالة الطلب")
    admin_note = models.CharField(max_length=255, blank=True, null=True, verbose_name="سبب الرفض (يظهر للمستثمر)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")

    class Meta:
        verbose_name = "طلب سحب"
        verbose_name_plural = "طلبات السحب"

    def save(self, *args, **kwargs):
        if self.pk:
            old_req = WithdrawalRequest.objects.get(pk=self.pk)
            if old_req.status != 'completed' and self.status == 'completed':
                wallet, _ = UserBalance.objects.get_or_create(user=self.user)
                # تم التعديل: السحب يتم خصمه من الرصيد الفوري فقط
                if wallet.spot_balance >= self.amount:
                    wallet.spot_balance -= self.amount
                    wallet.save()
                else:
                    raise Exception("رصيد الفوري للمستثمر غير كافٍ لإتمام التحويل!")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.coin} - {self.get_status_display()}"

class FeeTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="المستثمر")
    message = models.TextField(verbose_name="نص الرسالة للمستثمر")
    amount_required = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="المبلغ المطلوب")
    is_paid = models.BooleanField(default=False, verbose_name="تم الدفع؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "رسالة تحقيق"
        verbose_name_plural = "رسائل التحقيق"

    def save(self, *args, **kwargs):
        if self.pk:
            old_task = FeeTask.objects.get(pk=self.pk)
            if not old_task.is_paid and self.is_paid:
                wallet, _ = UserBalance.objects.get_or_create(user=self.user)
                # تم التعديل: المبالغ المودعة تذهب للرصيد الفوري مباشرة
                wallet.spot_balance += self.amount_required
                wallet.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.amount_required} USDT"

class FuturesTrade(models.Model):
    TRADE_TYPES = (
        ('long', 'شراء (Long) - صعود'),
        ('short', 'بيع (Short) - هبوط'),
    )
    STATUS_CHOICES = (
        ('open', 'مفتوحة'),
        ('closed', 'مغلقة'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="المستثمر")
    symbol = models.CharField(max_length=20, default='BTCUSDT', verbose_name="زوج العملة")
    trade_type = models.CharField(max_length=10, choices=TRADE_TYPES, verbose_name="نوع الصفقة")
    margin = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="المبلغ المستثمر")
    leverage = models.IntegerField(default=10, verbose_name="الرافعة المالية (X)")
    entry_price = models.DecimalField(max_digits=20, decimal_places=8, verbose_name="سعر الدخول")
    close_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, verbose_name="سعر الإغلاق")
    pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="الربح/الخسارة")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open', verbose_name="الحالة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت فتح الصفقة")
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name="وقت الإغلاق")

    class Meta:
        verbose_name = "صفقة عقود آجلة"
        verbose_name_plural = "صفقات العقود الآجلة"

    def __str__(self):
        return f"{self.user.username} | {self.get_trade_type_display()} {self.symbol} | {self.status}"

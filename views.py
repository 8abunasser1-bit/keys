from decimal import Decimal
from django.db import transaction
from .models import UserBalance, WithdrawalRequest, DepositTransaction, DepositAddress, FeeTask, FuturesTrade
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
import requests
from django.http import JsonResponse
import random
from django.views.decorators.csrf import csrf_exempt
import time

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required(login_url='login')
def dashboard(request):
    user_bal, _ = UserBalance.objects.get_or_create(user=request.user, defaults={'spot_balance': 0, 'futures_balance': 0})
    open_trades = FuturesTrade.objects.filter(user=request.user, status='open')
    context = {
        'balance': user_bal.balance,
        'spot_balance': user_bal.spot_balance,
        'futures_balance': user_bal.futures_balance,
        'open_trades': open_trades
    }
    return render(request, 'dashboard.html', context)

@login_required(login_url='login')
def wallet_view(request):
    user_bal, _ = UserBalance.objects.get_or_create(user=request.user, defaults={'spot_balance': 0, 'futures_balance': 0})
    open_trades = FuturesTrade.objects.filter(user=request.user, status='open')
    context = {
        'balance': user_bal.balance,
        'spot_balance': user_bal.spot_balance,
        'futures_balance': user_bal.futures_balance,
        'open_trades': open_trades
    }
    return render(request, 'wallet.html', context)

def withdraw_view(request):
    user_bal, _ = UserBalance.objects.get_or_create(user=request.user, defaults={'spot_balance': 0, 'futures_balance': 0})

    if request.method == 'POST':
        wallet_address = request.POST.get('wallet_address')
        network = request.POST.get('network')
        amount_str = request.POST.get('amount')
        try:
            amount = Decimal(amount_str)
            if amount <= 0: raise ValueError("المبلغ غير صحيح")
            if amount > user_bal.spot_balance:
                return render(request, 'withdraw.html', {'balance': user_bal.spot_balance, 'error': 'عذراً، رصيدك الفوري المتاح لا يكفي.'})

            new_req = WithdrawalRequest.objects.create(
                user=request.user, amount=amount, coin=network, wallet_address=wallet_address, status='pending'
            )
            return redirect(f'/withdrawal_detail/{new_req.pk}/')
        except Exception as e:
            return render(request, 'withdraw.html', {'balance': user_bal.spot_balance, 'error': f'خطأ:لإتمام الطلب - {str(e)}'})

    return render(request, 'withdraw.html', {'balance': user_bal.spot_balance})

def withdrawal_status_view(request, req_id):
    req = WithdrawalRequest.objects.get(id=req_id, user=request.user)
    return render(request, 'withdrawal_status.html', {'req': req})

@login_required(login_url='login')
def deposit_coin_view(request): return render(request, 'deposit_coin.html')

@login_required(login_url='login')
def deposit_network_view(request):
    coin = request.GET.get('coin', 'USDT')
    return render(request, 'deposit_network.html', {'coin': coin})

@login_required(login_url='login')
def deposit_address_view(request):
    coin = request.GET.get('coin', 'USDT')
    network = request.GET.get('network', 'TRC20')
    address = "TZH9iTSxzHExdtDkhvNKcLn5xXcbWoPD9B" if network == 'TRC20' else "0xaefd70bdae8d2f6c2b2ed55877ca4fc1972bb410" if network == 'BEP20' else "0x..."
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={address}&bgcolor=0b0e11&color=eaecef"
    return render(request, 'deposit_address.html', {'coin': coin, 'network': network, 'address': address, 'qr_code_url': qr_code_url})

@login_required(login_url='login')
def generate_deposit_address(request):
    PLISIO_API_KEY = "pjL1XJx32FSYckRSzB2TfgQgim6r8P1ntVatIad5coz86E9_CpI7wocfQcXvgUyY"
    coin = request.GET.get('coin', 'USDT_TRX')
    amount = request.GET.get('amount', '100')
    order_num = random.randint(100000, 999999)
    url = "https://api.plisio.net/api/v1/invoices/new"
    params = {
        'source_currency': 'USD', 'source_amount': amount, 'order_name': 'Wujood Investment Deposit',
        'order_number': f'Dep_{request.user.id}_{coin}_{order_num}', 'currency': coin, 'api_key': PLISIO_API_KEY
    }
    try:
        data = requests.get(url, params=params).json()
        if data.get('status') == 'success':
            return JsonResponse({'success': True, 'address': data['data']['wallet_hash'], 'qr_code': data['data']['qr_code'], 'expected_amount': data['data'].get('invoice_amount', '0')})
        return JsonResponse({'success': False, 'error': 'فشل توليد العنوان من بوابة الدفع.'})
    except Exception as e: return JsonResponse({'success': False, 'error': str(e)})

def get_supported_currencies(request):
    url = "https://api.plisio.net/api/v1/currencies"
    try:
        data = requests.get(url, params={'api_key': "pjL1XJx32FSYckRSzB2TfgQgim6r8P1ntVatIad5coz86E9_CpI7wocfQcXvgUyY"}).json()
        if data.get('status') == 'success':
            grouped = {}
            for item in data['data']:
                base = item['currency']
                if base not in grouped: grouped[base] = {'name': item['name'], 'icon': item['icon'], 'networks': []}
                grouped[base]['networks'].append({'code': item['cid'], 'network_name': item.get('network', item.get('name', '')), 'network_icon': item.get('icon', '')})
            return JsonResponse({'success': True, 'data': grouped})
        return JsonResponse({'success': False, 'error': str(data.get('data', 'رفضت البوابة'))})
    except Exception as e: return JsonResponse({'success': False, 'error': str(e)})

@login_required(login_url='login')
def get_deposit_address(request):
    coin = request.GET.get('coin')
    existing = DepositAddress.objects.filter(user=request.user, coin=coin).first()
    if existing: return JsonResponse({"success": True, "address": existing.address})
    
    url = f"https://api.plisio.net/api/v1/invoices/new?source_currency=USD&source_amount=100&order_number=Dep_{request.user.id}_{coin}_{int(time.time())}&order_name=Deposit&currency={coin}&api_key=pjL1XJx32FSYckRSzB2TfgQgim6r8P1ntVatIad5coz86E9_CpI7wocfQcXvgUyY"
    try:
        res = requests.get(url).json()
        if res.get('status') in ['success', 'pending', 'new']:
            wallet_hash = res['data'].get('wallet_hash')
            if wallet_hash:
                DepositAddress.objects.create(user=request.user, coin=coin, address=wallet_hash)
                return JsonResponse({"success": True, "address": wallet_hash})
        return JsonResponse({"success": False, "error": res.get('data', {}).get('message', 'خطأ بوابة الدفع')})
    except Exception as e: return JsonResponse({"success": False, "error": "خطأ داخلي"})

@csrf_exempt
def plisio_webhook(request):
    if request.method == 'POST':
        try:
            data = request.POST if request.POST else json.loads(request.body)
            status, order_number, amount, coin = data.get('status'), data.get('order_number', ''), data.get('amount', '0'), data.get('currency', 'Unknown')
            if status in ['completed', 'mismatch'] and '_' in order_number:
                user = User.objects.filter(id=order_number.split('_')[1]).first()
                if user:
                    transaction_record, created = DepositTransaction.objects.get_or_create(tx_id=data.get('tx_url', data.get('tx_id', 'unknown')), defaults={'user': user, 'coin': coin, 'amount': amount, 'status': status})
                    if created:
                        wallet, _ = UserBalance.objects.get_or_create(user=user)
                        wallet.spot_balance += Decimal(amount)
                        wallet.save()
                        if order_number.startswith('FEE_'):
                            task = FeeTask.objects.filter(user=user, is_paid=False).first()
                            if task: task.is_paid = True; task.save()
            return JsonResponse({"status": "ok"})
        except Exception as e: return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "invalid_method"})

def withdraw_coin(request): return render(request, 'withdraw_coin.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username') or request.POST.get('name') or request.POST.get('user')
        password = request.POST.get('password') or request.POST.get('pass')
        if not username or not password: return render(request, 'register.html', {'error': 'بيانات ناقصة.'})
        if User.objects.filter(username=username).exists(): return render(request, 'register.html', {'error': 'مستخدم مسبقاً.'})
        try:
            user = User.objects.create_user(username=username, email=request.POST.get('email', ''), password=password)
            login(request, user)
            return redirect('/dashboard/')
        except Exception as e: return render(request, 'register.html', {'error': str(e)})
    return render(request, 'register.html')

def withdrawal_detail(request, pk):
    if not request.user.is_authenticated: return redirect('/register/')
    return render(request, 'withdrawal_detail.html', {'req': get_object_or_404(WithdrawalRequest, pk=pk, user=request.user)})

@login_required(login_url='login')
def fee_task_view(request): return render(request, 'fee_task.html', {'tasks': FeeTask.objects.filter(user=request.user).order_by('created_at')})

@login_required(login_url='login')
def futures_trade_view(request):
    user_bal, _ = UserBalance.objects.get_or_create(user=request.user, defaults={'spot_balance': 0, 'futures_balance': 0})
    return render(request, 'futures.html', {
        'balance': user_bal.futures_balance, 'spot_balance': user_bal.spot_balance, 'futures_balance': user_bal.futures_balance,
        'open_trades': FuturesTrade.objects.filter(user=request.user, status='open').order_by('-created_at')
    })

@login_required(login_url='login')
def trade_view(request):
    user_bal, _ = UserBalance.objects.get_or_create(user=request.user, defaults={'spot_balance': 0, 'futures_balance': 0})
    return render(request, 'trade.html', {'balance': user_bal.spot_balance, 'spot_balance': user_bal.spot_balance, 'futures_balance': user_bal.futures_balance})

@csrf_exempt
@login_required(login_url='login')
def transfer_balance_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            amount, from_w, to_w = Decimal(str(data.get('amount', '0'))), data.get('from_wallet'), data.get('to_wallet')
            if amount <= 0: return JsonResponse({'success': False, 'error': 'مبلغ غير صحيح'})
            with transaction.atomic():
                user_bal = UserBalance.objects.select_for_update().get(user=request.user)
                if from_w == 'spot' and to_w == 'futures':
                    if user_bal.spot_balance >= amount:
                        user_bal.spot_balance -= amount; user_bal.futures_balance += amount; user_bal.save()
                        return JsonResponse({'success': True, 'message': 'تم النقل للآجلة'})
                    return JsonResponse({'success': False, 'error': 'رصيد الفوري غير كافٍ'})
                elif from_w == 'futures' and to_w == 'spot':
                    if user_bal.futures_balance >= amount:
                        user_bal.futures_balance -= amount; user_bal.spot_balance += amount; user_bal.save()
                        return JsonResponse({'success': True, 'message': 'تم النقل للفورية'})
                    return JsonResponse({'success': False, 'error': 'رصيد الآجلة غير كافٍ'})
            return JsonResponse({'success': False, 'error': 'تحديد خاطئ'})
        except Exception as e: return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required(login_url='login')
def execute_trade_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            margin = Decimal(str(data.get('margin', '0')))
            entry_price = Decimal(str(data.get('entry_price', '0')))
            if margin <= 0 or entry_price <= 0: return JsonResponse({'success': False, 'error': 'بيانات غير صحيحة'})
            
            with transaction.atomic():
                user_bal = UserBalance.objects.select_for_update().get(user=request.user)
                if user_bal.futures_balance < margin: 
                    return JsonResponse({'success': False, 'error': 'رصيد العقود الآجلة غير كافٍ'})
                
                user_bal.futures_balance -= margin 
                user_bal.save()

                trade_instance = FuturesTrade.objects.create(
                    user=request.user, symbol=data.get('symbol', 'BTCUSDT'), trade_type=data.get('type'),
                    margin=margin, leverage=int(data.get('leverage', '1')), entry_price=entry_price, status='open'
                )
            return JsonResponse({'success': True, 'message': 'تم فتح الصفقة بنجاح', 'trade_id': trade_instance.id})
        except Exception as e: return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required(login_url='login')
def close_trade_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            with transaction.atomic():
                trade = FuturesTrade.objects.select_for_update().get(id=data.get('trade_id'), user=request.user, status='open')
                user_bal = UserBalance.objects.select_for_update().get(user=request.user)
                
                pct = Decimal(str(data.get('percent', '100'))) / Decimal('100')
                close_price = Decimal(str(data.get('close_price', '0')))
                margin_mode = data.get('margin_mode', 'isolated')
                
                margin_closed = trade.margin * pct
                qty_closed = margin_closed / trade.entry_price
                
                pnl = (close_price - trade.entry_price) * qty_closed * trade.leverage if trade.trade_type == 'long' else (trade.entry_price - close_price) * qty_closed * trade.leverage
                
                if margin_mode == 'isolated':
                    if pnl < -margin_closed:
                        pnl = -margin_closed
                else:
                    max_loss = margin_closed + user_bal.futures_balance
                    if pnl < -max_loss:
                        pnl = -max_loss
                
                user_bal.futures_balance += (margin_closed + pnl) 
                user_bal.save()

                if pct == Decimal('1'):
                    trade.status = 'closed'; trade.close_price = close_price; trade.pnl = pnl; trade.save()
                else:
                    trade.margin -= margin_closed; trade.save()
            return JsonResponse({'success': True, 'message': 'تم الإغلاق بنجاح'})
        except Exception as e: return JsonResponse({'success': False, 'error': str(e)})

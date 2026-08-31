import os
import asyncio
from telethon.sync import TelegramClient
from telethon import functions, types

 =================================
C = "\033[1;36m"  # سماوي
G = "\033[1;32m"  # أخضر
Y = "\033[1;33m"  # أصفر
R = "\033[1;31m"  # أحمر
W = "\033[1;37m"  # أبيض
 =================================================

# بيانات حسابك في تيليجرام
API_ID = 11051416
API_HASH = '33cab7587b467d750c6d65434820c2e9' 
PHONE_NUMBER = '+967...' # استبدل النقاط برقم هاتفك مع الرمز الدولي

def print_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(C + "==================================================" + W)
    print(Y + "       🌟 تصميم عبد الملك للبحث القروبات 🌟       " + W)
    print(C + "==================================================" + W)
    print(G + " [✓] جاري تهيئة الاتصال بخوادم تيليجرام..." + W)
    print(C + "==================================================\n" + W)

async def search_telegram_groups():
    print_banner()
    
    client = TelegramClient('abdulmalik_session', API_ID, API_HASH)
    await client.start(phone=PHONE_NUMBER)

    while True:
        keyword = input(Y + " 🔍 أدخل الكلمة للبحث (أو اكتب 'خروج' للإيقاف): " + W)
        
        if keyword.strip() == '':
            continue
        if keyword.strip() in ['خروج', 'exit', 'quit']:
            print(R + "\n [!] تم إنهاء السكربت. في أمان الله!\n" + W)
            break

        print(G + f"\n [~] جاري البحث عن '{keyword}'...\n" + W)

        try:
            result = await client(functions.contacts.SearchRequest(
                q=keyword,
                limit=50
            ))

            found = False
            
            for chat in result.chats:
                if isinstance(chat, (types.Channel, types.Chat)):
                    if getattr(chat, 'megagroup', False) or isinstance(chat, types.Chat):
                        found = True
                        title = chat.title
                        # تحويل المعرف إلى رابط قابل للضغط
                        link = f"https://t.me/{chat.username}" if getattr(chat, 'username', None) else "لا يوجد رابط عام"
                        
                        print(C + f" 📌 اسم الجروب :" + W + f" {title}")
                        print(C + f" 🔗 الرابط      :" + W + f" {link}")
                        print(C + "-" * 40 + W)
                        
            if not found:
                print(R + " [!] لم يتم العثور على جروبات عامة تطابق هذه الكلمة." + W)
            
            print("\n")

        except Exception as e:
            print(R + f" [x] حدث خطأ أثناء البحث: {e}" + W)

    await client.disconnect()

if __name__ == '__main__':
    try:
        asyncio.run(search_telegram_groups())
    except KeyboardInterrupt:
        print(R + "\n\n [!] تم إغلاق السكربت." + W)

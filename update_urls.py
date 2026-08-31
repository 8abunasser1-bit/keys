import re
with open('investors/urls.py', 'r') as f:
    content = f.read()
if 'api/generate_address/' not in content:
    content = re.sub(r'(urlpatterns\s*=\s*\[)', r"\1\n    path('api/generate_address/', views.generate_deposit_address, name='api_generate_address'),", content)
    with open('investors/urls.py', 'w') as f
        f.write(content)

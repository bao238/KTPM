import time
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Các trang không cần kiểm tra
        exempt_urls = [reverse('login'), reverse('register'), reverse('home')]
        
        if request.user.is_authenticated and request.path not in exempt_urls:
            current_time = time.time()
            
            # Lần đầu tiên truy cập, tạo thời gian hoạt động
            if 'last_activity' not in request.session:
                request.session['last_activity'] = current_time
            
            last_activity = request.session.get('last_activity', current_time)
            
            # Chỉ kiểm tra timeout khi session đã tồn tại ít nhất 5 giây
            timeout = getattr(settings, 'SESSION_COOKIE_AGE', 86400)
            if current_time - last_activity > timeout and current_time - last_activity > 5:
                logout(request)
                request.session.flush()
                messages.error(request, "Phiên làm việc đã hết hạn. Vui lòng đăng nhập lại.")
                return redirect('login')
            
            # Cập nhật thời gian hoạt động gần nhất
            request.session['last_activity'] = current_time
            
        response = self.get_response(request)
        return response 
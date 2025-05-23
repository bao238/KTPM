from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from store.models import Profile
from django import forms
import time

# Form Profile mở rộng
class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(max_length=254, required=False)

    class Meta:
        model = Profile
        fields = [
            'avatar', 'bio', 'phone_number', 'address', 'birthdate',
            'website', 'facebook', 'twitter', 'instagram'
        ]
        widgets = {
            'birthdate': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

# View đăng ký
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đăng ký tài khoản thành công! Vui lòng đăng nhập.')
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})

# View đăng nhập (đã sửa fix lỗi CSRF)
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Xóa session cũ trước khi đăng nhập
            request.session.flush()
            
            # Đăng nhập với user mới
            user = form.get_user()
            login(request, user)
            
            # Khởi tạo thời gian hoạt động
            request.session['last_activity'] = time.time()
            
            # Đảm bảo session được lưu
            request.session.modified = True
            
            messages.success(request, 'Đăng nhập thành công!')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})

# View đăng xuất
def logout_view(request):
    # Lấy session key trước khi đăng xuất
    session_key = request.session.session_key
    
    # Đảm bảo đăng xuất hoàn toàn
    logout(request)
    
    # Xóa session cũ
    request.session.flush()
    
    # Nếu cần, xóa session trong database
    if session_key:
        from django.contrib.sessions.models import Session
        try:
            Session.objects.get(session_key=session_key).delete()
        except Session.DoesNotExist:
            pass
    
    messages.success(request, 'Bạn đã đăng xuất.')
    return redirect('home')

# View hồ sơ cá nhân
@login_required
def profile_view(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Cập nhật User
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()

            # Cập nhật Profile
            form.save()

            messages.success(request, 'Thông tin cá nhân đã được cập nhật thành công!')
            return redirect('account_profile')
    else:
        form = ProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
    }

    return render(request, 'accounts/profile.html', context)

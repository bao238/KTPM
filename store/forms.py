from django import forms
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import Product, Category, Profile, Color, Order, ProductImage, Province, District, Ward

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'discount_percent', 'category', 'image', 'colors']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'colors': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
        }

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['color', 'image']
        widgets = {
            'color': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Họ và tên người nhận'}))
    
    phone_regex = RegexValidator(
        regex=r'^[0-9]+$',
        message="Số điện thoại chỉ được nhập số."
    )
    phone = forms.CharField(
        max_length=15, 
        validators=[phone_regex],
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Số điện thoại',
            'pattern': '[0-9]*',
            'title': 'Vui lòng chỉ nhập số'
        })
    )
    
    address = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Địa chỉ'}))
    
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        empty_label="Chọn Tỉnh/Thành phố",
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    
    district = forms.ModelChoiceField(
        queryset=District.objects.none(),
        empty_label="Chọn Quận/Huyện",
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=False
    )
    
    ward = forms.ModelChoiceField(
        queryset=Ward.objects.none(),
        empty_label="Chọn Phường/Xã",
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=False
    )
    
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ghi chú đơn hàng'}))
    payment_method = forms.ChoiceField(
        choices=[('cod', 'Thanh toán khi nhận hàng'), ('bank', 'Chuyển khoản ngân hàng')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if 'province' in self.data:
            try:
                province_id = int(self.data.get('province'))
                self.fields['district'].queryset = District.objects.filter(province_id=province_id)
            except (ValueError, TypeError):
                pass
        
        if 'district' in self.data:
            try:
                district_id = int(self.data.get('district'))
                self.fields['ward'].queryset = Ward.objects.filter(district_id=district_id)
            except (ValueError, TypeError):
                pass 
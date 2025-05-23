from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Color(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, help_text="Mã màu HEX, ví dụ: #FF0000")
    
    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    discount_percent = models.IntegerField(default=0, blank=True, help_text="Phần trăm giảm giá từ 0-100")
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    colors = models.ManyToManyField(Color, blank=True, related_name='products')

    @property
    def has_discount(self):
        return self.discount_percent is not None and self.discount_percent > 0
    
    @property
    def discount_price(self):
        if not self.has_discount:
            return self.price
        discount_amount = (self.price * self.discount_percent) / 100
        return self.price - discount_amount
        
    @property
    def rating_avg(self):
        """Tính điểm đánh giá trung bình của sản phẩm"""
        reviews = self.reviews.all()
        if not reviews:
            return 0
        total_rating = sum(review.rating for review in reviews)
        return total_rating / len(reviews)
        
    @property
    def rating_count(self):
        """Đếm số lượng đánh giá của sản phẩm"""
        return self.reviews.count()

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='color_images')
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_colors/')
    
    class Meta:
        unique_together = ('product', 'color')
        
    def __str__(self):
        return f"{self.product.name} - {self.color.name}"

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Chờ xử lý'),
        ('confirmed', 'Đã xác nhận'),
        ('processing', 'Đang xử lý'),
        ('shipped', 'Đang giao hàng'),
        ('delivered', 'Đã giao hàng'),
        ('cancelled', 'Đã hủy'),
    )
    
    PAYMENT_CHOICES = (
        ('cod', 'Thanh toán khi nhận hàng (COD)'),
        ('bank_transfer', 'Chuyển khoản ngân hàng'),
        ('momo', 'Ví điện tử MoMo'),
        ('zalopay', 'ZaloPay'),
        ('vnpay', 'VNPAY'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    province = models.ForeignKey('Province', on_delete=models.PROTECT, null=True)
    district = models.ForeignKey('District', on_delete=models.PROTECT, null=True)
    ward = models.ForeignKey('Ward', on_delete=models.PROTECT, null=True)
    city = models.CharField(max_length=50, blank=True)
    district_name = models.CharField(max_length=50, blank=True)
    ward_name = models.CharField(max_length=50, blank=True)
    note = models.TextField(blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Đơn hàng #{self.id} - {self.user.username}"
        
    def save(self, *args, **kwargs):
        if self.province:
            self.city = self.province.name
        if self.district:
            self.district_name = self.district.name
        if self.ward:
            self.ward_name = self.ward.name
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=0)

    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class Review(models.Model):
    RATING_CHOICES = (
        (1, '1 sao'),
        (2, '2 sao'),
        (3, '3 sao'),
        (4, '4 sao'),
        (5, '5 sao'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    image = models.ImageField(upload_to='review_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Đánh giá của {self.user.username} cho {self.product.name}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png')
    bio = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.CharField(max_length=255, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    website = models.URLField(max_length=200, blank=True)
    facebook = models.URLField(max_length=200, blank=True)
    twitter = models.URLField(max_length=200, blank=True)
    instagram = models.URLField(max_length=200, blank=True)
    
    def __str__(self):
        return f'Profile của {self.user.username}'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)

class Province(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class District(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='districts')
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Ward(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='wards')
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

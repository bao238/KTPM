from django.contrib import admin
from .models import Product, Category, CartItem, Order, OrderItem, Review, Profile, Color, ProductImage
from django.contrib import messages
from django.db.models import Count

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'subtotal']
    fields = ['product', 'quantity', 'price', 'subtotal']
    can_delete = False
    
    def subtotal(self, obj):
        return obj.price * obj.quantity
    subtotal.short_description = 'Thành tiền'
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'discount_percent', 'discount_price', 'category']
    list_filter = ['category', 'discount_percent']
    search_fields = ['name', 'description']
    inlines = [ProductImageInline]
    list_editable = ['discount_percent']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'color']
    list_filter = ['user']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'full_name', 'status', 'total', 'created_at', 'item_count']
    list_filter = ['status', 'created_at', 'user']
    search_fields = ['full_name', 'phone', 'address', 'user__username', 'id']
    readonly_fields = ['created_at', 'total']
    list_editable = ['status']
    inlines = [OrderItemInline]
    
    def get_queryset(self, request):
        # Sử dụng annotate để thêm thông tin về số lượng item trong mỗi đơn hàng
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(items_count=Count('items'))
        return queryset
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Số món'
    
    def has_view_permission(self, request, obj=None):
        # Admin có thể xem tất cả đơn hàng
        return True
        
    def has_change_permission(self, request, obj=None):
        # Admin có thể chỉnh sửa tất cả đơn hàng
        return True

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'order_user', 'product', 'quantity', 'price', 'subtotal')
    list_filter = ('order__status', 'order__user')
    search_fields = ('order__id', 'product__name', 'order__user__username')
    
    def order_user(self, obj):
        return obj.order.user.username
    order_user.short_description = 'Khách hàng'
    
    def subtotal(self, obj):
        return obj.price * obj.quantity
    subtotal.short_description = 'Thành tiền'
    
    def get_queryset(self, request):
        # Đảm bảo hiển thị tất cả OrderItem cho admin
        qs = super().get_queryset(request).select_related('order', 'product', 'order__user')
        return qs
        
    def has_view_permission(self, request, obj=None):
        # Đảm bảo admin có thể xem tất cả OrderItem
        return True

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['comment', 'product__name', 'user__username']

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name']

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'color')
    list_filter = ('product', 'color')
    search_fields = ('product__name', 'color__name')

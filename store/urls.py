from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('update-cart-item-ajax/<int:item_id>/', views.update_cart_item_ajax, name='update_cart_item_ajax'),
    path('checkout/', views.checkout_form_view, name='checkout'),
    path('profile/', views.profile_view, name='store_profile'),
    path('orders/', views.order_history_view, name='order_history'),
    path('order/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('delete-order/<int:order_id>/', views.delete_order, name='delete_order'),
    path('update-order-address/<int:order_id>/', views.update_order_address, name='update_order_address'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('add-product/', views.add_product, name='add_product'),
    path('add-product/<int:product_id>/images/', views.add_product_images, name='add_product_images'),
    path('search/', views.search_products, name='search_products'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/review/', views.add_review, name='add_review'),
    path('delete-review/<int:review_id>/', views.delete_review, name='delete_review'),
    
    # API URLs cho địa chỉ
    path('api/districts/', views.get_districts, name='api_districts'),
    path('api/wards/', views.get_wards, name='api_wards'),
]

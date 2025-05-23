from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from store.views import home, product_list, product_detail, add_to_cart, cart_view, remove_from_cart, update_cart_item, update_cart_item_ajax, checkout_form_view, profile_view, order_history_view, add_product, add_product_images, add_review, search_products, delete_review, delete_order, update_order_address, cancel_order, order_detail_view, bulk_discount

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('products/', product_list, name='product_list'),
    path('products/<int:product_id>/', product_detail, name='product_detail'),
    path('products/<int:product_id>/add_to_cart/', add_to_cart, name='add_to_cart'),
    path('cart/', cart_view, name='cart'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', update_cart_item, name='update_cart_item'),
    path('cart/update-ajax/<int:item_id>/', update_cart_item_ajax, name='update_cart_item_ajax'),
    path('checkout/', checkout_form_view, name='checkout'),
    path('accounts/', include('allauth.urls')),
    path('profile/', profile_view, name='store_profile'),
    path('orders/', order_history_view, name='order_history'),
    path('orders/<int:order_id>/', order_detail_view, name='order_detail'),
    path('orders/<int:order_id>/cancel/', cancel_order, name='cancel_order'),
    path('orders/<int:order_id>/update-address/', update_order_address, name='update_order_address'),
    path('orders/<int:order_id>/delete/', delete_order, name='delete_order'),
    path('add-product/', add_product, name='add_product'),
    path('add-product/<int:product_id>/images/', add_product_images, name='add_product_images'),
    path('products/<int:product_id>/add-review/', add_review, name='add_review'),
    path('reviews/<int:review_id>/delete/', delete_review, name='delete_review'),
    path('search/', search_products, name='search_products'),
    path('admin/bulk-discount/', bulk_discount, name='bulk_discount'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
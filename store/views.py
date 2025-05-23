from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, CartItem, Order, OrderItem, Review, Color, ProductImage, Province, District, Ward
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .forms import UserProfileForm, ProductForm, CheckoutForm, ProductImageForm
from django import forms
from django.db import models, connection
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required

# Form tạm thời cho việc cập nhật giảm giá hàng loạt
class BulkDiscountForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    discount_percent = forms.IntegerField(
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Áp dụng cho sản phẩm có giá lớn hơn hoặc bằng giá này"
    )
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Áp dụng cho sản phẩm có giá nhỏ hơn hoặc bằng giá này"
    )


def home(request):
    # Lấy danh mục nổi bật (ví dụ: 3 danh mục đầu tiên)
    featured_categories = Category.objects.all()[:3]
    
    # Lấy tất cả danh mục để hiển thị trong bộ lọc
    categories = Category.objects.all()
    
    # Lấy tất cả sản phẩm nổi bật, nhưng hiển thị theo JavaScript
    initial_products_count = 8  # Số lượng sản phẩm hiển thị ban đầu
    
    # Lấy tối đa 50 sản phẩm để có thể xem thêm nhiều lần
    featured_products = Product.objects.all()[:50]
    
    # Kiểm tra xem có thể tải thêm sản phẩm không
    total_products = Product.objects.count()
    has_more_products = total_products > initial_products_count
    
    # Tính số lượng sản phẩm trong giỏ hàng nếu đã đăng nhập
    cart_items_count = 0
    if request.user.is_authenticated:
        cart_items_count = CartItem.objects.filter(user=request.user).count()
    
    return render(request, 'store/home.html', {
        'featured_categories': featured_categories,
        'categories': categories,
        'featured_products': featured_products,
        'initial_products_count': initial_products_count,
        'has_more_products': has_more_products,
        'total_products': total_products,
        'cart_items_count': cart_items_count
    })

def product_list(request):
    category_id = request.GET.get('category')
    if category_id:
        products = Product.objects.filter(category_id=category_id)
    else:
        products = Product.objects.all()

    # Lấy tất cả danh mục để hiển thị trong menu
    categories = Category.objects.all()
    
    # Tính số lượng sản phẩm trong giỏ hàng nếu đã đăng nhập
    cart_items_count = 0
    if request.user.is_authenticated:
        cart_items_count = CartItem.objects.filter(user=request.user).count()
    
    # Phân trang
    paginator = Paginator(products, 6)  # 6 sản phẩm mỗi trang
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    selected_category = int(category_id) if category_id else None

    context = {
        'categories': categories,
        'page_obj': page_obj,
        'selected_category': selected_category,
        'cart_items_count': cart_items_count
    }
    return render(request, 'store/product_list.html', context)

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Lấy màu sắc từ request nếu có
    color_id = request.POST.get('color')
    color = None
    if color_id:
        try:
            color = Color.objects.get(id=color_id)
        except Color.DoesNotExist:
            pass
    
    # Kiểm tra xem sản phẩm với màu đó đã có trong giỏ hàng chưa
    if color:
        item, created = CartItem.objects.get_or_create(
            user=request.user, 
            product=product,
            color=color,
            defaults={'quantity': 1}
        )
    else:
        item, created = CartItem.objects.get_or_create(
            user=request.user, 
            product=product,
            color=None,
            defaults={'quantity': 1}
        )
    
    if not created:
        item.quantity += 1
        item.save()
    
    # Cập nhật số lượng sản phẩm trong giỏ hàng
    cart_items_count = CartItem.objects.filter(user=request.user).count()
    
    # Nếu là ajax request thì trả về JsonResponse
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': f"Đã thêm {product.name} vào giỏ hàng thành công!",
            'cart_items_count': cart_items_count
        })
    
    # Nếu không phải ajax request thì hiển thị thông báo và chuyển hướng
    messages.success(request, f"Đã thêm {product.name} vào giỏ hàng thành công!")
    return redirect('cart')

@login_required
def cart_view(request):
    items = CartItem.objects.filter(user=request.user)
    total = sum(item.subtotal() for item in items)
    return render(request, 'store/cart.html', {'items': items, 'total': total})

@login_required
def remove_from_cart(request, item_id):
    try:
        item = CartItem.objects.get(id=item_id, user=request.user)
        item.delete()
        messages.success(request, "Đã xóa sản phẩm khỏi giỏ hàng")
    except CartItem.DoesNotExist:
        messages.error(request, "Không tìm thấy sản phẩm trong giỏ hàng")
    return redirect('cart')

@login_required
def checkout_form_view(request):
    items = CartItem.objects.filter(user=request.user)
    if not items.exists():
        messages.warning(request, "Giỏ hàng của bạn đang trống!")
        return redirect('cart')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                # Tạo đơn hàng mới
                order = Order(
                    user=request.user,
                    full_name=form.cleaned_data['full_name'],
                    phone=form.cleaned_data['phone'],
                    address=form.cleaned_data['address'],
                    province=form.cleaned_data['province'],
                    district=form.cleaned_data['district'],
                    ward=form.cleaned_data['ward'],
                    note=form.cleaned_data['note'],
                    payment_method=form.cleaned_data['payment_method'],
                    total=sum(item.subtotal() for item in items)
                )
                order.save()  # Đảm bảo đơn hàng được lưu vào cơ sở dữ liệu

                # Tạo các OrderItem
                for item in items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price if not item.product.has_discount else item.product.discount_price
                    )

                # Xóa tất cả sản phẩm trong giỏ hàng sau khi đặt hàng thành công
                items.delete()

                messages.success(request, "Đặt hàng thành công! Cảm ơn bạn đã mua hàng.")
                return redirect('order_detail', order_id=order.id)
            except Exception as e:
                messages.error(request, f"Có lỗi xảy ra khi đặt hàng: {str(e)}")
    else:
        form = CheckoutForm()
    
    return render(request, 'store/checkout_form.html', {
        'form': form,
        'cart_items': items,
        'total_price': sum(item.subtotal() for item in items)
    })

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thông tin của bạn đã được cập nhật thành công!')
            return redirect('store_profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'store/profile.html', {
        'user': request.user,
        'form': form
    })

@login_required
def order_history_view(request):
    # Bảo vệ bởi @login_required nên không cần kiểm tra thêm
    # Đảm bảo dữ liệu đơn hàng luôn được tải mới từ cơ sở dữ liệu (force refresh)
    connection.close()  # Đóng kết nối hiện tại để đảm bảo dữ liệu mới
    
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Sản phẩm đã được thêm thành công!')
            return redirect('add_product_images', product_id=product.id)
        else:
            messages.error(request, 'Đã xảy ra lỗi. Vui lòng kiểm tra lại thông tin.')
    else:
        form = ProductForm()
        
    return render(request, 'store/add_product.html', {
        'form': form
    })

@login_required
def add_product_images(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    colors = product.colors.all()
    
    if request.method == 'POST':
        color_id = request.POST.get('color')
        image = request.FILES.get('image')
        
        if color_id and image:
            color = get_object_or_404(Color, id=color_id)
            
            # Kiểm tra xem đã có hình ảnh cho màu này chưa
            product_image, created = ProductImage.objects.get_or_create(
                product=product,
                color=color,
                defaults={'image': image}
            )
            
            if not created:
                product_image.image = image
                product_image.save()
                
            messages.success(request, f'Đã thêm hình ảnh cho màu {color.name}!')
            
            # Kiểm tra xem đã thêm hình ảnh cho tất cả các màu chưa
            if ProductImage.objects.filter(product=product).count() == colors.count():
                messages.success(request, 'Đã thêm đầy đủ hình ảnh cho tất cả các màu!')
                return redirect('product_detail', product_id=product.id)
        else:
            messages.error(request, 'Vui lòng chọn màu sắc và tải lên hình ảnh.')
    
    # Lọc ra những màu đã có hình ảnh
    colors_with_images = Color.objects.filter(
        id__in=ProductImage.objects.filter(product=product).values_list('color_id', flat=True)
    )
    
    # Lọc ra những màu chưa có hình ảnh
    colors_without_images = colors.exclude(id__in=colors_with_images)
    
    return render(request, 'store/add_product_images.html', {
        'product': product,
        'colors_without_images': colors_without_images,
        'colors_with_images': colors_with_images
    })

@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        quantity = request.POST.get('quantity')
        try:
            item = CartItem.objects.get(id=item_id, user=request.user)
            item.quantity = int(quantity)
            item.save()
        except (CartItem.DoesNotExist, ValueError):
            messages.error(request, "Không thể cập nhật số lượng sản phẩm.")
    return redirect('cart')

@login_required
def update_cart_item_ajax(request, item_id):
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity < 1:
                quantity = 1
                
            item = CartItem.objects.get(id=item_id, user=request.user)
            item.quantity = quantity
            item.save()
            
            # Tính lại tổng tiền
            cart_items = CartItem.objects.filter(user=request.user)
            total = sum(item.subtotal() for item in cart_items)
            
            return JsonResponse({
                'status': 'success',
                'subtotal': item.subtotal(),
                'total': total,
                'cart_items_count': cart_items.count()
            })
        except (CartItem.DoesNotExist, ValueError):
            return JsonResponse({
                'status': 'error',
                'message': 'Không thể cập nhật số lượng sản phẩm.'
            }, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Phương thức không được hỗ trợ'}, status=405)

@login_required
def delete_order(request, order_id):
    if not request.user.is_staff:
        messages.error(request, "Bạn không có quyền xóa đơn hàng.")
        return redirect('order_history')
        
    order = get_object_or_404(Order, id=order_id)
    
    # Chỉ cho phép xóa đơn hàng khi đã giao hoặc đã hủy
    if order.status not in ['delivered', 'cancelled']:
        messages.error(request, "Chỉ có thể xóa đơn hàng khi đã giao hoặc đã hủy.")
        return redirect('order_history')
    
    order.delete()
    messages.success(request, "Đơn hàng đã được xóa thành công!")
    return redirect('order_history')

@login_required
def update_order_address(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status != 'pending':
        messages.error(request, "Chỉ có thể cập nhật địa chỉ cho đơn hàng đang chờ xử lý.")
        return redirect('order_history')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order.full_name = form.cleaned_data['full_name']
            order.phone = form.cleaned_data['phone']
            order.address = form.cleaned_data['address']
            order.province = form.cleaned_data['province']
            order.district = form.cleaned_data['district']
            order.ward = form.cleaned_data['ward']
            order.note = form.cleaned_data['note']
            order.payment_method = form.cleaned_data['payment_method']
            order.save()
            messages.success(request, "Thông tin giao hàng đã được cập nhật thành công!")
            return redirect('order_history')
    else:
        initial_data = {
            'full_name': order.full_name,
            'phone': order.phone,
            'address': order.address,
            'province': order.province,
            'district': order.district,
            'ward': order.ward,
            'note': order.note,
            'payment_method': order.payment_method
        }
        form = CheckoutForm(initial=initial_data)
        
        # Đặt queryset cho các dropdown
        if order.province:
            form.fields['district'].queryset = District.objects.filter(province=order.province)
        if order.district:
            form.fields['ward'].queryset = Ward.objects.filter(district=order.district)
    
    return render(request, 'store/checkout_form.html', {
        'form': form,
        'order': order,
        'is_update': True
    })

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status != 'pending':
        messages.error(request, "Chỉ có thể hủy đơn hàng đang chờ xử lý.")
        return redirect('order_history')
    
    order.status = 'cancelled'
    order.save()
    messages.success(request, "Đơn hàng đã được hủy thành công!")
    return redirect('order_history')

def search_products(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(name__icontains=query)
    else:
        products = Product.objects.all()
    
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'store/product_list.html', {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'query': query
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product).order_by('-created_at')
    
    # Lấy danh sách các màu của sản phẩm
    colors = product.colors.all()
    
    # Lấy danh sách hình ảnh theo màu
    color_images = ProductImage.objects.filter(product=product)
    
    # Tính điểm trung bình
    avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
    
    if request.method == 'POST' and request.user.is_authenticated:
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            Review.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'Đánh giá của bạn đã được gửi thành công!')
            return redirect('product_detail', product_id=product_id)
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'colors': colors,
        'color_images': color_images
    })

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        image = request.FILES.get('review_image')
        
        if rating and comment:
            review = Review.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment
            )
            
            # Lưu ảnh nếu có
            if image:
                review.image = image
                review.save()
                
            messages.success(request, 'Đánh giá của bạn đã được gửi thành công!')
        else:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin đánh giá!')
    
    return redirect('product_detail', product_id=product_id)

@login_required
def order_detail_view(request, order_id):
    # @login_required đã đảm bảo người dùng đăng nhập
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.all()
    
    # Tạo dữ liệu cho timeline theo dõi đơn hàng
    timeline_steps = [
        {'status': 'pending', 'label': 'Chờ xử lý', 'completed': True, 'current': order.status == 'pending'},
        {'status': 'confirmed', 'label': 'Đã xác nhận', 'completed': order.status in ['confirmed', 'processing', 'shipped', 'delivered'], 'current': order.status == 'confirmed'},
        {'status': 'processing', 'label': 'Đang xử lý', 'completed': order.status in ['processing', 'shipped', 'delivered'], 'current': order.status == 'processing'},
        {'status': 'shipped', 'label': 'Đang giao hàng', 'completed': order.status in ['shipped', 'delivered'], 'current': order.status == 'shipped'},
        {'status': 'delivered', 'label': 'Đã giao hàng', 'completed': order.status == 'delivered', 'current': order.status == 'delivered'},
    ]
    
    # Kiểm tra nếu đơn hàng đã bị hủy
    is_cancelled = order.status == 'cancelled'
    
    return render(request, 'store/order_detail.html', {
        'order': order,
        'items': items,
        'timeline_steps': timeline_steps,
        'is_cancelled': is_cancelled
    })

@login_required
def delete_review(request, review_id):
    # Lấy đánh giá theo ID
    review = get_object_or_404(Review, id=review_id)
    product_id = review.product.id
    
    # Kiểm tra quyền xóa (chỉ cho phép người dùng xóa đánh giá của chính họ hoặc admin)
    if review.user == request.user or request.user.is_staff:
        review.delete()
        messages.success(request, 'Đánh giá đã được xóa thành công!')
    else:
        messages.error(request, 'Bạn không có quyền xóa đánh giá này!')
    
    return redirect('product_detail', product_id=product_id)

@staff_member_required
def bulk_discount(request):
    if request.method == 'POST':
        form = BulkDiscountForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data['category']
            discount_percent = form.cleaned_data['discount_percent']
            min_price = form.cleaned_data['min_price']
            max_price = form.cleaned_data['max_price']
            
            # Xây dựng query cơ bản
            products = Product.objects.all()
            
            # Lọc theo danh mục nếu có
            if category:
                products = products.filter(category=category)
            
            # Lọc theo giá nếu có
            if min_price:
                products = products.filter(price__gte=min_price)
            if max_price:
                products = products.filter(price__lte=max_price)
            
            # Áp dụng giảm giá
            count = products.count()
            products.update(discount_percent=discount_percent)
            
            messages.success(request, f'Đã áp dụng giảm giá {discount_percent}% cho {count} sản phẩm.')
            return redirect('bulk_discount')
    else:
        form = BulkDiscountForm()
    
    # Hiển thị danh sách sản phẩm có giảm giá
    discounted_products = Product.objects.filter(discount_percent__gt=0)
    
    return render(request, 'store/bulk_discount.html', {
        'form': form,
        'discounted_products': discounted_products
    })

def get_districts(request):
    province_id = request.GET.get('province')
    print(f"DEBUG: Getting districts for province_id={province_id}")
    
    if province_id:
        try:
            province_id = int(province_id)
            districts = District.objects.filter(province_id=province_id).order_by('name')
            
            # Nếu không có quận/huyện nào, tạo dữ liệu mẫu
            if districts.count() == 0:
                print(f"DEBUG: Không có quận/huyện nào cho tỉnh id={province_id}, tạo dữ liệu mẫu")
                # Tạo dữ liệu mẫu - Không lưu vào DB
                dummy_districts = [
                    {'id': 900001, 'name': 'Quận 1'},
                    {'id': 900002, 'name': 'Quận 2'},
                    {'id': 900003, 'name': 'Quận 3'},
                    {'id': 900004, 'name': 'Huyện Hòa Vang'},
                    {'id': 900005, 'name': 'Huyện Điện Bàn'}
                ]
                result = dummy_districts
            else:
                result = [{'id': district.id, 'name': district.name} for district in districts]
            
            print(f"DEBUG: Found {len(result)} districts for province_id={province_id}")
            
            # In ra chi tiết dữ liệu để debug
            for i, district in enumerate(result[:5]):  # Chỉ hiển thị 5 phần tử đầu để tránh log quá dài
                print(f"  - District {i+1}: ID={district['id']}, Name={district['name']}")
                
            response = JsonResponse(result, safe=False)
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
            return response
        except (ValueError, TypeError) as e:
            print(f"DEBUG: Error converting province_id to int: {e}")
            response = JsonResponse([], safe=False)
            response["Access-Control-Allow-Origin"] = "*"
            return response
    
    print("DEBUG: No province_id provided, returning empty list")
    response = JsonResponse([], safe=False)
    response["Access-Control-Allow-Origin"] = "*"
    return response

def get_wards(request):
    district_id = request.GET.get('district')
    print(f"DEBUG: Getting wards for district_id={district_id}")
    
    if district_id:
        try:
            district_id = int(district_id)
            wards = Ward.objects.filter(district_id=district_id).order_by('name')
            
            # Nếu không có phường/xã nào, tạo dữ liệu mẫu
            if wards.count() == 0:
                print(f"DEBUG: Không có phường/xã nào cho quận/huyện id={district_id}, tạo dữ liệu mẫu")
                # Tạo dữ liệu mẫu - Không lưu vào DB
                dummy_wards = [
                    {'id': 910001, 'name': 'Phường Bến Nghé'},
                    {'id': 910002, 'name': 'Phường Bến Thành'},
                    {'id': 910003, 'name': 'Phường Tân Định'},
                    {'id': 910004, 'name': 'Xã Hòa Tiến'},
                    {'id': 910005, 'name': 'Xã Hòa Phong'}
                ]
                result = dummy_wards
            else:
                result = [{'id': ward.id, 'name': ward.name} for ward in wards]
            
            print(f"DEBUG: Found {len(result)} wards for district_id={district_id}")
            
            # In ra chi tiết dữ liệu để debug
            for i, ward in enumerate(result[:5]):  # Chỉ hiển thị 5 phần tử đầu để tránh log quá dài
                print(f"  - Ward {i+1}: ID={ward['id']}, Name={ward['name']}")
                
            response = JsonResponse(result, safe=False)
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
            return response
        except (ValueError, TypeError) as e:
            print(f"DEBUG: Error converting district_id to int: {e}")
            response = JsonResponse([], safe=False)
            response["Access-Control-Allow-Origin"] = "*"
            return response
    
    print("DEBUG: No district_id provided, returning empty list")
    response = JsonResponse([], safe=False)
    response["Access-Control-Allow-Origin"] = "*"
    return response
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from django.shortcuts import render
from django.db.models import Sum, Count
from django.contrib import messages
from django.http import HttpResponseRedirect

from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from django import forms
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from .models import *

# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('name', 'display_image', 'gallery_link')
#     readonly_fields = ('display_image',)

#     def display_image(self, obj):
#         """Display the main product image in the admin."""
#         if obj.image:
#             return format_html('<img src="{}" width="100" height="100" />', obj.image.url)
#         return "No Image"
    
#     display_image.short_description = "Main Image"
    
#     def gallery_link(self, obj):
#         """Provide a link to open the gallery in a popup."""
#         url = reverse('admin:product_gallery', args=[obj.pk])
#         return format_html('<a href="{}" class="button" target="_blank">View Gallery</a>', url)
    
#     gallery_link.short_description = "Product Gallery"
    
#     def get_urls(self):
#         """Add custom URLs for managing the product gallery in admin."""
#         urls = super().get_urls()
#         custom_urls = [
#             path('gallery/<int:product_id>/', self.admin_site.admin_view(self.product_gallery), name='product_gallery'),
#             path('gallery/delete/<int:image_id>/', self.admin_site.admin_view(self.delete_gallery_image), name='delete_gallery_image'),
#         ]
#         return custom_urls + urls

#     def product_gallery(self, request, product_id):
#         """Display the product gallery images in a popup."""
#         product = get_object_or_404(Product, pk=product_id)
#         images = ProductImage.objects.filter(product=product)

#         if request.method == 'POST':
#             # Handle main image upload
#             if 'main_image' in request.FILES:
#                 product.image = request.FILES['main_image']
#                 product.save()
#                 return redirect('admin:product_gallery', product_id=product.id)

#             # Handle gallery image upload
#             elif 'gallery_image' in request.FILES:
#                 ProductImage.objects.create(product=product, image=request.FILES['gallery_image'])
#                 return redirect('admin:product_gallery', product_id=product.id)

#         context = {
#             'product': product,
#             'images': images,
#         }
#         return TemplateResponse(request, 'admin/product_gallery.html', context)

#     def delete_gallery_image(self, request, image_id):
#         """Handle gallery image deletion."""
#         image = get_object_or_404(ProductImage, pk=image_id)
#         product_id = image.product.id
#         image.delete()
#         return redirect('admin:product_gallery', product_id=product_id)

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'place', 'is_active', 'created_at', 'display_image')
    list_filter = ('place', 'is_active', 'created_at')
    search_fields = ('title', 'tagline', 'button_text', 'place')
    readonly_fields = ('created_at',)
    actions = ['deactivate_banners']

    class Media:
        js = ('admin/js/banner_custom.js',)

    def display_image(self, obj):
        """Display the banner image in the admin."""
        if obj.image:
            return format_html('<img src="{}" width="100" height="50" />'.format(obj.image.url))
        return "No Image"
    
    display_image.short_description = "Banner Image"

    def deactivate_banners(self, request, queryset):
        """Admin action to deactivate selected banners."""
        queryset.update(is_active=False)
    deactivate_banners.short_description = "Deactivate selected banners"

    def get_form(self, request, obj=None, **kwargs):
        """Customize the form for different types of banners."""
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.place == 'primary':  # Main banner
            form.base_fields['button_text'].required = True
            form.base_fields['button_link'].required = True
        else:
            form.base_fields['button_text'].required = False
            form.base_fields['button_link'].required = False
        return form
    # Override get_model_perms to hide this model from Store Owners
    def get_model_perms(self, request):
        # If the user is a store owner, don't show this model in the navigation
        if request.user.groups.filter(name='Store Owner').exists() or request.user.groups.filter(name='Customer').exists():
            return {}  # Empty perms hide the model
        return super().get_model_perms(request)

class CustomUserAdmin(BaseUserAdmin):
    model = User
    list_display = ('id', 'username', 'email', 'phone_number', 'total_amount_spent', 'last_login', 'date_joined', 'display_groups')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('email', 'username', 'phone_number')
    readonly_fields = ('last_login', 'date_joined', 'total_amount_spent')

    # Define how fields are grouped in the detail view for admins
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username', 'phone_number', 'total_amount_spent')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'groups')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields for adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'phone_number', 'password1', 'password2', 'is_active', 'is_staff', 'groups')}
        ),
    )

    ordering = ('email',)

    # Hide permissions tab and show "User Role: Customer/Store Owner"
    def get_fieldsets(self, request, obj=None):
        if not request.user.is_superuser:
            # Custom fieldset for Store Owners and Customers
            return (
                (None, {'fields': ('email', 'username', 'phone_number')}),
                ('User Role', {'fields': ('user_role',)}),  # Use the user_role method to show the role
                ('Important Dates', {'fields': ('last_login', 'date_joined')}),
            )
        return super().get_fieldsets(request, obj)

    # Ensure only the logged-in user can modify their account (except for superusers)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(pk=request.user.pk)  # Store Owners and Customers only see their own account
        return qs  # Admins can see all users
    
    # Use get_readonly_fields to make the 'user_role' read-only
    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ('last_login', 'date_joined', 'total_amount_spent', 'user_role')
        return super().get_readonly_fields(request, obj)

    # This method provides the custom user role as a read-only property
    def user_role(self, obj):
        if obj.groups.filter(name='Store Owner').exists():
            return "Store Owner"
        elif obj.groups.filter(name='Customer').exists():
            return "Customer"
        return "User"
    
    user_role.short_description = 'User Role'  # Display label for the field

     # Custom page heading based on user role
    def changelist_view(self, request, extra_context=None):
        if request.user.groups.filter(name='Store Owner').exists() or request.user.groups.filter(name='Customer').exists():
            extra_context = extra_context or {}
            extra_context['title'] = 'Your Account'
        else:
            extra_context = extra_context or {}
            extra_context['title'] = 'All Users'
        return super().changelist_view(request, extra_context=extra_context)

    # Change the heading in the edit form (change view)
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if request.user.groups.filter(name='Store Owner').exists()  or request.user.groups.filter(name='Customer').exists():
            extra_context['title'] = 'Edit Account Details'
        else:
            extra_context['title'] = 'Edit Account Details'
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
    
    # Override the changelist view to redirect Store Owners and Customers to their own profile page
    def changelist_view(self, request, extra_context=None):
        # If the user is a Store Owner or Customer, redirect to their own account detail page
        if request.user.groups.filter(name__in=['Store Owner', 'Customer']).exists():
            user_change_url = reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change', args=[request.user.pk])
            return HttpResponseRedirect(user_change_url)

        # For superusers, show the normal changelist view
        return super().changelist_view(request, extra_context)
    # Helper method to display groups in the list display
    def display_groups(self, obj):
        return ', '.join([group.name for group in obj.groups.all()])
    display_groups.short_description = 'Groups'

    # Allow non-superusers to edit only their own account
    def has_change_permission(self, request, obj=None):
        if obj is None or request.user.is_superuser:
            return True
        return obj == request.user

    # Prevent non-superusers from deleting accounts
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser




class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'description', 'discount_percentage', 'max_discount_amount', 'valid_from', 'valid_until', 'is_active')
    search_fields = ('code', 'description')
    list_filter = ('is_active', 'valid_from', 'valid_until')
    filter_horizontal = ('specific_products', 'exclude_products', 'specific_categories', 'exclude_categories')
    
    # Customize fields displayed in the detail view
    fieldsets = (
        (None, {
            'fields': ('code', 'description', 'discount_percentage', 'max_discount_amount', 'valid_from', 'valid_until', 'is_active')
        }),
        ('Usage Restrictions', {
            'fields': ('minimum_spend', 'individual_use', 'exclude_sale_items', 'specific_products', 'exclude_products', 'specific_categories', 'exclude_categories')
        }),
        ('Usage Limits', {
            'fields': ('usage_limit_per_coupon', 'usage_limit_per_user')
        }),
    )
    
    ordering = ('-valid_from',)
    # Override get_model_perms to hide this model from Store Owners
    def get_model_perms(self, request):
        # If the user is a store owner, don't show this model in the navigation
        if request.user.groups.filter(name='Store Owner').exists() or request.user.groups.filter(name='Customer').exists():
            return {}  # Empty perms hide the model
        return super().get_model_perms(request)


# Custom StoreAdmin to manage the Store model in the admin interface
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner_name', 'owner_contact', 'commission_rate', 'is_featured', 'display_brands', 'display_categories')  # Display these fields in the list view
    search_fields = ('name', 'owner_name', 'owner_contact', 'contact_person_name')  # Allow search by store name and owner name
    list_filter = ('is_featured', 'categories', 'brands')

    # Group fields into sections for better organization
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'display_image', 'inventory_software', 'commission_rate', 'is_featured')
        }),
        ('Assigned Brands and Categories', {
            'fields': ('display_brands', 'display_categories')  # Read-only display of brands and categories
        }),
        ('Address Information', {
            'fields': ('street_address', 'city', 'state', 'pin_code', 'country')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Contact Information', {
            'fields': ('owner_name', 'owner_contact', 'contact_person_name', 'contact_person_number')
        }),
    )
    filter_horizontal = ()
    readonly_fields = ('slug', 'display_brands', 'display_categories')  # Brands and Categories are read-only
    
    # Display brands in a comma-separated format
    def display_brands(self, obj):
        return ", ".join([brand.name for brand in obj.brands.all()])
    display_brands.short_description = 'Brands'

    # Display categories in a comma-separated format
    def display_categories(self, obj):
        return ", ".join([category.name for category in obj.categories.all()])
    display_categories.short_description = 'Categories'

    def get_model_perms(self, request):
        # If the user is a store owner, don't show this model in the navigation
        if request.user.groups.filter(name='Customer').exists():
            return {}  # Empty perms hide the model
        return super().get_model_perms(request)
    # Display only stores linked to the store owner or all stores for admins
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.groups.filter(name='Store Owner').exists():
            return qs.filter(owner_name=request.user)  # Only show stores owned by the logged-in store owner
        return qs  # Admins can see all stores

    # Make all fields read-only for store owners
    def get_readonly_fields(self, request, obj=None):
        if request.user.groups.filter(name='Store Owner').exists():
            return [field.name for field in self.model._meta.fields] + ['display_brands', 'display_categories']  # Make all fields and brands/categories read-only for store owners
        return self.readonly_fields

     # Custom page heading based on user role
    def changelist_view(self, request, extra_context=None):
        if request.user.groups.filter(name='Store Owner').exists():
            extra_context = extra_context or {}
            extra_context['title'] = 'Your Stores'
        else:
            extra_context = extra_context or {}
            extra_context['title'] = 'All Stores'
        return super().changelist_view(request, extra_context=extra_context)

    # Change the heading in the edit form (change view)
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if request.user.groups.filter(name='Store Owner').exists():
            extra_context['title'] = 'Your Store Details'
        else:
            extra_context['title'] = 'Edit Store Details'
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    # Prevent store owners from adding new stores
    def has_add_permission(self, request):
        if request.user.groups.filter(name='Admin').exists():
            return True  
        return False  

    # Prevent store owners from deleting stores
    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Admin').exists():
            return True  
        return False  
    
    # Allow store owners to view only their linked stores
    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Store Owner').exists() or request.user.groups.filter(name='Customer').exists():
            if obj and obj.owner_name != request.user:
                return False  # Store owners can only view stores they own
        return True  # Admins can change any store

# Inline admin for AttributeValue, allowing them to be edited within the Attribute admin view
class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1  # Number of empty fields to display for adding new values
    fields = ('value',)
    verbose_name = 'Attribute Value'
    verbose_name_plural = 'Attribute Values'

# Admin view for Attribute
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description','display_values')  # Display these fields in the list view
    search_fields = ('name',)  # Allow search by attribute name
    inlines = [AttributeValueInline]  # Include AttributeValue as inline form for the Attribute model

    def display_values(self, obj):
        return ", ".join([value.value for value in obj.values.all()])
    
    display_values.short_description = 'Values'

    # Override get_model_perms to hide this model from Store Owners
    def get_model_perms(self, request):
        # If the user is a store owner, don't show this model in the navigation
        if request.user.groups.filter(name='Store Owner').exists() or request.user.groups.filter(name='Customer').exists():
            return {}  # Empty perms hide the model
        return super().get_model_perms(request)


# Custom admin view for Category
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at', 'updated_at')  # Display name, logo, parent, and timestamps
    search_fields = ('name',)  # Allow search by category name
    list_filter = ('parent',)  # Allow filtering by parent category
    readonly_fields = ('created_at', 'updated_at')  # Make timestamps read-only
    fields = ('name', 'description', 'parent', 'created_at', 'updated_at')  # Show fields in form

    # Override get_model_perms to hide this model from Store Owners
    def get_model_perms(self, request):
        # If the user is a store owner, don't show this model in the navigation
        if request.user.groups.filter(name='Store Owner').exists() or request.user.groups.filter(name='Customer').exists():
            return {}  # Empty perms hide the model
        return super().get_model_perms(request)

# Custom admin view for Brand
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_logo', 'created_at', 'updated_at')  # Display name, logo, and timestamps
    search_fields = ('name',)  # Allow search by brand name
    readonly_fields = ('created_at', 'updated_at')  # Make timestamps read-only
    fields = ('name', 'logo', 'description', 'created_at', 'updated_at')  # Show fields in form
    
    # Override get_model_perms to hide this model from Store Owners
    def get_model_perms(self, request):
        # If the user is a store owner, don't show this model in the navigation
        if request.user.groups.filter(name='Store Owner').exists():
            return {}  # Empty perms hide the model
        return super().get_model_perms(request)
    # Method to display the logo image in the admin list view
    def display_logo(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.logo.url)
        return "No Logo"
    
    display_logo.short_description = 'Logo'  # Set column header name for the logo

# class InventoryInline(admin.TabularInline):
#     model = Inventory
#     extra = 1  # Number of empty fields to display for adding new inventory
#     fields = ('store', 'quantity', 'last_updated')  # Display these fields in the form
#     readonly_fields = ('last_updated',)

# Inline admin for managing the product gallery (ProductImage) directly from the Product admin
# Inline admin for ProductImage
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image',)

    def save_new_instance(self, form, commit=True):
        instance = form.save(commit=False)
        if self.instance:
            instance.product = self.instance
        if commit:
            instance.save()
        return instance

# Admin view for Product
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'store', 'mrp', 'sale_price', 'display_image', 'created_at')
    search_fields = ('name', 'category__name', 'brand__name', 'store__name')
    list_filter = ('category', 'brand', 'store')
    readonly_fields = ('slug', 'display_image', 'display_gallery', 'created_at')
    fields = ('name', 'slug', 'inventory', 'description', 'mrp', 'sale_price', 'category', 'brand', 'store', 'image', 'display_image', 'display_gallery', 'attributes', 'created_at')
    inlines = [ProductImageInline]
    filter_horizontal = ('attributes',)

    # Restrict queryset to only show products for the store owner
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.groups.filter(name='Store Owner').exists():
            return qs.filter(store__owner_name=request.user)
        return qs

    # Restrict form so store owners can only add/edit products for their own store
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if request.user.groups.filter(name='Store Owner').exists():
            owned_stores = Store.objects.filter(owner_name=request.user)

            # Filter categories and brands associated with the store owner
            form.base_fields['category'].queryset = Category.objects.filter(stores__in=owned_stores).distinct()
            form.base_fields['brand'].queryset = Brand.objects.filter(stores__in=owned_stores).distinct()

            # Also filter the store field to only show the stores owned by the store owner
            form.base_fields['store'].queryset = owned_stores
            
        return form

    # Hide the store field from the store owner (auto-assign their store)
    # def get_readonly_fields(self, request, obj=None):
    #     readonly_fields = list(super().get_readonly_fields(request, obj))
    #     if request.user.groups.filter(name='Store Owner').exists():
    #         readonly_fields.append('store')  # Store owner can't change this field
    #     return readonly_fields

    # Automatically set the store when a product is being created by a store owner
    def save_model(self, request, obj, form, change):
        if request.user.groups.filter(name='Store Owner').exists() and not change:
            obj.store = Store.objects.get(owner_name=request.user)  # Automatically assign store
        obj.save()

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    
    display_image.short_description = "Main Image"

    def display_gallery(self, obj):
        gallery_images = obj.gallery.all()
        if gallery_images:
            images_html = ''.join([format_html('<img src="{}" width="50" height="50" style="margin: 2px; object-fit: cover;" />', image.image.url) for image in gallery_images])
            return mark_safe(images_html)
        return "No Gallery Images"
    
    display_gallery.short_description = "Product Gallery"

# Inline admin for managing OrderItems
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

    # Filter the products shown in OrderItem based on the store
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product" and request.user.groups.filter(name='Store Owner').exists():
            # Limit the products to those that belong to the store owned by the logged-in store owner
            kwargs["queryset"] = Product.objects.filter(store__owner_name=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# Inline admin for managing Payments
class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'store', 'total_amount', 'order_status', 'payment_status', 'placed_at', 'updated_at')
    search_fields = ('user__email', 'id')
    list_filter = ('order_status', 'payment_status', 'placed_at')
    readonly_fields = ('placed_at', 'updated_at', 'tracking_id', 'delivery_status')

    # Group fields into sections for better organization
    fieldsets = (
        (None, {
            'fields': ('user', 'store', 'total_amount', 'payment_status', 'order_status')
        }),
        ('Address Information', {
            'fields': ('street_address', 'city', 'state', 'pin_code', 'country')
        }),
        ('Tracking Information', {
            'fields': ('tracking_id', 'delivery_status')
        }),
        ('Timestamps', {
            'fields': ('placed_at', 'updated_at')
        }),
    )

    inlines = [OrderItemInline, PaymentInline]

    # Restrict the orders a store owner or customer can see
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # For Store Owners, show orders related to their store
        if request.user.groups.filter(name='Store Owner').exists():
            return qs.filter(store__owner_name=request.user)
        # For Customers, show only their own orders
        elif request.user.groups.filter(name='Customer').exists():
            return qs.filter(user=request.user)
        return qs

    # Automatically assign the store to the order when a store owner creates it
    def save_model(self, request, obj, form, change):
        if request.user.groups.filter(name='Store Owner').exists() and not change:
            obj.store = Store.objects.get(owner_name=request.user)
        obj.save()

    # Restrict the store selection in the order form for store owners
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if request.user.groups.filter(name='Store Owner').exists():
            form.base_fields['store'].queryset = Store.objects.filter(owner_name=request.user)
        return form

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment_method', 'amount', 'status', 'transaction_id', 'payment_date')
    search_fields = ('transaction_id', 'order__id')
    list_filter = ('payment_method', 'status', 'payment_date')
    readonly_fields = ('payment_date',)
    fieldsets = (
        (None, {
            'fields': ('order', 'payment_method', 'amount', 'status', 'transaction_id')
        }),
        ('Timestamps', {
            'fields': ('payment_date',)
        }),
    )

    # Restrict Payment data to the store owner's or customer's related orders
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # For Store Owners, show payments related to their store orders
        if request.user.groups.filter(name='Store Owner').exists():
            owned_stores = Store.objects.filter(owner_name=request.user)
            return qs.filter(order__store__in=owned_stores)
        # For Customers, show only their own payments
        elif request.user.groups.filter(name='Customer').exists():
            return qs.filter(order__user=request.user)
        return qs

    # Restrict orders to the customer's orders in the payment form
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if request.user.groups.filter(name='Store Owner').exists():
            form.base_fields['order'].queryset = Order.objects.filter(store__owner_name=request.user)
        elif request.user.groups.filter(name='Customer').exists():
            form.base_fields['order'].queryset = Order.objects.filter(user=request.user)
        return form


# Inventory Admin
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'store', 'quantity', 'last_updated')
    search_fields = ('product__name', 'store__name')
    list_filter = ('store', 'product')
    readonly_fields = ('last_updated',)
    fieldsets = (
        (None, {
            'fields': ('product', 'store', 'quantity')
        }),
        ('Timestamps', {
            'fields': ('last_updated',)
        }),
    )

    # Restrict Inventory data to store owner's related products
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.groups.filter(name='Store Owner').exists():
            owned_stores = Store.objects.filter(owner_name=request.user)
            return qs.filter(store__in=owned_stores)
        return qs
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if request.user.groups.filter(name='Store Owner').exists():
            form.base_fields['store'].queryset = Store.objects.filter(owner_name=request.user)
            form.base_fields['product'].queryset = Product.objects.filter(store__owner_name=request.user)

        return form

class WishlistAdmin(admin.ModelAdmin):
    list_display = ('product', 'added_at')  # Fields to display in the admin list
    search_fields = ('user__username', 'product__name')  # Enable searching by user or product name
    list_filter = ('added_at',)  # Allow filtering by the date when products were added
    readonly_fields = ('added_at',)  # Make 'added_at' field read-only

    # Modify the form to hide the 'user' field for customers
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Hide the 'user' field for customers
        if request.user.groups.filter(name='Customer').exists():
            form.base_fields.pop('user', None)  # Remove the 'user' field from the form
        return form

    # Automatically assign the logged-in customer as the 'user' when creating a wishlist
    def save_model(self, request, obj, form, change):
        if request.user.groups.filter(name='Customer').exists() and not change:
            obj.user = request.user  # Automatically assign the logged-in user
        obj.save()

    # Restrict the wishlist view for customers so they can only see their own wishlist
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.groups.filter(name='Customer').exists():
            return qs.filter(user=request.user)
        return qs

    # Prevent customers from modifying other wishlists
    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Customer').exists() and obj and obj.user != request.user:
            return False  # Deny permission to change others' wishlists
        return super().has_change_permission(request, obj)

    # Prevent customers from deleting other users' wishlists
    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Customer').exists() and obj and obj.user != request.user:
            return False  # Deny permission to delete others' wishlists
        return super().has_delete_permission(request, obj)


class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('order_item', 'reason', 'status', 'created_at', 'updated_at')
    search_fields = ('order_item__product__name', 'status')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'updated_at')

    # Only show return requests related to the logged-in customer or all for admin
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.groups.filter(name='Customer').exists():
            return qs.filter(order_item__order__user=request.user)  # Customers see only their requests
        elif request.user.groups.filter(name='Store Owner').exists():
            # Filter requests based on products owned by the store owner
            return qs.filter(order_item__product__store__owner_name=request.user)
        return qs

    # Restrict customers from changing the status field (admin manages this)
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if request.user.groups.filter(name='Customer').exists():
            form.base_fields.pop('status', None)  # Hide status for customers
        return form

    # Admin updates the status
    def save_model(self, request, obj, form, change):
        if request.user.groups.filter(name='Customer').exists():
            obj.status = 'pending'  # Ensure customers cannot set status
        obj.save()

    # Prevent customers from deleting return requests
    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Customer').exists():
            return False  # Customers can't delete return requests
        return super().has_delete_permission(request, obj)
    
# Custom form for users to update their profile
# class MyAccountForm(forms.ModelForm):
#     class Meta:
#         model = User
#         fields = ['first_name', 'last_name', 'email', 'phone_number']  # Adjust fields as needed
#         widgets = {
#             'email': forms.EmailInput(attrs={'readonly': 'readonly'})  # Make email readonly if necessary
#         }

# # Custom AdminSite class to add the "My Account" view
# class MyAdminSite(admin.AdminSite):

#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path('myaccount/', self.admin_view(self.my_account_view), name='myaccount'),
#         ]
#         return custom_urls + urls

#     # View for the "My Account" page
#     def my_account_view(self, request):
#         user = request.user
#         if request.method == 'POST':
#             form = MyAccountForm(request.POST, instance=user)
#             if form.is_valid():
#                 form.save()
#                 messages.success(request, 'Your profile has been updated.')
#                 return redirect('admin:myaccount')
#         else:
#             form = MyAccountForm(instance=user)

#         context = dict(
#             self.each_context(request),
#             title="My Account",
#             form=form,
#         )
#         return render(request, 'admin/my_account.html', context)

# # Create an instance of the custom admin site
# admin_site = MyAdminSite()
# Unregister the default User admin and register the custom MyAccountAdmin
# admin.site.unregister(User)
# admin.site.register(MyAccountAdmin)

# Register ReturnRequestAdmin
admin.site.register(ReturnRequest, ReturnRequestAdmin)
# Register WishlistAdmin
admin.site.register(Wishlist, WishlistAdmin)

# Register both models in the admin
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Inventory, InventoryAdmin)






class EcommerceAdminSite(admin.AdminSite):
    site_header = "E-commerce Dashboard"
    site_title = "E-commerce Admin"

    def get_urls(self):
        # Get the default admin URLs
        urls = super().get_urls()
        # Add our custom report view to the URLs
        custom_urls = [
            path('reports/', self.admin_view(self.reports_view), name='ecommerce_reports'),
        ]
        return custom_urls + urls

    # Define the reports view
    def reports_view(self, request):
        # Total sales
        total_sales = Order.objects.filter(payment_status='Completed').aggregate(total_amount=Sum('total_amount'))['total_amount'] or 0

        # Sales per store
        sales_per_store = Order.objects.filter(payment_status='Completed').values('store__name').annotate(store_sales=Sum('total_amount'))

        # Most popular products
        popular_products = OrderItem.objects.values('product__name').annotate(total_sold=Sum('quantity')).order_by('-total_sold')[:5]

        # Pass the data to the template
        context = {
            'total_sales': total_sales,
            'sales_per_store': sales_per_store,
            'popular_products': popular_products,
        }
        return render(request, 'admin/ecommerce_reports.html', context)

# Register the custom admin site
ecommerce_admin_site = EcommerceAdminSite(name='ecommerce_admin')

class ReportsLinkAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        # This prevents the model from showing in the changelist
        return False

    # We add a custom change list link to the reports
    def changelist_view(self, request, extra_context=None):
        return self.admin_site.reports_view(request)

# Register the Reports link so it appears in the Application section of the admin
# admin.site.register(Store, ReportsLinkAdmin)
# admin.site.register(EcommerceAdminSite)
# Register the Order model in the admin
admin.site.register(Order, OrderAdmin)

# Register both models in the admin
admin.site.register(Product, ProductAdmin)
# admin.site.register(ProductImage)
# Register both models
admin.site.register(Category, CategoryAdmin)
admin.site.register(Brand, BrandAdmin)
# Register both models
admin.site.register(Attribute, AttributeAdmin)
# admin.site.register(AttributeValue)
admin.site.register(Store, StoreAdmin)


# Register the admin with the custom CouponAdmin
admin.site.register(Coupon, CouponAdmin)


# Register the modified UserAdmin
admin.site.register(User, CustomUserAdmin)
# Define a custom UserAdmin for displaying customer-centric information


# admin.site.register(Product, ProductAdmin)


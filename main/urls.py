from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('account/', views.account, name='account'),
    path('account/edit/', views.account_edit, name='account_edit'),
    path('account/change_password/', views.account_change_password, name='account_change_password'),
    path('account/order_history/', views.account_order_history, name='account_order_history'),
    path('account/order/<int:order_id>/', views.account_order_detail, name='order_detail'),
    path('account/affiliate/add/', views.affiliate_dashboard, name='account_affiliate_add'),

    path('save-profile-info/', views.save_profile_info, name='save_profile_info'),
    path('save-contact-info/', views.save_contact_info, name='save_contact_info'),
    path('account/change_password_api/', views.change_password_api, name='change_password_api'),

    # Category Detail
    path('category/<slug:slug>', views.category_detail, name='category_detail'),
    path('product/', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    path('yookassa-webhook/', views.yookassa_webhook, name='yookassa_webhook'),
    
    path('create-robokassa-payment/', views.create_robokassa_payment, name='create_robokassa_payment'),
    path('robokassa/result/', views.robokassa_result, name='robokassa_result'),
    path('robokassa/success/', views.robokassa_success, name='robokassa_success'),
    path('robokassa/fail/', views.robokassa_fail, name='robokassa_fail'),
    


    # Cart button
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),  # ← страница корзины
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('verify-order-code/', views.verify_order_code, name='verify_order_code'),
    path('checkout/', views.checkout, name='checkout'),
    path('create-payment/', views.create_payment, name='create_payment'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    
    
    
    

    



 
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('', include('django.contrib.auth.urls')),

    # Переопределяем сброс пароля
    path(
        'accounts/password_reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',  # ← твой файл!
        ),
        name='password_reset'
    ),

    path(
        'accounts/password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html',
        ),
        name='password_reset_done'
    ),

    path(
        'accounts/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
        ),
        name='password_reset_confirm'
    ),

    path(
        'accounts/reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html',
        ),
        name='password_reset_complete'
    ),


    # path('order-success/', views.order_success, name='order_success'),  # потом добавишь
]
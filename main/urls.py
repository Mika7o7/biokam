from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('account/', views.account, name='account'),
    path('account/edit/', views.account_edit, name='account_edit'),
    path('account/change_password/', views.account_change_password, name='account_change_password'),
    path('account/change_address/', views.account_change_address, name='account_change_address'),
    path('account/change_bookmarks/', views.account_change_bookmarks, name='account_change_bookmarks'),
    path('account/order_history/', views.account_order_history, name='account_order_history'),
    path('account/bonus_points/', views.account_bonus_points, name='account_bonus_points'),
    path('account/return/', views.account_return, name='account_return'),
    path('account/transaction/', views.account_transaction, name='account_transaction'),
    path('account/recurring/', views.account_recurring, name='account_recurring'),
    path('account/affiliate/add/', views.account_affiliate_add, name='account_affiliate_add'),
    path('account/newsletter/', views.account_newsletter, name='account_newsletter'),

    # Category Detail
    path('category/<slug:slug>', views.category_detail, name='category_detail'),
    path('product/', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('quick-view/<int:pk>/', views.quick_view, name='quick_view'),
    


    # Cart button
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),  # ← страница корзины
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    
    
    
    

    



 
    
    path('register/', views.RegisterView.as_view(), name='register'),
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
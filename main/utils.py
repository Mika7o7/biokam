from .models import Cart



def get_cart(request):
    """Получает или создает корзину для текущего пользователя/сессии"""
    
    print("\n=== get_cart ===")
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"Session key before: {request.session.session_key}")
    
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        print(f"Auth user cart: {cart.id}, created: {created}")
        return cart

    # Для гостей - по session_key
    session_key = request.session.session_key
    if not session_key:
        print("No session key, creating...")
        request.session.create()
        session_key = request.session.session_key
        print(f"New session key: {session_key}")
    
    cart, created = Cart.objects.get_or_create(
        session_key=session_key,
        user=None
    )
    print(f"Guest cart: {cart.id}, created: {created}")
    print(f"Cart session_key: {cart.session_key}")
    
    # Добавим проверку товаров в корзине
    items_count = cart.items.count()
    print(f"Items in cart: {items_count}")
    if items_count > 0:
        for item in cart.items.all():
            print(f"  - Item ID: {item.id}, Product: {item.product.name}, Quantity: {item.quantity}")
    
    print("=== end get_cart ===\n")
    
    return cart

from django.urls import path
from .views import Index , store
from .views import Signup
from .views import Login , logout
from .views import Cart
from .views import CheckOut
from .views import OrderView
from .views import paymenthandler
from .middlewares.auth import  auth_middleware



urlpatterns = [
    path('', Index.as_view(), name='homepage'),
    path('store', store , name='store'),
    path('signup', Signup.as_view(), name='signup'),
    path('login', Login.as_view(), name='login'),
    path('logout', logout , name='logout'),
    path('cart', auth_middleware(Cart.as_view()) , name='cart'),
    path('check-out', CheckOut.as_view() , name='checkout'),
    path('orders', auth_middleware(OrderView.as_view()), name='orders'),
    path('paymenthandler/', paymenthandler, name='paymenthandler'),
]

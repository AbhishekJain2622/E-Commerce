
from django.shortcuts import render , redirect
from django.http import (HttpResponseBadRequest,HttpResponseRedirect )

from django.contrib.auth.hashers import  check_password
from .models import Customer
from django.views import  View
from .models import  Product
from .models import Customer
from .models import Product
from .models import Order
from .models import Category
from Internal.middlewares.auth import auth_middleware
from django.contrib.auth.hashers import make_password
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
# Create your views here.
############################################################################################
class Cart(View):
    def get(self , request):
        ids = list(request.session.get('cart').keys())
        products = Product.get_products_by_id(ids)
        print(products)
        return render(request , 'cart.html' , {'products' : products} )

############################################################################################
class CheckOut(View):
    def post(self, request):
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        customer_id = request.session.get('customer')
        cart = request.session.get('cart')
        products = Product.get_products_by_id(list(cart.keys()))

        total_amount = 0
        for product in products:
            total_amount += product.price * cart.get(str(product.id))

        # Razorpay order creation
        amount_in_paisa = total_amount * 100
        razorpay_order = razorpay_client.order.create(dict(amount=amount_in_paisa, currency='INR', payment_capture='1'))
        razorpay_order_id = razorpay_order['id']

        context = {
            'address': address,
            'phone': phone,
            'customer': customer_id,
            'cart': cart,
            'products': products,
            'total_amount': total_amount,
            'amount_in_paisa': amount_in_paisa,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_merchant_key': settings.RAZORPAY_API_KEY,
            'callback_url': '/paymenthandler/'
        }

        return render(request, 'payment.html', context)
############################################################################################
@csrf_exempt
def paymenthandler(request):
    if request.method == 'POST':
        try:
            # Get the payment details from Razorpay
            payment_id = request.POST.get('razorpay_payment_id')
            order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')

            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            # Verify the payment signature
            result = razorpay_client.utility.verify_payment_signature(params_dict)
            if result is None:
                amount = request.POST.get('amount')
                razorpay_client.payment.capture(payment_id, amount)

                # Save order details in the database
                address = request.POST.get('address')
                phone = request.POST.get('phone')
                customer_id = request.session.get('customer')
                cart = request.session.get('cart')
                products = Product.get_products_by_id(list(cart.keys()))

                for product in products:
                    order = Order(customer=Customer(id=customer_id),
                                  product=product,
                                  price=product.price,
                                  address=address,
                                  phone=phone,
                                  quantity=cart.get(str(product.id)))
                    order.save()
                
                request.session['cart'] = {}

                return render(request, 'success.html')
            else:
                return render(request, 'failure.html')
        except:
            return render(request, 'failure.html')
    else:
        return HttpResponseBadRequest()
############################################################################################
class Index(View):
    def post(self , request):
        product = request.POST.get('product')
        remove = request.POST.get('remove')
        cart = request.session.get('cart')
        if cart:
            quantity = cart.get(product)
            if quantity:
                if remove:
                    if quantity<=1:
                        cart.pop(product)
                    else:
                        cart[product]  = quantity-1
                else:
                    cart[product]  = quantity+1

            else:
                cart[product] = 1
        else:
            cart = {}
            cart[product] = 1

        request.session['cart'] = cart
        print('cart' , request.session['cart'])
        return redirect('homepage')



    def get(self , request):
        # print()
        return HttpResponseRedirect(f'/store{request.get_full_path()[1:]}')
############################################################################################
def store(request):
    cart = request.session.get('cart')
    if not cart:
        request.session['cart'] = {}
    products = None
    categories = Category.get_all_categories()
    categoryID = request.GET.get('category')
    if categoryID:
        products = Product.get_all_products_by_categoryid(categoryID)
    else:
        products = Product.get_all_products();

    data = {}
    data['products'] = products
    data['categories'] = categories

    print('you are : ', request.session.get('email'))
    return render(request, 'base.html', data)
############################################################################################
class Login(View):
    return_url = None
    def get(self , request):
        Login.return_url = request.GET.get('return_url')
        return render(request , 'login.html')

    def post(self , request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        customer = Customer.get_customer_by_email(email)
        error_message = None
        if customer:
            flag = check_password(password, customer.password)
            if flag:
                request.session['customer'] = customer.id

                if Login.return_url:
                    return HttpResponseRedirect(Login.return_url)
                else:
                    Login.return_url = None
                    return redirect('homepage')
            else:
                error_message = 'Email or Password invalid !!'
        else:
            error_message = 'Email or Password invalid !!'

        print(email, password)
        return render(request, 'login.html', {'error': error_message})
############################################################################################
def logout(request):
    request.session.clear()
    return redirect('login')
############################################################################################
class OrderView(View):


    def get(self , request ):
        customer = request.session.get('customer')
        orders = Order.get_orders_by_customer(customer)
        print(orders)
        return render(request , 'orders.html'  , {'orders' : orders})
############################################################################################
class Signup(View):
    def get(self, request):
        return render(request, 'signup.html')

    def post(self, request):
        postData = request.POST
        first_name = postData.get('firstname')
        last_name = postData.get('lastname')
        phone = postData.get('phone')
        email = postData.get('email')
        password = postData.get('password')
        # validation
        value = {
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone,
            'email': email
        }
        error_message = None

        customer = Customer(first_name=first_name,
                            last_name=last_name,
                            phone=phone,
                            email=email,
                            password=password)
        error_message = self.validateCustomer(customer)

        if not error_message:
            print(first_name, last_name, phone, email, password)
            customer.password = make_password(customer.password)
            customer.register()
            return redirect('homepage')
        else:
            data = {
                'error': error_message,
                'values': value
            }
            return render(request, 'signup.html', data)

    def validateCustomer(self, customer):
        error_message = None;
        if (not customer.first_name):
            error_message = "First Name Required !!"
        elif len(customer.first_name) < 4:
            error_message = 'First Name must be 4 char long or more'
        elif not customer.last_name:
            error_message = 'Last Name Required'
        elif len(customer.last_name) < 4:
            error_message = 'Last Name must be 4 char long or more'
        elif not customer.phone:
            error_message = 'Phone Number required'
        elif len(customer.phone) < 10:
            error_message = 'Phone Number must be 10 char Long'
        elif len(customer.password) < 6:
            error_message = 'Password must be 6 char long'
        elif len(customer.email) < 5:
            error_message = 'Email must be 5 char long'
        elif customer.isExists():
            error_message = 'Email Address Already Registered..'
        # saving

        return error_message




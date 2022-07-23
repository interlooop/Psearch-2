from django.shortcuts import render,redirect,get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.db.models import F

import json
import datetime
import re

from cart.cart import Cart
from .forms import ShippingAddressForm
from .models import *
from .utils import searchProducts,paginateProducts


def store(request):

    categories=Category.objects.all()

    searchValue=''

    products, search_query= searchProducts(request,searchValue)
    custom_range,products=paginateProducts(request,products,6)


    order = ['Books', 'Clothes', 'Software','Other']
    categories = sorted(categories, key=lambda x: order.index(x.name))

    context={'products':products,'search_query':search_query,'categories':categories,'custom_range':custom_range,}
       
    return render(request,'store/store.html',context)
    


def products(request, category_slug):
    category=None
    categories=Category.objects.all()
    
    searchValue=request.GET.get('searchValue')
    

    if category_slug:
        category = get_object_or_404(Category,slug=category_slug)
        
        products, search_query= searchProducts(request,searchValue,category)
        custom_range,products=paginateProducts(request,products,6)
    else:
        products, search_query= searchProducts(request,searchValue)
        custom_range,products=paginateProducts(request,products,6)


    order = ['Books', 'Clothes', 'Software','Other']
    categories = sorted(categories, key=lambda x: order.index(x.name))
    
    context={'products':products,'search_query':search_query,'category':category,'categories':categories,'custom_range':custom_range,}
        
    return render(request,'store/products.html',context)



@login_required(login_url="login-user")
@never_cache
def checkout(request):
        
        shippingAddressForm=ShippingAddressForm(request.POST)
          
        customer=request.user.customer
        if 'orderId' in request.session:
            orderId = request.session['orderId']
            order,created=Order.objects.get_or_create(id=orderId,customer=customer,complete=False)
        else:
            order,created=Order.objects.get_or_create(customer=customer,complete=False)

        total=order.get_cart_total
        cartItems=order.get_cart_items         
        shipping=order.shipping

        if cartItems == 0:
                return redirect('store')

        if shippingAddressForm.is_valid():

            address=shippingAddressForm.cleaned_data['address']
            city=shippingAddressForm.cleaned_data['city']
            state=shippingAddressForm.cleaned_data['state']
            zipcode=shippingAddressForm.cleaned_data['zipcode']

            addressTrimmed = re.sub("^\s+|\s+$", "", address, flags=re.UNICODE)

            cityTrimmed = re.sub("^\s+|\s+$", "", city, flags=re.UNICODE)
            cityNoExtraWhitespace = " ".join(re.split("\s+", cityTrimmed, flags=re.UNICODE))
            
            stateTrimmed = re.sub("^\s+|\s+$", "", state, flags=re.UNICODE)
            stateNoExtraWhiteSpace = " ".join(re.split("\s+", stateTrimmed, flags=re.UNICODE))

            zipcodeTrimmed = re.sub("^\s+|\s+$", "", zipcode, flags=re.UNICODE)
              
            context={'total':total,'address':addressTrimmed,'city':cityNoExtraWhitespace,
                    'state':stateNoExtraWhiteSpace,'zipcode':zipcodeTrimmed,'shipping':shipping}
                
                
            return render (request, 'store/checkout-payment.html',context)
                
        elif shipping == False and request.method == 'POST':
            context={'total':total,'shipping':shipping}
                
            return render (request, 'store/checkout-payment.html',context)
        else:
            items=order.orderitem_set.all()
            for orderItem in items:

                orderItemtQty=orderItem.quantity

                continueCheck = request.session.get('continue')

                if orderItemtQty > 10 or orderItemtQty <= 0 or continueCheck == False:
                    request.session['continue'] = True
                        
                    return redirect('cart:cart-summary')

            context={'shippingAddressForm':shippingAddressForm,'items':items,'order':order,'cartItems':cartItems,'total':total,'shipping':shipping}
                
            return render(request, 'store/checkout.html',context)
        


def singleProduct(request,product_slug):
    
    cart=Cart(request)
    product=Product.objects.get(slug=product_slug)
    
    cartProductQuantity=cart.get_product_quantity(product.id)
    if cartProductQuantity + product.availableQuantity > 10:
        maxQuantity=10
    else:
        maxQuantity=cartProductQuantity + product.availableQuantity
    context={'product':product,'maxQuantity':maxQuantity}
  
    return render(request, 'store/single-product.html',context)




from paypalcheckoutsdk.orders import OrdersGetRequest
from .paypal import PayPalClient

@login_required(login_url="login-user")
def paymentComplete(request):
    
    PPClient = PayPalClient()

    body=json.loads(request.body)
    orderID=body["orderID"]
    
    user_id=request.user.id

    requestOrder=OrdersGetRequest(orderID)
    response = PPClient.client.execute(requestOrder)

    transaction_id=datetime.datetime.now().timestamp()

    
    customer=request.user.customer
    if 'orderId' in request.session:
        orderId = request.session['orderId']
        order,created=Order.objects.get_or_create(id=orderId,customer=customer,complete=False)
    else:
        order,created=Order.objects.get_or_create(customer=customer,complete=False)
        
    items=order.orderitem_set.all()
        
    for item in items:
            
        product=Product.objects.get(name=item.product.name)
           
        try:
            product.qtyInStock = F('qtyInStock') - item.quantity
            product.reservedQuantity = F('reservedQuantity') - item.quantity
            product.save(update_fields=['qtyInStock','reservedQuantity'])
        except:
            print('Order item quantity can not be higher than the available quantity')
    

    order.transaction_id=transaction_id
    
    order.complete=True
    
    if order.shipping == True:
 
        shippingAddress,created=ShippingAddress.objects.get_or_create(
            customer=customer,
            address=body['shipping']['address'],
            city=body['shipping']['city'],
            state=body['shipping']['state'],
            zipcode=body['shipping']['zipcode'],
            
        )
        
        order.shipping_address=shippingAddress
        
    order.save()
    
    return JsonResponse("Payment completed!", safe=False)


@login_required(login_url="login-user")
def paymentSuccessful(request):
    if not request.user.is_authenticated:
        cart=Cart(request)
        cart.clear()
    else:
        pass
    
    return render(request,'store/payment-successful.html')




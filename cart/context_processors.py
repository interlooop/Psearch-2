from .cart import Cart
from store.models import *
from django.shortcuts import get_object_or_404

def cart(request):
    return {'cart': Cart(request)}

def orderItemsQty(request):

    if request.user.is_authenticated:
        customer,created=Customer.objects.get_or_create(
            user=request.user,
        )
        
        try:
            order=get_object_or_404(Order,customer=customer,complete=False)
            orderItemsQty=order.get_cart_items
            return {'orderItemsQty': orderItemsQty}
        except:
            return {'orderItemsQty': 0}
        

    else:
        return {'orderItemsQty': None}
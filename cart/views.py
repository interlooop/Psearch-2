from decimal import Decimal
from django.shortcuts import render,get_object_or_404,redirect
from django.http import JsonResponse
from .cart import Cart
from store.models import *
from django.core.exceptions import ValidationError
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.contrib import messages
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F


@method_decorator(cache_control(no_cache=True, must_revalidate=True, no_store=True), name='get')
class cart_summaryView(LoginRequiredMixin,View):
    
    def get(self, request):
       
        if request.session.get('continue') == None:
            request.session['continue'] = True
        
        cart=Cart(request)
        
        customer=request.user.customer
        order,created=Order.objects.get_or_create(customer=customer,complete=False)
        orderItems=OrderItem.objects.filter(order=order)
            
        context={'cart':cart,'order':order,'orderItems':orderItems}
        
        return render(request,'store/cart.html',context)


class cart_addView(LoginRequiredMixin,View):

    def post(self, request):

        data = {
                'msg': render_to_string('messages.html', {}),
                }
        
        productId=int(request.POST.get('productId'))
        
        try:
            product_qty=int(request.POST.get('productQty'))
        except ValueError:
            msg='Please specify correct ammount'
            messages.add_message(request, messages.ERROR, msg)
            return JsonResponse({'data':data})
            

        action= request.POST.get('action')

        user=request.user
        customer,created=Customer.objects.get_or_create(
                user=user,    
            )

            
        order,created=Order.objects.get_or_create(customer=customer,complete=False)

        request.session['orderId'] = order.id

        with transaction.atomic():

            product = Product.objects.select_for_update(nowait=True).get(id=productId)
            orderItem,created=OrderItem.objects.get_or_create(order=order,product=product)
            
            cartProductQuantity=orderItem.quantity

            if cartProductQuantity + product.availableQuantity > 10:
                maxQuantity=10
            else:
                maxQuantity=cartProductQuantity + product.availableQuantity


            try:
                if product_qty <= 10 and product_qty <= maxQuantity and product_qty > 0:
                        
                    if action == "add":
                        if created == True:
                            product.reservedQuantity+=product_qty
                            product.save(update_fields=['reservedQuantity'])
                        else:
                            product.reservedQuantity-=orderItem.quantity
                            product.reservedQuantity+=product_qty
                            product.save(update_fields=['reservedQuantity'])
                        orderItem.quantity=product_qty

                    orderItem.save(update_fields=['quantity'])
                    messages.add_message(request, messages.SUCCESS, "Item added to cart")
                else:
                    raise ValueError('Ordered amount is not available')
            except ValueError as ve:
                msg=str(ve)
                messages.add_message(request, messages.WARNING, msg)

                return JsonResponse({'data':data})


        cart_qty=order.get_cart_items
        return JsonResponse({'qty':cart_qty},safe=False)




class cart_deleteView(LoginRequiredMixin,View):
    def post(self,request):
        
        product_id=int(request.POST.get('productId'))
        
        if request.POST.get('action') == 'post':
            
            action2=request.POST.get('action2')

            customer=request.user.customer
                
            order,created=Order.objects.get_or_create(customer=customer,complete=False)
            
            with transaction.atomic():
                product = Product.objects.select_for_update(nowait=True).get(id=product_id)

                orderItem,created=OrderItem.objects.get_or_create(order=order,product=product)
                    
                if action2 == "remove":
                    product.reservedQuantity-=orderItem.quantity
                    product.save(update_fields=['reservedQuantity'])
                    orderItem.quantity=0
                    orderItem.save(update_fields=['quantity'])
                    orderItem.delete()

            cart_qty=order.get_cart_items
            cart_total_price=order.get_cart_total

            response =JsonResponse({'cart_qty':cart_qty,'cart_total_price':cart_total_price})
            return response




class cart_updateView(LoginRequiredMixin,View):
    def post(self,request):
        
        data = {
                'msg': render_to_string('messages.html', {}),
                }

        if request.POST.get('action') == 'post':
            
            product_id=int(request.POST.get('productId'))
            
            try:
                product_qty=int(request.POST.get('productQty'))
            except ValueError:
                msg='Please specify correct ammount'
                messages.add_message(request, messages.ERROR, msg)
                return JsonResponse({'data':data})

            product_qty_max=int(request.POST.get('productQtyMax'))
            product=get_object_or_404(Product, id=product_id)
            
            customer=request.user.customer
            
            order,created=Order.objects.get_or_create(customer=customer,complete=False)
            orderItem,created=OrderItem.objects.get_or_create(order=order,product=product)
                
            try:
                cartProductQty=orderItem.quantity

                if product_qty <= 10 and product_qty > 0 and product_qty <= product.availableQuantity + cartProductQty:

                    product.reservedQuantity = F('reservedQuantity') - orderItem.quantity
                    product.save(update_fields=['reservedQuantity'])
                    # product.refresh_from_db()
                    orderItem.quantity=0
                        
                    if product_qty == '' or product_qty <= 0 or product_qty > product_qty_max:
                        orderItem.quantity=0
                    else:
                        orderItem.quantity=(orderItem.quantity + product_qty)
                        
                    orderItem.save(update_fields=['quantity'])
                    
                    product.reservedQuantity = F('reservedQuantity') + orderItem.quantity
                    product.save(update_fields=['reservedQuantity'])
                    # product.refresh_from_db()
                else:
                        request.session['continue']=False
                        raise ValueError('Ordered quantity for ' + product.name + ' can not be higher than 10, higher than the remaining available quantity or lower than 1, please correct your order quantity if you want to proceed')
                
            except ValueError as ve:
                msg=str(ve)
                messages.add_message(request, messages.ERROR, msg)
                    
                return JsonResponse({'data':data})
                
            product_price=Decimal(product.price)
            product_total_price=product_qty * product_price
            cart_qty=order.get_cart_items
            cart_total_price=order.get_cart_total

            
            response=JsonResponse({'cart_qty':cart_qty,'cart_total_price':cart_total_price,'product_total_price':round(product_total_price,2)})
            return response





   


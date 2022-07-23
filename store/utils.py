from . models import *
from django.core.paginator import Paginator,PageNotAnInteger,EmptyPage
from django.db.models import Q


def paginateProducts(request, products,results):
    
    
    page=request.GET.get('page')
    
    
    paginator=Paginator(products, results)

    try:
       products=paginator.page(page)
    except PageNotAnInteger:
        page=1
        products=paginator.page(page)
    except EmptyPage:
        page=paginator.num_pages
        products=paginator.page(page)

    
    leftIndex=(int(page)-4)
    if leftIndex<1:
        leftIndex=1

    rightIndex=(int(page)+5)
    if rightIndex>paginator.num_pages:
        rightIndex=paginator.num_pages+1

    custom_range=range(leftIndex,rightIndex)

    return custom_range, products



def searchProducts(request,search_query,category=None):

    if search_query == None:
        search_query=''

    if category:

        products=Product.objects.distinct().filter(
        Q(name__icontains=search_query),
        category=category)
        
    else:
        
        products=Product.objects.distinct().filter(
            Q(name__icontains=search_query)
        )

    return products,search_query

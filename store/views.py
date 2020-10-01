from django.http import JsonResponse
from django.shortcuts import render
import json
import datetime

from django.views.decorators.csrf import csrf_exempt

from .utils import cookie_cart, cart_data, guest_order
from .models import *


def main_page(request):
    context = {}
    return render(request, 'store/main.html', context)


def cart(request):
    data = cookie_cart(request)
    items = data['items']
    order = data['order']
    cart_items = data['cart_items']

    context = {'items': items, 'order': order, 'cart_items':cart_items,}
    return render(request, 'store/cart.html', context)

@csrf_exempt
def checkout(request):
    data = cookie_cart(request)
    items = data['items']
    order = data['order']
    cart_items = data['cart_items']


    context = {'items': items, 'order': order, 'cart_items':cart_items }
    return render(request, 'store/checkout.html', context)


def store(request):
    data = cookie_cart(request)
    cart_items = data['cart_items']


    products = Product.objects.all()
    context = {'products': products, 'cart_items':cart_items }
    return render(request, 'store/store.html', context)


def update_item(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added..', safe=False)


def process_order(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)

    else:
        print('User is not logged in!')
        customer, order = guest_order(request=request, data=data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == float(order.get_cart_total):
        order.complete = True
    order.save()


    if order.shipping == True:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )



    return JsonResponse('Payment complete!', safe=False)
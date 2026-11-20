from apps.store.models import ProductVariant


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')

        if not cart:
            cart = self.session['cart'] = {}

        self.cart = cart


    def add(self, variant_id, quantity=1):
        variant_id = str(variant_id)

        variant = ProductVariant.objects.filter(id=variant_id).first()
        if not variant:
            return

        max_allowed = min(variant.stock, 5)

        if variant_id in self.cart:
            new_quantity = self.cart[variant_id] + quantity
        else:
            new_quantity = quantity

        self.cart[variant_id] = min(new_quantity, max_allowed)

        self.save()

    def remove(self, variant_id):
        variant_id = str(variant_id)

        if variant_id in self.cart:
            del self.cart[variant_id]
            self.save()

    def increase(self, variant_id):
        variant_id = str(variant_id)

        variant = ProductVariant.objects.filter(id=variant_id).first()
        if not variant:
            return

        if variant_id in self.cart:

            max_allowed = min(variant.stock, 5)

            if self.cart[variant_id] < max_allowed:
                self.cart[variant_id] += 1

            self.save()

    def decrease(self, variant_id):
        variant_id = str(variant_id)

        if variant_id in self.cart:
            if self.cart[variant_id] > 1:
                self.cart[variant_id] -= 1
            else:
                del self.cart[variant_id]

            self.save()

    def get_items(self):
        variant_ids = self.cart.keys()
        variants = ProductVariant.objects.filter(id__in=variant_ids)

        items = []

        for variant in variants:
            quantity = self.cart[str(variant.id)]

            items.append({
                'variant': variant,
                'product': variant.product,
                'size': variant.size,
                'quantity': quantity,
                'price': variant.product.get_final_price()* quantity,
                'mrp': variant.product.mrp,
                'total_price': variant.product.get_final_price() * quantity,

                'mrp_total': variant.product.mrp * quantity,
                'savings': (variant.product.mrp - variant.product.get_final_price()) * quantity
                
            })

        return items
    
    def get_total_price(self):
      total = 0
      items = self.get_items()

      for item in items:
        total += item['total_price']

      return total
    
    def get_total_mrp(self):
       total = 0
       items = self.get_items()

       for item in items:
          total += item['product'].mrp * item['quantity']

       return total

    def clear(self):
        self.session['cart'] = {}
        self.save()

    def save(self):
        self.session.modified = True
from flask import Flask, render_template, request, session, jsonify
from database.model import (
   get_db_connection,
   close_db_connection,
   select,
   fields
)

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Замените на свой ключ
app.config['SESSION_TYPE'] = 'filesystem'


@app.route('/')
def main_page():
    print(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
    product_array = select('select * from products limit 30')

    products = upd_dict(product_array)
    return render_template('main.html', products=products)


@app.route('/promotions/')
def promotions():
    return ''


@app.route('/profile/')
def profile():
    return ''


@app.route('/search/', methods=['GET'])
@app.route('/search', methods=['GET'])
def search():
    categories = select("select category from categories", one_argument=True)
    query = request.args.get('query', '')  # Получаем данные из строки запроса
    category = request.args.get('category', '')
    if query or category:
        # Здесь вы можете обработать запрос и найти нужные данные
        results = perform_search(query, category)
        return render_template('search.html', query=query, results=results, categories=categories)
    else:
        return render_template('search.html', categories=categories)


def perform_search(query, category):
   if category:
      category_num = select("select id from categories where category = ?", [category], True, True)
   if query:
      if category:
         res = select(
            "select * from products where tags like '%{}%' and product_category = ?".format(query.lower()), [category_num])
      else:
         res = select(
            "select * from products where tags like '%{}%'".format(query.lower()))
   else:
      res = select(
         "select * from products where product_category = ?".format(query.lower()), [category_num])
      
   results = upd_dict(res)
   return results


@app.route('/product/<string:slug>/')
def product(slug: str):
    slug = slug.split("-")[-1]
    product = select('select * from products where slug = ?', [slug], True)
    product = upd_dict([product])[0]
    cart = session.get('cart', [])
    el = next((x for x in cart if x["id"] == str(product["id"])), None)
    if el:
        quantity = el["quantity"]
    else:
        quantity = 0
    return render_template('product.html', product=product, quantity=quantity)


def upd_dict(product_array):
    if not product_array:
        return []
    keys = fields("products")
    categories = select('select * from categories')
    products = []
    for product in product_array:
        products.append(dict(zip(keys, product)))
        products[-1]["price"] /= products[-1]["price_modificator"]
        if products[-1]["previous_price"]:
            products[-1]["previous_price"] /= products[-1]["price_modificator"]
        products[-1]["category"] = next(x[1] for x in categories if x[0]
                                        == products[-1]["product_category"])
        products[-1]["images"] = products[-1]["photo_sources"].split()
        products[-1]["image"] = products[-1]["images"][0]
    return products


# Отображение корзины
@app.route('/cart')
def cart():
    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    summ = sum((item['previous_price'] * item['quantity']) if 
               item['previous_price'] else (item['price'] * item['quantity']) for item in cart)
    return render_template('cart.html', cart=cart, total=total, summ=summ)


@app.route("/update-cart", methods=["POST"])
def update_cart():
    cart = session.get('cart', [])
    action = request.json.get("action")
    product_id = request.json.get("product_id")
    adder = 1 if action == "add" else -1
    quantity = adder

    data = select("select * from products where id = ?", [product_id], True)
    product = upd_dict([data])[0]

    for item in cart:
        if str(item["id"]) == product_id:
            quantity += item["quantity"]
            if quantity <= 0:
                cart.remove(item)
                break
            if quantity > product["count"]:
                quantity = product["count"]
            item["quantity"] = quantity
            break

    if quantity == adder:
        product["quantity"] = quantity
        cart.append(product)
        
    session['cart'] = cart
    return jsonify({"quantity": quantity})


if __name__ == '__main__':
    get_db_connection()
    try:
        app.run()
    except Exception as e:
        print(e)
    finally:
        close_db_connection()

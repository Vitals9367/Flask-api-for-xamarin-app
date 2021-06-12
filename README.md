# Xamarin Eshop Mobile App API #
🛒 Ecommerce app made with Xamarin.Forms framework.<br/>
Made during third semester of my studies at Kaunas University of Applied Sciences.<br/>

Connected to same database as Flask eShop.<br/>
🔗 [Flask eShop](https://github.com/Vitals9367/Flask_eshop)<br/>
🔗 [Xamarin Mobile App](https://github.com/Vitals9367/Xamarin_eshop_app)

***Mobile App ->*** Xamarin XML templates, business logic<br/>
***Backend ->*** Flask API<br/>
***Database ->*** PostgresSQL<br/>
***Hosting ->*** Heroku<br/>
***Payments ->*** Stripe<br/>

🔌 [Example Endpoint](https://flaskeshopapi.herokuapp.com/api/products)<br/>

***Endpoints:***
- /image
- /api/user/defined_items
- /api/user/cart_items
- /api/user/add/cart_items/<int:item_id>
- /test
- /api/user/delete_cart_item
- /api/user/complete_order/<int:order_id>
- /api/user/orders
- /api/user/delete_order
- /api/delete_orders
- /api/user/create_order
- /api/products
- /api/product/addtocart
- /api/product/<int:item_id>
- /api/users/check/<string:uname>
- /api/user
- /api/user/<string:public_id>
- /api/users
- /api/user_info
- /api/user_info/update
- /api/reviews/product/<int:item_id>
- /api/create_review
- /login

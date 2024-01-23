from flask import Flask, render_template, request,jsonify
import sqlite3
import nltk
import random
import ast
import re
from nltk.tokenize import word_tokenize

app = Flask(__name__)


# @app.route('/')
# def dashboard():
#
#     return render_template('dashboard.html', data=scraped_data)

def execute_sql_query(query):
    connection = sqlite3.connect('detailsofphone.db')
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    connection.close()
    return result


def ask_question_to_dashboard(question, answer):
    search_term = question  # The user's search term
    connection = sqlite3.connect('detailsofphone.db')
    cursor = connection.cursor()

    #Product listing
    cursor.execute(
        "SELECT COUNT(*) AS row_count, AVG(`Product Price`) AS average_price FROM Product WHERE `Product Name` LIKE '%' || ? || '%' OR `Product Description` LIKE '%' || ? || '%'",(search_term, search_term))

    # Fetch and process the results
    results = cursor.fetchall()

    row_count = results[0][0] if results else 0
    average_price = results[0][1] if results else None
    average_price=int(average_price)

    #Product rating
    cursor.execute("""
        SELECT AVG(`Product rating`) AS average_rating
        FROM Product P
        JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
        WHERE P.`Product Name` LIKE '%' || ? || '%' OR P.`Product Description` LIKE '%' || ? || '%'
    """, (search_term, search_term))

    new_result = cursor.fetchall()
    average_rating = new_result[0][0] if new_result else None
    average_rating = round(average_rating, 1)

    #review per product
    cursor.execute("""
        SELECT R.`Product reviews`
        FROM Product P
        JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
        WHERE P.`Product Name` LIKE '%' || ? || '%' OR P.`Product Description` LIKE '%' || ? || '%'
    """, (search_term, search_term))

    # Fetch and process the results
    result = cursor.fetchall()

    count = 0
    for i in result:
        for j in i:
            try:
                list_data = ast.literal_eval(j)
                if isinstance(list_data, list):
                    for j in list_data:
                        count += 1

            except (ValueError, SyntaxError) as e:
                continue

    review_per_prod=count/row_count
    review_per_prod=round(review_per_prod, 1)
    question_asked =  random.randint(1, 3)

    #top 5 best product
    cursor.execute("""
        SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
        FROM Product P
        JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
        WHERE P.`Product Name` LIKE '%' || ? || '%' OR P.`Product Description` LIKE '%' || ? || '%'
        ORDER BY R.`Product Rating` DESC, R.`Review Score` DESC
        LIMIT 5
    """, (search_term, search_term))

    result = cursor.fetchall()
    listofdict = []

    for i in result:
        mydict = {}
        mydict["name"] = i[0]
        mydict["price"] = i[1]
        mydict["rating"] = i[2]
        mydict["score"] = i[3]
        mydict["link"] = i[4]
        listofdict.append(mydict)

    final_data = {
        "total_listings": row_count,
        "average_price": average_price,
        "average_ratings": average_rating,
        "average_review_count": review_per_prod,
        "total_questions": question_asked,
        "top_products": listofdict
    }

    print(f"Number of rows: {row_count}")
    print(f"Average product price: {average_price}")
    print(f"Average product rating: {average_rating}")
    print(f"Average review per product: {review_per_prod}")

    # Don't forget to close the cursor and connection
    cursor.close()
    connection.close()

    answer.append(final_data)
    return answer


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    dashboard_data = [] # To store the conversation history

    if request.method == 'POST':
        user_input = request.form['dashboard_input']
        ask_question_to_dashboard(user_input, dashboard_data)


    return render_template('second.html', response=dashboard_data)

def ask_question(question, conversation):
    pattern = r'(\d+)k'
    matches = re.findall(pattern, question, flags=re.IGNORECASE)

    # Convert each match to numeric value
    for match in matches:
        numeric_value = int(match) * 1000
        question = question.replace(match + 'k', str(numeric_value))

    #all smartphone between a range
    if "between" in question.lower() and "all" in question.lower() and "price" in question.lower():
        try:
            price_range = [int(x) for x in question.split() if x.isdigit()]

            query = f"""
                SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
                FROM Product P
                JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
                WHERE `Product Price` BETWEEN {price_range[0]} AND {price_range[1]}
            """

            result = execute_sql_query(query)
            if result:
                conversation.append("The phones in this range are: ")
                conversation.append(result)
            else:
                conversation.append("No matching products found.")

        except ValueError:
            conversation.append("Invalid input. Please provide a valid price range.")

    # the best smartphone between a range
    elif "between" in question.lower() and "best" in question.lower() and ("all" not in question.lower() or "price" in question.lower()):
        try:
            price_range = [int(x) for x in question.split() if x.isdigit()]
            if len(price_range) == 2:
                query = f"""
                    SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
                    FROM Product P
                    JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
                    WHERE P.`Product Price` BETWEEN {price_range[0]} AND {price_range[1]}
                    ORDER BY R.`Product Rating` DESC, R.`Review Score` DESC
                    LIMIT 4
                """

                result = execute_sql_query(query)
                if result:
                    conversation.append(f"The best mobile phones between {price_range[0]} and {price_range[1]} are :")
                    conversation.append(result)
                else:
                    conversation.append("No matching products found.")
            else:
                conversation.append("Invalid input. Please provide a valid price range.")
        except ValueError:
            conversation.append("Invalid input. Please provide a valid price range.")

    #show me the products b/w 10000 and 2000 with rating atleast 3.5 rating
    elif "between" in question.lower() and "price" in question.lower() and ("rating" in question.lower() or 'brand' in question.lower()):
        price_range = [int(x) for x in question.split() if x.isdigit()]


        if "rating" in question.lower() and "atleast" in question.lower():
            query = f"""
                 SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
                 FROM Product P
                 JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                 WHERE (`Product Price` BETWEEN {price_range[0]} AND {price_range[1]}) AND (`Product rating` >= {price_range[2]})
             """

        if "brand" in question.lower():
            tokens = word_tokenize(question)

            # Find the index of the word "brand" in the tokens
            brand_index = tokens.index("brand") - 1

            # Extract the brand name
            brand_name = tokens[brand_index]

            query = f"""
                 SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
                 FROM Product P
                 JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
                 WHERE P.`Product Price` BETWEEN {price_range[0]} AND {price_range[1]} AND `Product Brand` = '{brand_name}' OR `Product Name` LIKE '%{brand_name}%'
             """

        if "rating" in question.lower() and "brand" in question.lower():
            query = f"""
                 SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
                 FROM Product P
                 JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                 WHERE P.`Product Price` BETWEEN {price_range[0]} AND {price_range[1]} AND R.`Product rating` >= {price_range[2]} AND `Product Brand` = '{brand_name}' OR `Product Name` LIKE '%{brand_name}%'
             """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The mobile phones based on your preference are  :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")


    #show me the best smartphone
    elif "best" in question.lower() and ("smart phone" in question.lower() or "mobile phone" in question.lower()):

        query = f"""
            SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
            FROM Product P
            JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
            ORDER BY R.`Product Rating` DESC, R.`Review Score` DESC
            LIMIT 4
        """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The top 4 best mobile phones are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    # all phone of a certain brand
    elif "brand" in question.lower() and "all" in question.lower():
        tokens = word_tokenize(question)

        # Find the index of the word "brand" in the tokens
        brand_index = tokens.index("brand") - 1

        # Extract the brand name
        brand_name = tokens[brand_index]

        query = f"""
            SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
            FROM Product P
            JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
            WHERE `Product Brand` = '{brand_name}' OR `Product Name` LIKE '%{brand_name}%'
        """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"All the phones of {brand_name} are : ")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    # phone of a certain brand with altleast 3 rating
    elif "brand" in question.lower() and "atleast" in question.lower() and "rating" in question.lower() and "under" not in question.lower() and "above" not in question.lower():
        price_range = [int(x) for x in question.split() if x.isdigit()]
        tokens = word_tokenize(question)

        # Find the index of the word "brand" in the tokens
        brand_index = tokens.index("brand") - 1

        # Extract the brand name
        brand_name = tokens[brand_index]

        query = f"""
            SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
            FROM Product P
            JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
            WHERE (`Product Brand` = '{brand_name}' OR `Product Name` LIKE '%{brand_name}%') AND `Product rating`>={price_range[0]}
        """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"All the phones of {brand_name} based on your criteria are : ")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    # best phone of a certain brand
    elif "brand" in question.lower() and "best" in question.lower():
        tokens = word_tokenize(question)

        # Find the index of the word "brand" in the tokens
        brand_index = tokens.index("brand") - 1

        # Extract the brand name
        brand_name = tokens[brand_index]

        query = f"""
            SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
            FROM Product P
            JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
            WHERE P.`Product Brand` = '{brand_name}' OR `Product Name` LIKE '%{brand_name}%'
            ORDER BY R.`Product Rating` DESC, R.`Review Score` DESC
            LIMIT 4
        """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The best phones of {brand_name} are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")



    # recommend me a good phone
    elif "recommend" in question.lower() and ("good" in question.lower() or "best" in question.lower()):

        query = f"""SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
                FROM Product P
                JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                ORDER BY R.`Product Rating` DESC, R.`Review Score` DESC
                LIMIT 4
            """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The top four best phones are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #show me all the phones under certain price range
    elif "under" in question.lower() and "all" in question.lower():
        price_range = [int(x) for x in question.split() if x.isdigit()]

        query = f"""
            SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
            FROM Product P
            JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
            WHERE `Product Price` <= '{price_range[0]}'
        """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"All the phones under {price_range[0]} are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #show me best the phones under certain price range
    elif "under" in question.lower() and "best" in question.lower():
        price_range = [int(x) for x in question.split() if x.isdigit()]

        query = f"""SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
                FROM Product P
                JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                WHERE P.`Product Price` <= '{price_range[0]}' 
                ORDER BY R.`Product Rating` DESC, R.`Review Score` DESC
                LIMIT 4
            """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The top 4 best the phones under {price_range[0]} are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #show me the phones under certain price range with atleast 3.5 rating and samsung brand
    elif "under" in question.lower() and ("rating" in question.lower() or "brand" in question.lower()):
        print(" i am true")
        price_range = [int(x) for x in question.split() if x.isdigit()]

        if "rating" in question.lower() and "atleast" in question.lower():
            query = f"""
                 SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
                 FROM Product P
                 JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                 WHERE P.`Product Price` <= '{price_range[0]}' AND (`Product rating` >= {price_range[1]})
             """


        if "brand" in question.lower():
            tokens = word_tokenize(question)

            # Find the index of the word "brand" in the tokens
            brand_index = tokens.index("brand") - 1

            # Extract the brand name
            brand_name = tokens[brand_index]

            query = f"""
                 SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
                 FROM Product P
                 JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
                 WHERE P.`Product Price` <= '{price_range[0]}'  AND (P.`Product Brand` = '{brand_name}' OR P.`Product Name` LIKE '%{brand_name}%')
             """

        if "rating" in question.lower() and "brand" in question.lower():

            query = f"""
                 SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
                 FROM Product P
                 JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                 WHERE P.`Product Price` <= '{price_range[0]}' AND R.`Product rating` >= {price_range[1]} AND P.`Product Brand` = '{brand_name}' OR P.`Product Name` LIKE '%{brand_name}%'
             """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The phones under {price_range[0]} based on your preference are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #show me all the phones above certain price range
    elif "above" in question.lower() and "all" in question.lower():
        price_range = [int(x) for x in question.split() if x.isdigit()]

        query = f"""
            SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
            FROM Product P
            JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
            WHERE `Product Price` >= '{price_range[0]}'
        """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"All the phones above {price_range[0]} are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #show me best the phones above certain price range
    elif "above" in question.lower() and "best" in question.lower():
        price_range = [int(x) for x in question.split() if x.isdigit()]

        query = f"""SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
                FROM Product P
                JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                WHERE P.`Product Price` >= '{price_range[0]}' 
                ORDER BY R.`Product Rating` DESC, R.`Review Score` DESC
                LIMIT 4
            """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The top 4 best the phones above {price_range[0]} are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #show me the phones above certain price range with atleast 3.5 rating and samsung brand
    elif "above" in question.lower() and ("rating" in question.lower() or "brand" in question.lower()):
        price_range = [int(x) for x in question.split() if x.isdigit()]

        if "rating" in question.lower() and "atleast" in question.lower():
            query = f"""
                 SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
                 FROM Product P
                 JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                 WHERE P.`Product Price` >= '{price_range[0]}' AND (`Product rating` >= {price_range[1]})
             """

        if "brand" in question.lower():
            tokens = word_tokenize(question)

            # Find the index of the word "brand" in the tokens
            brand_index = tokens.index("brand") - 1

            # Extract the brand name
            brand_name = tokens[brand_index]

            query = f"""
                 SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
                 FROM Product P
                 JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
                 WHERE P.`Product Price` >= '{price_range[0]}'  AND (P.`Product Brand` = '{brand_name}' OR P.`Product Name` LIKE '%{brand_name}%')
             """

        if "rating" in question.lower() and "brand" in question.lower():

            query = f"""
                 SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`, P.`Product link`
                 FROM Product P
                 JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                 WHERE P.`Product Price` >= '{price_range[0]}' AND R.`Product rating` >= {price_range[1]} AND P.`Product Brand` = '{brand_name}' OR P.`Product Name` LIKE '%{brand_name}%'
             """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The phones above {price_range[0]} based on your preference are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #budget friendly phones or cheapest
    elif "budget" in question.lower() and "friendly" or "cheapest" in question.lower():

        query = f"""
            SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
            FROM Product P
            JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
            ORDER BY `Product Price` ASC LIMIT 4
        """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The top 4 best cheapest phones are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #find me high-end or expensive smartphone
    elif "high end" in question.lower() or "expensive" in question.lower():

        query = f"""
            SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
            FROM Product P
            JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
            ORDER BY `Product Price` DESC LIMIT 4
        """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The top 4 best expensive phones are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #"Show me phones with a good camera."
    elif "camera" in question.lower() and "good" in question.lower() or "best" in question.lower():

        query = f"""
            SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
            FROM Product P
            JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
            WHERE `Product Name` LIKE '%50 MP%' OR `Product Description` LIKE '%50 MP%' 
            ORDER BY `Product Price` DESC LIMIT 4
        """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The top 4 best camera phones are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #show me phones with atleast 50 MP
    elif "camera" in question.lower() and "atleast" in question.lower() or "mp" in question.lower():

        price_range = [int(x) for x in question.split() if x.isdigit()]

        string=str(price_range[0])+"MP"

        query = f"""
            SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
            FROM Product P
            JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
            WHERE `Product Name` LIKE '%{string}%' OR `Product Description` LIKE '%{string}%'
        """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The best camera phones with {string} are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #"Which phones have a long battery life?"
    elif "battery" in question.lower() and "long" in question.lower() or "life" in question.lower() or "mah" in question.lower():

        query = f"""
            SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
            FROM Product P
            JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
            WHERE `Product Description` LIKE '%5000%' ORDER BY `Product Price` ASC LIMIT 4
        """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The top 4 best phones with good battery life are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #"Show me phones with a 5G network."
    elif "5G" in question:

        query = f"""
            SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
            FROM Product P
            JOIN Reviews R ON P.`Product ID` = R.`Review_ID` 
            WHERE `Product Name` LIKE '%5G%' OR `Product Description` LIKE '%5G%'
        """

        result = execute_sql_query(query)

        if result:
            conversation.append(f"The phones with 5G network are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #Highest rated phones
    elif "highest" in question.lower() or "high" in question.lower() and "rating" in question.lower() or "rated" in question.lower():

        query = f"""
                SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
                FROM Product P
                JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                ORDER BY R.`Product Rating` DESC, P.`Product Price` ASC 
                LIMIT 4
            """
        result = execute_sql_query(query)
        if result:
            conversation.append(f"The phones with highest rating are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #Positive review phones
    elif "positive" in question.lower() or "good" in question.lower() and "review" in question.lower() or "feedback" in question.lower():

        query = f"""
                SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
                FROM Product P
                JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                ORDER BY R.`Review score` DESC
                LIMIT 4
            """
        result = execute_sql_query(query)
        if result:
            conversation.append(f"The  top 4 phones with positive feedback are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #Show me phones with atleast 80 review score
    elif "atleast" in question.lower() and "score" in question.lower() and "review" in question.lower():

        price_range = [int(x) for x in question.split() if x.isdigit()]

        query = f"""
                SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
                FROM Product P
                JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                WHERE R.`Review score`>={price_range[0]}
            """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The phones with atleast {price_range[0]} review score are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #"Find phones with a rating atleast -- stars."
    elif "rating" in question.lower() and 'atleast' in question.lower():
        price_range = [int(x) for x in question.split() if x.isdigit()]

        star_name = (price_range[0])

        query = f"""
                SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
                FROM Product P
                JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                WHERE R.`Product rating`>={star_name}
            """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The phones with atleast {star_name} ratings are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #show all details of "___" product id
    elif "all" in question.lower() and "details" in question.lower() and "id" in question:
        price_range = [int(x) for x in question.split() if x.isdigit()]

        spec_name = price_range[0]

        query = f"""SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
                FROM Product P
                JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                WHERE P.`Product ID`={spec_name}
            """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The details of {spec_name} phone is :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #show me ____ details of "___" product id
    elif "all" not in question.lower() and "details" in question.lower() and "id" in question and "product" in question:
        tokens = word_tokenize(question)

        #product id
        price_range = [int(x) for x in question.split() if x.isdigit()]
        spec_name=price_range[0]

        brand_spec = tokens.index("product") + 1
        string=tokens[brand_spec]
        try:
            product_detail = "Product " + string
            print(product_detail)

            query = f"""SELECT R.`{product_detail}`
                        FROM Product P
                        JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                        WHERE P.`Product ID`={spec_name}
                     """

            result = execute_sql_query(query)

        except sqlite3.OperationalError as e:
            product_detail = "Product " + string
            print(product_detail)

            query = f"""SELECT P.`{product_detail}`
                                    FROM Product P
                                    JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                                    WHERE P.`Product ID`={spec_name}
                                 """

            result = execute_sql_query(query)
        if result:
            conversation.append(f"The details of {spec_name} phone is :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #"Tell me about the model iPhone 13 Pro Max"
    elif "model" in question.lower() and "show" in question.lower() or "tell" in question.lower() and "specification" not in question.lower():
        pattern = r'\bmodel\s+(\S+)'

        match = re.search(pattern, question, re.IGNORECASE)
        model_name = match.group(1)

        query = f"""SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
                FROM Product P
                JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                WHERE `Product Name` LIKE '%{model_name}%' OR `Product Description` LIKE '%{model_name}%'
            """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The phones of {model_name} are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #"Tell me about specification the model iPhone 13 Pro Max"
    elif "model" in question.lower() and "show" in question.lower() or "tell" in question.lower() and "specification" in question.lower():
        pattern = r'\bmodel\s+(\S+)'

        match = re.search(pattern, question, re.IGNORECASE)
        model_name = match.group(1)

        query = f"""SELECT  P.`Product Name`, P.`Product Price`, R.`Product Rating`,P.`Product Description`,P.`Product link`
                FROM Product P
                JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                WHERE `Product Name` LIKE '%{model_name}%' OR `Product Description` LIKE '%{model_name}%'
            """


        result = execute_sql_query(query)
        if result:
            conversation.append(f"The phones of {model_name} are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    #find phone with atleast ___ ___ specification(eg: 128GB memory)
    elif "specification" in question.lower() and "atleast" in question.lower():
        tokens = word_tokenize(question)

        # Find the index of the word "brand" in the tokens
        brand_spec = tokens.index("atleast") + 1

        # Extract the brand name
        spec_name = tokens[brand_spec]

        query = f"""SELECT P.`Product Name`, P.`Product Price`, R.`Product Rating`, R.`Review Score`,P.`Product link`
                FROM Product P
                JOIN Reviews R ON P.`Product ID` = R.`Review_ID`
                WHERE `Product Name` LIKE '%{brand_spec}%' OR `Product Description` LIKE '%{brand_spec}%'
            """

        result = execute_sql_query(query)
        if result:
            conversation.append(f"The phones for your prefered specs are :")
            conversation.append(result)
        else:
            conversation.append("No matching products found.")

    else:
        conversation.append("I'm sorry, I don't understand that question.")

    return conversation


@app.route('/', methods=['GET', 'POST'])
def index():
    conversation = []  # To store the conversation history

    if request.method == 'POST':
        user_input = request.form['user_input']
        ask_question(user_input, conversation)


    return render_template('dashboard.html', response=conversation)


if __name__ == '__main__':
    app.run(debug=True)
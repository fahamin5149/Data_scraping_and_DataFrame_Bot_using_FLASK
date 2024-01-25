<h1>Advanced Mobile Product Analysis and Interactive Chatbot System</h1>
In this project, I have undertaken a comprehensive task that involves sophisticated web scraping of mobile products from daraz.pk, data storage, and the development of an advanced chatbot. The project is focus on extracting detailed information about mobile products, creating an intelligent chatbot for user interaction, and presenting the data through an insightful and interactive dashboard.

# Web Scraping

## Objective
Extract mobile product data from daraz.pk, specifically from the first five pages.

## Example
Using Selenium or BeautifulSoup, a script has been written to navigate to the mobile phone section of daraz.pk. The script then parses through the HTML of each page, extracting product details such as name, price, brand, and reviews. For instance, if a product is named "Samsung Galaxy S21," the script extracts its price, specifications, and user reviews.

## Extracted Information
- Product ID
- Name
- Price
- Company
- Reviews (including Review ID, Score, and Content)

## Data Storage
The extracted product details and reviews are stored in separate files (excel or csv), each uniquely identified with an ID.

## Key Focus
Filtering out irrelevant products has been achieved by setting conditions to exclude listings containing keywords like "case," "cover," or "charger."

# Database Integration

## Objective
Create a structured storage system for the scraped data.

## Example
I have designed tables for structured storage, using MySQL as an example. The tables include Products (storing ID, name, price, brand) and Reviews (storing review text, rating, associated product ID). This design allows for efficient querying and analysis of data.

## Key Focus
Ensuring the database schema is robust enough to handle various types of data and queries, such as retrieving all products within a certain price range or the average rating of a brand.

# Chatbot Development

## Objective
Develop a chatbot capable of handling user queries based on the previously scraped data.

## Example
I have developed a chatbot that utilizes the stored data. For instance, if a user asks, "What is the best phone under $300?" the chatbot can analyze the data and respond with options like "Based on user ratings and price, the best phones under $300 are [Product A], [Product B]."

## Key Focus
Implementing natural language processing (NLP) capabilities for the chatbot to understand and accurately respond to complex queries.

# Dashboard Development

## Objective
I have created a dashboard to visually present the previously scraped data.

## Elements with Examples
- Input field for querying data (chatbot)
- Total number of listings.
- Average product price.
- Average ratings of products.
- Average review count per product.
- Total number of questions asked.
- Top 5 products based on defined criteria (e.g., highest ratings, most reviews). A dynamic section showcasing the top 5 mobile phones based on a selected criterion like highest rating or most reviews. Each product has a visual representation of a clickable link (not a real URL, but a placeholder for demonstration purposes).
- Make product details clickable with URLs linking back to the respective product on daraz.pk.
- Utilized Flask technology to build this dashboard.


import csv
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd

app = Flask(__name__)

with open('Address.csv', 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    headers = next(csvreader)  # Extract the header row

print(headers)  # Print the headers

# Read in all the data tables and merge them into a single data table
with open('Address.csv') as file:
    address_table = list(csv.DictReader(file))

with open('Bidders.csv') as file:
    bidder_table = list(csv.DictReader(file))

merged_table = []
for bidder in bidder_table:
    home_address_id = bidder['home_address_id']
    address = next((address for address in address_table if address['ï»¿address_id'] == home_address_id), None)
    if address is None:
        continue
    merged_row = {**bidder, **address}

    with open('Credit_Cards.csv') as file:
        credit_card = next((card for card in csv.DictReader(file) if card['Owner_email'] == merged_row['ï»¿email']),
                           None)
    if credit_card is None:
        continue
    merged_row.update(credit_card)

    with open('Zipcode_Info.csv') as file:
        zipcode_info = next(
            (zipinfo for zipinfo in csv.DictReader(file) if zipinfo['ï»¿zipcode'] == merged_row['zipcode']), None)
    if zipcode_info is None:
        continue
    merged_row.update(zipcode_info)

    merged_table.append(merged_row)

    # turn it into a pandas dataframe
    df = pd.DataFrame(merged_table)

# Read in Auction_Listings.csv and create pandas dataframe
auction_listings = pd.read_csv('Auction_Listings.csv', header=0)

with open('Users.csv') as file:
    users_table = list(csv.DictReader(file))


# Helper function to securely hash the passwords
def hash_password(password):
    # Add your secure password hashing code here
    return password


# Route for the login page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        option = request.form['type']

        # Check if the email and password match a user in the users table
        for user in users_table:
            if user['ï»¿email'] == email and user['password'] == hash_password(password):
                print("true dat")
                if option == 'bidder':
                    # Redirect to the bidder page
                    print("bidder spotted")
                    return redirect(url_for('bidder', email=email))

                elif option == 'seller':
                    # Redirect to the seller page
                    print("seller spotted")
                    return redirect(url_for('/seller', email=email))

        # If no matching user was found, show an error message
        return render_template('login.html', error='Wrong email or password')

    # If the request method is GET, just show the login page
    return render_template('login.html')


# Route for the bidder page
@app.route('/bidder', methods=['GET', 'POST'])
def bidder():
    if request.method == 'POST' and 'search' in request.form:
        return render_template('auctions.html', auction_listings=auction_listings[
            ['Product_Name', 'Product_Description', 'Quantity', 'Seller_Email']])
    else:
        email = request.args.get('email')
        bidder_info = df.loc[df['ï»¿email'] == email]
        return render_template('bidder.html', bidder_info=bidder_info.to_html(index=False), email=email)


@app.route('/auctions', methods=['GET', 'POST'])
def auctions():
    if request.method == 'POST':
        # handle form submission here
        return render_template('auctions.html', auctions=auction_listings.to_dict('records'))
    else:
        # display the auctions page
        return render_template('auctions.html', auctions=auction_listings.to_dict('records'))


# Route for the seller page
@app.route('/seller/<email>')
def seller(email):
    # Add your code here to show the seller page
    return "Seller page"


if __name__ == '__main__':
    app.run(debug=True)

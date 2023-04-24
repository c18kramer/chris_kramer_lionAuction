import csv
from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import math
import hashlib

app = Flask(__name__)
app.secret_key = 'secretkey123'

# Read in Auction_Listings.csv and create pandas dataframe
auction_listings = pd.read_csv('Auction_Listings.csv', header=0)
# same for categories
categories_df = pd.read_csv('Categories.csv', header=0)
categories = set(categories_df['category_name'].unique())
# read in the bidding history
bids_df = pd.read_csv("Bids.csv", header=0)

with open('Address.csv', 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    headers = next(csvreader)  # Extract the header row

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

with open('Users.csv') as file:
    users_table = list(csv.DictReader(file))

# read in the seller data so that we can log in as a seller as well
with open('Sellers.csv') as file:
    sellers_table = list(csv.DictReader(file))


# Helper function to securely hash the passwords
def hash_password(password):
    return password


# Route for the login page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        option = request.form['type']

        if option == 'bidder':
            # Check if the email and password match a user in the users table
            for user in users_table:
                if user['ï»¿email'] == email and user['password'] == hash_password(password):
                    print("true dat")
                    session['email'] = email
                    flash('Logged in successfully.', 'success')
                    print("bidder spotted")
                    return redirect(url_for('bidder', email=email))

        # when checking for seller, we don't look for the email in the sellers.csv file because the emails are all different
        # some are similar, but have a different @ address, so we cannot match them up
        elif option == 'seller':
            # Redirect to the seller page
            for user in sellers_table:
                if user['ï»¿email'] == email:
                    print("got em")
                    session['email'] = email
                    flash('Logged in successfully.', 'success')
                    print("seller spotted")
                    return redirect(url_for('seller', email=email))

        # If no matching user was found, show an error message
        return render_template('login.html', error='Wrong email or password')

    # If the request method is GET, just show the login page
    return render_template('login.html')


@app.route('/bidder', methods=['GET', 'POST'])
def bidder():
    if request.method == 'POST' and 'search' in request.form:
        return render_template('auctions.html', auction_listings=auction_listings[
            ['Product_Name', 'Product_Description', 'Quantity', 'Seller_Email']])
    else:
        email = request.args.get('email')
        bidder_info = df.loc[df['Owner_Email'] == email]
        bidder_info = pd.DataFrame(bidder_info)
        bidder_info_html = bidder_info.to_html(index=False)  # call to_html() on the DataFrame
        return render_template('bidder.html', bidder_info=bidder_info_html, email=email)


@app.route('/auctions', methods=['GET', 'POST'])
def auctions():
    if request.method == 'POST':
        selected_category = request.form.get('category')
        print(selected_category)
        if selected_category == 'All':
            filtered_auctions = auction_listings
        else:
            filtered_auctions = auction_listings[auction_listings['Category'] == selected_category]

        print(filtered_auctions)

        return render_template('auctions.html', auction_listings=filtered_auctions.to_dict('records'),
                               categories=categories)
    else:
        return render_template('auctions.html', auction_listings=auction_listings, categories=categories)


# Route for the seller page
@app.route('/seller/<email>', methods=['GET', 'POST'])
def seller(email):
    # Get the seller's email from the session
    seller_email = session['email']

    # Get the seller's information from merged_table using their email
    seller_info = df[df['ï»¿email'] == seller_email]
    print(seller_info)
    print(df['ï»¿email'])
    print(seller_email)

    # Get all the auctions from auction_listings with the seller's email
    seller_auctions = auction_listings[auction_listings['Seller_Email'] == seller_email]

    if request.method == 'POST':
        listing_id = request.form['listing_id']
        print(listing_id)
        auction_listings.loc[auction_listings['Listing_ID'] == int(listing_id), 'Product_Description'] = 'AUCTION REMOVED'
        return redirect(url_for('seller', email=seller_email))

    # Render the seller.html template with the seller's information and auctions
    return render_template('seller.html', seller_info=seller_info.to_dict('records'), seller_auctions=seller_auctions.to_dict('records'))


@app.route('/item/<int:listing_id>')
def item(listing_id):
    # Filter the auction_listings dataframe to extract the relevant information
    auction = auction_listings.loc[auction_listings['Listing_ID'] == listing_id].iloc[0]

    if listing_id in bids_df['Listing_ID'].values:

        # find the highest bid for the selected item
        highest_bid_price = 0
        for index, row in bids_df.iterrows():
            if row['Listing_ID'] == listing_id and row['Bid_Price'] > highest_bid_price:
                highest_bid_price = row['Bid_Price']
                bidder_email = row['Bidder_Email']

        current_bid = highest_bid_price

    else:
        print("Listing_ID is not found in the bids_df dataset.")
        bidder_email = "No Bidder"
        current_bid = 0

    # Extract the relevant information for the item
    product_name = auction['Product_Name']
    product_description = auction['Product_Description']
    quantity = auction['Quantity']
    seller_email = auction['Seller_Email']

    # Render the item.html template with the relevant information
    return render_template('item.html', product_name=product_name, product_description=product_description,
                           quantity=quantity, seller_email=seller_email, bidder_email=bidder_email,
                           current_bid=current_bid, listing_id=listing_id)


@app.route('/submit_bid', methods=['POST'])
def submit_bid():
    listing_id = request.form['listing_id']
    bid_amount = int(request.form['bid_amount'])
    bidder_email = session['email']
    global bids_df
    # get the auction they are bidding on so we can abstract relevant information
    # auction = auction_listings.loc[auction_listings['Listing_ID'] == listing_id].iloc[0]

    # Check if user is the current highest bidder
    current_bid = bids_df.loc[bids_df['Listing_ID'] == listing_id]['Bid_Price'].max()
    print(current_bid)
    print(bids_df['Bidder_Email'])
    print(bids_df.shape[1])
    # seller_email = auction['Seller_Email']
    if math.isnan(current_bid) or bids_df['Bidder_Email'].empty:
        print("No Bids on this item")
        # Add new bid to bids_df
        bids_df.loc[len(bids_df.index)] = [999, "seller_email", listing_id, bidder_email, bid_amount]
        # Save the new bid to a CSV file
        bids_df.to_csv('bids.csv', index=False)

        flash('Your bid has been submitted!', 'success')
        return redirect(url_for('item', listing_id=listing_id))

    else:
        print("There are bids on this item")
        current_highest_bidder = bids_df.loc[bids_df['Bid_Price'] == current_bid]['Bidder_Email'].values[0]
        if bidder_email == current_highest_bidder:
            flash('You are already the highest bidder for this item!', 'danger')
            return redirect(url_for('item', listing_id=listing_id))
        elif bid_amount <= current_bid:
            flash('Bid amount must be at least 1 unit higher than the current highest bid!', 'danger')
            return redirect(url_for('item', listing_id=listing_id))
        elif bid_amount > current_bid:
            # Add new bid to bids_df
            bids_df.loc[len(bids_df.index)] = [999, "seller_email", listing_id, bidder_email, bid_amount]
            # Save the new bid to a CSV file
            bids_df.to_csv('bids.csv', index=False)

            flash('Your bid has been submitted!', 'success')
            return redirect(url_for('item', listing_id=listing_id))


# view the bids the user has placed
@app.route('/view_user_bids', methods=['GET', 'POST'])
def view_user_bids():
    email = session.get('email')
    user_bids_df = bids_df[bids_df['Bidder_Email'] == email]
    user_bids = user_bids_df.to_dict('records')
    return render_template('bid_history.html', user_bids=user_bids)


if __name__ == '__main__':
    app.run(debug=True)

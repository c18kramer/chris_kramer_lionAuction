# importing the many packages we need for the project
import csv
from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import math
import bcrypt

# starting flask app
app = Flask(__name__)
# create the secret key
app.secret_key = "secretkey123"

# Read in Auction_Listings.csv and create pandas dataframe
auction_listings = pd.read_csv('Auction_Listings.csv', header=0)
# same for categories
categories_df = pd.read_csv('Categories.csv', header=0)
categories = set(categories_df['category_name'].unique())
# read in the bidding history
bids_df = pd.read_csv("Bids.csv", header=0)

# next long chunk is taking in all bidder information and merging it into one table
with open('Address.csv', 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    headers = next(csvreader)  # Extract the header row

with open('Address.csv') as file:
    address_table = list(csv.DictReader(file))

with open('Bidders.csv') as file:
    bidder_table = list(csv.DictReader(file))

# creating the merged table
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

# read in the user's emails and passwords
with open('Users.csv') as file:
    users_table = list(csv.DictReader(file))

# read in the seller data so that we can log in as a seller as well
with open('Sellers.csv') as file:
    sellers_table = list(csv.DictReader(file))


# hashes the passwords
def hash_password(password):
    # encode the password string as bytes using utf-8, common method
    password_bytes = password.encode('utf-8')
    # generate a salt to use for the password hash
    salt = bcrypt.gensalt()
    # hash the password using the salt
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    # Return the hashed password as a bytes object
    return hashed_password


# matches the passwords to check if they are the same
# allows us to match entered password to encrypted password
def match_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)


# this code hashes every password in the Users.csv file, takes very long time to run
# for row in users_table:
#   row['password'] = hash_password(row['password'])


# Route for the login page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST': # takes in the email and password they entered
        email = request.form['email']
        password = request.form['password']
        option = request.form['type']

        if option == 'bidder': # if they are logging in as a bidder
            # Check if the email and password match a user in the users table
            for user in users_table:
                if user['ï»¿email'] == email and user['password'] == password:
                    session['email'] = email # setting the universal log in email
                    flash('Logged in successfully.', 'success')
                    return redirect(url_for('bidder', email=email))

        # check to make sure they are a seller, with their email being in Sellers.csv
        elif option == 'seller':
            # Redirect to the seller page
            for user in sellers_table:
                if user['ï»¿email'] == email:
                    session['email'] = email # setting the global session email for later use
                    flash('Logged in successfully.', 'success')
                    return redirect(url_for('seller', email=email))

        # If no matching user was found, show an error message
        return render_template('login.html', error='Wrong email or password')

    # If the request method is GET, just show the login page
    return render_template('login.html') # if they fail to log in


@app.route('/bidder', methods=['GET', 'POST']) # first route if they are a bidder
def bidder():
    if request.method == 'POST' and 'search' in request.form: # lists all the auctions in selected category
        return render_template('auctions.html', auction_listings=auction_listings[
            ['Product_Name', 'Product_Description', 'Quantity', 'Seller_Email']])
    else: # if they want to display their own personal information
        email = request.args.get('email')
        bidder_info = df.loc[df['Owner_email'] == email]
        bidder_info = pd.DataFrame(bidder_info)
        bidder_info_html = bidder_info.to_html(index=False)  # call to_html() on the DataFrame
        return render_template('bidder.html', bidder_info=bidder_info_html, email=email)


@app.route('/auctions', methods=['GET', 'POST']) # route for viewing filtered auctions
def auctions():
    if request.method == 'POST':
        selected_category = request.form.get('category')
        print(selected_category)
        if selected_category == 'All': # if they want to view all auctions
            filtered_auctions = auction_listings
        else: # if they selected a category
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

    # Get all the auctions from auction_listings with the seller's email
    seller_auctions = auction_listings[auction_listings['Seller_Email'] == seller_email]

    if request.method == 'POST': # if they clicked to remove an auction, change its description
        listing_id = request.form['listing_id']
        print(listing_id)
        auction_listings.loc[
            auction_listings['Listing_ID'] == int(listing_id), 'Product_Description'] = 'AUCTION REMOVED'
        return redirect(url_for('seller', email=seller_email))

    # Render the seller.html template with the seller's information and auctions
    return render_template('seller.html', seller_info=seller_info.to_dict('records'),
                           seller_auctions=seller_auctions.to_dict('records'))


@app.route('/item/<int:listing_id>') # if a bidder clicked on a specific item
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

    else: # if the item has no bids yet
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


@app.route('/submit_bid', methods=['POST']) # for submitting a bid on their selected item
def submit_bid():
    # get all the necessary information to place the bid
    listing_id = request.form['listing_id']
    bid_amount = int(request.form['bid_amount'])
    bidder_email = session['email']
    global bids_df
    seller_email = bids_df[bids_df['Listing_ID'] == listing_id]['Seller_Email']

    # Check if user is the current highest bidder
    current_bid = bids_df.loc[bids_df['Listing_ID'] == listing_id]['Bid_Price'].max()
    print(current_bid)
    print(bids_df['Bidder_Email'])
    print(bids_df.shape[1])
    if math.isnan(current_bid) or bids_df['Bidder_Email'].empty: # if there are no bids, we can just place the bid
        print("No Bids on this item")
        # Add new bid to bids_df
        bids_df.loc[len(bids_df.index)] = [999, seller_email, listing_id, bidder_email, bid_amount]
        # Save the new bid to a CSV file
        bids_df.to_csv('bids.csv', index=False)

        flash('Your bid has been submitted!', 'success')
        return redirect(url_for('item', listing_id=listing_id))

    else: # if there are bids, we must run a few checks
        print("There are bids on this item")
        current_highest_bidder = bids_df.loc[bids_df['Bid_Price'] == current_bid]['Bidder_Email'].values[0]
        if bidder_email == current_highest_bidder: # check to make sure they aren't highest bidder
            flash('You are already the highest bidder for this item!', 'danger')
            return redirect(url_for('item', listing_id=listing_id))
        elif bid_amount <= current_bid: # check to make sure their bid is higher than the last
            flash('Bid amount must be at least 1 unit higher than the current highest bid!', 'danger')
            return redirect(url_for('item', listing_id=listing_id))
        elif bid_amount > current_bid: # if conditions met, place the bid
            # Add new bid to bids_df
            bids_df.loc[len(bids_df.index)] = [999, seller_email, listing_id, bidder_email, bid_amount]
            # Save the new bid to a CSV file
            bids_df.to_csv('bids.csv', index=False)

            flash('Your bid has been submitted!', 'success')
            return redirect(url_for('item', listing_id=listing_id))


# view the bids the user has placed
@app.route('/view_user_bids', methods=['GET', 'POST'])
def view_user_bids():
    # displays each bid that is attached to the email they logged in with
    email = session.get('email')
    user_bids_df = bids_df[bids_df['Bidder_Email'] == email]
    user_bids = user_bids_df.to_dict('records')
    return render_template('bid_history.html', user_bids=user_bids)


# this route is meant to display the account information of the signed in user
@app.route('/account')
def account():
    email = session['email'] # session email /= stored email
    account_info = df[df['ï»¿email'] == email]
    return render_template('account.html', account_info=account_info) # the email inconsistency makes this not work


# running the main file
if __name__ == '__main__':
    app.run(debug=True)

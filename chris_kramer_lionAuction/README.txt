LionAuction Prototype V1

i) The beginning of the code is reading in the many datasets used to make the prototype work. This includes but is not limited to: User data, auction data, seller data, address and zipcode data, bidding history, etc.

The code includes routes for each pages that handles their specific functionality as requested in the proposal, such as logging in securely, listing the many different auctions, filtering the many different auctions by category, placing bids on various auctions, viewing bidding history, etc.

The html code lays out the foundation for each page, and is then filled with the necessary data from our stored pandas dataframes through the route functions. Pages include brief css styling at the top in order to make each page presentable and visually appealing to the user.

ii) The features list of the prototype includes but is not limited to: Logging in securely as either a bidder or a seller, viewing ones own information, viewing the verious listings as a bidder, viewing the various bids placed as a bidder, filtering auctions by specific cateogories as a bidder, viewing the auctions you are hosting as a seller, and removing any auction you'd like to take down as a seller.

iii) The main app.py file can be found in the main folder, and each html file can be found in the 'templates' folder within the primary chris_kramer_lionAuction folder. Within the main folder you can also find the README file and each dataset that was used for the purposes of demonstrating the functionality of this prototype.

iv) In order to run the program, you must load the project folder into PyCharm Professional as a whole, which will open each individual file as will in the project manager screen located on the left of your UI. Assuming you've opened the project folder correctly, and can see all the necessary files within your project manager window, all you need to do is run the app.py file. And remember, sometimes these files take a long time to run, so be patient!
# recipe-book
## Video Demo:  <https://youtu.be/nFBnCfiY2VE>
## Description:
For my final project, I decided to make a flask web-app where users can add and save all of their recipes, as well as create a shopping list. Users can also add recipe ingredients directly to their list by clicking on them. I decided to use Bootstrap for the styling and to focus my effort on the back-end python code primarily. I also had to learn how to switch from my sqlite database to a postgres database and learned how to use SQLalchemy for my postgres database queries. I wanted to share this project with family and friends so they could use it as well, so I learned how to deploy the project to Heroku, which had a learning curve as well, but once everything was up and running I was proud of my finished product.
## Files:
### app.py:
This is all of the backend flask logic for the application. It imports all of the libraries I used such as sqlalchemy for database queries, datetime for setting the length of cookie expiration, and password hash checking with werkzeug. Four postgres tables as made, users for storing user information, recipes for storing recipe information, ingredients to store ingredient and amount information, and list to store all shopping list data. 
#### route /:
On GET it queries the recipes table for all recipes for the current user ordered from oldest to newest (asc by unique id), then sends that list to index.html to display the list of recipes.
On POST it get the new recipe name from index.html and check the recipes table to see if that user already has a recipe with that name. If the recipe already exists, an error is displayed, otherwise it is added to the table.
#### route /delete_recipe:
Gets the name of the recipe from index.html and deletes if from the recipes table then redirects back to /.
#### route /list:
Gets the name of the item and optionally notes. First it checks if the item already exists in the user's list. An error displays if the item is already in the list, otherwise the item is added to the sql table.
#### route /toggle_item:
This allows each list item to be able to be displayed as 'checked' with a line through. The item and current status of on or off is collected from list.html and if it is on, it will be updated to off in the table and if it is off it will be switched to on.
#### route /delete_item:
Gets the name of the selected item from list.html and deletes it from the sql table.
#### route /register:
Gets the username, password, and verify password values from register.html. Queries the users table to see if the username is available, and checks if the password fields match. An error will display if the username is not available, the password fields don't match or if any field is blank. Otherwise a new user will be created and added to the table.
#### route /login:
First clears the session, then checks the username and password fields. The users database is queried to see if the username exists and then the password hash is checked to ensure it is correct for that user. If successful, a new session will begin for that user.
#### route /logout:
Clears the session to log the user out.
#### route /recipe:
The recipe name is set to the user table field current recipe so that if they come back to /recipe as a GET request, it will remember which recipe to display. The recipes and ingredients tables are queried to find the list of ingredients, prep directions, cook directions, and notes for that recipe and displays them on the page.
#### route /ingredientToList:
Gets the ingredient name from recipe.html and queries the list table to see if that item already exists in the user's shopping list. An error is shown if it is already on the list, otherwise it is added to the table.
#### route /ingredient:
Gets the ingredient name and amount as well as the recipe id from recipe.html fields and uses that info to query the ingredients table to add the new ingredient.
#### route /delete_ingredient:
Gets the recipe name and id from recipe.html and uses that info to query the ingredients table and remove the correct item from the database.
#### route /prep:
Gets the prep directions from recipe.html and adds the text to the recipe sql table.
#### route /cook:
Gets the cook directions from recipe.html and adds the text to the recipe sql table.
#### route /note:
Gets the notes from recipe.html and adds the text to the recipe sql table.
#### route /account:
Queries the user table for the current user's username to display it on GET, on POST it gets the values from the old password, new password and verify password fields. It checks if the old password is correct and makes sure the new password matches the verify password field. Otherwise an error is displayed if any of those conditions aren't met or if any field is blank.
### account.html:
This file displays the user's username and allows them to optionally change their password. It also displays error messages if the password is incorrect or the new password field doesn't match the verify new password field.
### index.html:
This file displays the list of the user's recipes which can be clicked on to view and edit that recipe. There is also a button to delete a recipe which has a popup asking if the user is sure first. A button at the top of the list allows user's to add a new recipe.
### layout.html:
This file is the layout that all other html files for the project use. It has the navigation bar that show the menu of index, list, and account pages if a user is logged in, or register and login if a user is not logged in. It also contains all of the head html tag syntax such as the meta tags, css links, script tags and the title tag which fills in a variable depending on which page is loaded.
### list.html:
This file displays the user's shopping list. There is a button to add a new list item, and optionally a note can be added. When the item is clicked in the list, the note will display as a modal popup.
### login.html:
This page allows users to log in. Pages that require login will redirect here by default if a user is not already logged in.
### recipe.html:
This page allows users to add ingredients and their amounts to a recipe, to add the preperation directions, to add cooking directions, and to add any additional notes. When an ingredient is clicked, a modal popup will ask the user if they would like to add that item to their shopping list.
### register.html:
This page allows a new user to register with a new username and password. It will display an error if the username is already in use, the password fields do not match, or if any of the fields are left blank.
### styles.css:
Most of the styles are bootstrap defaults, but in the css file some adjustments were here made such as making elements display: flex to adjust their positioning on the page more effectively. The box shadow on focus was also removed from some transparent buttons here so that the text could be clicked without the element looking like a button, but still using submit to send a request to the backend.
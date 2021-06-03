import pymongo
from passlib.hash import pbkdf2_sha256
from flask import Flask, render_template, request, redirect, flash, session
from bson import ObjectId
import os
connection_string = os.environ.get("MONGO_URI")
if connection_string == None:
  file = open("connection_string.txt")
  connection_string = file.read().strip()
  file.close()
client = pymongo.MongoClient(connection_string)
database = client["Entrepreneurship_Project_Database"]
collection = database["My_Entrepreneurship_Project_Collection"]
request_collection = database["Request_Collection"]
app = Flask(__name__)
SECRET_KEY = os.environ.get("SECRET_KEY")
if SECRET_KEY == None:
  file = open("secret_key.txt")
  app.config["SECRET_KEY"] = file.read().strip()
  file.close()

@app.route("/")
def welcome():
  return render_template("welcome.html")

@app.route("/signup", methods = ["GET","POST"])
def Signup():
  if request.method == "GET":
    return render_template("Signup.html")
  else:
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    email_adress = request.form["email_adress"]
    password = request.form["password_input"]
    encrypted_password = pbkdf2_sha256.hash(password)
    record = {"First Name":first_name,"Last Name":last_name,"Email Adress":email_adress,"Password":encrypted_password}
    collection.insert_one(record)
    return redirect("/")

@app.route("/volunteerlogin", methods = ["GET","POST"])
def volunteerlogin():
  if request.method == "GET":
    return render_template("volunteerlogin.html")
  else:
    email_adress = request.form["email_adress"]
    password = request.form["password_input"]
    user = collection.find_one({"Email Adress":email_adress})
    if user != None:
      if pbkdf2_sha256.verify(password, user["Password"]) == True:
        return redirect("/volunteerpage?email="+email_adress)
      else:
        return "login failed"
    else:
      return "Email Adress Does Not Exist"

@app.route("/customerlogin", methods = ["GET","POST"])
def customerlogin():
  if request.method == "GET":
    return render_template("customerlogin.html")
  else:
    email_adress = request.form["email_adress"]
    password = request.form["password_input"]
    user = collection.find_one({"Email Adress":email_adress})
    if user != None:
      if pbkdf2_sha256.verify(password, user["Password"]) == True:
        session["email"] = email_adress
        return redirect("/customerrequestpage")
      else:
        flash ("Login failed")
        return redirect("/customerlogin")
    else:
      flash ("Password incorrect")
      return redirect("/customerlogin")

@app.route("/customerrequestpage", methods = ["GET","POST"])
def customerrequest():
  if "email" not in session:
    flash("Please log in to continue")
    return redirect("/")
  user_email = session["email"]
  if request.method == "GET":
    return render_template("customerorderpage.html")
  else:
    library_adress = request.form["library_adress"]
    delivery_adress = request.form["delivery_adress"]
    library_code = request.form["library_code"]
    phone_number = request.form["phone_number"]
    insert = {"Email Adress":user_email,"Library Adress":library_adress,"Delivery Adress":delivery_adress,"Pickup Code":library_code,"Phone Number":phone_number,"Status":"Open","Volunteer":""}
    request_collection.insert_one(insert)
    return redirect("/myrequests?email="+user_email)

@app.route("/myrequests", methods = ["GET","POST"])
def myrequests():
  if "email" not in session:
    flash("Please log in to continue")
    return redirect("/")
  user_email = request.args.get("email")
  user_requests = request_collection.find({"Email Adress":user_email})
  return render_template("myrequests.html",user_requests = user_requests)

@app.route("/remove")
def remove():
    if "email" not in session:
      flash("Please log in to continue")
      return redirect("/")
    #Deleting a Task with various references
    user_email = request.args.get("email")
    key = request.values.get("_id")
    request_collection.remove({"_id":ObjectId(key)})
    return redirect("/myrequests?email="+user_email)

@app.route("/volunteerpage", methods = ["GET","POST"])
def volunteerpage():
  if "email" not in session:
    flash("Please log in to continue")
    return redirect("/")
  user_email = request.args.get("email")
  user_requests = request_collection.find({"Status":"Open"})
  my_picks = request_collection.find({"Volunteer":user_email, "Status":"Picked"})
  my_delivered = request_collection.find({"Volunteer":user_email, "Status":"Delivered"})

  return render_template("volunteerpage.html", user_requests = user_requests, my_picks = my_picks, my_delivered=my_delivered)

@app.route("/cancel")
def cancel():
    if "email" not in session:
      flash("Please log in to continue")
      return redirect("/")
    #Deleting a Task with various references
    user_email = request.args.get("email")
    key = request.values.get("_id")    
    request_collection.update({"_id":ObjectId(key)},{"$set":{"Status":"Open", "Volunteer":""}})
    return redirect("/volunteerpage?email="+user_email)

@app.route("/picked")
def picked():
    if "email" not in session:
      flash("Please log in to continue")
      return redirect("/")
    #Deleting a Task with various references
    user_email = request.args.get("email")
    key = request.values.get("_id")    
    request_collection.update({"_id":ObjectId(key)},{"$set":{"Status":"Picked","Volunteer":user_email}})
    return redirect("/volunteerpage?email="+user_email)
  
@app.route("/delivered")
def delivered():
    if "email" not in session:
      flash("Please log in to continue")
      return redirect("/")
    #Deleting a Task with various references
    user_email = request.args.get("email")
    key = request.values.get("_id")    
    request_collection.update({"_id":ObjectId(key)},{"$set":{"Status":"Delivered"}})
    return redirect("/volunteerpage?email="+user_email)

@app.route("/ourtermsandconditions")
def termsandconditions():
    return render_template("termsandconditions.html")

@app.route("/instructions")
def instructions():
    return render_template("instructions.html")

@app.route("/test")
def test():
    return render_template("test.html")

@app.route("/logout")
def logout():
  session.pop("email")
  return redirect("/")

if __name__ == "__main__":
  app.run()
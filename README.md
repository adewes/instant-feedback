instant-feedback
================

This is a simple Flask application that allows you to add inline feedback elements to any website and collect user feedback on-the-fly. Just include a small code snippet in your site's HTML and add special SPAN elements to your code to dynamically create feedback widgets wherever you want.  All user input is submitted asynchronously via jQuery, so no submitting of forms is required.

Built with Bootstrap, jQuery, font-awesome and MongoDB.

For more information and examples, visit the website: http://feedback.7scientists.com

Installation
============

To run the application, you will need to install the following dependencies:

* Flask
* PyMongo
* Mongobean (https://github.com/adewes/mongobean)

Running the development server
------------------------------

```bash
cd get_feedback
python app.py
```

Have fun!

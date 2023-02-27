from website import create_app

# The IF statement validates that the 'app.py' file is run and that the code was imported from elsewhere.
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
        # The above code makes it so that every time the code is changed, the Flask web server is automatically rerun.




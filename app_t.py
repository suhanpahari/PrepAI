from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login.html')
def login():
    return render_template('login.html')

@app.route('/pricing.html')
def pricing():
    return render_template('pricing.html')

@app.route('/verification.html')
def verification():
    return render_template('verification.html')

@app.route('/interview.html')
def interview():
    return render_template('interview.html')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

from flask import Flask
from flask import jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def hello():
    return jsonify({'greeting': 'Hello from notification microservice!'})

if __name__ == '__main__':
    app.run(debug=True, port=8002)

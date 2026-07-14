from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        data = {'message': 'Hello, World!'}
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/api/endpoint', methods=['GET'])
def get_data():
    data = {'message': 'Hello, World!'}
    return jsonify(data)

if __name__ == '__main__':
    import subprocess
    import sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'flask'])
    app.run()
from flask import Flask, request, jsonify
from flask_cors import CORS
from weather_engine import check_alert

app = Flask(__name__)
CORS(app)

@app.route("/api/weather", methods=["GET"])
def weather():
    city = request.args.get("city", "Chennai")
    zone = request.args.get("zone", "MA13")
    result = check_alert(city, zone)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)

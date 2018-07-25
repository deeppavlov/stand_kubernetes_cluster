from flask import Flask, request, jsonify, redirect
from flasgger import Swagger
from flask_cors import CORS
from run_test import init_all_models


TWO_ARGUMENTS_MODELS = ['kpi2']


app = Flask(__name__)
Swagger(app)
CORS(app)

models = None


@app.route('/')
def index():
    return redirect('/apidocs/')


@app.route('/answer', methods=['POST'])
def answer_kpi2():
    """
    KPI 2: Paraphraser
    ---
    parameters:
     - name: data
       in: body
       required: true
       type: json
    """
    return answer("kpi2")


def answer(kpi_name):
    if not request.is_json:
        return jsonify({
            "error": "request must contains json data"
        }), 400

    text1 = request.get_json().get('text1') or ""
    text2 = request.get_json().get('text2') or ""

    if text1.strip() == "":
        return jsonify({
            "error": "request must contain non empty 'text1' parameter"
        }), 400

    if kpi_name in TWO_ARGUMENTS_MODELS and text2.strip() == "":
        return jsonify({
            "error": "request must contain non empty 'text2' parameter"
        }), 400

    (model, in_q, out_q) = models[kpi_name]
    in_q.put([text1, text2])
    result = out_q.get()
    if isinstance(result, dict) and result.get("ERROR"):
        return jsonify(result), 400
    return jsonify(result), 200


if __name__ == "__main__":
    models = init_all_models()
    app.run(host='0.0.0.0', port=6003, threaded=True)

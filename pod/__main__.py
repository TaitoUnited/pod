import io

from flask import abort, Flask, request, send_file

from weasyprint import CSS, HTML

application = Flask(__name__)


@application.route('/', methods=['GET'])
def status():
    return 'Welcome to P.O.D.', 200


@application.route('/', methods=['POST'])
def generate():
    html_input = request.form.get('html')
    css_input = request.form.get('css', '')

    if not html_input:
        abort(400)

    output = io.BytesIO()

    html_object = HTML(string=html_input)
    css_object = CSS(string=css_input)

    html_object.write_pdf(output, stylesheets=[css_object])

    output.seek(0)
    return send_file(output, mimetype='application/pdf')


if __name__ == '__main__':
    application.run(host='0.0.0.0')

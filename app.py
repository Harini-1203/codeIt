from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import nltk
import spacy
import re
from flask_cors import CORS

# Download necessary NLP models
nltk.download('punkt')
spacy.cli.download("en_core_web_sm")
nlp = spacy.load('en_core_web_sm')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # This will enable CORS for all origins
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(msg):
    response = process_message(msg)
    emit('response', response)
    print(response)

def extract_info(message):
    message = message.lower()
    html_elements = re.findall(r'(\d+)\s*(inputs?|submit\s*buttons?|headings?|checkboxes?)', message)
    color_match = re.search(r'background\s*color\s*(\w+)', message)
    nav_match = re.search(r'navbar', message)
    form_match = re.search(r'login\s*form', message)

    info = {
        'inputs': 0,
        'submit_buttons': 0,
        'headings': 0,
        'checkboxes': 0,
        'background_color': color_match.group(1) if color_match else None,
        'navbar': bool(nav_match),
        'login_form': bool(form_match),
        'username': False,
        'emails': 0,
        'select': False
    }

    for count, element in html_elements:
        count = int(count)
        if 'input' in element:
            info['inputs'] += count
        elif 'submit' in element:
            info['submit_buttons'] += count
        elif 'heading' in element:
            info['headings'] += count
        elif 'checkbox' in element:
            info['checkboxes'] += count

    if form_match:
        form_elements = re.findall(r'(\d+)\s*(emails?|select|username)', message)
        for count, element in form_elements:
            count = int(count)
            if 'email' in element:
                info['emails'] += count
            elif 'select' in element:
                info['select'] = True
            elif 'username' in element:
                info['username'] = True

    return info

def generate_code(info):
    html = ""
    css = ""
    js = ""

    if info['navbar']:
        html += "<nav style='background-color: {};'>\n".format(info['background_color'] if info['background_color'] else 'white')
        for i in range(info['headings']):
            html += "  <h1>Heading {}</h1>\n".format(i + 1)
        html += "</nav>\n"

    if info['login_form']:
        html += "<form>\n"
        if info['username']:
            html += "  <input type='text' placeholder='Username'>\n"
        for i in range(info['emails']):
            html += "  <input type='email' placeholder='Email {}'>\n".format(i + 1)
        if info['select']:
            html += "  <select>\n    <option>Option 1</option>\n    <option>Option 2</option>\n  </select>\n"
        for i in range(info['checkboxes']):
            html += "  <input type='checkbox'> Checkbox {}\n".format(i + 1)
        html += "</form>\n"

    if info['inputs'] or info['submit_buttons']:
        html += "<form>\n"
        for i in range(info['inputs']):
            html += "  <input type='text' placeholder='Input {}'>\n".format(i + 1)
        for i in range(info['submit_buttons']):
            html += "  <button type='submit'>Submit {}</button>\n".format(i + 1)
        html += "</form>\n"
    return html, css, js

def process_message(message):
    info = extract_info(message)
    html, css, js = generate_code(info)

    response = ""
    if html:
        response += "HTML:\n" + html
    if css:
        response += "CSS:\n" + css
    if js:
        response += "JavaScript:\n" + js

    return response.strip()

if __name__ == '__main__':
    socketio.run(app, debug=True)

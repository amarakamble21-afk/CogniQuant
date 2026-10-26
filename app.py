import csv
import os
import json
import re
import ssl
import math
import statistics
from pathlib import Path
import certifi
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
DEFAULT_GROQ_MODEL = 'openai/gpt-oss-120b'


def format_assistant_reply(text):
    text = re.sub(r'(?m)^\s*#{1,6}\s*', '', text)
    text = re.sub(r'(?m)^\s*[-*+]\s+', '• ', text)
    text = re.sub(r'(?m)^\s*>\s?', '', text)
    text = re.sub(r'(?m)^\s*(?:-{3,}|\*{3,}|_{3,})\s*$', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'[*_~`]{1,3}', '', text)
    text = re.sub(r'[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]', '', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


@app.route('/landing')
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/index')
@app.route('/app')
def home():
    disease = request.args.get('disease', 'parkinsons')
    if disease not in {'alzheimers', 'parkinsons', 'huntingtons'}:
        return jsonify({'error': 'Choose Alzheimer’s, Parkinson’s, or Huntington’s disease.'}), 400
    return render_template('index.html', selected_disease=disease)

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/api/chat/status')
def chat_status():
    return jsonify({
        'configured': bool(os.environ.get('GROQ_API_KEY')),
        'model': os.environ.get('GROQ_MODEL', DEFAULT_GROQ_MODEL)
    })

@app.route('/panel')
def panel():
    return render_template('panel.html')

@app.route('/api/chat', methods=['POST'])
def chat_completion():
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        return jsonify({'error': 'Chat is not configured. Set the GROQ_API_KEY environment variable on the server.'}), 503

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Request body must be a JSON object.'}), 400
    messages = data.get('messages')
    if not isinstance(messages, list) or not messages or len(messages) > 20:
        return jsonify({'error': 'Provide between 1 and 20 chat messages.'}), 400

    validated_messages = []
    for message in messages:
        if not isinstance(message, dict) or message.get('role') not in ('user', 'assistant'):
            return jsonify({'error': 'Each message must have a user or assistant role.'}), 400
        content = message.get('content')
        if not isinstance(content, str) or not content.strip() or len(content) > 4000:
            return jsonify({'error': 'Each message must contain 1 to 4000 characters.'}), 400
        validated_messages.append({'role': message['role'], 'content': content.strip()})
    if validated_messages[-1]['role'] != 'user':
        return jsonify({'error': 'The latest message must be from the user.'}), 400

    payload = {
        'model': os.environ.get('GROQ_MODEL', DEFAULT_GROQ_MODEL),
        'messages': [
            {
                'role': 'system',
                'content': 'You are NeuroQuant, a friendly educational assistant for a neurodegeneration research prototype. Give concise, polished general information about neuroscience and the app. Format replies as clean plain text with short paragraphs and simple bullet points when helpful. Do not use Markdown heading markers, bold/italic syntax, decorative separators, or emojis. Do not diagnose, interpret personal medical data, or recommend treatment; encourage users to consult a qualified clinician for medical concerns.'
            },
            *validated_messages
        ],
        'temperature': 0.6,
        'max_tokens': 800
    }
    groq_request = Request(
        'https://api.groq.com/openai/v1/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        method='POST'
    )
    groq_request.add_header('User-Agent', 'NeuroQuant-Research-App/1.0')
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(groq_request, timeout=30, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))
    except HTTPError as error:
        try:
            error_text = error.read().decode('utf-8')
        except UnicodeDecodeError:
            error_text = ''
        try:
            error_body = json.loads(error_text)
        except json.JSONDecodeError:
            error_body = {}
        api_message = error_body.get('error', {}).get('message') if isinstance(error_body, dict) else None
        lower_error_text = error_text.lower()
        if '1010' in lower_error_text and ('cloudflare' in lower_error_text or 'error code' in lower_error_text):
            api_message = 'Groq’s Cloudflare protection blocked this request (error 1010). The app now sends an application User-Agent; if the error persists, try a different network without a VPN/proxy or contact Groq support. Rotating the API key will not fix an IP/network block.'
        elif not isinstance(api_message, str):
            api_message = {
                401: 'The Groq API key was rejected. Check GROQ_API_KEY.',
                403: 'The Groq API denied access. Check the key permissions and network access.',
                404: 'The configured Groq model was not found. Check GROQ_MODEL.',
                429: 'The Groq API rate limit or quota was reached. Try again later.'
            }.get(error.code, 'Check the server API key and model configuration.')
        return jsonify({'error': f'Groq API request failed (HTTP {error.code}): {api_message}'}), 502
    except URLError as error:
        if isinstance(error.reason, ssl.SSLCertVerificationError):
            return jsonify({'error': 'The server could not verify the Groq API TLS certificate. Check the server certificate bundle.'}), 502
        return jsonify({'error': 'Could not connect to the Groq API. Check the server network connection and try again.'}), 502
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return jsonify({'error': 'The Groq API returned an unexpected response.'}), 502

    try:
        reply = result['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError):
        return jsonify({'error': 'The Groq API returned an unexpected response.'}), 502
    if not isinstance(reply, str) or not reply.strip():
        return jsonify({'error': 'The Groq API returned an empty response.'}), 502
    return jsonify({'reply': format_assistant_reply(reply)})

PROGRESSION_SCALES = {
    'alzheimers': {'name': 'CDR-SB', 'maximum': 18},
    'parkinsons': {'name': 'UPDRS Part III motor score', 'maximum': 108},
    'huntingtons': {'name': 'UHDRS Total Motor Score', 'maximum': 124},
}

def load_parkinsons_cohort():
    data_path = Path(__file__).resolve().parent / 'Datasets' / 'parkinsons_updrs.data'
    participants = {}
    with data_path.open(newline='', encoding='utf-8-sig') as data_file:
        for row in csv.DictReader(data_file):
            participant_id = row['subject#']
            participants.setdefault(participant_id, []).append({
                'days': float(row['test_time']),
                'score': float(row['motor_UPDRS'])
            })

    cases = []
    participant_rates = []
    all_scores = []
    for participant_id, observations in sorted(participants.items(), key=lambda item: int(item[0])):
        observations.sort(key=lambda observation: observation['days'])
        first, last = observations[0], observations[-1]
        interval_years = (last['days'] - first['days']) / 365.25
        if interval_years <= 0:
            continue
        participant_rates.append((last['score'] - first['score']) / interval_years)
        all_scores.extend(observation['score'] for observation in observations)
        cases.append({
            'label': f'Cohort example {len(cases) + 1:02d}',
            'earlier_score': round(first['score'], 2),
            'later_score': round(last['score'], 2),
            'years_between': round(interval_years, 3),
            'annualized_change': round((last['score'] - first['score']) / interval_years, 2)
        })

    ordered_rates = sorted(participant_rates)
    middle = len(ordered_rates) // 2
    lower_half = ordered_rates[:middle]
    upper_half = ordered_rates[middle + (len(ordered_rates) % 2):]
    return {
        'source': 'Oxford Parkinson’s Disease Telemonitoring Dataset (UCI, dataset 189)',
        'participants': len(cases),
        'recordings': sum(len(observations) for observations in participants.values()),
        'study_span_months': round(statistics.median(
            case['years_between'] for case in cases
        ) * 12, 1),
        'minimum_interval_years': round(min(case['years_between'] for case in cases), 3),
        'maximum_interval_years': round(max(case['years_between'] for case in cases), 3),
        'score_minimum': round(min(all_scores), 2),
        'score_maximum_observed': round(max(all_scores), 2),
        'median_endpoint_rate': round(statistics.median(participant_rates), 2),
        'middle_50_rate_minimum': round(statistics.median(lower_half), 2),
        'middle_50_rate_maximum': round(statistics.median(upper_half), 2),
        'default_case': min(
            range(len(cases)),
            key=lambda index: abs(cases[index]['annualized_change'] - statistics.median(participant_rates))
        ),
        'cases': cases
    }

@app.route('/api/progression-data')
def progression_data():
    try:
        return jsonify(load_parkinsons_cohort())
    except OSError:
        app.logger.exception('Could not read the supplied Parkinson UPDRS dataset.')
        return jsonify({'error': 'The supplied Parkinson’s cohort file could not be read.'}), 503

@app.route('/progression', methods=['POST'])
def progression():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'status': 'error', 'error': 'Request body must be a JSON object.'}), 400
    disease = data.get('disease')
    scale = PROGRESSION_SCALES.get(disease)
    if scale is None:
        return jsonify({'status': 'error', 'error': 'Choose Alzheimer’s, Parkinson’s, or Huntington’s disease.'}), 400
    try:
        earlier = float(data['earlier_score'])
        later = float(data['later_score'])
        gap = float(data['years_between'])
        horizon_value = float(data['horizon_years'])
        effect_points = float(data.get('effect_points', 0))
        effect_fraction = float(data.get('effect_fraction', 0))
        effect_window = float(data.get('effect_window_years', 1))
    except (KeyError, TypeError, ValueError, OverflowError):
        return jsonify({'status': 'error', 'error': 'Enter numeric scores, the interval, the projection range, and valid scenario settings.'}), 400
    if not all(math.isfinite(value) for value in (earlier, later, gap, effect_points, effect_fraction, effect_window)):
        return jsonify({'status': 'error', 'error': 'Scores, elapsed time, and scenario settings must be finite numbers.'}), 400
    if not 0 <= earlier <= scale['maximum'] or not 0 <= later <= scale['maximum']:
        return jsonify({'status': 'error', 'error': f"{scale['name']} scores must be between 0 and {scale['maximum']}."}), 400
    if not 0 < gap <= 50:
        return jsonify({'status': 'error', 'error': 'Time between measurements must be greater than 0 and no more than 50 years.'}), 400
    if not math.isfinite(horizon_value) or not horizon_value.is_integer():
        return jsonify({'status': 'error', 'error': 'Projection range must be a whole number of years.'}), 400
    horizon = int(horizon_value)
    if horizon not in (1, 5, 10):
        return jsonify({'status': 'error', 'error': 'Choose a projection horizon of 1, 5, or 10 years.'}), 400
    scenario_mode = data.get('scenario_mode', 'none')
    if scenario_mode not in {'none', 'study_difference'}:
        return jsonify({'status': 'error', 'error': 'Choose a supported what-if scenario model.'}), 400
    if effect_points < 0 or effect_fraction < 0 or effect_fraction > 1 or effect_window <= 0:
        return jsonify({'status': 'error', 'error': 'Scenario effect must be nonnegative, its fraction must be 0–1, and its evidence window must be positive.'}), 400

    annualized_change = (later - earlier) / gap
    years = list(range(horizon + 1))
    untreated_scores = []
    scenario_scores = []
    for year in years:
        untreated = max(0, min(scale['maximum'], later + annualized_change * year))
        if scenario_mode == 'study_difference':
            scenario_effect = effect_points * effect_fraction * min(year / effect_window, 1)
            scenario_value = later + annualized_change * year - scenario_effect
        else:
            scenario_value = later + annualized_change * year
        scenario = max(0, min(scale['maximum'], scenario_value))
        untreated_scores.append(round(untreated, 3))
        scenario_scores.append(round(scenario, 3))
    return jsonify({
        'status': 'success', 'disease': disease,
        'measure': scale['name'], 'score_maximum': scale['maximum'],
        'annualized_change': round(annualized_change, 3),
        'chart_data': {
            'observed_years': [-gap, 0],
            'observed_scores': [earlier, later],
            'projection_years': years,
            'projected_scores': untreated_scores,
            'scenario_scores': scenario_scores,
        },
        'method': 'Observed score change per year = (later score − earlier score) / elapsed years. A supported study-difference scenario subtracts the published group-average score difference through its study period; it is not an individualized treatment estimate. Scores are clamped to scale limits, and linear score extension is not a validated prognosis.'
    })

if __name__ == '__main__':
    print("\n==================================================")
    print("Launching Local Web App: http://127.0.0.1:5000/")
    print("==================================================\n")
    app.run(debug=True, port=5000)
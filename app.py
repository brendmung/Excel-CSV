from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import pandas as pd
import io
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'File Conversion API',
        'endpoints': {
            '/convert': 'POST - Convert files (csv to excel or excel to csv)',
            '/health': 'GET - Health check'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

@app.route('/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: csv, xlsx, xls'}), 400
    
    try:
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        
        # Read the file based on its type
        if file_ext == 'csv':
            df = pd.read_csv(file)
            output_ext = 'xlsx'
            output_filename = filename.rsplit('.', 1)[0] + '.xlsx'
            
            # Convert to Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            output.seek(0)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
        else:  # xlsx or xls
            df = pd.read_excel(file)
            output_ext = 'csv'
            output_filename = filename.rsplit('.', 1)[0] + '.csv'
            
            # Convert to CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            output = io.BytesIO(output.getvalue().encode('utf-8'))
            mimetype = 'text/csv'
        
        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=output_filename
        )
    
    except Exception as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

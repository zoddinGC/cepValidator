from models import Validator
from flask import Flask, request, jsonify, send_file
import pandas as pd
import io

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Check if the POST request has the file part
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']

        # Check if the file has a valid name and extension
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Ensure the file is an Excel file
        if file and file.filename.endswith('.xlsx'):
            # Read the Excel file into a DataFrame
            excel_data = pd.read_excel(file)

            # Validator to check the excel data 
            validator = Validator(dataframe=excel_data)
            validator.style_dataframe()

            # Check data
            excel_data = validator.get_dataframe()

            # Save the updated DataFrame to a new Excel file
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='openpyxl')

            excel_data.to_excel(writer, index=False)
            writer.close()
            output.seek(0)

            # Return the updated Excel file to the user
            return send_file(output, download_name='planilha_atualizada.xlsx', as_attachment=True)

        else:
            return jsonify({'error': 'Invalid file format, must be .xlsx'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

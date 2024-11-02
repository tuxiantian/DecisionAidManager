from flask import Flask, request, jsonify, send_file, Blueprint
import os
import subprocess
import uuid
import time

mermaid_bp = Blueprint('mermaid', __name__)

# Define the directory for storing temporary files
TEMP_DIR = "temp_diagrams"
os.makedirs(TEMP_DIR, exist_ok=True)

@mermaid_bp.route('/generate-mermaid', methods=['POST'])
def generate_mermaid():
    try:
        # Step 1: Get the Mermaid code from the request
        data = request.get_json()
        if not data or 'mermaid_code' not in data:
            return jsonify({"error": "Mermaid code not provided"}), 400

        mermaid_code = data['mermaid_code']

        # Step 2: Create a unique filename for the Mermaid diagram
        unique_id = str(uuid.uuid4())
        input_file = os.path.join(TEMP_DIR, f"{unique_id}.mmd")
        output_file = os.path.join(TEMP_DIR, f"{unique_id}.png")

        # Step 3: Write the Mermaid code to a temporary file
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(mermaid_code)

        # Step 4: Run the Mermaid CLI to generate the diagram
        mmdc_path = r'C:\Users\tuxia\AppData\Roaming\npm\mmdc.cmd'  # Assuming 'mmdc' is available in PATH
        subprocess.run([mmdc_path, '-i', input_file, '-o', output_file, '-f', 'png'], check=True)

        # Step 5: Send the generated diagram as a response
        return send_file(output_file, mimetype='image/png', as_attachment=True, download_name='diagram.png')
    except FileNotFoundError:
        return jsonify({"error": "Mermaid CLI (mmdc) not found. Please ensure it's installed and in your PATH."}), 500
    except subprocess.CalledProcessError:
        return jsonify({"error": "Failed to generate the Mermaid diagram."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Step 6: Clean up the temporary files
        if os.path.exists(input_file):
            os.remove(input_file)


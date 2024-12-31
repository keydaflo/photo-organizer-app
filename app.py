from flask import Flask, render_template, request, redirect, url_for
import os
import shutil
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)

# Configurations
UPLOAD_FOLDER = 'uploads'
TEMP_FOLDER = 'temp'
OUTPUT_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def rename_and_save_files(location, date, files, destination, start_index=1):
    if not os.path.exists(destination):
        os.makedirs(destination)

    # Ensure date format is YYYY-MM-DD
    try:
        year, month, day = date.split('-')
        if len(year) != 4 or len(month) != 2 or len(day) != 2:
            raise ValueError("Invalid date format")
    except ValueError:
        raise ValueError("Date must be in the format YYYY-MM-DD")

    for index, file in enumerate(files, start=start_index):
        ext = file.filename.rsplit('.', 1)[1].lower()
        new_filename = f"{year}-{month}-{day} ({index}) {location}.{ext}"
        filepath = os.path.join(destination, new_filename)
        file.save(filepath)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get user inputs
        location = request.form.get('location')
        date = request.form.get('date')
        destination_name = request.form.get('destination')
        files = request.files.getlist('files')

        if not location or not date or not destination_name:
            return "Please provide all required inputs."

        if not all(file and allowed_file(file.filename) for file in files):
            return "Ensure all uploaded files are valid images."

        destination_path = os.path.join(app.config['TEMP_FOLDER'], secure_filename(destination_name))

        if not os.path.exists(destination_path):
            os.makedirs(destination_path)

        # Count existing files to continue numbering
        existing_count = len([f for f in os.listdir(destination_path) if os.path.isfile(os.path.join(destination_path, f))])

        try:
            rename_and_save_files(location, date, files, destination_path, start_index=existing_count + 1)
        except ValueError as e:
            return str(e)

        return render_template('review.html', temp_path=destination_path, destination=destination_path)

    return render_template('index.html')

@app.route('/save-to-downloads', methods=['POST'])
def save_to_downloads():
    temp_path = request.form.get('temp_path')
    destination_name = os.path.basename(temp_path)
    final_path = os.path.join(app.config['OUTPUT_FOLDER'], destination_name)

    if os.path.exists(temp_path):
        shutil.move(temp_path, final_path)
    
    return render_template('success.html', destination=final_path)

@app.route('/add-more', methods=['POST'])
def add_more():
    destination = request.form.get('destination')

    if request.method == 'POST':
        location = request.form.get('location')
        date = request.form.get('date')
        files = request.files.getlist('files')

        if not location or not date:
            return "Please provide both location and date."

        if not all(file and allowed_file(file.filename) for file in files):
            return "Ensure all uploaded files are valid images."

        # Count existing files to continue numbering
        existing_count = len([f for f in os.listdir(destination) if os.path.isfile(os.path.join(destination, f))])

        try:
            rename_and_save_files(location, date, files, destination, start_index=existing_count + 1)
        except ValueError as e:
            return str(e)

        return render_template('review.html', temp_path=destination, destination=destination)

    return render_template('add_more_photos.html', destination=destination)

@app.route('/start-over')
def start_over():
    # Clear uploads and temp folder
    shutil.rmtree(app.config['UPLOAD_FOLDER'], ignore_errors=True)
    shutil.rmtree(app.config['TEMP_FOLDER'], ignore_errors=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
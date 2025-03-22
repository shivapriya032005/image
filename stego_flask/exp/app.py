from flask import Flask, render_template, request, send_from_directory
import os
import cv2

app = Flask(__name__)
UPLOAD_FOLDER = 'exp/static/uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Encryption function
def encrypt_message(image_path, output_path, message, password):
    img = cv2.imread(image_path)
    if img is None:
        return "Error: Could not open image."

    # Dictionary for character mapping
    d = {chr(i): i for i in range(255)}

    # Ensure message fits in image
    if len(message) > img.shape[0] * img.shape[1]:
        return "Error: Message too long for the image size."

    # Store message length in the first pixel
    img[0, 0] = [len(message), 0, 0]

    # Embed message in pixels
    n, m, z = 0, 0, 0
    for i, char in enumerate(message):
        n, m = divmod(i + 1, img.shape[1])
        img[n, m, z] = d.get(char, 0)
        z = (z + 1) % 3

    # Save encrypted image in BMP format
    success = cv2.imwrite(output_path, img)
    if not success:
        return "Error: Failed to save encrypted image."

    # Store password securely
    password_file = output_path + "_password.txt"
    with open(password_file, "w") as f:
        f.write(password)

    return None


# Decryption function
def decrypt_message(image_path, entered_password):
    if not os.path.exists(image_path):
        return "Error: Encrypted image file not found."

    img = cv2.imread(image_path)
    if img is None:
        return "Error: Could not open or find the image."

    # Check if password file exists
    password_file = image_path + "_password.txt"
    if not os.path.exists(password_file):
        return "Error: Password file missing."

    # Read stored password
    with open(password_file, "r") as f:
        stored_password = f.read().strip()

    # Password verification
    if entered_password != stored_password:
        return "Error: Incorrect password. Access denied!"

    # Dictionary for reverse character mapping
    c = {i: chr(i) for i in range(255)}

    # Read message length
    msg_length = img[0, 0, 0]

    n, m, z = 0, 0, 0
    message = ""

    for i in range(msg_length):
        n, m = divmod(i + 1, img.shape[1])
        message += c.get(img[n, m, z], '')
        z = (z + 1) % 3

    return message if message else "Error: No hidden message found."


# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/encrypt', methods=['GET', 'POST'])
def encrypt():
    if request.method == 'POST':
        image = request.files['image']
        message = request.form['message']
        password = request.form['password']

        input_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        output_filename = 'encrypted_' + os.path.splitext(image.filename)[0] + '.bmp'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        image.save(input_path)

        error = encrypt_message(input_path, output_path, message, password)
        if error:
            return render_template('encrypt.html', error=error)

        return render_template('encrypt.html', success=True, output_image=output_filename)

    return render_template('encrypt.html')


@app.route('/decrypt', methods=['GET', 'POST'])
def decrypt():
    if request.method == 'POST':
        image = request.files['image']
        password = request.form['password']

        input_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(input_path)

        result = decrypt_message(input_path, password)
        return render_template('decrypt.html', result=result)

    return render_template('decrypt.html')


@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)

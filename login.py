from keras.models import load_model
from flask import Flask, redirect, request, render_template, url_for, jsonify, session

import numpy as np
import csv
import os
from time import sleep
from threading import Thread
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

app = Flask(__name__)
app.secret_key = '9f7c6d5b4a3e2f1'

model = load_model('model/diabetes_lstm.h5')

def predict_from_csv(file_path):
    results = []
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        last_row = None
        for row in reader:
            last_row = row
        if last_row is not None:
            values = [float(x) for x in last_row]
            values = np.array(values).reshape(1, 8, 1)

            prediction = model.predict(values)
            if prediction[0][0] > 0.5:
                result = 'Tendo em conta o limite da glicose no sangue entre 70 a 140 mg/dl, e o os valores apresentados é PROVÁVEL que tenha uma variação de insulina que afetará os níveis de glicose no sangue.'
            else:
                result = 'Os niveis de glicose no sangue continuarão estáveis'
            results.append({'data': row, 'result': result})
    return results


def predict_from_csv_interval(file_path, interval=30):  # Intervalo de 300 segundos (5 minutos)
    while True:
        results = predict_from_csv(file_path)
        print("Resultado para os dados do CSV:")
        for result in results:
            print(result)
        sleep(interval)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/index')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

@app.route('/predict', methods=['POST'])
def predict():
    user_data = read_user_data()
    form_data = {
            'glucose': float(request.form['glucose']),
            'blood_pressure': float(request.form['blood_pressure']),
            'insulin': float(request.form['insulin']),
            'gravidez': float(user_data.get('gravidez')), 
            'imc': float(user_data.get('imc')), 
            'espessura_pele': float(user_data.get('espessura_pele')), 
            'dpf': float(user_data.get('dpf')), 
            'idade': int(user_data.get('idade'))  
        }
    
    values = [float(x) for x in form_data.values()]
    values = np.array(values).reshape(1, 8, 1)

    prediction = model.predict(values)
    if prediction[0][0] > 0.5:
       #result = 'É provável que em 30 minutos à 1 hora tenha uma variação que afetará os niveis de insulina no sangue'
       result = 'Tendo em conta o limite da glicose no sangue entre 70 a 140 mg/dl, e o os valores apresentados é PROVÁVEL que tenha uma variação de insulina que afetará os níveis de glicose no sangue.'
    else:
        result = 'Os niveis de glicose no sangue continuarão estáveis'
    return render_template('index.html', result=result)

def verify_credentials(username, password):
    with open('users.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            if row[0] == username and row[1] == password:
                return True
        return False
    
@app.route('/logout')
def logout():
    session.pop('username', None) 
    return redirect(url_for('login'))
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        entered_username = request.form['username']
        entered_password = request.form['password']
        
        if verify_credentials(entered_username, entered_password):
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        else:
            error = 'Invalid credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/register', methods=['POST'])
def register():
    # Recuperar os dados do formulário de registro
    reg_username = request.form['reg_username']
    reg_password = request.form['reg_password']
    reg_email = request.form['reg_email']
    if 'reg_gravidez' in request.form:
        reg_gravidez = request.form['reg_gravidez']
    else:
        reg_gravidez = 0  # Defina um valor padrão de 0 quando 'reg_gravidez' não está presente

    reg_imc = request.form['reg_imc']
    reg_espe_pele = request.form['reg_espe_pele']
    reg_dpf = request.form['reg_dpf']
    reg_idade = request.form['reg_idade']

    # Salvar os dados do usuário em algum lugar (por exemplo, em um arquivo CSV)
    with open('users.csv', 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([reg_username, reg_password, reg_email,reg_gravidez, reg_imc,reg_espe_pele, reg_dpf, reg_idade])

    # Redirecionar para a página de login após o registro
    return redirect(url_for('login'))


@app.route('/visualizar_dados')
def visualizar_dados():
    if 'username' not in session:
        return redirect(url_for('login'))
    data = []  
    with open('dados_formulario.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip the first row (header)
        for row in csv_reader:
            data.append(row)
    return render_template('data_display.html', data=data)
@app.route('/delete_data', methods=['POST'])
def delete_data():
    try:
        row_index = int(request.form['row_index'])
        # Implement the logic to delete the data row at the specified index
        # You can update the 'dados_formulario.csv' or your data storage accordingly
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/monitor')
def monitor():
    thread = Thread(target=predict_from_csv_interval, args=('dados_formulario.csv',))
    thread.start()
    return render_template('templates/monitor.html')

@app.route('/predict_from_csv', methods=['GET'])
def predict_from_csv_route():
    results = predict_from_csv('dados_formulario.csv')
    return jsonify(results)

def get_user_email(username):
    with open('users.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0] == username:
                return row[2]  # Índice 2 representa o email no CSV
    return None

@app.route('/predict_send_email', methods=['GET'])
def send_email():
    results = predict_from_csv('dados_formulario.csv')
    if 'username' in session:
        username = session['username']
        email = get_user_email(username)
        if email:
            # Formatar os resultados para o corpo do email
            email_body = "Resultados da Previsão de Diabetes:\n\n"
            for result in results:
                data_fields = ["Glicose", "Pressão sanguinea", "insulina", "gravidez", "Espessura da pele", "Indice da massa corporal", "DPF", "Idade"]

                data_values = result['data']
                formatted_data = "\n".join([f"{field}: {value}" for field, value in zip(data_fields, data_values)])
                email_body += f"{formatted_data}\nResultados:\n{result['result']}\n\n"

            # Configurações do email
            sender_email = 'danielproemio@gmail.com'
            sender_password = 's m x c l bsxd t w p g l c q'
            sender_password = 'hrzz qiaj qiyc maxu'
            receiver_email =email #'stanybless@gmail.com'

            # Criar a mensagem do email
            subject = 'Resultados da Previsão de Diabetes'
            message = MIMEText(email_body, _charset='utf-8')
            message['Subject'] = Header(subject, 'utf-8')
            message['From'] = sender_email
            message['To'] = email

            # Conectar ao servidor SMTP e enviar o email
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, receiver_email, message.as_string())
                server.quit()
                return render_template('index.html')
            except Exception as e:
                return jsonify({'error': str(e)})

def read_user_data():
    user_data = {}  # Criar um dicionário para armazenar os dados do usuário
    try:
        with open('users.csv', newline='') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                user_data = row  # Substituir user_data pelo último registro no CSV
    except FileNotFoundError:
        user_data = {}  # Se o arquivo users.csv não existir, inicie com um dicionário vazio
    return user_data
@app.route('/save_data', methods=['POST'])
def save_data():
    try:
        user_data = read_user_data()  # Obter os dados do usuário a partir de users.csv
        print(user_data)
        print(user_data.get('gravidez'))
        data = [
              
            request.form['glicose'],
            request.form['pressao_sanguinea'],
            request.form['insulina'],
            user_data.get('gravidez'),
            user_data.get('imc'),
            user_data.get('espessura_pele'),
            user_data.get('dpf'),
            user_data.get('idade'),
        ]
        print(data)
        with open('dados_formulario.csv', 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(data)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)})
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Obtenha os dados enviados no formulário de edição
        new_password = request.form['new_password']
        new_email = request.form['new_email']
        new_gravidez = request.form['new_gravidez']
        new_imc = request.form['new_imc']
        new_espe = request.form['new_espe']
        new_dpf = request.form['new_dpf']
        new_idade = request.form['new_idade']

        # Atualize os dados do usuário no arquivo users.csv
        username = session['username']
        with open('users.csv', 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            users = list(csv_reader)

        for user in users:
            if user[0] == username:
                user[1] = new_password   
                user[2] = new_email     
                user[3] = new_gravidez     
                user[4] = new_imc     
                user[5] = new_espe     
                user[6] = new_dpf     
                user[7] = new_idade     

        with open('users.csv', 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerows(users)

        return redirect(url_for('index'))

    return render_template('edit_profile.html')


@app.route('/monitor_content', methods=['GET'])
def monitor_content():
    with open('templates/monitor.html', 'r',encoding='utf-8') as monitor_file:
        content = monitor_file.read()
    return content



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
    




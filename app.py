 
# Carrega o modelo LSTM salvo anteriormente
from keras.models import load_model

from flask import Flask, render_template, request
import numpy as np

app = Flask(__name__)
model = load_model('model/diabetes_lstm.h5')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    values = [float(x) for x in request.form.values()]
    values = np.array(values).reshape(1, 8, 1)
    prediction = model.predict(values)
    if prediction[0][0] > 0.5:
        result = 'positivo'
    else:
        result = 'negativo'
    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)



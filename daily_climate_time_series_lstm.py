# -*- coding: utf-8 -*-
"""Daily Climate Time Series LSTM.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1xvdElHJUVK0_s5A534UYpsm8nZxErreI
"""

from google.colab import files

uploaded = files.upload()

for fn in uploaded.keys():
  print('User uploaded file "{name}" with length {length} bytes'.format(
      name=fn, length=len(uploaded[fn])))
  
# Then move kaggle.json into the folder where the API expects to find it.
!mkdir -p ~/.kaggle/ && mv kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json

!kaggle datasets download -d sumanthvrao/daily-climate-time-series-data

!unzip daily-climate-time-series-data.zip

"""# Import Library"""

import numpy as np
import pandas as pd 
import tensorflow as tf
from dateutil.parser import parse
dateparse=lambda dates:parse(dates)
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.layers import LSTM,Dense,Bidirectional,Dropout
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

"""# Load Data Test and Train"""

clim_test = pd.read_csv('/content/DailyDelhiClimateTest.csv',
                         parse_dates=['date'],date_parser=dateparse)
clim_test.head()

clim_train = pd.read_csv('/content/DailyDelhiClimateTrain.csv',
                         parse_dates=['date'],date_parser=dateparse)
clim_train.head()

"""# Check General Data Test and Train Info"""

print(clim_train.info())
print(clim_test.info())

# Check missing value
print(clim_train.isnull().sum())
print(clim_test.isnull().sum())

# Check shape
print(clim_train.shape)
print(clim_test.shape)

# plot daily climate 
date = clim_train['date'].values
wind_speed  = clim_train['wind_speed'].values
 
 
plt.figure(figsize=(14,4))
plt.plot(date, wind_speed)
plt.title('Temperature average',
          fontsize=18);

"""# Split Data"""

x_train, x_test , y_train, y_test  = train_test_split(wind_speed, date, test_size=0.2)
print("Total Data Train: ", len(x_train))
print("Total Data Test: ", len(x_test))

def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    ds = ds.shuffle(shuffle_buffer)
    ds = ds.map(lambda w: (w[:-1], w[-1:]))
    return ds.batch(batch_size).prefetch(1)

train_check = windowed_dataset(x_train, window_size=33, batch_size=50, shuffle_buffer=500)

val_check = windowed_dataset(x_test, window_size=33, batch_size=50, shuffle_buffer=500)

model = tf.keras.models.Sequential([
  tf.keras.layers.Conv1D(filters=32, kernel_size=5,
                      strides=1, padding="causal",
                      activation="relu",
                      input_shape=[None, 1]),
  tf.keras.layers.LSTM(64, return_sequences=True),
  tf.keras.layers.LSTM(64, return_sequences=True),
  tf.keras.layers.Dense(30, activation="relu"),
  tf.keras.layers.Dense(10, activation="relu"),
  tf.keras.layers.Dense(1),
  tf.keras.layers.Lambda(lambda x: x * 100)
])

Mae = (clim_train['wind_speed'].max() - clim_train['wind_speed'].min()) * 10/100
print(Mae)

class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('mae')<1.79 and logs.get('val_mae')<1.79):
      print("\nMAE < 10% data scale")
      self.model.stop_training = True
callbacks = myCallback()

lr_schedule = tf.keras.callbacks.LearningRateScheduler(
    lambda epoch: 1e-8 * 10**(epoch / 20))

optimizer = tf.keras.optimizers.SGD(learning_rate=1e-8, momentum=0.9)
model.compile(loss=tf.keras.losses.Huber(),
              optimizer=optimizer,
              metrics=["mae"])

history_lstm = model.fit(train_check, epochs=100, validation_data = val_check, callbacks=[lr_schedule, callbacks])

# Plot Accuracy
plt.plot(history_lstm.history['mae'])
plt.plot(history_lstm.history['val_mae'])
plt.title('Accuracy Model')
plt.ylabel('Mae')
plt.xlabel('epoch')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.show()

# Plot Loss
plt.plot(history_lstm.history['loss'])
plt.plot(history_lstm.history['val_loss'])
plt.title('Loss Model')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.show()
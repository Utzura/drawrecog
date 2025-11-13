import json
import paho.mqtt.client as mqtt

    client1= paho.Client("z4m")                           
    client1.on_publish = on_publish                          
    client1.connect(broker,port)  
    message =json.dumps({"Act1":choice})
    ret= client1.publish("cmqtt_z4m", message)

broker="broker.mqttdashboard.com"
port=1883
client1= paho.Client("z4m")
client1.on_message = on_message

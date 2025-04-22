#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// WiFi and MQTT settings
const char* ssid = "JARVIS";
const char* password = "jarvis$100";
const char* mqtt_server = "192.168.43.4";
const int mqtt_port = 1883;

// DHT11 settings
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// MQ135 settings
#define MQ135PIN 34

// MQTT topics
const char* tempTopic = "home/sensors/temperature";
const char* humidTopic = "home/sensors/humidity";
const char* airQualityTopic = "home/sensors/air_quality";

// Device control topics for subscription
const char* acControlTopic = "home/devices/ac";
const char* purifierControlTopic = "home/devices/purifier";
const char* dehumidifierControlTopic = "home/devices/dehumidifier";

// Relay pins for controlling devices
#define AC_RELAY_PIN 5   // 16
#define PURIFIER_RELAY_PIN 17
#define DEHUMIDIFIER_RELAY_PIN 18

WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastSensorReadTime = 0;
const long sensorReadInterval = 10000; // Read sensors every 10 seconds

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  payload[length] = '\0';
  String message = String((char*)payload);
  
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(message);

  // Control devices based on commands
  if (String(topic) == acControlTopic) {
    digitalWrite(AC_RELAY_PIN, message == "ON" ? HIGH : LOW);
  } else if (String(topic) == purifierControlTopic) {
    digitalWrite(PURIFIER_RELAY_PIN, message == "ON" ? HIGH : LOW);
  } else if (String(topic) == dehumidifierControlTopic) {
    digitalWrite(DEHUMIDIFIER_RELAY_PIN, message == "ON" ? HIGH : LOW);
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      
      // Subscribe to device control topics
      client.subscribe(acControlTopic);
      client.subscribe(purifierControlTopic);
      client.subscribe(dehumidifierControlTopic);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  // Initialize DHT sensor
  dht.begin();
  
  // Initialize relay pins
  pinMode(AC_RELAY_PIN, OUTPUT);
  pinMode(PURIFIER_RELAY_PIN, OUTPUT);
  pinMode(DEHUMIDIFIER_RELAY_PIN, OUTPUT);
  
  // Set relays to OFF initially
  digitalWrite(AC_RELAY_PIN, LOW);
  digitalWrite(PURIFIER_RELAY_PIN, LOW);
  digitalWrite(DEHUMIDIFIER_RELAY_PIN, LOW);
  
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void readAndPublish() {
  // Read temperature and humidity
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  // Read air quality from MQ135
  int airQualityRaw = analogRead(MQ135PIN);
  // Convert raw value to PPM (approximate)
  // This is a simple conversion - may need calibration for accurate results
  float airQualityPPM = map(airQualityRaw, 0, 4095, 0, 1000);
  
  // Check if readings are valid
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }
  
  // Print values to serial
  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.print(" °C, Humidity: ");
  Serial.print(humidity);
  Serial.print(" %, Air Quality: ");
  Serial.print(airQualityPPM);
  Serial.println(" PPM");
  
  // Publish to MQTT topics
  client.publish(tempTopic, String(temperature).c_str());
  client.publish(humidTopic, String(humidity).c_str());
  client.publish(airQualityTopic, String(airQualityPPM).c_str());
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Read sensors at regular intervals
  unsigned long currentMillis = millis();
  if (currentMillis - lastSensorReadTime >= sensorReadInterval) {
    lastSensorReadTime = currentMillis;
    readAndPublish();
  }
}

#include <Arduino.h>

void setup() {
  // put your setup code here, to run once:
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(9600);

  while(!Serial) {
    delay(1);
  }
  Serial.println("*****");
  Serial.println("");
  Serial.println("");
  Serial.println("");
  Serial.println("Hello from Arduino Firmware!");
}

void loop() {
  // put your main code here, to run repeatedly:

  Serial.println("Echo from the Arduino Firmware Image.");
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  Serial.println("Echo from the Arduino Firmware Image.");
  digitalWrite(LED_BUILTIN, LOW);
  delay(1000);
}

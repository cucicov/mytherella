const int pinPot1 = 0;
const int pinPot2 = 1;
int prevInput1 = 0;
int prevInput2 = 0;
int inputValue1;
int inputValue2;


void setup() {
  Serial.begin(9600);
}

void
loop() {

  int inputValue1 = analogRead(pinPot1);
  int inputValue2 = analogRead(pinPot2);

  if (inputValue1 != prevInput1 && inputValue2 != prevInput2) {
    Serial.print(inputValue1); 
    Serial.println(-1 * inputValue2);
  }
  
  prevInput1 = inputValue1;
  prevInput1 = inputValue2;

  delay(100);

}

const int pinPot1 = 0;
const int pinPot2 = 1;
int prevInput1 = 0;
int prevInput2 = 0;
int inputValue1;
int inputValue2;

const int numReadings = 10;
int readIndex = 0;              // the index of the current reading

int readings1[numReadings];      // the readings from the analog input
int total1 = 0;                  // the running total
int average1 = 0;                // the average

int readings2[numReadings];      // the readings from the analog input
int total2 = 0;                  // the running total
int average2 = 0;                // the average


void setup() {
  Serial.begin(9600);
  for (int thisReading = 0; thisReading < numReadings; thisReading++) {
    readings1[thisReading] = 0;
    readings2[thisReading] = 0;
  }
}

void
loop() {
  
  int inputValue1 = analogRead(pinPot1);
  int inputValue2 = analogRead(pinPot2);
  
  // data smoothing
  total1 = total1 - readings1[readIndex];

  readings1[readIndex] = inputValue1;
  // add the reading to the total:
  total1 = total1 + readings1[readIndex];

  // calculate the average:
  average1 = total1 / numReadings;

  // %%%%

  total2 = total2 - readings2[readIndex];

  readings2[readIndex] = inputValue2;
  // add the reading to the total:
  total2 = total2 + readings2[readIndex];

  // calculate the average:
  average2 = total2 / numReadings;


  // ***

  // advance to the next position in the array:
  readIndex = readIndex + 1;

  // if we're at the end of the array...
  if (readIndex >= numReadings) {
    // ...wrap around to the beginning:
    readIndex = 0;
  }

  // ------------------

  if (inputValue1 != prevInput1 && inputValue2 != prevInput2 && readIndex == 0) {
    Serial.print(average1); 
    Serial.println(-1 * average2);
  }
  
  prevInput1 = inputValue1;
  prevInput1 = inputValue2;

  delay(10);
}

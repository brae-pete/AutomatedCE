
String inputString = "";   // a String to hold incoming data
int8_t inputBytes[4];
int inputCount = 0;
bool stringComplete = false;  // whether the string is complete
bool byteRead = false;
unsigned long inputSignal = 0;


// PowerStep01 Motor Library 
#include <powerSTEP01ArduinoLibrary.h>
#include <SPI.h>

SPISettings powerstep1(200000, MSBFIRST, SPI_MODE3);

// Pin definitions for the X-NUCLEO-IHM03A1 connected to an Uno-compatible board
#define nCS_PIN 41
#define STCK_PIN 9
#define nSTBY_nRESET_PIN 8
#define nBUSY_PIN 32
// Set up variables for motors
int outlet_div = 2;
// Set variables for Pressure
int SOLENOID1 = 23;
int SOLENOID2 = 29;

// powerSTEP library instance, parameters are distance from the end of a daisy-chain
// of driver1s, !CS pin, !STBY/!Reset pin
powerSTEP driver1(0, nCS_PIN, nSTBY_nRESET_PIN);



void setup() {

  // initialize serial:
  Serial.begin(115200);
  // reserve 200 bytes for the inputString:
  inputString.reserve(200);
  // Prepare Pins for SPI
  pinMode(nSTBY_nRESET_PIN, OUTPUT);
  pinMode(nCS_PIN, OUTPUT);
  pinMode(MOSI, OUTPUT); 
  pinMode(MISO, OUTPUT);
  pinMode(SCK, OUTPUT);

 // Prepare Pin for Pressure
  pinMode(SOLENOID1, OUTPUT);
  pinMode(SOLENOID2, OUTPUT);
  digitalWrite(SOLENOID1,HIGH);
  digitalWrite(SOLENOID2,HIGH);
  pinMode(3, INPUT_PULLUP);
  
  // Reset powerSTEP and set CS
  digitalWrite(nSTBY_nRESET_PIN, HIGH);
  digitalWrite(nSTBY_nRESET_PIN, LOW);
  delay(0.2);
  digitalWrite(nSTBY_nRESET_PIN, HIGH);
  digitalWrite(nCS_PIN, HIGH);
  // Start SPI
  SPI.begin();
  SPI.setDataMode(SPI_MODE3);
}
void loop() {
  // print the string when a newline arrives:
  if (stringComplete) {
    Serial.println(inputString);
   
    Serial.println("DATA: ");
    Serial.println(inputSignal);
    Serial.println(" :END DATA"); 
    if (inputString[0]=='M'){
      motorTalk();
    }else if (inputString[0]=='P'){
      pressureTalk();
    }
    // clear the string:
    inputString = "";
    stringComplete = false;
  }
}

/*
  SerialEvent occurs whenever a new data comes in the hardware serial RX. This
  routine is run between each time loop() runs, so using delay inside loop can
  delay response. Multiple bytes of data may be available.
*/
void serialEvent() {
  while (Serial.available()) {
    
    // get the new byte:
    if (byteRead == true){
      inputBytes[inputCount]=Serial.read();
      inputCount =inputCount +1;
      inputSignal = Serial.read();
      if (inputCount>3){
        inputSignal =0;
        // Convert our 4 bytes to 32ByteMessage
        unsigned long sID = ((unsigned long)(inputBytes[0]) << 24)
           | ((unsigned long)(inputBytes[1]) << 16)
           | ((unsigned long)(inputBytes[2]) << 8)
           | inputBytes[3];
        //inputSignal += inputBytes[3];
        byteRead = false;
        
        inputCount = 0;
        Serial.println("starting SPI");
        Serial.println(sID,HEX);
        digitalWrite(nCS_PIN, LOW);
        SPI.beginTransaction(SPISettings(400000,MSBFIRST,SPI_MODE0));
        SPI.transfer(&sID,4);
        Serial.println(sID,HEX);
        inputSignal = sID;
        SPI.endTransaction();
        digitalWrite(nCS_PIN,HIGH);
        Serial.println("EndingSPI");
      }
    }
    else{
      char inChar = (char)Serial.read();
      // add it to the inputString:
      // if the incoming character is a newline, set a flag so the main loop can
      // do something about it:
      if (inChar == 'S'){
        byteRead = true;
        inputString+=inChar;
      }
      else if (inChar == '\n') {
        stringComplete = true;
      } else{
        inputString += inChar;
      }
  }
}
}

void motorTalk(){
  // If the motor command (M) was issued determine the channel, and the command. 
  // M0L+000100 Move to step position 100 for motor channel 0. 
  // Commands: L+0000 Move to position
  // L? Request Postion
  // H Set home/origin position 
  // S+00000 set speed
  int chnl = atoi(inputString[1]);
  if (inputString[2]=='L'){
    if (inputString[3]=='?'){
      getMotorPos();
    } else {
    moveMotor();
    }
  }
  else if (inputString[2]=='H'){
    setHome();
  } else if (inputString[2]=='S'){
    setMotorSpeed();
  } else if (inputString[2]=='R'){
    resetDriver();
  }
}

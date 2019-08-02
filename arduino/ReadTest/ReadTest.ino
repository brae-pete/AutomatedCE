
String inputString = "";   // a String to hold incoming data
int inputBytes[4];
int inputCount = 0;
bool stringComplete = false;  // whether the string is complete
bool byteRead = false;


// PowerStep01 Motor Library 
#include <powerSTEP01ArduinoLibrary.h>
#include <SPI.h>

// Pin definitions for the X-NUCLEO-IHM03A1 connected to an Uno-compatible board
#define nCS_PIN 10
#define STCK_PIN 9
#define nSTBY_nRESET_PIN 8
#define nBUSY_PIN 4
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
  
  // Reset powerSTEP and set CS
  digitalWrite(nSTBY_nRESET_PIN, HIGH);
  digitalWrite(nSTBY_nRESET_PIN, LOW);
  digitalWrite(nSTBY_nRESET_PIN, HIGH);
  digitalWrite(nCS_PIN, HIGH);
  // Start SPI
  SPI.begin();
  SPI.setDataMode(SPI_MODE3);
  
  // Configure powerSTEP
  driver1.SPIPortConnect(&SPI); // give library the SPI port (only the one on an Uno)
  
  driver1.configSyncPin(nBUSY_PIN, 0); // use SYNC/nBUSY pin as nBUSY, 
                                     // thus syncSteps (2nd paramater) does nothing
                                     
  driver1.configStepMode(STEP_FS_2); // 1/128 microstepping, full steps = STEP_FS,
                                // options: 1, 1/2, 1/4, 1/8, 1/16, 1/32, 1/64, 1/128
                                
  driver1.setMaxSpeed(1200); // max speed in units of full steps/s 
  driver1.setFullSpeed(2000); // full steps/s threshold for disabling microstepping
  //driver1.setMinSpeed();
  driver1.setAcc(6000); // full steps/s^2 acceleration
  driver1.setDec(6000); // full steps/s^2 deceleration
  
  driver1.setSlewRate(SR_980V_us); // faster may give more torque (but also EM noise),
                                  // options are: 114, 220, 400, 520, 790, 980(V/us)
                                  
  driver1.setOCThreshold(8); // over-current threshold for the 2.8A NEMA23 motor
                            // used in testing. If your motor stops working for
                            // no apparent reason, it's probably this. Start low
                            // and increase until it doesn't trip, then maybe
                            // add one to avoid misfires. Can prevent catastrophic
                            // failures caused by shorts
  driver1.setOCShutdown(OC_SD_ENABLE); // shutdown motor bridge on over-current event
                                      // to protect against permanant damage
  
  driver1.setPWMFreq(PWM_DIV_1, PWM_MUL_2); // 16MHz*0.75/(512*1) = 23.4375kHz 
                            // power is supplied to stepper phases as a sin wave,  
                            // frequency is set by two PWM modulators,
                            // Fpwm = Fosc*m/(512*N), N and m are set by DIV and MUL,
                            // options: DIV: 1, 2, 3, 4, 5, 6, 7, 
                            // MUL: 0.625, 0.75, 0.875, 1, 1.25, 1.5, 1.75, 2
                            
  driver1.setVoltageComp(VS_COMP_DISABLE); // no compensation for variation in Vs as
                                          // ADC voltage divider is not populated
                                          
  driver1.setSwitchMode(SW_USER); // switch doesn't trigger stop, status can be read.
                                 // SW_HARD_STOP: TP1 causes hard stop on connection 
                                 // to GND, you get stuck on switch after homing
                                      
  driver1.setOscMode(INT_16MHZ); // 16MHz internal oscillator as clock source

  // KVAL registers set the power to the motor by adjusting the PWM duty cycle,
  // use a value between 0-255 where 0 = no power, 255 = full power.
  // Start low and monitor the motor temperature until you find a safe balance
  // between power and temperature. Only use what you need
  driver1.setRunKVAL(255);
  driver1.setAccKVAL(255);
  driver1.setDecKVAL(125);
  driver1.setHoldKVAL(32);

  driver1.setParam(ALARM_EN, 0x8F); // disable ADC UVLO (divider not populated),
                                   // disable stall detection (not configured),
                                   // disable switch (not using as hard stop)

  driver1.getStatus(); // clears error flags
}

void loop() {
  // print the string when a newline arrives:
  if (stringComplete) {
    Serial.println(inputString);
    //Serial.println((int)driver1.getStatus(), HEX);
    //int i;
    //for (i = 0; i < 4; i = i + 1) {
    //  Serial.println(inputBytes[i]);
    //  }
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
      inputCount = inputCount +1;
      Serial.println(inputBytes[inputCount-1]);
      if (inputCount>3){
        byteRead = false;
        inputCount = 0;
      }
    }
    else{
      char inChar = (char)Serial.read();
      // add it to the inputString:
      // if the incoming character is a newline, set a flag so the main loop can
      // do something about it:
      if (inChar == 'S'){
        byteRead = true;
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

void moveMotor(){
  // Move the motor to specified position.
  int chnl = atoi(inputString[1]);
  String location = inputString.substring(3,10);
  float steps = location.toFloat();
  //#Serial.print("Move Motor ");
  //#Serial.print(inputString[1]);
  //#Serial.print(" To Location: ");
  Serial.println(steps);
  steps = int(steps/8.*200.*outlet_div);
  driver1.goTo(steps);
}


void getMotorPos(){
  int chnl = atoi(inputString[1]);
  //Serial.print("Get Motor  Position for channel ");
  //Serial.print(chnl);
  //Serial.println(": ");
  long steps = driver1.getPos();
  steps = steps/2;
  Serial.println(steps);
}

void setHome(){
  int chnl = atoi(inputString[1]);
  //Serial.print("Setting Home Position for channel: ");
  Serial.println(chnl);
  driver1.resetPos();
}

void setMotorSpeed(){
  int chnl = atoi(inputString[1]);
  String location = inputString.substring(3,8);
  int stepspersec = location.toInt();
  //Serial.print(" Setting speed ");
  //Serial.print(stepspersec);
  //Serial.print(" for channnel: ");
  //Serial.println(chnl);
  driver1.setMaxSpeed(stepspersec);
}

void pressureTalk(){
  int chnl = atoi(inputString[1]);
  //Serial.print("Setting Pressure ");
  //Serial.print(chnl);
  //Serial.println(": ");
  //Serial.println(inputString[2]);
  if (inputString[2]=='R'){
    Serial.println("ON");
    digitalWrite(SOLENOID2,LOW);  
    digitalWrite(SOLENOID1,HIGH);
  } else if(inputString[2]=='L'){
    digitalWrite(SOLENOID2,HIGH);
    digitalWrite(SOLENOID1,LOW);
    Serial.println("OFF");
  } else if(inputString[2]=='X'){
    digitalWrite(SOLENOID1,LOW);
    digitalWrite(SOLENOID2,LOW);
    Serial.println("All OPEN");
  } else if (inputString[2]=='C'){
    digitalWrite(SOLENOID1, HIGH);
    digitalWrite(SOLENOID2, HIGH);
    Serial.println("All CLOSED");
  }
}

void resetDriver(){
  digitalWrite(nSTBY_nRESET_PIN, HIGH);
  digitalWrite(nSTBY_nRESET_PIN, LOW);
  digitalWrite(nSTBY_nRESET_PIN, HIGH);
  digitalWrite(nSTBY_nRESET_PIN, LOW);
  digitalWrite(nCS_PIN, HIGH);
}

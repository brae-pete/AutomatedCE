#include <QuickMedianLib.h>

// Program demonstrating how to control a powerSTEP01-based ST X-NUCLEO-IHM03A1 
// stepper motor driver shield on an Arduino Uno-compatible board
// If you copy the powerSTEP01_Arduino_Library from git hub you must change the 
// contstuctors for the drivers so that it does not add _numboards for every new instance
// I did not daisy chain the nucleos so that will mess it up. 
// you can copy the library on this computer or change constructors to _numboards = 1


// AT the moment 10 mm travel on the microscope objective. 
// use the big nob to move the objective to center 
// Send move to zero command (0)
// Move objective to bottom using big nobs
// Move objective up by sending 1000. (6000 is close to stage)
// change INVERT_INPUT -1/+1 if motor goes backwards. 



#include <powerSTEP01ArduinoLibrary.h>
#include <SPI.h>
#include <QuickMedianLib.h>

// Pin definitions for the X-NUCLEO-IHM03A1 connected to an Uno-compatible board
#define nCS_PIN_2 10
#define STCK_PIN_2 9
#define nSTBY_nRESET_PIN_2 8
#define nBUSY_PIN_2 4
#define flag_2 2

#define LED_R A0
#define LED_G A1
#define LED_B A2
#define LIMIT 3
// powerSTEP library instance, parameters are distance from the end of a daisy-chain
// of drivers, !CS pin, !STBY/!Reset pin

// powerSTEP library instance, parameters are distance from the end of a daisy-chain
// of drivers, !CS pin, !STBY/!Reset pin
powerSTEP driver_2(0, nCS_PIN_2, nSTBY_nRESET_PIN_2, nBUSY_PIN_2);


// Set up variables for motors
int outlet_div = 32;
// Set variables for Pressure
int SOLENOID1 = 4;
int SOLENOID2 = 6;
int SOLENOID3 = 7;


byte dir = B0;
//SERIAL 
String inputString = "";   // a String to hold incoming data
int inputCount = 0;
bool stringComplete = false;  // whether the string is complete
bool inversion = 0;
unsigned long switch_time = 0;
bool first = true;

#define CHECK_BIT(var,pos) ((var) & (1<<(pos)))




void setup() 
{
  // Start serial
  Serial.begin(1000000);
  Serial.println("powerSTEP01 Arduino control initialising...");

  // Prepare pins
  pinMode(nSTBY_nRESET_PIN_2, OUTPUT);
  pinMode(nCS_PIN_2, OUTPUT);
  pinMode(MOSI, OUTPUT);
  pinMode(MISO, OUTPUT);
  pinMode(SCK, OUTPUT);
  pinMode(LED_R, OUTPUT);
  pinMode(LED_G, OUTPUT);
  pinMode(LED_B, OUTPUT);
  pinMode(SOLENOID1, OUTPUT);
  pinMode(SOLENOID2, OUTPUT);
  pinMode(SOLENOID3, OUTPUT);

  pinMode(LIMIT, INPUT);
  pinMode(LIMIT, INPUT_PULLUP);  // set pull-up on analog pin 0 
  //digitalWrite(LIMIT, HIGH);
  pinMode(A5, OUTPUT);
  digitalWrite(A5,LOW);


  // Reset powerSTEP and set CS
  digitalWrite(nSTBY_nRESET_PIN_2, HIGH);
  digitalWrite(nSTBY_nRESET_PIN_2, LOW);
  digitalWrite(nSTBY_nRESET_PIN_2, HIGH);
  digitalWrite(nCS_PIN_2, HIGH);

 // Turn pressure off
 digitalWrite(SOLENOID1, HIGH);
 digitalWrite(SOLENOID2,LOW);
 digitalWrite(SOLENOID3, LOW);

 // Turn LED ON
 digitalWrite(LED_R, HIGH);
 digitalWrite(LED_G, LOW);
 digitalWrite(LED_B, LOW);

 


  // Start SPI
  SPI.begin();
  SPI.setDataMode(SPI_MODE3);

  // Configure powerSTEP

  driver_2.SPIPortConnect(&SPI); // give library the SPI port (only the one on an Uno)
  
  driver_2.configSyncPin(BUSY_PIN, 0); // use SYNC/nBUSY pin as nBUSY, 
                                     // thus syncSteps (2nd paramater) does nothing
                                     
  driver_2.configStepMode(STEP_FS_32); // 1/128 microstepping, full steps = STEP_FS,
                                // options: 1, 1/2, 1/4, 1/8, 1/16, 1/32, 1/64, 1/128

                                
  driver_2.setMaxSpeed(1000); // max speed in units of full steps/s 
  driver_2.setMinSpeed(20);
  driver_2.setFullSpeed(2000); // full steps/s threshold for disabling microstepping
  driver_2.setAcc(1000); // full steps/s^2 acceleration
  driver_2.setDec(800); // full steps/s^2 deceleration
  
  driver_2.setSlewRate(SR_980V_us); // faster may give more torque (but also EM noise),
                                  // options are: 114, 220, 400, 520, 790, 980(V/us)
                                  
  driver_2.setOCThreshold(2); // over-current threshold for the 2.8A NEMA23 motor
                            // used in testing. If your motor stops working for
                            // no apparent reason, it's probably this. Start low
                            // and increase until it doesn't trip, then maybe
                            // add one to avoid misfires. Can prevent catastrophic
                            // failures caused by shorts
  driver_2.setOCShutdown(OC_SD_ENABLE); // shutdown motor bridge on over-current event
                                      // to protect against permanant damage
  
  driver_2.setPWMFreq(PWM_DIV_1, PWM_MUL_0_75); // 16MHz*0.75/(512*1) = 23.4375kHz 
                            // power is supplied to stepper phases as a sin wave,  
                            // frequency is set by two PWM modulators,
                            // Fpwm = Fosc*m/(512*N), N and m are set by DIV and MUL,
                            // options: DIV: 1, 2, 3, 4, 5, 6, 7, 
                            // MUL: 0.625, 0.75, 0.875, 1, 1.25, 1.5, 1.75, 2
                            
  driver_2.setVoltageComp(VS_COMP_DISABLE); // no compensation for variation in Vs as
                                          // ADC voltage divider is not populated
                                          
  driver_2.setSwitchMode(SW_HARD_STOP); // 
                                 // SW_HARD_STOP: TP1 causes hard stop on connection 
                                 // to GND, you get stuck on switch after homing
                                      
  driver_2.setOscMode(INT_16MHZ); // 16MHz internal oscillator as clock source

  // KVAL registers set the power to the motor by adjusting the PWM duty cycle,
  // use a value between 0-255 where 0 = no power, 255 = full power.
  // Start low and monitor the motor temperature until you find a safe balance
  // between power and temperature. Only use what you need
  driver_2.setRunKVAL(128);
  driver_2.setAccKVAL(128);
  driver_2.setDecKVAL(128);
  driver_2.setHoldKVAL(32);

  driver_2.setParam(ALARM_EN, 0x8F); // disable ADC UVLO (divider not populated),
                                   // disable stall detection (not configured),
                                   // disable switch (not using as hard stop)

  driver_2.getStatus(); // clears error flags

  
  attachInterrupt(digitalPinToInterrupt(LIMIT),interrupt_home, LOW);
  Serial.println("INIT");
}

void interrupt_home(){
  unsigned long temp_time = millis();
  if (temp_time-switch_time >100){
    driver_2.hardStop();
    driver_2.getStatus(); // clears error flags
    switch_time = temp_time;
    driver_2.resetPos();
    float steps_per_mm = (200. * outlet_div / 0.75);
    long steps = long(-.25*steps_per_mm);
    driver_2.goTo(steps);
    //Serial.println("Pause:");
    first = true;
  }
}
void serialCheck() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    // add it to the inputString:
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\n') {
      stringComplete = true;
      }else{
      inputString += inChar;
      }
  }
}

bool checkHome(){
  unsigned int sw_val;
  sw_val = driver_2.getParam(STATUS);
  //Serial.println(sw_val);
  sw_val &= 0x0004;
  //Serial.println(sw_val);
  driver_2.getStatus(); // clears error flags
  bool at_home = (sw_val==4);
  return at_home;
}

void releaseSW(){
  int at_home=true;
  Serial.println("Backing from SW");
  while (at_home){
    delay(100);
    at_home = checkHome();
  }
}
void moveMotor(){
  // Move the motor to specified position.
  driver_2.hardStop();
  bool at_home = checkHome();
  if (at_home){
        driver_2.releaseSw(B0,inversion);
        releaseSW();
  }
  driver_2.setSwitchMode(CONFIG_SW_HARD_STOP); // Set switch mode to hard stop. 
  int chnl = atoi(inputString[1]);
  String location = inputString.substring(3,13);
  float mm_pos = location.toFloat();
  //#Serial.print("Move Motor ");
  //#Serial.print(inputString[1]);
  //#Serial.print(" To Location: ");
  //Serial.println(steps);
  float steps_per_mm = (200. * outlet_div / 0.75);
  long steps = long(mm_pos*steps_per_mm);
  driver_2.goTo(steps);
  Serial.println("OK");
}

void motorHomePosition(){
  unsigned int sw_val;
  sw_val = driver_2.getParam(STATUS);
  //Serial.println(sw_val);
  sw_val &= 0x0004;
  //Serial.println(sw_val);
  driver_2.getStatus(); // clears error flags



  // Move Motor until it hits the switch
  char user_dir = inputString[2];
  //Serial.println("Starting Move...");
  byte dir = B0;
  if (user_dir=='1'){
   dir = true;
   Serial.println("HEY!");
  }
  if (sw_val == 4){
    Serial.println("Go Down");
    if (dir){
      dir = 0;
    }
    else{
      dir=1;
    }
    driver_2.releaseSw(B0,dir);
  }else{
  driver_2.goUntil(B0,dir,400);
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
    }
    else {
    moveMotor();
    }
  }
  else if (inputString[2]=='G'){
    setHome();
  } else if (inputString[2]=='S'){
    setMotorSpeed();
  } else if (inputString[2]=='A'){
    setAccel();
  }
  else if (inputString[2]=='R'){
    resetDriver();
  }
}

void getMotorPos(){
  int chnl = atoi(inputString[1]);
  //Serial.print("Get Motor  Position for channel ");
  //Serial.print(chnl);
  //Serial.println(": ");
  long steps = driver_2.getPos();
  float steps_per_mm = (200. * outlet_div / 0.75);
  float return_steps = float(float(steps)/steps_per_mm);
  Serial.print("L?");
  Serial.println(return_steps,3);
}

void setHome(){
  int chnl = atoi(inputString[1]);
  char user_dir = inputString[3];
  //Serial.println("Starting Move...");
  if (user_dir=='1'){
   inversion = true;
  } else{
    inversion = false;
  }
  //Serial.print("Setting Home Position for channel: ");
  driver_2.resetPos();
}

void setAccel(){
  int chnl = atoi(inputString[1]);
  String location = inputString.substring(3,9);
  int stepspersec2 = location.toInt();
  driver_2.setAcc(stepspersec2); // full steps/s^2 acceleration
  driver_2.setDec(stepspersec2); // full steps/s^2 deceleration
}
void setMotorSpeed(){
  int chnl = atoi(inputString[1]);
  String location = inputString.substring(3,8);
  int stepspersec = location.toInt();
  //Serial.print(" Setting speed ");
  //Serial.print(stepspersec);
  //Serial.print(" for channnel: ");
  //Serial.println(chnl);
  driver_2.setMaxSpeed(stepspersec);
}

void pressureTalk(){
  int chnl = atoi(inputString[1]);
  //Serial.print("Setting Pressure ");
  //Serial.print(chnl);
  //Serial.println(": ");
  //Serial.println(inputString[2]);
  if (inputString[2]=='R'){
    Serial.println("ON");
    digitalWrite(SOLENOID2,HIGH);  
    digitalWrite(SOLENOID1,LOW);
    digitalWrite(SOLENOID3, LOW);
  } else if(inputString[2]=='S'){
    digitalWrite(SOLENOID2,LOW);
    digitalWrite(SOLENOID1,HIGH);
    digitalWrite(SOLENOID3, LOW);
  } else if(inputString[2]=='X'){
    digitalWrite(SOLENOID1,HIGH);
    digitalWrite(SOLENOID2,HIGH);
    digitalWrite(SOLENOID3, LOW);
    Serial.println("All OPEN");
  } else if (inputString[2]=='C'){
    digitalWrite(SOLENOID1, LOW);
    digitalWrite(SOLENOID2, LOW);
    digitalWrite(SOLENOID3, LOW);
  } else if (inputString[2]=='V'){
    digitalWrite(SOLENOID1, LOW);
    digitalWrite(SOLENOID2, LOW);
    digitalWrite(SOLENOID3, HIGH);
  }
}

void resetDriver(){
  digitalWrite(nSTBY_nRESET_PIN_2, HIGH);
  digitalWrite(nSTBY_nRESET_PIN_2, LOW);
  digitalWrite(nSTBY_nRESET_PIN_2, HIGH);
  digitalWrite(nSTBY_nRESET_PIN_2, LOW);
  digitalWrite(nCS_PIN_2, HIGH);
}

void lightTalk(){
  
  // Select the RGB channel
  int pin = LED_R; // R is default
  if (inputString[1]=='G'){
    pin = LED_G;
  }
  else if (inputString[1]=='B'){
    pin = LED_B;
  }
  // Turn on or off the LED
  if (inputString[2]=='1'){
    digitalWrite(pin, HIGH);
  }
  else if (inputString[2]=='0'){
    digitalWrite(pin, LOW);
  }
}

void loop() 
{ 
   // print the string when a newline arrives:

  serialCheck();
  if (stringComplete) {
    Serial.println(inputString);
    if (inputString[0]=='M'){
      motorTalk();
    }else if (inputString[0]=='P'){
      pressureTalk();
    }
    else if (inputString[0]=='S'){
      Serial.println("Run");
    }
    else if (inputString[0]=='L'){
      lightTalk();
    }
    // clear the string:
    inputString = "";
    stringComplete = false;
  }
}

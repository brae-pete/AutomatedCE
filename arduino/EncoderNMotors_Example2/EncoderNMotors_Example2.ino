// Program demonstrating how to control a powerSTEP01-based ST X-NUCLEO-IHM03A1 
// stepper motor driver shield on an Arduino Uno-compatible board

#include <powerSTEP01ArduinoLibrary.h>
#include <SPI.h>
#include "QuickMedianLib.h"

// Pin definitions for the X-NUCLEO-IHM03A1 connected to an Uno-compatible board
#define nCS_PIN 7
#define STCK_PIN 9
#define nSTBY_nRESET_PIN 6
#define nBUSY_PIN 5
 
#define eCS 3 //Chip or Slave select 



// Pin definitions for the X-NUCLEO-IHM03A1 connected to an Uno-compatible board
#define nCS_PIN_2 10
#define STCK_PIN_2 9
#define nSTBY_nRESET_PIN_2 8
#define nBUSY_PIN_2 4
#define flag_2 3


// powerSTEP library instance, parameters are distance from the end of a daisy-chain
// of drivers, !CS pin, !STBY/!Reset pin
powerSTEP driver(1, nCS_PIN, nSTBY_nRESET_PIN, nBUSY_PIN);
// powerSTEP library instance, parameters are distance from the end of a daisy-chain
// of drivers, !CS pin, !STBY/!Reset pin
powerSTEP driver_2(1, nCS_PIN_2, nSTBY_nRESET_PIN_2, nBUSY_PIN_2);

// Set up variables for motors
int outlet_div = 128;
// Set variables for Pressure
int SOLENOID1 = 1;
int SOLENOID2 = 2;

//SERIAL 
String inputString = "";   // a String to hold incoming data
int inputCount = 0;
bool stringComplete = false;  // whether the string is complete

//ENCODER
uint16_t ABSposition = 0;
long ABSposition_last = 0;
int32_t old_ABS =0;
int32_t new_ABS = 0;
uint8_t temp[2];    //This one.
float microStepsCount = 0.78125;
float dialConversion = 4096./100;
 
int deg = 0;
long pos = 0;
int pos_idx = 0; 
float pos_list[]={0,0,0,0,0};
float pos_length = sizeof(pos_list) / sizeof(float);
bool runEncoder = false;
float setEncoder = 0;
bool initialRead = true;

SPISettings encoderSPI(500000, MSBFIRST, SPI_MODE0); 

void setup() 
{
  // Start serial
  Serial.begin(230400);
  Serial.println("powerSTEP01 Arduino control initialising...");

  // Prepare pins
  pinMode(nSTBY_nRESET_PIN, OUTPUT);
  pinMode(nCS_PIN, OUTPUT);
  pinMode(nSTBY_nRESET_PIN_2, OUTPUT);
  pinMode(nCS_PIN_2, OUTPUT);
  pinMode(MOSI, OUTPUT);
  pinMode(MISO, OUTPUT);
  pinMode(SCK, OUTPUT);
  pinMode(eCS,OUTPUT);//Slave Select



  // Reset powerSTEP and set CS
  digitalWrite(nSTBY_nRESET_PIN, HIGH);
  digitalWrite(nSTBY_nRESET_PIN, LOW);
  digitalWrite(nSTBY_nRESET_PIN, HIGH);
  digitalWrite(nCS_PIN, HIGH);

  digitalWrite(nSTBY_nRESET_PIN_2, HIGH);
  digitalWrite(nSTBY_nRESET_PIN_2, LOW);
  digitalWrite(nSTBY_nRESET_PIN_2, HIGH);
  digitalWrite(nCS_PIN_2, HIGH);

  digitalWrite(eCS,HIGH);

 


  // Start SPI
  SPI.begin();
  SPI.setDataMode(SPI_MODE3);

  // Configure powerSTEP
  driver.SPIPortConnect(&SPI); // give library the SPI port (only the one on an Uno)
  
  driver.configSyncPin(BUSY_PIN, 0); // use SYNC/nBUSY pin as nBUSY, 
                                     // thus syncSteps (2nd paramater) does nothing
                                     
  driver.configStepMode(STEP_FS_16); // 1/128 microstepping, full steps = STEP_FS,
                                // options: 1, 1/2, 1/4, 1/8, 1/16, 1/32, 1/64, 1/128
                                
  driver.setMaxSpeed(1500); // max speed in units of full steps/s 
  driver.setFullSpeed(2000); // full steps/s threshold for disabling microstepping
  driver.setAcc(2000); // full steps/s^2 acceleration
  driver.setDec(2000); // full steps/s^2 deceleration
  
  driver.setSlewRate(SR_520V_us); // faster may give more torque (but also EM noise),
                                  // options are: 114, 220, 400, 520, 790, 980(V/us)
                                  
  driver.setOCThreshold(8); // over-current threshold for the 2.8A NEMA23 motor
                            // used in testing. If your motor stops working for
                            // no apparent reason, it's probably this. Start low
                            // and increase until it doesn't trip, then maybe
                            // add one to avoid misfires. Can prevent catastrophic
                            // failures caused by shorts
  driver.setOCShutdown(OC_SD_ENABLE); // shutdown motor bridge on over-current event
                                      // to protect against permanant damage
  
  driver.setPWMFreq(PWM_DIV_1, PWM_MUL_0_75); // 16MHz*0.75/(512*1) = 23.4375kHz 
                            // power is supplied to stepper phases as a sin wave,  
                            // frequency is set by two PWM modulators,
                            // Fpwm = Fosc*m/(512*N), N and m are set by DIV and MUL,
                            // options: DIV: 1, 2, 3, 4, 5, 6, 7, 
                            // MUL: 0.625, 0.75, 0.875, 1, 1.25, 1.5, 1.75, 2
                            
  driver.setVoltageComp(VS_COMP_DISABLE); // no compensation for variation in Vs as
                                          // ADC voltage divider is not populated
                                          
  driver.setSwitchMode(SW_USER); // switch doesn't trigger stop, status can be read.
                                 // SW_HARD_STOP: TP1 causes hard stop on connection 
                                 // to GND, you get stuck on switch after homing
                                      
  driver.setOscMode(INT_16MHZ); // 16MHz internal oscillator as clock source

  // KVAL registers set the power to the motor by adjusting the PWM duty cycle,
  // use a value between 0-255 where 0 = no power, 255 = full power.
  // Start low and monitor the motor temperature until you find a safe balance
  // between power and temperature. Only use what you need
  driver.setRunKVAL(64);
  driver.setAccKVAL(64);
  driver.setDecKVAL(64);
  driver.setHoldKVAL(32);

  driver.setParam(ALARM_EN, 0x8F); // disable ADC UVLO (divider not populated),
                                   // disable stall detection (not configured),
                                   // disable switch (not using as hard stop)

  driver.getStatus(); // clears error flags

  Serial.println(F("Initialisation complete"));

  driver_2.SPIPortConnect(&SPI); // give library the SPI port (only the one on an Uno)
  
  driver_2.configSyncPin(BUSY_PIN, 0); // use SYNC/nBUSY pin as nBUSY, 
                                     // thus syncSteps (2nd paramater) does nothing
                                     
  driver_2.configStepMode(STEP_FS_128); // 1/128 microstepping, full steps = STEP_FS,
                                // options: 1, 1/2, 1/4, 1/8, 1/16, 1/32, 1/64, 1/128
                                
  driver_2.setMaxSpeed(1100); // max speed in units of full steps/s 
  driver_2.setFullSpeed(2000); // full steps/s threshold for disabling microstepping
  driver_2.setAcc(2000); // full steps/s^2 acceleration
  driver_2.setDec(2000); // full steps/s^2 deceleration
  
  driver_2.setSlewRate(SR_980V_us); // faster may give more torque (but also EM noise),
                                  // options are: 114, 220, 400, 520, 790, 980(V/us)
                                  
  driver_2.setOCThreshold(8); // over-current threshold for the 2.8A NEMA23 motor
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
                                          
  driver_2.setSwitchMode(SW_USER); // switch doesn't trigger stop, status can be read.
                                 // SW_HARD_STOP: TP1 causes hard stop on connection 
                                 // to GND, you get stuck on switch after homing
                                      
  driver_2.setOscMode(INT_16MHZ); // 16MHz internal oscillator as clock source

  // KVAL registers set the power to the motor by adjusting the PWM duty cycle,
  // use a value between 0-255 where 0 = no power, 255 = full power.
  // Start low and monitor the motor temperature until you find a safe balance
  // between power and temperature. Only use what you need
  driver_2.setRunKVAL(64);
  driver_2.setAccKVAL(64);
  driver_2.setDecKVAL(64);
  driver_2.setHoldKVAL(32);

  driver_2.setParam(ALARM_EN, 0x8F); // disable ADC UVLO (divider not populated),
                                   // disable stall detection (not configured),
                                   // disable switch (not using as hard stop)

  driver_2.getStatus(); // clears error flags

  Serial.println(F("Initialisation 2 complete"));
  
}

uint8_t SPI_T (uint8_t msg)    //Repetive SPI transmit sequence
{
   uint8_t msg_temp = 0;  //vairable to hold recieved data
   digitalWrite(eCS,LOW);     //select spi device
   msg_temp = SPI.transfer(msg);    //send and recieve   
   digitalWrite(eCS,HIGH);    //deselect spi device
   //if (msg_temp != 0x1F){
   
    //Serial.println(msg_temp,HEX);
   //}
   return(msg_temp);      //return recieved byte
}

void readEncoder(){ 
   uint8_t recieved = 0xA5;    //just a temp vairable
   int new_deg = 0; // new temp float position
   ABSposition = 0;    //reset position vairable
   
   SPI.beginTransaction(encoderSPI);    //start transmition
   digitalWrite(eCS,LOW);
   
   SPI_T(0x10);   //issue read command
   
   recieved = SPI_T(0x00);    //issue NOP to check if encoder is ready to send
   
   while (recieved != 0x10)    //loop while encoder is not ready to send
   {
     recieved = SPI_T(0x00);    //cleck again if encoder is still working 
      delayMicroseconds(80);
   }
   
   temp[0] = SPI_T(0x00);    //Recieve MSB
   temp[1] = SPI_T(0x00);    // recieve LSB
   
   digitalWrite(eCS,HIGH);  //just to make sure   
   SPI.endTransaction();    //end transmition
   SPI.setDataMode(SPI_MODE3); // Change the datamode back for PowerStep Drivers.... 
   
   temp[0] &=~ 0xF0;    //mask out the first 4 bits
    
   ABSposition = temp[0] << 8;    //shift MSB to correct ABSposition in ABSposition message
   ABSposition += temp[1];    // add LSB to ABSposition message to complete message
   old_ABS = ABSposition_last;
   new_ABS = long(ABSposition);
   //if (ABSposition != ABSposition_last)    //if nothing has changed dont wast time sending position
   //{
      
      //Serial.println(ABSposition_last);
      if (new_ABS-old_ABS > 2000){
        pos = pos + (new_ABS-old_ABS)-4095L;
      } else if (new_ABS-old_ABS < -2000){
        pos = pos +(new_ABS-old_ABS)+4095L;
      } else if (abs(new_ABS - old_ABS)<4096 | initialRead){
        pos = pos +(new_ABS-old_ABS);
        initialRead = false;
      }
      //Serial.print(ABSposition);
      //Serial.print(" ");
      //Serial.print(ABSposition_last);
      //Serial.print(" ");
      //Serial.println(pos);
      pos_list[pos_idx]=long(pos);
      pos_idx = (pos_idx+1)%5;
      ABSposition_last = new_ABS;  
}

void serialEvent() {
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

void moveMotor(){
  // Move the motor to specified position.
  int chnl = atoi(inputString[1]);
  String location = inputString.substring(3,13);
  float steps = location.toFloat();
  //#Serial.print("Move Motor ");
  //#Serial.print(inputString[1]);
  //#Serial.print(" To Location: ");
  Serial.println(steps);
  steps = long(steps/8.*200.*outlet_div);
  Serial.println(steps);
  driver_2.goTo(steps);
}

void moveEncoder(){
  String location = inputString.substring(2,13);
  setEncoder = long(location.toFloat()*dialConversion);
  runEncoder = true; 
}

void checkEncoder(){
  if (runEncoder){
    checkMove();
  }
}

void sortPos(){
  long holder;
    int x;
    int y;
    for(x = 0; x < 5; x++)
    for(y = 0; y < 4; y++)
     if(pos_list[y] > pos_list[y+1]) {
       holder = pos_list[y+1];
       pos_list[y+1] = pos_list[y];
       pos_list[y] = holder;
     }
}

void checkMove(){
  
  if(!driver.busyCheck()){
    sortPos();
    long check_pos = pos_list[2];
    long diff_set = (check_pos)-setEncoder;
    Serial.println("CheckMove");
    Serial.println(diff_set);
    Serial.println("CheckPos: ");
    Serial.println(check_pos);
    Serial.print("move to: ");
    Serial.println(setEncoder);
    
    if (abs(diff_set)<2){
      runEncoder = false;
    } else if (diff_set>0){
      long steps = round(abs(diff_set *microStepsCount));
      Serial.print("Steps: ");
      Serial.println(steps);
      driver.move(FWD,steps);
    } else{
      long steps = round(abs(diff_set *microStepsCount));
      driver.move(REV,steps);
      Serial.print("Steps: ");
      Serial.println(steps);
    }
  }
}

void encoderTalk(){
  if (inputString[1]=='L'){
    moveEncoder();
    
  }
  else if (inputString[1]=='R'){
    sortPos();
    Serial.println(float(pos_list[2]/dialConversion));
  }
  else if (inputString[1]=='S'){
    runEncoder=false;
    driver.softStop();
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

void getMotorPos(){
  int chnl = atoi(inputString[1]);
  //Serial.print("Get Motor  Position for channel ");
  //Serial.print(chnl);
  //Serial.println(": ");
  long steps = driver_2.getPos();
  steps = steps;
  Serial.println("Position");
  Serial.println(steps);
}

void setHome(){
  int chnl = atoi(inputString[1]);
  //Serial.print("Setting Home Position for channel: ");
  Serial.println(chnl);
  driver_2.resetPos();
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
    digitalWrite(SOLENOID2,LOW);  
    digitalWrite(SOLENOID1,HIGH);
  } else if(inputString[2]=='S'){
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

void loop() 
{ 
   // print the string when a newline arrives:
  readEncoder();
  checkEncoder();
  if (stringComplete) {
    Serial.println(inputString);
    if (inputString[0]=='M'){
      motorTalk();
    }else if (inputString[0]=='P'){
      pressureTalk();
    }else if (inputString[0]=='E'){
      encoderTalk();
    }
    // clear the string:
    inputString = "";
    stringComplete = false;
  }
}
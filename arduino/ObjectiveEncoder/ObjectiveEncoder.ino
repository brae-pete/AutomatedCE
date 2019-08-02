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
#include "QuickMedianLib.h"

// Pin definitions for the X-NUCLEO-IHM03A1 connected to an Uno-compatible board
#define nCS_PIN 10
#define STCK_PIN 9
#define nSTBY_nRESET_PIN 8
#define nBUSY_PIN 4

//Encoder 
#define eCS 7 //Chip or Slave select 


// powerSTEP library instance, parameters are distance from the end of a daisy-chain
// of drivers, !CS pin, !STBY/!Reset pin

// powerSTEP library instance, parameters are distance from the end of a daisy-chain
// of drivers, !CS pin, !STBY/!Reset pin
powerSTEP driver(0, nCS_PIN, nSTBY_nRESET_PIN, nBUSY_PIN);

// Set up variables for motors
int outlet_div = 128;

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
float INVERT_INPUT = -1.;
//SPI commands used by the AMT20
#define nop 0x00            //no operation
#define rd_pos 0x10         //read position
#define set_zero_point 0x70 //set zero point
 
int deg = 0;
long pos = 0;
int pos_idx = 0; 
float pos_list[]={0,0,0,0,0};
float pos_length = sizeof(pos_list) / sizeof(float);
bool runEncoder = false;
float setEncoder = 0;
bool initialRead = true;
int step_idx = 0;
int count = 0;

SPISettings encoderSPI(500000, MSBFIRST, SPI_MODE0); 

void setup() 
{
  // Start serial
  Serial.begin(1000000);
  Serial.println("Encoder+Motor Initializing");

  // Prepare pins
  pinMode(nSTBY_nRESET_PIN, OUTPUT);
  pinMode(nCS_PIN, OUTPUT);
  pinMode(MOSI, OUTPUT);
  pinMode(MISO, OUTPUT);
  pinMode(SCK, OUTPUT);
  pinMode(eCS,OUTPUT);//Slave Select



  // Reset powerSTEP and set CS
  digitalWrite(nSTBY_nRESET_PIN, HIGH);
  digitalWrite(nSTBY_nRESET_PIN, LOW);
  digitalWrite(nSTBY_nRESET_PIN, HIGH);

  //Set both CS to high
  digitalWrite(nCS_PIN, HIGH);
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
                                
  driver.setMaxSpeed(1200); // max speed in units of full steps/s 
  driver.setFullSpeed(2000); // full steps/s threshold for disabling microstepping
  driver.setAcc(1000); // full steps/s^2 acceleration
  driver.setDec(1000); // full steps/s^2 deceleration
  
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
  driver.setRunKVAL(128);
  driver.setAccKVAL(128);
  driver.setDecKVAL(128);
  driver.setHoldKVAL(0);

  driver.setParam(ALARM_EN, 0x8F); // disable ADC UVLO (divider not populated),
                                   // disable stall detection (not configured),
                                   // disable switch (not using as hard stop)

  driver.getStatus(); // clears error flags

  Serial.println(F("Initialisation complete"));


  
}

uint8_t SPI_T (uint8_t msg)    //Repetive SPI transmit sequence
{
   uint8_t msg_temp = 0;  //vairable to hold recieved data
    
   SPI.beginTransaction(encoderSPI);    //start transmition
   delayMicroseconds(50);
   digitalWrite(eCS,LOW);     //select spi device
   msg_temp = SPI.transfer(msg);    //send and recieve   
   digitalWrite(eCS,HIGH);    //deselect spi device
   SPI.endTransaction();    //end transmition
   SPI.setDataMode(SPI_MODE3); // Change the datamode back for PowerStep Drivers.... 
   
   return(msg_temp);      //return recieved byte
   
}

void readEncoder(){ 
 
   int new_deg = 0; // new temp float position
   ABSposition = 0;    //reset position vairable
   if (step_idx == 0){
     SPI_T(rd_pos);   //issue read command
     step_idx=1;
   }

   uint8_t recieved;    //just a temp vairable
   if (step_idx ==1){
      recieved = SPI_T(nop);    //issue NOP to check if encoder is ready to send
      count = count + 1;
      if (count >= 5){
        count = 0;
        step_idx=0;
      }
      
      if (recieved == rd_pos){
          step_idx=2;
          count = 0;
        }
      else{       
        return;
        }
    }
   //while (recieved != 0x10)    //loop while encoder is not ready to send
   //{
   //  recieved = SPI_T(0x00);    //cleck again if encoder is still working 
   //  delayMicroseconds(90);
   //}
   if (step_idx==2){
    //Serial.println("Step3");
   temp[0] = SPI_T(nop);    //Recieve MSB
   temp[1] = SPI_T(nop);    // recieve LSB
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
      
   pos_list[pos_idx]=long(pos);
   pos_idx = (pos_idx+1)%5;
   ABSposition_last = new_ABS;  
   step_idx=0;
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


void moveEncoder(){
  String location = inputString.substring(2,13);
  setEncoder = long(location.toFloat()*dialConversion*INVERT_INPUT);
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
    //Serial.println("CheckMove");
    //Serial.println(diff_set);
    //Serial.println("CheckPos: ");
    //Serial.println(check_pos);
    //Serial.print("move to: ");
    //Serial.println(setEncoder);
    
    if (abs(diff_set)<1){
      runEncoder = false;
    } else if (diff_set>0){
      long steps = round(abs(diff_set *microStepsCount));
      //Serial.print("Steps: ");
      //Serial.println(steps);
      driver.move(FWD,steps);
    } else{
      long steps = round(abs(diff_set *microStepsCount));
      driver.move(REV,steps);
      //Serial.print("Steps: ");
      //Serial.println(steps);
    }
  }
}

void encoderTalk(){
  if (inputString[1]=='L'){
    moveEncoder();
    
  }
  else if (inputString[1]=='R'){
    sortPos();
    Serial.println(float(pos_list[2]/dialConversion*INVERT_INPUT));
  }
  else if (inputString[1]=='S'){
    runEncoder=false;
    driver.softStop();
  }
  else if (inputString[1]=='H'){
    pos = 0;
  }

  else if (inputString[1]=='R'){
    
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
  serialCheck();
  
  if (stringComplete) {
    Serial.println(inputString);
    if (inputString[0]=='E'){
      encoderTalk();
    }
    else if (inputString[0]=='S'){
      Serial.println("Run");
    }
    // clear the string:
    inputString = "";
    stringComplete = false;
    
  }
}

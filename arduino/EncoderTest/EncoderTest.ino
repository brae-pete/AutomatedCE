 
#include <SPI.h>
 
#define eCS 3 //Chip or Slave select 
#define nCS 10 // 
#define nCS_2 7 //

 
uint16_t ABSposition = 0;
uint16_t ABSposition_last = 0;
uint8_t temp[2];    //This one.
 
float deg = 0.00;

SPISettings encoderSPI(500000, MSBFIRST, SPI_MODE0); 
 
void setup()
{
  pinMode(eCS,OUTPUT);//Slave Select
  pinMode(nCS,OUTPUT);//Slave Select
  pinMode(nCS_2,OUTPUT);//Slave Select
  digitalWrite(eCS,HIGH);
  digitalWrite(nCS,HIGH);
  digitalWrite(nCS_2,HIGH);
  SPI.begin();
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE0);
  SPI.setClockDivider(SPI_CLOCK_DIV32);
  Serial.begin(115200);
  Serial.println("starting");
  Serial.flush();
  delay(2000);
  SPI.end();
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
   ABSposition = 0;    //reset position vairable
   
   SPI.beginTransaction(encoderSPI);    //start transmition
   digitalWrite(eCS,LOW);
   
   SPI_T(0x10);   //issue read command
   
   recieved = SPI_T(0x00);    //issue NOP to check if encoder is ready to send
   
   while (recieved != 0x10)    //loop while encoder is not ready to send
   {
     recieved = SPI_T(0x00);    //cleck again if encoder is still working 
     delay(2);    //wait a bit
   }
   
   temp[0] = SPI_T(0x00);    //Recieve MSB
   temp[1] = SPI_T(0x00);    // recieve LSB
   
   digitalWrite(eCS,HIGH);  //just to make sure   
   SPI.endTransaction();    //end transmition
   
   temp[0] &=~ 0xF0;    //mask out the first 4 bits
    
   ABSposition = temp[0] << 8;    //shift MSB to correct ABSposition in ABSposition message
   ABSposition += temp[1];    // add LSB to ABSposition message to complete message
    
   if (ABSposition != ABSposition_last)    //if nothing has changed dont wast time sending position
   {
     ABSposition_last = ABSposition;    //set last position to current position
     deg = ABSposition;
     deg = deg * 0.08789;    // aprox 360/4096
     Serial.println(deg);     //send position in degrees
   }   
 
   delay(10);    //wait a bit till next check
 
}

void loop()
{
  readEncoder();
}

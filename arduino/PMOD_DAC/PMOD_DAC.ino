#include <SPI.h>

// Serial Communication Settings
long BAUD = 1000000;

// SPI Communication Settings
long SPI_FREQ = 50000;
int SPI_MODE = SPI_MODE0;
int SPI_ENDIAN = MSBFIRST;
int CS =10;

// Bertan Pins
int ENABLE = 9;

// Byte variables for SPI communication
long WRITE = B0000;
long UPDATE = B0001;
long LDAC = B0010;
long WRITE_UPDATE = B0011;
long POWERDOWN = B0100;
long LOAD_CLEAR_CODE = B0101;
long LOAD_LDAC = B0110;
long RESET = B0111;
long SET_INTERNAL_REF = B1000;

//Address bytes for AD5628
byte DAC_A = B0000;
byte DAC_B = B0001;
byte DAC_C = B0010;
byte DAC_D = B0011;
byte DAC_E = B0100;
byte DAC_F = B0101;
byte DAC_G = B0110;
byte DAC_H = B0111;
byte ALL_DAC = B1111;


// Class definitions

class Channel {
  /*
   *  Channel for a Analog devices AD5628 DAC from Digilent
   *  12 bit Digital to analog converter with a 2.5 V reference voltage
   *  Vout = 2x Vref x D / 2^12
   *  
   *  SPI protocol will send 32 bits of information
   *  xxx C3 C2 C1 C0 A3 A2 A1 A0 D11 ... D0 xxxxxxx I0
   * Commands are referenced at the start of the file as macros
   * 
   * This class keeps the DAC and ADC channels together
   * 
   */
  private:    
    unsigned long _command=0;
  public:
    byte dac_pin;
    long voltage_to_write;
    unsigned int voltage_pin = 255;
    unsigned int current_pin = 255;
    Channel();
    float set_voltage(uint16_t voltage);
    float get_voltage();
    float get_current();  
};

class DAC {
  /*
   * This class is keeps all the DAC channels. It is responsible for group commands to the PMOD 
   *  ie load DAC, reset, shutdown etc...
   *  
   *  It also contains the voltage and current arrays that contain data from all the channels
   */
  private:
    unsigned long _command=0;
    unsigned int _transfer[2];
    void _convert_command();
  public:
    DAC();
    //Fields
    Channel chans[8];
    float voltage_out[8];
    float current_out[8];

    // Methods
    void init_channels();
    void set_ref();
    void reset();
    void get_data(); 
    void send_command(byte command, byte addr, byte data_msb, byte data_lsb);
};

void DAC::get_data(){
  //Serial.println("Getting Data...");
  for (int i = 0; i < 8; i++){
    voltage_out[i]=chans[i].get_voltage();
    current_out[i]=chans[i].get_current();
    
  }
}

class Oracle {
  /*
   * This class is responsible for communicating with the computer, interpreting and calling commands from the other classes. 
   * _rx_msg contains a character array that will hold the incoming message from the computer
   * First char is the command
   * Second char is the channel (if applicable)
   * Third char can be the pin number for the ADC,  
   * Or 
   * The 3rd-10th char are the float encoded in ascii text for the set voltage command
   * 
   */
  private:
  // Our messages back and forth should be shorter than 32 characters (including terminator '\n')
   char _rx_msg[32];
   bool _str_complete;
   int _msg_idx = 0;
   float _get_float_portion(int start, int finish);
   
  public: 
    Oracle();
    DAC dc;
    long baud;
    void interpret();
    void serialCheck();
    void send_data_array(float *arg, int buffer_size);
    void send_float(float f);
};

//***************************** Oracle ****************************
Oracle::Oracle(){
  
}

void Oracle::interpret(){
  byte chnl=0;
  long somevar = 0;
  float in_data=0;
  byte int_voltage=0;
  byte msb = 0;
  byte lsb =0;

  // The first letter of the message is used to determine what function to call
  // Second char corresponds to the channel (0-7)
  // The remaining chars are the inputs for that command (if required)
  switch(_rx_msg[0]){
    case 'S':
    {
      chnl = _rx_msg[1]-'0';
      //in_data = this-> _get_float_portion(2,10);
      byte msb = _rx_msg[2];
      byte lsb = _rx_msg[3];
      int_voltage = (msb << 8) + lsb;
      dc.send_command(WRITE, chnl, msb, lsb);
    }
      break;
    case 'R':
    {
      //Serial.println("Read Data");
      chnl = _rx_msg[1]-'0';
      dc.get_data();
      //Serial.print("S");
      this -> send_data_array( dc.voltage_out, 8);
      this -> send_data_array( dc.current_out, 8);
    }
      break;
    case 'L':
    {
      //Serial.println("Write and Load DAC");
      chnl = _rx_msg[1]-'0';
      //in_data = this-> _get_float_portion(2,10);
      byte msb = _rx_msg[2];
      byte lsb = _rx_msg[3];
      int_voltage = (msb << 8) + lsb;
      dc.send_command(WRITE_UPDATE, chnl, msb, lsb);
      dc.send_command(LDAC, chnl, 0 , 0);
    }
      break;
    case 'U':
    {
      chnl = _rx_msg[1]-'0';
      //in_data = this-> _get_float_portion(2,10);
      byte msb = _rx_msg[2];
      byte lsb = _rx_msg[3];
      int_voltage = (msb << 8) + lsb;
      dc.send_command(UPDATE, chnl, 0, 0);
      
    }
    case 'E':
    // Enable the Betran Controller
    {
      digitalWrite(ENABLE,HIGH);
    }
    break;
    case 'X':
    {
      //Serial.println("PowerDown");
      digitalWrite(ENABLE,LOW);
      dc.reset();    
    }
      break;
    case 'V':
    {
    // Set voltage ADC pin for channel (V02 -> Channel 0, ADC pin 2)
      chnl = _rx_msg[1]-'0';
      Serial.print("RV");
      chnl = Serial.println(analogRead(chnl));
      
      //dc.chans[chnl].voltage_pin = int(_rx_msg[2]-'0');
    }
      break;
    case 'C':
    {
    // Set curernt ADC pin for channel ('C31' -> Channel 3, ADC pin 1)
      //Serial.println("Set Current Pin");
      // convert char to int
      chnl = _rx_msg[1]-'0';
      Serial.print("RC");
      chnl = Serial.println(analogRead(chnl));
    }
      break;
      
  }
  //Serial.println(_rx_msg);  
}
float Oracle::_get_float_portion(int start, int finish){
 /*
  * Returns the float portion of the recieved message specified by start and finish
  */
    float volt;
    char temp_array[finish-start];
    for (int i=start; i<finish; i++){
      temp_array[i-2]=_rx_msg[i];
    }

    volt = atof(temp_array);
    return volt;
}


void Oracle::serialCheck() {
  int data_count = 0;
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    // add it to the _rcx_msg:
    // if the incoming character is a newline,call the interpret function
    
    if (inChar == '\n' and (_msg_idx > 3)) {
       _msg_idx = 0;
      this -> interpret();
      }
    else{
      _rx_msg[_msg_idx]= inChar;
      _msg_idx +=1;
      }
  }
}

void Oracle::send_data_array(float *arg, int buffer_size){
  for (int i = 0; i < buffer_size; i++){
    this-> send_float(arg[i]);
  }
  
}

void Oracle::send_float(float f){
  byte *b = (byte *) &f;
  Serial.write(b,4);  
}


// ******************************** Channel *************************************
Channel::Channel(){
}


float Channel::get_voltage(){
  int data = 0;
  if (voltage_pin != 1024){
    data = analogRead(voltage_pin);
  }
  return data;
}

float Channel::get_current(){
  int data = 0;
  if (current_pin != 1024){
    data = analogRead(current_pin);
  }
  return data;
}

// **************************** DAC **********************************
DAC::DAC(){
}

void DAC::init_channels(){
  
  //Serial.println("Initializing Channels...");
  for (int i = 0; i<8; i++){
    chans[i].dac_pin = i;
    //Serial.print("Initialized Channel ");
    //Serial.println(i); 
  }
}

void DAC::reset(){
  digitalWrite(CS,LOW);
  SPI.transfer(RESET);
  SPI.transfer(0);
  SPI.transfer (0);
  SPI.transfer(0);
  digitalWrite(CS,HIGH);
}
void DAC::set_ref(){
  digitalWrite(CS,LOW);
  SPI.transfer(SET_INTERNAL_REF);
  SPI.transfer(0);
  SPI.transfer (0);
  SPI.transfer(1);
  digitalWrite(CS,HIGH);
}

void DAC::send_command(byte command, byte addr, byte data_msb, byte data_lsb ){
  // xxxxc3c2c1c0  a3a2a1a0D11D10D9D8  D7D6D5D4D3D2D1D0 xxxxxxxx
  // command pattern (for everything but internal references. 
  digitalWrite(CS,LOW);
  SPI.transfer(command);
  SPI.transfer(addr << 4 | data_msb);
  SPI.transfer(data_lsb);
  SPI.transfer(0);
  digitalWrite(CS,HIGH);
  
  
}

// ******************************** Setup and Loop **************************
Oracle orc;
void setup() {
  // put your setup code here, to run once:
  //Set Serial Settings
  Serial.begin(BAUD)
  ;
  //Serial.println("Starting PMOD...");
  // Set up SPI Settings
  SPI.begin();
  SPI.setDataMode(SPI_MODE0);
  SPI.setClockDivider(SPI_CLOCK_DIV16);
  pinMode(CS, OUTPUT);
  orc.dc.init_channels();
  // Return the Voltage to Zero
  orc.dc.reset();
  // Set up the internal Reference
  orc.dc.set_ref();
}

void loop() {
  // put your main code here, to run repeatedly:
  orc.serialCheck();
  //SPI.transfer(int 64);
//SPI.transfer(0b11110000);

  
}

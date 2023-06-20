#===============================================================================
# RMS_pyAPI.py 
#
# tested on Ubuntu20.04, 20May2023, Rahim Jamali
#===============================================================================
import zlib
import serial
import time
import requests
from requests.exceptions import ConnectionError
import json
          
PORT = '/dev/ttyUSB0'
# PORT = '/dev/ttyS1'
BAUD_RATE = 115200
lable_list = ['gate:', 'rack:', 'pir:', 'voltage12v:', 'voltage5v:', 'voltage3_3v:','boardTemp:']
sens_list = ['', '', '', '', '', '', '']

#------------------------------------------------------------------------------ 
def info_func(data: str) -> bool:
    """
    This function takes a string message as input. The message should have 4 parts delimited by '~'.
    If all parts are numbers, the function writes them to a text file named "RMS_INFO.txt" and returns True.
    Otherwise, the function returns False.
    """
    # Split the message into parts using '~' as the delimiter
    parts = data.split('~')
    
    # Check if the number of parts is equal to 4
    if len(parts) != 4:
        return False
        
    for part in parts:
        if not part.replace(".", "").isnumeric():   # change float and check is number
            return False
        
    sens_list[-4:] = parts  # replace the last fourth elements in list
    # Open the file in write mode
    with open("RMS_INFO.txt", "w") as f:
        sensData = '~'.join([x+y for x,y in zip(lable_list, sens_list)])
        f.write('$' + sensData + '*')    # Write the message to the file
        f.close()
    
    # All conditions are met, return True
    print(f"pyAPI:> Voltage Sensors and temperature: {parts}")
    return True

#------------------------------------------------------------------------------ 
def sens_func(message: str) -> bool:
    """
    This function takes a string message as input. The message
    should have 3 parts delimited by '~'. If all parts are alphabet,
    the function writes them to a text file named "RMS_sensor.txt"
    and returns True. Otherwise, the function returns False.
    """
    # Split the message into parts using '~' as the delimiter
    parts = message.split('~')
    
    # Check if the number of parts is equal to 3
    if len(parts) != 3:
        print("pyAPI:> Error! Message STRUCTURE is wrong.")
        return False
    
    # Check if all parts are alphabet
    for part in parts:
        if not part.isalpha():
            return False
        
    sens_list[:3] = parts   # replace the first three elements in list
    # Open the file in write mode
    with open("RMS_INFO.txt", "w") as f:
        sensData = '~'.join([x+y for x,y in zip(lable_list, sens_list)])
        f.write('$' + sensData + '*')    # Write the message to the file
        f.close()
    
    # Return True to indicate success
    print(f"pyAPI:> Sensors state: {parts}")
    return True

#------------------------------------------------------------------------------ 
def token_func(data: str) -> bool:
    """
    This function takes a dictionary as an argument and sends it as a 
    JSON payload in a POST request to the specified URL.
    """
    # Set the URL for the POST request
    url = "http://localhost:8085/token"
    timeout = 10  # seconds
    while True: 
        try:
            #print(f"pyAPI:> Token POST request: {data}") # for debuging
            tokenJSON = json.loads(data)  # convert string token to json object
            response = requests.post(url, json=tokenJSON, timeout=timeout)    # Send a token to the server; method post
            print(f"javaAPI:> Post response:{response.json()}") # for loging
            
            responseStr = json.dumps(response.json())
            responseBytes = responseStr.encode()         
            ser.reset_output_buffer()
            ser.reset_input_buffer()
            ser.flushOutput()
            ser.read_all()            
            ser.write(responseBytes)  # write the data to the serial port
            print(f"pyAPI:> Bytes send: {responseBytes}")   # for loging
            
            time.sleep(0.1)  # Wait for 0.1 seconds before trying again
            
            resp = ser.readline().decode().strip()
            print(f"ESP:> replay received: {resp}")
            if resp == responseStr:
                print(f"pyAPI:> response successfull")
                return True
            elif resp == "deserialize error":
                print(f"pyAPI:> Error! response deserialize")
                return False
            else:
                print(f"pyAPI:> Error! response not recognized")
                # print(f"pyAPI:> Post response send to UART: {responseBytes}")
                return False       
            ser.read_all()            
            break  # Exit the loop
        except requests.exceptions.Timeout:
            print('pyAPI:> Token Post Request: timed out')
        except ConnectionError:  # Catch a ConnectionError if the server is not available
            print("pyAPI:> The server is not available. Waiting for 5 seconds before trying again.")  # Print a message indicating that the server is not available
            time.sleep(5)  # Wait for 5 seconds before trying again




#===============================================================================
# # dictionary of functions
#===============================================================================
functions = {
    "INFO": info_func,
    "SENS": sens_func,
    "TOKN": token_func
}

#------------------------------------------------------------------------------ 
def check_message(message: str) -> bool:
    """
    This function takes a string message as input. The message should have 6 parts delimited by '_'.
    Part 1 must be '$' and part 6 must be '*'. Part 2 must be one of "INFO", "SENS" or "TOKN"
    and call the relative function using a dictionary, passing part 4 as an argument to the function.
    Parts 3 and 5 must be numbers. Part 3 must equal the length of part 4.
    If all these conditions are met, the function returns True. Otherwise, it returns False.
    """
    print()
    print(message)
    if "token" in message:
        functions["TOKN"](message)
        return True
    else:
        # Split the message into parts using '_' as the delimiter    
        parts = message.split('_')
        # print(parts)
        # Check if the number of parts is equal to 6
        if len(parts) != 6:
            # print(len(parts))
            # print(parts)
            print("pyAPI:> Error! Message STRUCTURE is wrong.")
            return False
        
        # Check if part 1 is '$' and part 6 is '*'
        if parts[0] != 'ESP:> $' or parts[5] != '*':
            print("pyAPI:> Error! START or END Character Missed.")
            return False
        
        # Check if parts 3 and 5 are numbers
        if not parts[2].isnumeric() or not parts[4].isnumeric():
            print("pyAPI:> Error! LEN or CRC type is wrong.")
            return False
        
        # Check if part 3 equals the length of part 4
        if int(parts[2]) != len(parts[3]):
            print("pyAPI:> Error! The message LEN is incorrect.")
            return False
    
        # Check if CRC of part 4 equals the part 5
        check_sum = zlib.adler32(bytes(parts[3], 'ascii'))
        if check_sum != int(parts[4]):
            print("pyAPI:> Error! The message CRC is incorrect.")
            return False
        
        # Check if part 2 is one of "INFO", "SENS" or "TOKN" and call
        # the relative function using a dictionary, passing part 4 as an argument
        if parts[1] in functions:
            functions[parts[1]](parts[3])
            return True  # All conditions are met, return True
        else:
            print("pyAPI:> Error! message ID is wrong.")
            return False

#------------------------------------------------------------------------------ 
try:
    ser = serial.Serial(PORT)  # open the Serial Port
    ser.baudrate = BAUD_RATE  # set Baud rate to 9600
    ser.bytesize = 8  # Number of data bits = 8
    ser.parity = 'N'  # No parity
    ser.stopbits = 1  # Number of Stop bits = 1                                           
    ser.timeout = 5  # set the Read Timeout
    
except serial.SerialException as error:  # var contains details of issue
    print("pyAPI:> An Exception Occured!")
    print("pyAPI:> Exception Details --> {error}")
else:
    print("pyAPI:> Ready...")
    print(f"pyAPI:> Serial Port Opened: {ser.name}")
    print(f"pyAPI:> Serial Port baudrate: {ser.baudrate}")
    ser.read_all()      
    print("pyAPI:> Serial Port buffer Flushed.")       

    while(True):
        if ser.inWaiting() > 0:
            readStr = ser.readline().decode().strip()  # readline btes and Remove any \r and \n chars
            check_message(readStr)
    ser.close()  # Close the serial port
        

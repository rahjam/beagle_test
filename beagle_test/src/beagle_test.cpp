//============================================================================
// Name        : beagle_test.cpp
// Author      : RaJa
// Version     :
// Copyright   : Your copyright notice
// Description : Read text message from UART-1 and write to text file
//============================================================================

// C library headers
#include <stdio.h>
#include <string.h>
#include <fstream>
#include <iostream>
#include <unistd.h>

// Linux headers
#include <fcntl.h> 				// Contains file controls like O_RDWR
#include <errno.h> 				// Error integer and strerror() function
#include <termios.h> 			// Contains POSIX terminal control definitions
#include <unistd.h> 			// write(), read(), close()
#include <filesystem>

#define DEFAULT_PORT "/dev/ttyO1"
#define BAUD_RATE B115200   	// 115200 to form B115200

#define Path "/home/debian/rms/"

using namespace std;

int main() {

	string filename = string(Path) + "tokenfile.txt";

	int num_bytes = 0;

	// Create and open a text file and append text to end of file
	ofstream tkFile(filename, std::ios_base::app);
	if (tkFile) {
		cout << filename + " exists." << endl;
	} else {
		cout << filename + " doesn't exist." << endl;
	}

	// Open the serial port. Change device path as needed (currently set to an standard FTDI USB-UART cable type device)
	int serial_port = open(DEFAULT_PORT, O_RDWR);

	// Create new termios struct, we call it 'tty' for convention
	struct termios tty;

	// Read in existing settings, and handle any error
	if (tcgetattr(serial_port, &tty) != 0) {
		cout << "Error " << errno << " from tcgetattr: " <<  strerror(errno) << endl;
		return 1;
	}

	tty.c_cflag &= ~PARENB; 		// Clear parity bit, disabling parity (most common)
	tty.c_cflag &= ~CSTOPB; 		// Clear stop field, only one stop bit used in communication (most common)
	tty.c_cflag &= ~CSIZE; 			// Clear all bits that set the data size
	tty.c_cflag |= CS8; 			// 8 bits per byte (most common)
	tty.c_cflag &= ~CRTSCTS; 		// Disable RTS/CTS hardware flow control (most common)
	tty.c_cflag |= CREAD | CLOCAL; 	// Turn on READ & ignore ctrl lines (CLOCAL = 1)

	tty.c_lflag &= ~ICANON;
	tty.c_lflag &= ~ECHO; 			// Disable echo
	tty.c_lflag &= ~ECHOE; 			// Disable erasure
	tty.c_lflag &= ~ECHONL; 		// Disable new-line echo
	tty.c_lflag &= ~ISIG; 			// Disable interpretation of INTR, QUIT and SUSP
	tty.c_iflag &= ~(IXON | IXOFF | IXANY); // Turn off s/w flow ctrl
	tty.c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL); // Disable any special handling of received bytes

	tty.c_oflag &= ~OPOST; 		// Prevent special interpretation of output bytes (e.g. newline chars)
	tty.c_oflag &= ~ONLCR; 		// Prevent conversion of newline to carriage return/line feed
	// tty.c_oflag &= ~OXTABS; 	// Prevent conversion of tabs to spaces (NOT PRESENT ON LINUX)
	// tty.c_oflag &= ~ONOEOT; 	// Prevent removal of C-d chars (0x004) in output (NOT PRESENT ON LINUX)

	tty.c_cc[VTIME] = 10; 		// Wait for up to 1s (10 deciseconds), returning as soon as any data is received.
	tty.c_cc[VMIN] = 0;

	// Set in/out baud rate to be 115200
	cfsetispeed(&tty, BAUD_RATE);
	cfsetospeed(&tty, BAUD_RATE);

	// Save tty settings, also checking for error
	if (tcsetattr(serial_port, TCSANOW, &tty) != 0) {
		cout << "Error " << errno << " from tcsetattr: " <<  strerror(errno) << endl;
		return 1;
	}

	// Allocate memory for read buffer, set size according to your needs
	char read_buf[256];

	// Normally you wouldn't do this memset() call, but since we will just receive
	// ASCII data for this example, we'll set everything to 0 so we can
	// call printf() easily.
	memset(&read_buf, '\0', sizeof(read_buf));

	// Read bytes. The behavior of read() (e.g. does it block?,
	// how long does it block for?) depends on the configuration
	// settings above, specifically VMIN and VTIME
	while (num_bytes == 0) {
		num_bytes = read(serial_port, &read_buf, sizeof(read_buf));
		if (num_bytes < 142){
			if (tcflush(serial_port, TCIFLUSH) != 0){
						perror("tcflush() error");
						return 1;
					}
			cout << "Partial read: " << num_bytes << " bytes." << endl;
			num_bytes = 0;
		}
		usleep(1000000);
	}
	// n is the number of bytes read. n may be 0 if no bytes were received, and can also be -1 to signal an error.
	if (num_bytes < 0) {
		cout << "Error reading: " <<  strerror(errno) << endl;
		return 1;
	}

	// Here we assume we received ASCII data, but you might be sending raw bytes (in that case, don't try and
	// print it to the screen like this!)
	// Write to the file
	tkFile << read_buf << endl;
	cout << "Write " << num_bytes << " bytes to " << filename << endl;
	cout << "Received message: " << endl << read_buf << endl;

	write(serial_port, read_buf, num_bytes);
	cout << "Send message to UART-1." << endl;

	// Close the file
	tkFile.close();

	// Close serial port
	close(serial_port);
	return 0; // success
}
;


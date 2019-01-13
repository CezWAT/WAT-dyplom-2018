/**
 ** i2c LCD test application
 **
 ** Author: Kaj-Michael Lang <milang@tal.org>
 ** Copyright 2014 - Under creative commons license 3.0 Attribution-ShareAlike CC BY-SA
 **/
#include "LiquidCrystal_I2C.h"
#include <string>
#include <iostream>
#include <stdio.h>
using namespace std;

int main (int argc, char *argv[]) {
	// i2c address
	uint8_t i2c=0x3f;
	// Control line PINs
	uint8_t en=2;
	uint8_t rw=1;
	uint8_t rs=0;

	// Data line PINs
	uint8_t d4=4;
	uint8_t d5=5;
	uint8_t d6=6;
	uint8_t d7=7;

	// Backlight PIN
	uint8_t bl=3;

	// LCD display size
	uint8_t rows=2;
	uint8_t cols=16;

	LiquidCrystal_I2C lcd("/dev/i2c-0", i2c, en, rw, rs, d4, d5, d6, d7, bl, POSITIVE);
	
	/*	argv[1]:
		0 - nic nie przekazywane
		1 - standardowe dane: Va, SN, IL, C
		2 -	VL, N, GR
	*/
	lcd.begin(cols, rows);
	lcd.on();
	lcd.clear();
	//ustawienie kursora (kolumna, rzad); przy pisaniu kursor przesuwa sie i wstawia litere w pozycji x+1
	if (*argv[1] == '1'){ //uzupelnienie danymi standardowymi
		lcd.setCursor(0, 0); //napiecie [xx.xx]
		lcd.print("Va      V");
		lcd.setCursor(3, 0);
		lcd.print(argv[2]);
		lcd.setCursor(10, 0); //stan naladowania [xx]
		lcd.print("SN   %");
		lcd.setCursor(13, 0);
		lcd.print(argv[3]);
		lcd.setCursor(0, 1); //prad ladowania [xx.xx]
		lcd.print("IL      A");
		lcd.setCursor(3, 1);
		lcd.print(argv[4]);
		lcd.setCursor(10, 1); //pojemnosc [xx]
		lcd.print("C   Ah");
		lcd.setCursor(12, 1);
		lcd.print(argv[5]);
	}
	else if(*argv[1] == '2'){ //uzupelnienie danymi dodatkowymi
		lcd.clear();
		lcd.setCursor(0, 0); //napiecie ladowania [xx.xx]
		lcd.print("VL      V");
		lcd.setCursor(3, 0);
		lcd.print(argv[2]);
		lcd.setCursor(10, 0); //sprawnosc elektryczna [xx]
		lcd.print("N   %");
		lcd.setCursor(12, 0);
		lcd.print(argv[3]);
		lcd.setCursor(0, 1); //glebokosc rozladowania [xx]
		lcd.print("GR   %");
		lcd.setCursor(3, 1);
		lcd.print(argv[4]);
	}
	else if (*argv[1] == '0'){ //LCD mozna wylaczyc
		lcd.clear();
		lcd.off();
	}


/*lcd.print("ABCDEFGH");
if (rows>2) {
	lcd.setCursor(0, 2);
	lcd.print("ABCDEFGH");
	lcd.setCursor(0, 3);
	lcd.print("12345678");
}
lcd.clear();
lcd.write('H');
if (rows>2) {
	lcd.setCursor(0,2);
	lcd.print("We say");
	lcd.print("H'ello back!");
}

sleep(2);
lcd.blink();
lcd.cursor();
lcd.autoscroll();
for (uint8_t i=33; i<255; i++) {
	usleep(35000);
	lcd.write((char)i);
	if (i % 8==0)
		sleep(1);
}
lcd.noBlink();
lcd.noCursor();
lcd.clear();*/
}

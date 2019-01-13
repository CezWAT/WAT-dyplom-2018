#!/usr/bin/python

#ToDo: (* - somehow done) 
# * make sure updater doesnt enable output without permission from db
# cleanup

import serial
import subprocess
import sys
import time
import os
import MySQLdb
import MySQLdb.cursors
from datetime import datetime
serStatus = {'output': -1, 'vin': -1, 'vout': -1, 'cout': -1, 'constant': -1} #initialize with unmet values

def uart(datain, val): #takes arg1 = message, arg2 - value to send
	if datain == 'voltage' or datain == 'current':
		data = '%s %5.3f\r\n' % (datain, val)
		oneline = True
	elif datain == 'output':
		data = 'output %d\r\n' % val
		oneline = True
	elif datain == 'status':
		data = 'status\r\n'
		oneline = False
	else:
		print "Error, unknown command"
		return
	ser = serial.Serial(0, baudrate=38400, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.5)
	if ser.isOpen() and oneline: #connection exists, voltage/current/output command
		ser.write(data)	#write data to serial port
	elif ser.isOpen() and not oneline: #connection exists, status command
		ser.write(data)
		response = ser.readlines()
		serStatus = status(response)
		return serStatus
	else:
		return False

def lcd(lcd_type, batt_param):
	''' LCD can get:
		0 to turn off
		1 to show Va, SN, IL, C || Uakum.; Stan Nalad.; prad lad.; pojemnosc
		2 to show VL, N, GR || Uladowania; sprawnosc; glebokosc rozladowania
	'''
	param1 = lcd_type, batt_param["volt_aku_cur"], batt_param["chst"], batt_param["I_ch"], batt_param["cap"] #select what data will be used
	run = './test-lcd %d "%5.2f" "%d" "%5.2f" "%d"' % param1 #put needed data with formatting
	subprocess.call(run, shell=True) #run independent lcd update program

def status(lines):
	output = 'UNKNOWN' #initialize data
	vin = 0
	vout = 0
	cout = 0
	const = 'UNKNOWN' #/initialize

	for line in lines: #split known response
		part = line.split(':')
		if part[0] == 'OUTPUT':
			output = part[1].strip()
		elif part[0] == 'VIN':
			vin = float(part[1].strip())
		elif part[0] == 'VOUT':
			vout = float(part[1].strip())
		elif part[0] == 'COUT':
			cout = float(part[1].strip())
		elif part[0] == 'CONSTANT':
			const = part[1].strip()
	chargr_param = {'output': output, 'vin': vin, 'vout': vout, 'cout': cout, 'constant': const} #put it into dictionary
	return chargr_param

def sqlconn(cmd, batt_var):
	conn = MySQLdb.connect("localhost", "root", "root", "ABC_data") #describe DB parameters
	cur = conn.cursor() #connect to DB
	cur.execute("SELECT current_serial FROM control") #look what serial number is going to be charged
	current_serial, = cur.fetchone() #get current serial; comma after current_serial reduces response to value
	command = "SELECT serial_num FROM data WHERE serial_num='" + current_serial + "';" #call table to look into
	if cmd == "control": #try to find serial entered in VI
		try:
			if cur.execute(command):
				cur.close()
				return 1 #found
			else:
				cur.close()
				return 0 #not found
		except:
			return -1 #error during connection
	elif cmd == "charge": #read battery parameters and write to DB found serial number
		cur = conn.cursor()
		cur.execute("SELECT * FROM data WHERE serial_num='" + current_serial + "';") #call for specific S/N
		cur.close()
		batt_param_tmp = [] #create list (array)
		columns = tuple([d[0] for d in cur.description])
		for row in cur:
			batt_param_tmp.append(dict(zip(columns, row))) #append data to list
		batt_param = batt_param_tmp[0] #select first element of list which is battery_parameters dictionary
		return batt_param
	elif cmd == "update":
		volt_aku_cur = str(batt_var["volt_aku_cur"]) #assing float converted to string to temp variable
		charged = str(batt_var["charged"])
		cmd0 = "UPDATE data SET volt_aku_cur='" + volt_aku_cur + "' WHERE serial_num='" + current_serial + "';" #concatenate strings
		cmd1 = "UPDATE data SET charged='" + charged + "' WHERE serial_num='" + current_serial + "';"
		cmd2 = "UPDATE data SET volt_ch='" + str(batt_var["volt_ch"]) + "' WHERE serial_num='" + current_serial + "';"
		cmd3 = "UPDATE data SET I_ch='" + str(batt_var["I_ch"]) + "' WHERE serial_num='" + current_serial + "';"
		cmd4 = "UPDATE data SET chst='" + str(batt_var["chst"]) + "' WHERE serial_num='" + current_serial + "';"
		cur = conn.cursor()
		cur.execute(cmd0) #execute concatenated strings
		cur.execute(cmd1)
		cur.execute(cmd2)
		cur.execute(cmd3)
		cur.execute(cmd4)
		conn.commit()
		cur.close()
	elif cmd == "error": #tell VI that something went wrong with DB
		cur = conn.cursor()
		cur.execute("UPDATE control SET found='False';") #write to DB
		cur.close()

def updater(batt_param): #reads battery parameters and writes them to DB
	uart("output", 0) #disable charger
	time.sleep(5) #wait to stabilize voltage
	battery_raw = os.popen('cat /sys/bus/iio/devices/iio\:device0/in_voltage0_raw').read() #read ADC0 = battery voltage
	battery_vol = float("{:.3f}".format(((float(battery_raw)/4095)*5)*1.622549)) #calculate raw to voltage, 4095 is adc resolution, 5 because of range, 1.622549 is arbitrary number based on manual voltage recalculation
	batt_param["volt_aku_cur"] = battery_vol #current battery voltage
	if (battery_vol >= (int(batt_param["volt_aku"]/2)*1.75)) & (battery_vol < (int(batt_param["volt_aku"]/2)*2.15)): #battery not dead, higher than lower limit and lower than charged state
		batt_param["chst"] = float("{:.3f}".format(battery_vol/((batt_param["volt_aku"]/2)*2.15)*100)) #percentage of battery charge
		batt_param["charged"] = "False" #uncharged
	elif battery_vol < (int(batt_param["volt_aku"]/2)*1.75): #if voltage is lower than lower limit, battery might be dead
		batt_param["chst"] = 0 #make some variable indicating dead battery here
		batt_param["charged"] = "False" #uncharged
	elif battery_vol > (int(batt_param["volt_aku"]/2)*2.15): #if battery is already charged
		batt_param["chst"] = float("{:.3f}".format(battery_vol/((batt_param["volt_aku"]/2)*2.15)*100)) #calculate and set charge percentage
		batt_param["charged"] = "True"
	sqlconn("update", batt_param) #update data in DB
	return batt_param #return read and calculated data // useless in this version

def main():
	#subprocess.call("/home/expand_i2c_pins.sh", shell=True) #export I2C ||| doesn't work
	#subprocess.call("/home/expand_adc_pins", shell=True) #export ADC
	lcd_type = 1 #temporary to set what will be on the LCD; functionality to be expanded
	while True: #main loop
		serial_found = sqlconn("control", "") #call DB for S/N
		if serial_found == 1: #if existing in DB
			batt_param = sqlconn("charge", "") #read battery parameters
			current_set = 0.2 #batt_param["cap"]/10 #calculate charging current
			voltage_set = (int(batt_param["volt_aku"]/2)*2.25) + 1.25 #calculate charging voltage: number of cells * 2,25 V/cell
			uart("voltage", voltage_set) #set voltage
			uart("current", current_set) #set current
			batt_param["I_ch"] = current_set
			batt_param["volt_ch"] = voltage_set
			updater(batt_param) #request parameters update
			lcd(lcd_type, batt_param) #refresh LCD
			if batt_param["perm"] == "y":
				batt_param["perm"] == True
			else:
				batt_param["perm"] == False
			if batt_param["charged"] in [False, "False"]: #permission and uncharged state to enable charging
				uart("output", 1) #enable output
			else:
				uart("output", 0) #disable output
				print "Battery charged"
				sys.exit()
			est_time = 6*(batt_param["cap"]/batt_param["I_ch"])*(100 - batt_param["chst"]) #6(capacitance/charging current)*(100% - charge percent); take 1/10 of the estimated time to prevent overcharge and update data
		elif serial_found == 0: #if not existing
			sqlconn("error", "") #write that error to DB in control table
			print "Error: S/N not found" #print to user
		elif serial_found == -1: #if error in DB call
			sqlconn("error", "") #write to DB in control table
			print "Error: Something went wrong in SQL connection" #print to user
		print "Estimated time: '%s' sec ~= %4.2d min, battery voltage: %s" % (est_time, est_time/60, batt_param["volt_aku_cur"]) #tell the user how much time to wait
		print datetime.now().time()
		time.sleep(est_time) #wait estimated amount of time

if __name__ == '__main__':
	main()

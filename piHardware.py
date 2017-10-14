import RPi.GPIO as GPIO
import time

# Import the PCA9685 module.
import Adafruit_PCA9685

class config:
   window_size=(1920, 1200)

class coinDispense:
     def __init__(self):
        pwm = Adafruit_PCA9685.PCA9685()
        # Configure min and max servo pulse lengths
        servo_min = 370  # Min pulse length out of 4096
        servo_max = 575  # Max pulse length out of 4096
        # Set frequency to 60hz, good for servos.
        pwm.set_pwm_freq(60)


     def dispenseCoin(self,number):
         print("dispense coin:"+str(number))
         for i in range(number):
           print("dispense one coin")
           pwm.set_pwm(0, 0, servo_max)
           time.sleep(1)
           pwm.set_pwm(0, 0, servo_min)
           time.sleep(1)



class hardwareButton:
     def __init__(self):
       GPIO.setmode(GPIO.BCM)
       GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
     def checkButton(self):
        input_state = GPIO.input(18)
        if input_state == False:
            print('Button Pressed')
            time.sleep(0.2)
            return True
        return False

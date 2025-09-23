import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
led = 26
GPIO.setup(led, GPIO.OUT)
state = 1
sens = 6
GPIO.setup(sens, GPIO.IN)
while True:
    if GPIO.input(sens):
        GPIO.output(led, state)
    else:
        GPIO.output(led, not state)
import RPi.GPIO as GPIO


class PWM_DAC:
    def __init__(self, gpio_pin, pwm_frequency, dynamic_range, verbose = False):
        self.gpio_pin = gpio_pin
        self.pwm_frequency = pwm_frequency
        self.dynamic_range = dynamic_range
        self.verbose = verbose
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.gpio_pin, self.pwm_frequency)
        self.pwm.start(0)
        

    def deinit(self):
        GPIO.cleanup()

    def set_voltage(self, voltage):
        if not(0.0 <= voltage <= self.dynamic_range):
            print(f"Напряжение выходит за динамический диапазон ЦАП (0.00 - {self.dynamic_range:.2f}) B")
            print("Устанавливаем 0.0 В")
            return 0
        a = float(voltage/3.29)
        print("bobobo: ")
        print(a)
        self.pwm.ChangeDutyCycle(voltage*100/self.dynamic_range)
    
if __name__ == "__main__":
    try:
        dac = PWM_DAC(12, 500, 3.290, True)
        #print(self.voltage / self.dynamic_range)

        while True:
            try:
                
                voltage = float(input("Введите напряжение в вольтах: "))
                dac.set_voltage(voltage)

            except ValueError:
                print("You num is incorrect. Try again\n")

    finally:
        dac.deinit()
    
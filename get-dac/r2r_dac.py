import RPi.GPIO as GPIO

class R2R_DAC:
    def __init__(self, gpio_bits, dynamic_range, verbose = False):
        self.gpio_bits = gpio_bits
        self.dynamic_range = dynamic_range
        self.verbose = verbose
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_bits, GPIO.OUT, initial = 0)

    def deinit(self):
        GPIO.output(self.gpio_bits, 0)
        GPIO.cleanup()

    def set_number(self, number):
        dec2bin = [int(element) for element in bin(number)[2:].zfill(8)]
        for i in range(len(dec2bin)):
            if dec2bin[i] == 1:
                GPIO.output(self.gpio_bits[i], 1)
            else:
                GPIO.output(self.gpio_bits[i], 0)

    def set_voltage(self, voltage):
        if not(0.0 <= voltage <= self.dynamic_range):
            print(f"Напряжение выходит за динамический диапазон ЦАП (0.00 - {self.dynamic_range:.2f} B")
            print("Устанавливаем 0.0 В")
            return 0
        a = int(voltage / self.dynamic_range * 255)
        self.set_number(a)

if __name__ == "__main__":
    try:
        dac = R2R_DAC([16, 20, 21, 25, 26, 17, 27, 22], 3.16, True)

        while True:
            try:
                voltage = float(input("Введите напряжение в вольтах: "))
                dac.set_voltage(voltage)

            except ValueError:
                print("Вы ввели не то число. Попробуйте ещё раз\n")

    finally:
        dac.deinit()
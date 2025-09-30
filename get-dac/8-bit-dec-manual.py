import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
pins = [16, 20, 21, 25, 26, 17, 27, 22]
GPIO.setup(pins, GPIO.OUT)
GPIO.output(pins, 0)
dynamic_range = 3.3
def voltage_to_number(voltage):
    if not (0.0 <= voltage <= dynamic_range):
        print(f"Напряжениевыходит за динамический диапазон ЦАП (0.0 - {dynamic_range:.2f} В")
        return 0
    return int(voltage / dynamic_range * 255)
def number_to_dac(value):
    return [int(element) for element in bin(value)[2:].zfill(8)]


for i in range(8):
    print(number_to_dac(i))
    if number_to_dac(i) == 1:
        GPIO.output(pins[i], 1)
    else:
        GPIO.output(pins[i], 0)

try:
    while True:
        try:
            voltage = float(input("Введите напряжение в вольтах: "))
            number = voltage_to_number(voltage)
            number_to_dac(number)     
            mass = number_to_dac(number)
            
            print(mass)

            for i in range(8):
                if mass[i] == 1:
                    GPIO.output(pins[i], 1)
                else:
                    GPIO.output(pins[i], 0)



        except ValueError:
            print("Вы ввели не то число. Попробуйте ещё раз\n")
finally:
    GPIO.output(pins, 0)
    GPIO.cleanup()
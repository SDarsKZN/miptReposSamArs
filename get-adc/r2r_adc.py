import RPi.GPIO as GPIO
import time

class R2R_ADC:
    def __init__(self, dynamic_range, compare_time=0.01, verbose=False):
        self.dynamic_range = dynamic_range
        self.verbose = verbose
        self.compare_time = compare_time
        
        self.bits_gpio = [26, 20, 19, 16, 13, 12, 25, 11]
        self.comp_gpio = 21

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.bits_gpio, GPIO.OUT, initial=0)
        GPIO.setup(self.comp_gpio, GPIO.IN)
    
    def __del__(self):
        """Деструктор - выставляет 0 на выход ЦАП и очищает настройки GPIO"""
        GPIO.output(self.bits_gpio, 0)
        GPIO.cleanup()
    
    def number_to_dac(self, number):
        """Подает число number на вход ЦАП"""
        binary = format(number, '08b')
        for i, pin in enumerate(self.bits_gpio):
            GPIO.output(pin, int(binary[i]))
    
    def sequential_counting_adc(self):
        """Последовательный счетный АЦП"""
        max_value = 255  # Максимальное значение для 8-битного ЦАП
        
        for number in range(max_value + 1):
            self.number_to_dac(number)
            time.sleep(self.compare_time)
            
            # Читаем состояние компаратора (0 = U_DAC < U_ADC, 1 = U_DAC > U_ADC)
            comparator_state = GPIO.input(self.comp_gpio)
            
            if self.verbose:
                print(f"Number: {number}, Binary: {format(number, '08b')}, Comparator: {comparator_state}")
            
            # Если напряжение на ЦАП превысило входное напряжение
            if comparator_state == 1:
                return number
        
        # Если не превысило - возвращаем максимальное значение
        return max_value
    
    def get_sc_voltage(self):
        """Возвращает измеренное напряжение в Вольтах"""
        digital_value = self.sequential_counting_adc()
        voltage = (digital_value / 255) * self.dynamic_range
        return voltage


if __name__ == "__main__":
    try:
        # Создаем объект ADC с измеренным динамическим диапазоном
        # ЗАМЕНИТЕ 3.3 на реально измеренное значение напряжения вашего ЦАП!
        adc = R2R_ADC(dynamic_range=3.3, verbose=False)
        
        while True:
            voltage = adc.get_sc_voltage()
            print(f"Измеренное напряжение: {voltage:.2f} В")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nПрограмма завершена пользователем")
    finally:
        # Вызываем деструктор
        if 'adc' in locals():
            adc.__del__()